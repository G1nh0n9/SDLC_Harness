from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from .handoff import ArtifactMismatch, HandoffValidator, SchemaViolation
from .methodology import (
    GoalDefinition,
    KnowledgeStatus,
    MethodologyPlanner,
    StageKind,
    WorkflowPlan,
)


def _payload_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class OutputKind(StrEnum):
    STRUCTURED = "structured"
    ARTIFACT = "artifact"
    CANDIDATE = "candidate"
    POLICY_DECISION = "policy-decision"
    RELEASE_ARTIFACT = "release-artifact"


@dataclass(frozen=True)
class OutputBinding:
    output_id: str
    kind: OutputKind
    reference: str
    sha256: str


def _initial_output_bindings(
    goal: GoalDefinition, plan: WorkflowPlan
) -> dict[str, OutputBinding]:
    goal_payload = {
        "statement": goal.statement,
        "decision_action": goal.decision_action,
        "outcome": goal.outcome,
        "population": goal.population,
        "analysis_unit": goal.analysis_unit,
        "time_horizon": goal.time_horizon,
        "constraints": list(goal.constraints),
        "question_type": goal.question_type,
        "data_description": goal.data_description,
        "decision_threshold": goal.decision_threshold,
    }
    goal_hash = _payload_hash(goal_payload)
    outputs = {
        "goal-draft": OutputBinding(
            "goal-draft", OutputKind.STRUCTURED, "mission-goal", goal_hash
        )
    }
    if StageKind.GOAL_DISCOVERY not in plan.stage_kinds:
        outputs["goal-definition"] = OutputBinding(
            "goal-definition", OutputKind.STRUCTURED, "mission-goal", goal_hash
        )
    if StageKind.METHOD_DISCOVERY not in plan.stage_kinds:
        method_hash = _payload_hash(
            {"track": plan.track.value, "reasons": list(plan.reasons)}
        )
        outputs["method-decision"] = OutputBinding(
            "method-decision", OutputKind.STRUCTURED, "workflow-plan", method_hash
        )
    return outputs


def _optional_text(value: Any) -> str | None:
    return str(value) if value is not None else None


class ResultDisposition(StrEnum):
    ACCEPTED_AS_INPUT = "accepted-as-input"
    QUARANTINED_FOREIGN_MISSION = "quarantined-foreign-mission"
    QUARANTINED_STALE_REVISION = "quarantined-stale-revision"
    REJECTED_UNEXPECTED_TASK = "rejected-unexpected-task"
    REJECTED_INVALID_PAYLOAD = "rejected-invalid-payload"


class StageGateDenied(RuntimeError):
    """Raised when the current stage lacks a required passing result or artifact."""


@dataclass
class WorkTask:
    task_id: str
    mission_id: str
    revision: int
    stage: StageKind
    assignee_role: str
    candidate_id: str | None
    attempt_id: str
    worker_id: str
    workspace_id: str
    status: str = "issued"


@dataclass(frozen=True)
class AgentResult:
    mission_id: str
    revision: int
    task_id: str
    stage: StageKind
    sender_role: str
    candidate_id: str | None
    payload: Mapping[str, Any]
    payload_sha256: str
    artifact_root: Path

    @classmethod
    def create(
        cls,
        *,
        mission_id: str,
        revision: int,
        task_id: str,
        stage: StageKind,
        sender_role: str,
        candidate_id: str | None,
        payload: Mapping[str, Any],
        artifact_root: Path,
    ) -> AgentResult:
        return cls(
            mission_id=mission_id,
            revision=revision,
            task_id=task_id,
            stage=stage,
            sender_role=sender_role,
            candidate_id=candidate_id,
            payload=dict(payload),
            payload_sha256=_payload_hash(payload),
            artifact_root=artifact_root.resolve(),
        )

    def has_valid_hash(self) -> bool:
        return self.payload_sha256 == _payload_hash(self.payload)

    def handoff_document(self) -> dict[str, Any]:
        return {
            "schema_version": "2.0",
            "document_type": "work-order-result",
            "mission_id": self.mission_id,
            "revision": self.revision,
            "task_id": self.task_id,
            "stage": self.stage.value,
            "candidate_id": self.candidate_id,
            "sender_role": self.sender_role,
            "receiver_role": "mission-manager",
            "claims": self.payload.get("claims"),
            "expected_results": self.payload.get("expected_results"),
            "decision_rules": self.payload.get("decision_rules"),
            "observations": self.payload.get("observations"),
            "decision": self.payload.get("decision"),
            "assumptions": self.payload.get("assumptions"),
            "unresolved": self.payload.get("unresolved"),
            "artifacts": self.payload.get("artifacts"),
        }

    def has_valid_handoff(self) -> bool:
        document = self.handoff_document()
        try:
            HandoffValidator().validate_and_verify(document, self.artifact_root)
        except (ArtifactMismatch, SchemaViolation, OSError, ValueError):
            return False
        decision = document.get("decision")
        if not isinstance(decision, Mapping):
            return False
        return self.payload.get("gate") == decision.get("outcome")


