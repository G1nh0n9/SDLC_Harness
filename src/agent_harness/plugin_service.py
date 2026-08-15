from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .authority import AuthorityDenied, AuthorityRequest, AuthorityStore, VerifiedAuthority
from .candidate import Candidate, CandidateState, CandidateStore
from .evidence import EvidenceLedger, EvidenceRecord, EvidenceStatus
from .methodology import GoalDefinition, KnowledgeStatus, StageKind, WorkflowPlan
from .mission import (
    AgentResult,
    Mission,
    MissionManager,
    ResultDisposition,
    StageGateDenied,
    WorkTask,
)
from .policy import GatePolicy
from .release import ReleaseDecision, ReleaseDisposition, ReleasePackager
from .state_machine import CandidateStateMachine
from .workflow_policy import WorkflowPolicyEngine
from .workflow_state import EventType, WorkflowEventStore
from .workspace import RoleCatalog, RoleProfile, RoleWorkspace, WorkspaceBroker

_MISSION_ID = re.compile(r"^mis-[0-9a-f]{32}$")
_CRITICAL_FIELDS = (
    "decision_action",
    "outcome",
    "analysis_unit",
    "question_type",
    "data_description",
)
_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


class WorkflowPluginError(RuntimeError):
    """Raised when a workflow tool request violates mission policy."""


def _lock_for(path: Path) -> threading.RLock:
    key = os.path.normcase(str(path.resolve(strict=False)))
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.RLock())


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _goal_from_params(
    params: Mapping[str, Any], base: GoalDefinition | None = None
) -> GoalDefinition:
    statement = _optional_text(params.get("goal"))
    if statement is None and base is not None:
        statement = base.statement
    if statement is None:
        raise WorkflowPluginError("goal is required")

    def select(name: str) -> Any:
        if name in params:
            return params[name]
        return getattr(base, name) if base is not None else None

    constraints_value = select("constraints")
    if constraints_value is None:
        constraints: tuple[str, ...] = ()
    elif isinstance(constraints_value, list) and all(
        isinstance(item, str) for item in constraints_value
    ):
        constraints = tuple(item.strip() for item in constraints_value if item.strip())
    else:
        raise WorkflowPluginError("constraints must be an array of strings")

    supplied_status = params.get("field_status", {})
    if not isinstance(supplied_status, Mapping):
        raise WorkflowPluginError("field_status must be an object")
    field_status: dict[str, KnowledgeStatus] = {}
    for name in _CRITICAL_FIELDS:
        if name in supplied_status:
            field_status[name] = KnowledgeStatus(str(supplied_status[name]))
        elif name in params:
            field_status[name] = (
                KnowledgeStatus.CONFIRMED
                if _optional_text(params[name]) is not None
                else KnowledgeStatus.UNVERIFIED
            )
        elif base is not None:
            field_status[name] = base.field_status.get(name, KnowledgeStatus.UNVERIFIED)
        else:
            field_status[name] = KnowledgeStatus.UNVERIFIED

    risk_level = int(select("risk_level") if select("risk_level") is not None else 1)
    if risk_level < 0 or risk_level > 3:
        raise WorkflowPluginError("risk_level must be between 0 and 3")
    research_value = select("research_artifact")
    return GoalDefinition(
        statement=statement,
        decision_action=_optional_text(select("decision_action")),
        outcome=_optional_text(select("outcome")),
        population=_optional_text(select("population")),
        analysis_unit=_optional_text(select("analysis_unit")),
        time_horizon=_optional_text(select("time_horizon")),
        constraints=constraints,
        question_type=_optional_text(select("question_type")),
        data_description=_optional_text(select("data_description")),
        decision_threshold=_optional_text(select("decision_threshold")),
        field_status=field_status,
        risk_level=risk_level,
        research_artifact=bool(research_value) if research_value is not None else False,
    )