@dataclass
class Mission:
    mission_id: str
    revision: int
    goal: GoalDefinition
    plan: WorkflowPlan
    current_stage_index: int = 0
    tasks: dict[str, WorkTask] = field(default_factory=dict)
    accepted_results: list[AgentResult] = field(default_factory=list)
    output_bindings: dict[str, OutputBinding] = field(default_factory=dict)
    steering_log: list[str] = field(default_factory=list)
    active_candidate_id: str | None = None
    candidate_approved: bool = False
    release_artifact_sha256: str | None = None
    completed: bool = False

    @property
    def current_stage(self) -> StageKind:
        return self.plan.stages[self.current_stage_index].kind

    @property
    def available_outputs(self) -> set[str]:
        return set(self.output_bindings)


class MissionManager:
    def __init__(self, planner: MethodologyPlanner | None = None) -> None:
        self._planner = planner or MethodologyPlanner()
        self._missions: dict[str, Mission] = {}
        self._current_mission_id: str | None = None
        self._inbox: list[AgentResult] = []

    @property
    def current_mission(self) -> Mission:
        if self._current_mission_id is None:
            raise RuntimeError("no current mission")
        return self._missions[self._current_mission_id]

    @property
    def inbox_size(self) -> int:
        return len(self._inbox)

    def create_mission(self, goal: GoalDefinition) -> Mission:
        plan = self._planner.plan(goal)
        mission = Mission(
            mission_id=f"mis-{uuid.uuid4().hex}",
            revision=1,
            goal=goal,
            plan=plan,
            output_bindings=_initial_output_bindings(goal, plan),
        )
        self._missions[mission.mission_id] = mission
        self._current_mission_id = mission.mission_id
        return mission

    def snapshot(self) -> dict[str, Any]:
        mission = self.current_mission
        return {
            "format_version": 1,
            "mission_id": mission.mission_id,
            "revision": mission.revision,
            "goal": {
                "statement": mission.goal.statement,
                "decision_action": mission.goal.decision_action,
                "outcome": mission.goal.outcome,
                "population": mission.goal.population,
                "analysis_unit": mission.goal.analysis_unit,
                "time_horizon": mission.goal.time_horizon,
                "constraints": list(mission.goal.constraints),
                "question_type": mission.goal.question_type,
                "data_description": mission.goal.data_description,
                "decision_threshold": mission.goal.decision_threshold,
                "field_status": {
                    name: status.value for name, status in mission.goal.field_status.items()
                },
                "risk_level": mission.goal.risk_level,
                "research_artifact": mission.goal.research_artifact,
            },
            "current_stage_index": mission.current_stage_index,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "mission_id": task.mission_id,
                    "revision": task.revision,
                    "stage": task.stage.value,
                    "assignee_role": task.assignee_role,
                    "candidate_id": task.candidate_id,
                    "attempt_id": task.attempt_id,
                    "worker_id": task.worker_id,
                    "workspace_id": task.workspace_id,
                    "status": task.status,
                }
                for task in mission.tasks.values()
            ],
            "accepted_results": [
                {
                    "mission_id": result.mission_id,
                    "revision": result.revision,
                    "task_id": result.task_id,
                    "stage": result.stage.value,
                    "sender_role": result.sender_role,
                    "candidate_id": result.candidate_id,
                    "payload": dict(result.payload),
                    "payload_sha256": result.payload_sha256,
                    "artifact_root": str(result.artifact_root),
                }
                for result in mission.accepted_results
            ],
            "output_bindings": {
                output_id: {
                    "kind": binding.kind.value,
                    "reference": binding.reference,
                    "sha256": binding.sha256,
                }
                for output_id, binding in sorted(mission.output_bindings.items())
            },
            "steering_log": list(mission.steering_log),
            "active_candidate_id": mission.active_candidate_id,
            "candidate_approved": mission.candidate_approved,
            "release_artifact_sha256": mission.release_artifact_sha256,
            "completed": mission.completed,
        }

    @classmethod
    def restore(
        cls,
        snapshot: Mapping[str, Any],
        planner: MethodologyPlanner | None = None,
    ) -> MissionManager:
        if snapshot.get("format_version") != 1:
            raise ValueError("unsupported mission snapshot format")
        raw_goal = snapshot.get("goal")
        if not isinstance(raw_goal, Mapping):
            raise ValueError("mission snapshot has no goal")
        raw_status = raw_goal.get("field_status", {})
        if not isinstance(raw_status, Mapping):
            raise ValueError("goal field_status must be an object")
        goal = GoalDefinition(
            statement=str(raw_goal.get("statement", "")),
            decision_action=_optional_text(raw_goal.get("decision_action")),
            outcome=_optional_text(raw_goal.get("outcome")),
            population=_optional_text(raw_goal.get("population")),
            analysis_unit=_optional_text(raw_goal.get("analysis_unit")),
            time_horizon=_optional_text(raw_goal.get("time_horizon")),
            constraints=tuple(str(item) for item in raw_goal.get("constraints", [])),
            question_type=_optional_text(raw_goal.get("question_type")),
            data_description=_optional_text(raw_goal.get("data_description")),
            decision_threshold=_optional_text(raw_goal.get("decision_threshold")),
            field_status={
                str(name): KnowledgeStatus(str(value)) for name, value in raw_status.items()
            },
            risk_level=int(raw_goal.get("risk_level", 1)),
            research_artifact=bool(raw_goal.get("research_artifact", False)),
        )
        manager = cls(planner)
        plan = manager._planner.plan(goal)
        raw_bindings = snapshot.get("output_bindings")
        output_bindings = _initial_output_bindings(goal, plan)
        if isinstance(raw_bindings, Mapping):
            output_bindings = {}
            for output_id, raw_binding in raw_bindings.items():
                if not isinstance(raw_binding, Mapping):
                    raise ValueError("output binding must be an object")
                output_bindings[str(output_id)] = OutputBinding(
                    output_id=str(output_id),
                    kind=OutputKind(str(raw_binding["kind"])),
                    reference=str(raw_binding["reference"]),
                    sha256=str(raw_binding["sha256"]),
                )
        mission = Mission(
            mission_id=str(snapshot["mission_id"]),
            revision=int(snapshot["revision"]),
            goal=goal,
            plan=plan,
            current_stage_index=int(snapshot.get("current_stage_index", 0)),
            steering_log=[str(item) for item in snapshot.get("steering_log", [])],
            active_candidate_id=_optional_text(snapshot.get("active_candidate_id")),
            candidate_approved=bool(snapshot.get("candidate_approved", False)),
            release_artifact_sha256=_optional_text(
                snapshot.get("release_artifact_sha256")
            ),
            completed=bool(snapshot.get("completed", False)),
            output_bindings=output_bindings,
        )
        for raw_task in snapshot.get("tasks", []):
            if not isinstance(raw_task, Mapping):
                raise ValueError("task snapshot must be an object")
            task = WorkTask(
                task_id=str(raw_task["task_id"]),
                mission_id=str(raw_task["mission_id"]),
                revision=int(raw_task["revision"]),
                stage=StageKind(str(raw_task["stage"])),
                assignee_role=str(raw_task["assignee_role"]),
                candidate_id=_optional_text(raw_task.get("candidate_id")),
                attempt_id=str(
                    raw_task.get("attempt_id", f"attempt-{raw_task['task_id']}")
                ),
                worker_id=str(
                    raw_task.get(
                        "worker_id",
                        f"expert:{raw_task['stage']}:{raw_task['assignee_role']}",
                    )
                ),
                workspace_id=str(
                    raw_task.get("workspace_id", f"workspace-{raw_task['task_id']}")
                ),
                status=str(raw_task.get("status", "issued")),
            )
            mission.tasks[task.task_id] = task
        for raw_result in snapshot.get("accepted_results", []):
            if not isinstance(raw_result, Mapping):
                raise ValueError("result snapshot must be an object")
            payload = raw_result.get("payload", {})
            if not isinstance(payload, Mapping):
                raise ValueError("result payload must be an object")
            result = AgentResult(
                mission_id=str(raw_result["mission_id"]),
                revision=int(raw_result["revision"]),
                task_id=str(raw_result["task_id"]),
                stage=StageKind(str(raw_result["stage"])),
                sender_role=str(raw_result["sender_role"]),
                candidate_id=_optional_text(raw_result.get("candidate_id")),
                payload=dict(payload),
                payload_sha256=str(raw_result["payload_sha256"]),
                artifact_root=Path(str(raw_result["artifact_root"])),
            )
            if not result.has_valid_hash() or not result.has_valid_handoff():
                raise ValueError("result handoff is invalid in mission snapshot")
            mission.accepted_results.append(result)
        manager._missions[mission.mission_id] = mission
        manager._current_mission_id = mission.mission_id
        return manager

    def issue_task(
        self,
        stage: StageKind,
        assignee_role: str,
        candidate_id: str | None = None,
    ) -> WorkTask:
        mission = self.current_mission
        if mission.completed:
            raise ValueError("cannot issue a task for a completed mission")
        if stage is not mission.current_stage:
            raise ValueError(
                f"cannot issue {stage.value}; current stage is {mission.current_stage.value}"
            )
        if assignee_role not in mission.plan.stage(stage).roles:
            raise ValueError(f"role {assignee_role!r} is not assigned to {stage.value}")
        missing_inputs = (
            mission.plan.stage(stage).required_inputs - mission.available_outputs
        )
        if missing_inputs:
            raise StageGateDenied(
                "stage inputs are unavailable: " + ", ".join(sorted(missing_inputs))
            )
        bound_candidate_id = candidate_id
        if bound_candidate_id is None and stage in {
            StageKind.INTEGRATION_VERIFICATION,
            StageKind.VALIDATION,
            StageKind.RELEASE,
        }:
            bound_candidate_id = mission.active_candidate_id
        task_id = f"task-{uuid.uuid4().hex}"
        task = WorkTask(
            task_id=task_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            stage=stage,
            assignee_role=assignee_role,
            candidate_id=bound_candidate_id,
            attempt_id=f"attempt-{uuid.uuid4().hex}",
            worker_id=mission.plan.stage(stage).expert_profiles[assignee_role].expert_id,
            workspace_id=f"workspace-{task_id}",
        )
        mission.tasks[task.task_id] = task
        return task

    def receive_result(self, result: AgentResult) -> ResultDisposition:
        mission = self.current_mission
        if result.mission_id != mission.mission_id:
            self._inbox.append(result)
            return ResultDisposition.QUARANTINED_FOREIGN_MISSION
        if result.revision != mission.revision:
            self._inbox.append(result)
            return ResultDisposition.QUARANTINED_STALE_REVISION
        task = mission.tasks.get(result.task_id)
        if (
            task is None
            or task.stage is not result.stage
            or task.assignee_role != result.sender_role
            or task.candidate_id != result.candidate_id
        ):
            return ResultDisposition.REJECTED_UNEXPECTED_TASK
        if not result.has_valid_hash() or not result.has_valid_handoff():
            return ResultDisposition.REJECTED_INVALID_PAYLOAD
        task.status = "result-received"
        mission.accepted_results.append(result)
        return ResultDisposition.ACCEPTED_AS_INPUT

    def apply_user_steering(self, updated_goal: GoalDefinition, instruction: str) -> Mission:
        if not instruction.strip():
            raise ValueError("steering instruction must not be empty")
        mission = self.current_mission
        for task in mission.tasks.values():
            if task.status != "completed":
                task.status = "stale"
        mission.revision += 1
        mission.goal = updated_goal
        mission.plan = self._planner.plan(updated_goal)
        mission.current_stage_index = 0
        mission.active_candidate_id = None
        mission.candidate_approved = False
        mission.release_artifact_sha256 = None
        mission.completed = False
        mission.output_bindings = _initial_output_bindings(updated_goal, mission.plan)
        mission.steering_log.append(instruction)
        return mission

    def advance_if_ready(self) -> StageKind | None:
        mission = self.current_mission
        if mission.completed:
            raise StageGateDenied("mission is already completed")
        stage = mission.current_stage
        required_roles = mission.plan.stage(stage).roles - {"mission-manager"}
        passing_results: dict[str, AgentResult] = {}
        for role in sorted(required_roles):
            role_results = [
                result
                for result in mission.accepted_results
                if result.revision == mission.revision
                and result.stage is stage
                and result.sender_role == role
            ]
            if not role_results:
                raise StageGateDenied(f"missing passing result for role {role}")
            latest = role_results[-1]
            if latest.payload.get("gate") != "pass":
                raise StageGateDenied(f"failed result for role {role}")
            passing_results[role] = latest

        produced_bindings: dict[str, OutputBinding] = {}
        for result in passing_results.values():
            for entry in result.payload.get("artifacts", []):
                if not isinstance(entry, Mapping):
                    continue
                output_id = str(entry.get("artifact_type", ""))
                digest = str(entry.get("sha256", "")).lower()
                existing = produced_bindings.get(output_id)
                if existing is not None and existing.sha256 != digest:
                    raise StageGateDenied(
                        f"conflicting artifact hashes for stage output {output_id}"
                    )
                produced_bindings[output_id] = OutputBinding(
                    output_id=output_id,
                    kind=OutputKind.ARTIFACT,
                    reference=f"{result.task_id}:{entry.get('path', '')}",
                    sha256=digest,
                )
        required_outputs = mission.plan.stage(stage).required_outputs
        missing_outputs = required_outputs - set(produced_bindings)
        if missing_outputs:
            raise StageGateDenied(
                "stage outputs are unavailable: " + ", ".join(sorted(missing_outputs))
            )

        if stage is StageKind.IMPLEMENTATION and mission.active_candidate_id is None:
            raise StageGateDenied("implementation stage requires a frozen candidate")
        if stage is StageKind.VALIDATION and not mission.candidate_approved:
            raise StageGateDenied("validation stage requires candidate approval")
        if stage is StageKind.RELEASE and mission.release_artifact_sha256 is None:
            raise StageGateDenied("release stage requires a release package")

        for role, latest in passing_results.items():
            for task in mission.tasks.values():
                if task.task_id == latest.task_id:
                    task.status = "completed"
                elif (
                    task.revision == mission.revision
                    and task.stage is stage
                    and task.assignee_role == role
                    and task.status == "result-received"
                ):
                    task.status = "superseded"

        mission.output_bindings.update(
            {
                output_id: produced_bindings[output_id]
                for output_id in required_outputs
            }
        )

        if mission.current_stage_index == len(mission.plan.stages) - 1:
            mission.completed = True
            return None
        mission.current_stage_index += 1
        return mission.current_stage

    def bind_candidate(
        self, candidate_id: str, candidate_manifest_sha256: str
    ) -> Mission:
        mission = self.current_mission
        if mission.current_stage is not StageKind.IMPLEMENTATION:
            raise StageGateDenied("candidate can only be frozen during implementation")
        if mission.active_candidate_id not in {None, candidate_id}:
            raise StageGateDenied("mission already has a different active candidate")
        mission.active_candidate_id = candidate_id
        mission.candidate_approved = False
        mission.release_artifact_sha256 = None
        mission.output_bindings["frozen-candidate"] = OutputBinding(
            "frozen-candidate",
            OutputKind.CANDIDATE,
            candidate_id,
            candidate_manifest_sha256,
        )
        for task in mission.tasks.values():
            if task.revision == mission.revision and task.stage is StageKind.IMPLEMENTATION:
                task.candidate_id = candidate_id
        return mission

    def mark_candidate_approved(
        self, candidate_id: str, decision_reference: str = "direct-policy-decision"
    ) -> Mission:
        mission = self.current_mission
        if mission.current_stage is not StageKind.VALIDATION:
            raise StageGateDenied("candidate approval is only accepted during validation")
        if mission.active_candidate_id != candidate_id:
            raise StageGateDenied("approval candidate does not match active candidate")
        mission.candidate_approved = True
        decision_hash = _payload_hash(
            {"candidate_id": candidate_id, "decision_reference": decision_reference}
        )
        for output_id in ("approved-candidate", "gate-decision"):
            mission.output_bindings[output_id] = OutputBinding(
                output_id,
                OutputKind.POLICY_DECISION,
                decision_reference,
                decision_hash,
            )
        return mission

    def bind_release(
        self,
        candidate_id: str,
        artifact_sha256: str,
        release_reference: str = "release-package",
    ) -> Mission:
        mission = self.current_mission
        if mission.current_stage is not StageKind.RELEASE:
            raise StageGateDenied("release package can only be bound during release")
        if mission.active_candidate_id != candidate_id:
            raise StageGateDenied("release candidate does not match active candidate")
        if not mission.candidate_approved:
            raise StageGateDenied("release candidate is not approved")
        mission.release_artifact_sha256 = artifact_sha256
        mission.output_bindings["release-package"] = OutputBinding(
            "release-package",
            OutputKind.RELEASE_ARTIFACT,
            release_reference,
            artifact_sha256,
        )
        return mission