class WorkflowPluginService:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve(strict=False)
        self.missions_dir = self.root / "missions"
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self._lock = _lock_for(self.root)

    def start(self, params: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            manager = MissionManager()
            mission = manager.create_mission(_goal_from_params(params))
            policy = WorkflowPolicyEngine.attach_created(
                manager,
                self._event_store(mission.mission_id),
                command_id=f"start:{mission.mission_id}",
            )
            self._ensure_stage_tasks(policy)
            self._save(manager)
            return self._response(manager)

    def status(self, mission_id: str) -> dict[str, Any]:
        with self._lock:
            return self._response(self._load(mission_id))

    def submit_result(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            task_id = str(params.get("task_id", ""))
            task = mission.tasks.get(task_id)
            if task is None:
                raise WorkflowPluginError("unknown task_id")
            self._require_revision(task.revision, params.get("revision"))
            supplied_candidate = _optional_text(params.get("candidate_id"))
            if supplied_candidate != task.candidate_id:
                raise WorkflowPluginError(
                    "result candidate does not match authority-bound task"
                )
            self._reject_role_claims(params)
            authority = self._authorize(task, params, "submit-result")
            payload = params.get("payload")
            if not isinstance(payload, Mapping):
                raise WorkflowPluginError("payload must be an object")
            result = AgentResult.create(
                mission_id=mission_id,
                revision=int(params.get("revision", 0)),
                task_id=task_id,
                stage=task.stage,
                sender_role=authority.role,
                candidate_id=supplied_candidate,
                payload=payload,
                artifact_root=self._workspace_for_task(task, mission.plan).work,
            )
            disposition = policy.receive_result(
                result, command_id=f"{authority.grant_id}:result-received"
            )
            gate_reason: str | None = None
            if disposition is ResultDisposition.ACCEPTED_AS_INPUT:
                try:
                    policy.advance_if_ready(
                        command_id=f"{authority.grant_id}:stage-advance"
                    )
                except StageGateDenied as exc:
                    gate_reason = str(exc)
                if not mission.completed:
                    self._ensure_stage_tasks(policy)
            self._save(manager)
            response = self._response(manager)
            response["disposition"] = disposition.value
            response["gate_reason"] = gate_reason
            return response

    def record_checkpoint(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            self._require_revision(mission.revision, params.get("revision"))
            self._reject_role_claims(params)
            task = self._operation_task(mission, params, "record-checkpoint")
            authority = self._authorize(task, params, "record-checkpoint")
            policy.record_checkpoint(
                task.task_id,
                Path(str(params.get("artifact_path", ""))).expanduser(),
                command_id=f"{authority.grant_id}:checkpoint-recorded",
            )
            return self._response(manager)

    def interrupt_attempt(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            self._require_revision(mission.revision, params.get("revision"))
            self._reject_role_claims(params)
            task = self._operation_task(mission, params, "interrupt-attempt")
            authority = self._authorize(task, params, "interrupt-attempt")
            policy.interrupt_attempt(
                task.task_id,
                str(params.get("reason", "")),
                command_id=f"{authority.grant_id}:attempt-interrupted",
            )
            self._save(manager)
            return self._response(manager)

    def retry_attempt(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            self._require_revision(mission.revision, params.get("revision"))
            self._reject_role_claims(params)
            task = self._operation_task(mission, params, "retry-attempt")
            authority = self._authorize(task, params, "retry-attempt")
            policy.retry_attempt(
                task.task_id,
                str(params.get("retry_class", "")),
                command_id=f"{authority.grant_id}:retry-scheduled",
            )
            self._save(manager)
            return self._response(manager)

    def revise(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        instruction = _optional_text(params.get("instruction"))
        if instruction is None:
            raise WorkflowPluginError("instruction is required")
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            goal = _goal_from_params(params, mission.goal)
            invalidated = 0
            if mission.active_candidate_id is not None:
                ledger = self._evidence_ledger(mission_id)
                records = ledger.records_for(
                    mission_id, mission.revision, mission.active_candidate_id
                )
                for record in records:
                    if ledger.status(record.event_id) is EvidenceStatus.VALID:
                        ledger.invalidate(
                            record.event_id,
                            producer_role="mission-manager",
                            reason=instruction,
                        )
                        invalidated += 1
            next_revision = mission.revision + 1
            policy.apply_user_steering(
                goal,
                instruction,
                command_id=f"revision:{mission_id}:{next_revision}",
            )
            self._ensure_stage_tasks(policy)
            self._save(manager)
            response = self._response(manager)
            response["invalidated_evidence_count"] = invalidated
            return response

    def freeze_candidate(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            self._require_revision(mission.revision, params.get("revision"))
            if mission.current_stage is not StageKind.IMPLEMENTATION:
                raise WorkflowPluginError(
                    "candidate can only be frozen during implementation"
                )
            if mission.active_candidate_id is not None:
                raise WorkflowPluginError("mission already has an active candidate")
            self._reject_role_claims(params)
            task = self._operation_task(mission, params, "freeze-candidate")
            authority = self._authorize(task, params, "freeze-candidate")
            raw_inputs = params.get("inputs")
            if not isinstance(raw_inputs, Mapping) or not raw_inputs:
                raise WorkflowPluginError("inputs must be a non-empty object")
            inputs: dict[str, Path] = {}
            for label, raw_path in raw_inputs.items():
                clean_label = str(label).strip()
                if not clean_label or "/" in clean_label or "\\" in clean_label:
                    raise WorkflowPluginError("input labels must be simple names")
                inputs[clean_label] = Path(str(raw_path)).expanduser()
            raw_toolchain = params.get("toolchain")
            if not isinstance(raw_toolchain, Mapping):
                raise WorkflowPluginError("toolchain must be an object")
            toolchain = {str(key): str(value) for key, value in raw_toolchain.items()}
            required_evidence = {"acceptance-test"}
            if mission.goal.risk_level >= 2:
                required_evidence.add("security-review")
            required_evidence.update(
                claim.value for claim in mission.plan.required_assurance_claims
            )
            store = self._candidate_store(mission_id)
            candidate = store.freeze_candidate(
                mission_id=mission_id,
                revision=mission.revision,
                inputs=inputs,
                toolchain=toolchain,
                required_evidence=required_evidence,
                parent_candidate_id=_optional_text(params.get("parent_candidate_id")),
                created_by_role=authority.role,
            )
            if not store.verify(candidate.candidate_id):
                store.save_state(candidate)
                raise WorkflowPluginError("candidate snapshot verification failed")
            policy.bind_candidate(
                candidate.candidate_id,
                candidate.manifest_sha256,
                command_id=f"{authority.grant_id}:candidate-frozen",
            )
            self._save(manager)
            response = self._response(manager)
            response.update(
                {
                    "candidate_id": candidate.candidate_id,
                    "candidate_state": candidate.state.value,
                    "required_evidence": list(candidate.manifest["required_evidence"]),
                }
            )
            return response

    def record_evidence(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            self._require_revision(mission.revision, params.get("revision"))
            candidate_id = str(params.get("candidate_id", ""))
            if mission.active_candidate_id != candidate_id:
                raise WorkflowPluginError("evidence candidate does not match active candidate")
            self._reject_role_claims(params)
            task = self._operation_task(mission, params, "record-evidence")
            authority = self._authorize(task, params, "record-evidence")
            producer_role = authority.role
            assigned_roles = {
                role for stage in mission.plan.stages for role in stage.roles
            }
            if producer_role not in assigned_roles or producer_role == "mission-manager":
                raise WorkflowPluginError("evidence producer is not an assigned expert role")
            outcome = str(params.get("outcome", ""))
            if outcome not in {"pass", "fail"}:
                raise WorkflowPluginError("evidence outcome must be pass or fail")
            artifact_path = Path(str(params.get("artifact_path", ""))).expanduser()
            try:
                resolved_artifact = artifact_path.resolve(strict=True)
            except OSError as exc:
                raise WorkflowPluginError("evidence artifact does not exist") from exc
            if not resolved_artifact.is_file() or resolved_artifact.is_symlink():
                raise WorkflowPluginError("evidence artifact must be a real file")
            details = params.get("details", {})
            if not isinstance(details, Mapping):
                raise WorkflowPluginError("evidence details must be an object")
            evaluation_fields: dict[str, list[Mapping[str, Any]]] = {}
            for field in ("expected_results", "decision_rules", "observations"):
                entries = params.get(field)
                if not isinstance(entries, list) or not entries or any(
                    not isinstance(entry, Mapping) for entry in entries
                ):
                    raise WorkflowPluginError(f"evidence {field} must be a non-empty array")
                evaluation_fields[field] = list(entries)
            store, candidate = self._verified_candidate(mission, candidate_id)
            evidence_type = str(params.get("evidence_type", ""))
            allowed_roles = self._allowed_evidence_roles(
                mission.plan, evidence_type, set(candidate.manifest["required_evidence"])
            )
            if producer_role not in allowed_roles:
                raise WorkflowPluginError(
                    "producer_role is not allowed for this evidence type"
                )
            if candidate.state is CandidateState.FROZEN:
                CandidateStateMachine().transition(candidate, CandidateState.VERIFYING)
                store.save_state(candidate)
            ledger = self._evidence_ledger(mission_id)
            record = ledger.append(
                mission_id=mission_id,
                revision=mission.revision,
                candidate_id=candidate_id,
                evidence_type=evidence_type,
                producer_role=producer_role,
                outcome=outcome,
                artifact_path=resolved_artifact,
                expected_results=evaluation_fields["expected_results"],
                decision_rules=evaluation_fields["decision_rules"],
                observations=evaluation_fields["observations"],
                details=dict(details),
            )
            policy.record_event(
                EventType.EVIDENCE_RECORDED,
                {
                    "candidate_id": candidate_id,
                    "evidence_event_id": record.event_id,
                    "evidence_type": evidence_type,
                    "artifact_sha256": record.artifact_sha256,
                },
                command_id=f"{authority.grant_id}:evidence-recorded",
            )
            return {
                **self._response(manager),
                "candidate_id": candidate_id,
                "candidate_state": candidate.state.value,
                "evidence_event_id": record.event_id,
                "evidence_status": ledger.status(record.event_id).value,
                "ledger_chain_valid": ledger.verify_chain(),
            }

    def approve_candidate(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            self._require_revision(mission.revision, params.get("revision"))
            candidate_id = str(params.get("candidate_id", ""))
            self._reject_role_claims(params)
            task = self._operation_task(mission, params, "approve-candidate")
            if mission.active_candidate_id != candidate_id:
                raise WorkflowPluginError(
                    "approval candidate does not match active candidate"
                )
            if mission.current_stage is not StageKind.VALIDATION:
                raise WorkflowPluginError(
                    "candidate approval is only accepted during validation"
                )

            store, candidate = self._verified_candidate(mission, candidate_id)
            self._verify_evidence_artifacts(candidate, self._evidence_ledger(mission_id))
            if candidate.state is CandidateState.VERIFYING:
                CandidateStateMachine().transition(candidate, CandidateState.REVIEWING)
            role_catalog = RoleCatalog.default()
            for stage in mission.plan.stages:
                for role in stage.roles:
                    role_catalog.register_dynamic_role(
                        role,
                        can_execute_commands=stage.kind
                        in {
                            StageKind.IMPLEMENTATION,
                            StageKind.INTEGRATION_VERIFICATION,
                            StageKind.RELEASE,
                        },
                        can_approve=stage.kind is StageKind.VALIDATION,
                    )
            evidence_roles = {
                evidence_type: self._allowed_evidence_roles(
                    mission.plan,
                    evidence_type,
                    set(candidate.manifest["required_evidence"]),
                )
                for evidence_type in candidate.manifest["required_evidence"]
            }
            decision = GatePolicy(
                role_catalog=role_catalog,
                evidence_roles=evidence_roles,
            ).approve(
                candidate,
                self._evidence_ledger(mission_id),
                authority_store=self._authority_store(mission_id),
                authority_token=str(params.get("authority_token", "")),
                authority_request=self._authority_request(task, "approve-candidate"),
                expected_mission_id=mission.mission_id,
                expected_revision=mission.revision,
            )
            store.save_state(candidate)
            policy.mark_candidate_approved(
                candidate_id,
                command_id=f"{decision.authority_grant_id}:quality-decided",
            )
            gate_reason = self._try_advance(
                policy, command_id=f"{decision.authority_grant_id}:stage-advance"
            )
            if not mission.completed:
                self._ensure_stage_tasks(policy)
            self._save(manager)
            return {
                **self._response(manager),
                "candidate_id": candidate_id,
                "candidate_state": candidate.state.value,
                "approved_evidence": sorted(decision.evidence_types),
                "gate_reason": gate_reason,
            }

    def package_release(self, params: Mapping[str, Any]) -> dict[str, Any]:
        mission_id = self._mission_id(params.get("mission_id"))
        with self._lock:
            manager = self._load(mission_id)
            policy = self._policy(manager)
            mission = manager.current_mission
            self._require_revision(mission.revision, params.get("revision"))
            candidate_id = str(params.get("candidate_id", ""))
            self._reject_role_claims(params)
            task = self._operation_task(mission, params, "package-release")
            if mission.active_candidate_id != candidate_id:
                raise WorkflowPluginError(
                    "release candidate does not match active candidate"
                )
            if mission.current_stage is not StageKind.RELEASE:
                raise WorkflowPluginError(
                    "release package can only be created during release"
                )
            authority = self._authorize(task, params, "package-release")
            store, candidate = self._verified_candidate(mission, candidate_id)
            self._verify_release_evidence(
                candidate, self._evidence_ledger(mission_id)
            )
            try:
                decision = ReleaseDecision(
                    disposition=ReleaseDisposition(str(params.get("disposition", ""))),
                    reasons=tuple(str(item) for item in params.get("reasons", ())),
                    scope=str(params["scope"]) if params.get("scope") else None,
                    expires_at=(
                        str(params["expires_at"]) if params.get("expires_at") else None
                    ),
                    rollback_plan=(
                        str(params["rollback_plan"])
                        if params.get("rollback_plan")
                        else None
                    ),
                    out_of_scope_controls=tuple(
                        str(item) for item in params.get("out_of_scope_controls", ())
                    ),
                )
            except ValueError as exc:
                raise WorkflowPluginError(str(exc)) from exc
            release = ReleasePackager().package(
                candidate,
                self._mission_data_root(mission_id) / "release",
                decision=decision,
                expected_mission_id=mission.mission_id,
                expected_revision=mission.revision,
            )
            store.save_state(candidate)
            policy.bind_release(
                candidate_id,
                release.sha256,
                command_id=f"{authority.grant_id}:package-created",
            )
            gate_reason = self._try_advance(
                policy, command_id=f"{authority.grant_id}:stage-advance"
            )
            if not mission.completed:
                self._ensure_stage_tasks(policy)
            self._save(manager)
            return {
                **self._response(manager),
                "candidate_id": candidate_id,
                "candidate_state": candidate.state.value,
                "release_path": str(release.path),
                "release_sha256": release.sha256,
                "release_disposition": release.decision.disposition.value,
                "gate_reason": gate_reason,
            }

    def _mission_data_root(self, mission_id: str) -> Path:
        path = self.root / "mission-data" / self._mission_id(mission_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _candidate_store(self, mission_id: str) -> CandidateStore:
        return CandidateStore(self._mission_data_root(mission_id) / "candidate-store")

    def _verified_candidate(
        self, mission: Mission, candidate_id: str
    ) -> tuple[CandidateStore, Candidate]:
        binding = mission.output_bindings.get("frozen-candidate")
        if binding is None or binding.reference != candidate_id:
            raise WorkflowPluginError("candidate manifest binding is unavailable")
        store = self._candidate_store(mission.mission_id)
        try:
            candidate = store.get(candidate_id)
        except (KeyError, OSError, ValueError) as exc:
            raise WorkflowPluginError("candidate manifest binding cannot be verified") from exc
        if not store.verify(
            candidate_id, expected_manifest_sha256=binding.sha256
        ):
            store.save_state(candidate)
            raise WorkflowPluginError("candidate manifest binding does not match")
        if (
            candidate.mission_id != mission.mission_id
            or candidate.revision != mission.revision
        ):
            raise WorkflowPluginError("candidate manifest binding has stale provenance")
        return store, candidate

    def _evidence_ledger(self, mission_id: str) -> EvidenceLedger:
        return EvidenceLedger(self._mission_data_root(mission_id) / "evidence.sqlite3")

    def _authority_store(self, mission_id: str) -> AuthorityStore:
        return AuthorityStore(self._mission_data_root(mission_id) / "authority.sqlite3")

    def _event_store(self, mission_id: str) -> WorkflowEventStore:
        return WorkflowEventStore(self._mission_data_root(mission_id) / "workflow.sqlite3")

    def _policy(self, manager: MissionManager) -> WorkflowPolicyEngine:
        store = self._event_store(manager.current_mission.mission_id)
        if not store.verify_chain(manager.current_mission.mission_id):
            raise WorkflowPluginError("workflow event hash chain is invalid")
        return WorkflowPolicyEngine(manager, store)

    @staticmethod
    def _reject_role_claims(params: Mapping[str, Any]) -> None:
        forbidden = {"role", "producer_role", "reviewer_role", "created_by_role"}
        if forbidden & set(params):
            raise WorkflowPluginError(
                "caller-supplied role identity is forbidden; use an authority grant"
            )

    @staticmethod
    def _operations_for_task(task: WorkTask) -> tuple[str, ...]:
        if task.status == "interrupted":
            return ("retry-attempt",)
        operations = ["submit-result", "record-checkpoint", "interrupt-attempt"]
        if task.stage is StageKind.IMPLEMENTATION:
            operations.append("freeze-candidate")
        if task.stage is StageKind.INTEGRATION_VERIFICATION:
            operations.append("record-evidence")
        if task.stage is StageKind.VALIDATION:
            operations.extend(("record-evidence", "approve-candidate"))
        if task.stage is StageKind.RELEASE:
            operations.append("package-release")
        return tuple(operations)

    def _operation_task(
        self, mission: Mission, params: Mapping[str, Any], operation: str
    ) -> WorkTask:
        task_id = str(params.get("task_id", ""))
        task = mission.tasks.get(task_id)
        if (
            task is None
            or task.revision != mission.revision
            or task.stage is not mission.current_stage
            or operation not in self._operations_for_task(task)
        ):
            raise WorkflowPluginError("task is not authorized for this operation")
        return task

    @staticmethod
    def _authority_request(task: WorkTask, operation: str) -> AuthorityRequest:
        return AuthorityRequest(
            mission_id=task.mission_id,
            revision=task.revision,
            task_id=task.task_id,
            attempt_id=task.attempt_id,
            worker_id=task.worker_id,
            workspace_id=task.workspace_id,
            candidate_id=task.candidate_id,
            role=task.assignee_role,
            operation=operation,
            tool=None,
        )

    def _authorize(
        self, task: WorkTask, params: Mapping[str, Any], operation: str
    ) -> VerifiedAuthority:
        try:
            return self._authority_store(task.mission_id).consume(
                str(params.get("authority_token", "")),
                self._authority_request(task, operation),
            )
        except AuthorityDenied as exc:
            raise WorkflowPluginError(str(exc)) from exc

    @staticmethod
    def _require_revision(current: int, supplied: Any) -> None:
        if int(supplied or 0) != current:
            raise WorkflowPluginError("result revision is not current")

    @staticmethod
    def _allowed_evidence_roles(
        plan: WorkflowPlan, evidence_type: str, required_evidence: set[str]
    ) -> set[str]:
        if evidence_type == "acceptance-test":
            return set(plan.stage(StageKind.INTEGRATION_VERIFICATION).roles)
        if evidence_type == "security-review":
            return {
                role
                for role in plan.stage(StageKind.VALIDATION).roles
                if role in {"independent-code-reviewer", "independent-spec-reviewer"}
            }
        if evidence_type in required_evidence:
            return set(plan.stage(StageKind.VALIDATION).roles)
        return {role for stage in plan.stages for role in stage.roles} - {
            "mission-manager"
        }

    def _verify_evidence_artifacts(
        self, candidate: Candidate, ledger: EvidenceLedger
    ) -> None:
        required = set(candidate.manifest["required_evidence"])
        records = ledger.records_for(
            candidate.mission_id, candidate.revision, candidate.candidate_id
        )
        latest_by_type = {}
        for record in records:
            latest_by_type[record.evidence_type] = record
        for evidence_type in sorted(required):
            latest_record = latest_by_type.get(evidence_type)
            if (
                latest_record is not None
                and latest_record.outcome == "pass"
                and ledger.status(latest_record.event_id) is EvidenceStatus.VALID
                and not self._evidence_artifact_matches(latest_record)
            ):
                raise WorkflowPluginError(
                    f"evidence artifact verification failed: {evidence_type}"
                )

    def _verify_release_evidence(
        self, candidate: Candidate, ledger: EvidenceLedger
    ) -> None:
        if not ledger.verify_chain():
            raise WorkflowPluginError("evidence ledger hash chain is invalid")
        records = ledger.records_for(
            candidate.mission_id, candidate.revision, candidate.candidate_id
        )
        latest_by_type = {}
        for record in records:
            latest_by_type[record.evidence_type] = record
        fresh_types = {
            record.evidence_type
            for record in latest_by_type.values()
            if record.outcome == "pass"
            and ledger.status(record.event_id) is EvidenceStatus.VALID
        }
        missing = set(candidate.manifest["required_evidence"]) - fresh_types
        if missing:
            raise WorkflowPluginError(
                f"missing fresh passing evidence: {', '.join(sorted(missing))}"
            )
        self._verify_evidence_artifacts(candidate, ledger)

    def _evidence_artifact_matches(self, record: EvidenceRecord) -> bool:
        raw_path = record.details.get("artifact_path")
        if not isinstance(raw_path, str) or not raw_path:
            return False
        try:
            path = Path(raw_path).resolve(strict=True)
        except OSError:
            return False
        return (
            path.is_file()
            and not path.is_symlink()
            and self._sha256_file(path) == record.artifact_sha256
        )

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _try_advance(
        policy: WorkflowPolicyEngine, *, command_id: str
    ) -> str | None:
        try:
            policy.advance_if_ready(command_id=command_id)
        except StageGateDenied as exc:
            return str(exc)
        return None

    def _mission_id(self, value: Any) -> str:
        mission_id = str(value or "")
        if not _MISSION_ID.fullmatch(mission_id):
            raise WorkflowPluginError("invalid mission_id")
        return mission_id

    def _path(self, mission_id: str) -> Path:
        return self.missions_dir / f"{self._mission_id(mission_id)}.json"

    def _load(self, mission_id: str) -> MissionManager:
        path = self._path(mission_id)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise WorkflowPluginError("mission not found") from exc
        except json.JSONDecodeError as exc:
            raise WorkflowPluginError("mission state is not valid JSON") from exc
        if not isinstance(raw, Mapping):
            raise WorkflowPluginError("mission state must be an object")
        return MissionManager.restore(raw)

    def _save(self, manager: MissionManager) -> None:
        path = self._path(manager.current_mission.mission_id)
        temporary = path.with_suffix(".json.tmp")
        data = json.dumps(manager.snapshot(), sort_keys=True, ensure_ascii=False, indent=2)
        temporary.write_text(data + "\n", encoding="utf-8")
        os.replace(temporary, path)

    @staticmethod
    def _ensure_stage_tasks(policy: WorkflowPolicyEngine) -> None:
        manager = policy.manager
        mission = manager.current_mission
        if mission.completed:
            return
        stage = mission.current_stage
        roles = mission.plan.stage(stage).roles - {"mission-manager"}
        for role in sorted(roles):
            exists = any(
                task.revision == mission.revision
                and task.stage is stage
                and task.assignee_role == role
                and task.status not in {"stale", "superseded"}
                for task in mission.tasks.values()
            )
            if not exists:
                policy.issue_task(
                    stage,
                    role,
                    command_id=(
                        f"task:{mission.mission_id}:{mission.revision}:{stage.value}:{role}"
                    ),
                )

    def _workspace_for_task(self, task: WorkTask, plan: WorkflowPlan) -> RoleWorkspace:
        permission = plan.stage(task.stage).role_permissions[task.assignee_role]
        profile = RoleProfile(
            name=task.assignee_role,
            tools=permission.tools,
            writable_areas=permission.writable_areas,
            network_allowed=permission.network_allowed,
            can_execute_commands=permission.can_execute_commands,
            can_approve=permission.can_approve,
        )
        catalog = RoleCatalog({task.assignee_role: profile})
        return WorkspaceBroker(self.root / "workspaces", catalog).create(
            mission_id=task.mission_id,
            revision=task.revision,
            task_id=task.task_id,
            role=task.assignee_role,
        )

    def _task_response(self, task: WorkTask, mission: Mission) -> dict[str, Any]:
        plan = mission.plan
        workspace = self._workspace_for_task(task, plan)
        authority_store = self._authority_store(task.mission_id)
        grants: dict[str, Any] = {}
        for operation in self._operations_for_task(task):
            authority_store.revoke_issued(task_id=task.task_id, operation=operation)
            grant = authority_store.issue(
                mission_id=task.mission_id,
                revision=task.revision,
                task_id=task.task_id,
                attempt_id=task.attempt_id,
                worker_id=task.worker_id,
                workspace_id=task.workspace_id,
                candidate_id=task.candidate_id,
                role=task.assignee_role,
                allowed_operations={operation},
                allowed_tools=set(),
                expires_at=datetime.now(UTC) + timedelta(minutes=15),
            )
            grants[operation] = {
                "grant_id": grant.grant_id,
                "token": grant.token,
                "expires_at": grant.expires_at.isoformat(),
                "max_uses": grant.max_uses,
            }
        candidate_snapshot: str | None = None
        if task.candidate_id is not None:
            _store, candidate = self._verified_candidate(mission, task.candidate_id)
            candidate_snapshot = str(candidate.snapshot_root)
        return {
            "task_id": task.task_id,
            "role": task.assignee_role,
            "stage": task.stage.value,
            "revision": task.revision,
            "candidate_id": task.candidate_id,
            "candidate_snapshot": candidate_snapshot,
            "status": task.status,
            "attempt_id": task.attempt_id,
            "worker_id": task.worker_id,
            "workspace_id": task.workspace_id,
            "authority_grants": grants,
            "required_inputs": sorted(plan.stage(task.stage).required_inputs),
            "required_outputs": sorted(plan.stage(task.stage).required_outputs),
            "input_bindings": {
                output_id: {
                    "kind": mission.output_bindings[output_id].kind.value,
                    "reference": mission.output_bindings[output_id].reference,
                    "sha256": mission.output_bindings[output_id].sha256,
                }
                for output_id in sorted(plan.stage(task.stage).required_inputs)
            },
            "workspace": {
                "root": str(workspace.root),
                "work": str(workspace.work),
                "build": str(workspace.build),
                "tmp": str(workspace.tmp),
                "home": str(workspace.home),
                "inputs": str(workspace.inputs),
            },
            "permissions": {
                "tools": sorted(workspace.profile.tools),
                "writable_areas": sorted(workspace.profile.writable_areas),
                "network_allowed": workspace.profile.network_allowed,
                "can_execute_commands": workspace.profile.can_execute_commands,
                "can_approve": workspace.profile.can_approve,
            },
        }

    def _response(self, manager: MissionManager) -> dict[str, Any]:
        mission = manager.current_mission
        event_store = self._event_store(mission.mission_id)
        events = event_store.events(mission.mission_id)
        if not event_store.verify_chain(mission.mission_id):
            raise WorkflowPluginError("workflow event hash chain is invalid")
        projection = WorkflowPolicyEngine(manager, event_store).projection()
        expected_stage = None if mission.completed else mission.current_stage.value
        if (
            projection.revision != mission.revision
            or projection.current_stage != expected_stage
            or projection.completed != mission.completed
        ):
            raise WorkflowPluginError("mission snapshot does not match event projection")
        current_tasks = [
            self._task_response(task, mission)
            for task in mission.tasks.values()
            if not mission.completed
            and task.revision == mission.revision
            and task.stage is mission.current_stage
            and task.status not in {"stale", "superseded", "completed"}
        ]
        return {
            "mission_id": mission.mission_id,
            "revision": mission.revision,
            "track": mission.plan.track.value,
            "current_stage": None if mission.completed else mission.current_stage.value,
            "completed": mission.completed,
            "active_candidate_id": mission.active_candidate_id,
            "candidate_approved": mission.candidate_approved,
            "release_artifact_sha256": mission.release_artifact_sha256,
            "workflow_event_count": len(events),
            "workflow_event_chain_valid": True,
            "reasons": list(mission.plan.reasons),
            "required_assurance_claims": sorted(
                claim.value for claim in mission.plan.required_assurance_claims
            ),
            "stages": [
                {
                    "kind": stage.kind.value,
                    "roles": sorted(stage.roles),
                }
                for stage in mission.plan.stages
            ],
            "tasks": sorted(current_tasks, key=lambda item: (item["role"], item["task_id"])),
            "steering_log": list(mission.steering_log),
        }
