from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .agent_runner import AgentRunRequest, RecordingAgentRunner
from .authority import AuthorityRequest, AuthorityStore
from .candidate import CandidateState, CandidateStore
from .evidence import EvidenceLedger
from .methodology import GoalDefinition, StageKind
from .mission import AgentResult, MissionManager
from .policy import GatePolicy
from .release import ReleaseDecision, ReleaseDisposition, ReleasePackager
from .result_evidence import build_evidence_evaluation, build_result_evidence
from .state_machine import CandidateStateMachine
from .workspace import RoleCatalog, WorkspaceBroker


def _require_current_stage(manager: MissionManager, expected: StageKind) -> None:
    actual = manager.current_mission.current_stage
    if actual is not expected:
        raise RuntimeError(f"unexpected stage: {actual.value}")


def _artifact_payload(
    workspace: Path,
    claim: str,
    artifact_types: Sequence[str],
    **extra: object,
) -> dict[str, object]:
    artifact = workspace / "stage-result.json"
    artifact.write_text('{"gate":"pass"}\n', encoding="utf-8")
    return build_result_evidence(
        artifact_path=artifact,
        artifact_root=workspace,
        artifact_types=artifact_types,
        claim=claim,
        gate="pass",
        extra=extra,
    )


def _agent_authority(store: AuthorityStore, task) -> str:  # type: ignore[no-untyped-def]
    return store.issue(
        mission_id=task.mission_id,
        revision=task.revision,
        task_id=task.task_id,
        attempt_id=task.attempt_id,
        worker_id=task.worker_id,
        workspace_id=task.workspace_id,
        candidate_id=task.candidate_id,
        role=task.assignee_role,
        allowed_operations={"execute-task"},
        allowed_tools={"recording-agent"},
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    ).token


def _complete_current_stage(
    manager: MissionManager,
    workspace_root: Path,
    *,
    candidate_id: str | None,
    advance: bool = True,
) -> str:
    mission = manager.current_mission
    stage = mission.current_stage
    authority_store = AuthorityStore(workspace_root.parent / "authority.sqlite3")
    required_roles = mission.plan.stage(stage).roles - {"mission-manager"}
    for role in sorted(required_roles):
        task = manager.issue_task(stage, role, candidate_id)
        catalog = RoleCatalog.default_with_dynamic_role(
            role,
            can_execute_commands=False,
            can_approve="reviewer" in role,
        )
        workspace = WorkspaceBroker(workspace_root, catalog).create(
            mission_id=mission.mission_id,
            revision=mission.revision,
            task_id=task.task_id,
            role=role,
        )
        runner = RecordingAgentRunner(
            response=_artifact_payload(
                workspace.work,
                f"{stage.value} stage passed",
                sorted(mission.plan.stage(stage).required_outputs),
                stage=stage.value,
                role=role,
            )
        )
        result = runner.dispatch(
            AgentRunRequest(
                task=task,
                prompt=f"{stage.value} 단계를 판정하라",
                workspace=workspace,
                authority_store=authority_store,
                authority_token=_agent_authority(authority_store, task),
            )
        )
        manager.receive_result(result)
    if advance:
        manager.advance_if_ready()
    return stage.value


def run_demo(root: Path) -> dict[str, object]:
    run_root = (root / f"run-{uuid.uuid4().hex}").resolve()
    run_root.mkdir(parents=True)
    goal = GoalDefinition(
        statement="작은 평균 계산 라이브러리를 구현한다",
        decision_action="시연용 패키지 생성 여부를 결정한다",
        outcome="고정 입력에서 기대 평균을 반환하는 함수",
        population="시연용 숫자 목록",
        analysis_unit="함수 호출",
        time_horizon="이번 시연 실행",
        constraints=("네트워크 사용 금지",),
        question_type="implementation",
        data_description="시연 과정에서 만든 고정 입력",
        decision_threshold="실제 수락 검사 종료 코드 0",
        field_status={},
        risk_level=1,
        research_artifact=False,
    )
    manager = MissionManager()
    mission = manager.create_mission(goal)
    task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")

    catalog = RoleCatalog.default_with_dynamic_role(
        "risk-analyst", can_execute_commands=False, can_approve=False
    )
    workspace = WorkspaceBroker(run_root / "workspaces", catalog).create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=task.task_id,
        role=task.assignee_role,
    )
    foreign = AgentResult.create(
        mission_id="mis-foreign",
        revision=mission.revision,
        task_id=task.task_id,
        stage=task.stage,
        sender_role=task.assignee_role,
        candidate_id=None,
        payload=_artifact_payload(
            workspace.work,
            "foreign result must be quarantined",
            sorted(mission.plan.stage(task.stage).required_outputs),
        ),
        artifact_root=workspace.work,
    )
    foreign_disposition = manager.receive_result(foreign)
    runner = RecordingAgentRunner(
        response=_artifact_payload(
            workspace.work,
            "scope and risk assessed",
            sorted(mission.plan.stage(task.stage).required_outputs),
            risk_level=1,
            stage_decision="continue",
        )
    )
    authority_store = AuthorityStore(run_root / "authority.sqlite3")
    result = runner.dispatch(
        AgentRunRequest(
            task=task,
            prompt="범위와 위험을 판정하라",
            workspace=workspace,
            authority_store=authority_store,
            authority_token=_agent_authority(authority_store, task),
        )
    )
    accepted_disposition = manager.receive_result(result)

    manager.advance_if_ready()
    stage_gate_log = [StageKind.SCOPE_RISK.value]

    before_candidate = {
        StageKind.REQUIREMENTS,
        StageKind.ORACLE,
        StageKind.DESIGN,
    }
    while mission.current_stage in before_candidate:
        stage_gate_log.append(
            _complete_current_stage(
                manager,
                run_root / "workspaces",
                candidate_id=None,
            )
        )

    candidate_inputs = {}
    for label in ("source", "requirements", "design", "build-config", "dependencies"):
        directory = run_root / "inputs" / label
        directory.mkdir(parents=True)
        candidate_inputs[label] = directory
    source = candidate_inputs["source"]
    requirements = candidate_inputs["requirements"]
    (source / "analysis.py").write_text(
        "def estimate(values):\n    return sum(values) / len(values)\n",
        encoding="utf-8",
    )
    (requirements / "acceptance.md").write_text(
        "estimate([1, 2, 3])은 2.0을 반환해야 한다.\n",
        encoding="utf-8",
    )
    (candidate_inputs["design"] / "design.md").write_text(
        "입력 합계를 항목 수로 나눈다.\n", encoding="utf-8"
    )
    (candidate_inputs["build-config"] / "python.txt").write_text(
        "python=3.11\n", encoding="utf-8"
    )
    (candidate_inputs["dependencies"] / "dependencies.txt").write_text(
        "stdlib-only\n", encoding="utf-8"
    )
    required_evidence = {"acceptance-test"}
    store = CandidateStore(run_root / "candidate-store")
    candidate = store.freeze_candidate(
        mission_id=mission.mission_id,
        revision=mission.revision,
        inputs=candidate_inputs,
        toolchain={"python": "3.11"},
        required_evidence=required_evidence,
        created_by_role="implementation-specialist",
    )
    if not store.verify(candidate.candidate_id):
        raise RuntimeError("candidate snapshot verification failed")
    manager.bind_candidate(candidate.candidate_id, candidate.manifest_sha256)
    stage_gate_log.append(
        _complete_current_stage(
            manager,
            run_root / "workspaces",
            candidate_id=candidate.candidate_id,
        )
    )

    ledger = EvidenceLedger(run_root / "evidence.sqlite3")
    evidence_root = run_root / "evidence-artifacts"
    evidence_root.mkdir()
    candidate_source = candidate.snapshot_root / "source"
    check_code = (
        "import sys; "
        f"sys.path.insert(0, {str(candidate_source)!r}); "
        "from analysis import estimate; "
        "actual = estimate([1, 2, 3]); "
        "assert actual == 2.0, actual; "
        "print(actual)"
    )
    command = [sys.executable, "-I", "-B", "-c", check_code]
    child_environment = {
        name: value
        for name in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP")
        if (value := os.environ.get(name))
    }
    child_environment["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        command,
        cwd=run_root,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    evidence_artifact = evidence_root / "acceptance-test.json"
    evidence_artifact.write_text(
        json.dumps(
            {
                "candidate_id": candidate.candidate_id,
                "command": command,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "expected": "estimate([1, 2, 3]) == 2.0",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    evidence_outcome = "pass" if completed.returncode == 0 else "fail"
    ledger.append(
        mission_id=mission.mission_id,
        revision=mission.revision,
        candidate_id=candidate.candidate_id,
        evidence_type="acceptance-test",
        producer_role="verification-specialist",
        outcome=evidence_outcome,
        artifact_path=evidence_artifact,
        **build_evidence_evaluation(
            artifact_path=evidence_artifact, outcome=evidence_outcome
        ),
        details={
            "scope": "one deterministic acceptance check",
            "command": command,
            "exit_code": completed.returncode,
        },
    )

    _require_current_stage(manager, StageKind.INTEGRATION_VERIFICATION)
    stage_gate_log.append(
        _complete_current_stage(
            manager,
            run_root / "workspaces",
            candidate_id=candidate.candidate_id,
        )
    )

    machine = CandidateStateMachine()
    machine.transition(candidate, CandidateState.VERIFYING)
    machine.transition(candidate, CandidateState.REVIEWING)
    _require_current_stage(manager, StageKind.VALIDATION)
    stage_gate_log.append(
        _complete_current_stage(
            manager,
            run_root / "workspaces",
            candidate_id=candidate.candidate_id,
            advance=False,
        )
    )
    approval_grant = authority_store.issue(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id="task-demo-approval",
        attempt_id="attempt-demo-approval",
        worker_id="expert:validation:independent-code-reviewer",
        workspace_id="workspace-demo-approval",
        candidate_id=candidate.candidate_id,
        role="independent-code-reviewer",
        allowed_operations={"approve-candidate"},
        allowed_tools=set(),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    GatePolicy(machine).approve(
        candidate,
        ledger,
        authority_store=authority_store,
        authority_token=approval_grant.token,
        authority_request=AuthorityRequest(
            mission_id=mission.mission_id,
            revision=mission.revision,
            task_id="task-demo-approval",
            attempt_id="attempt-demo-approval",
            worker_id="expert:validation:independent-code-reviewer",
            workspace_id="workspace-demo-approval",
            candidate_id=candidate.candidate_id,
            role="independent-code-reviewer",
            operation="approve-candidate",
            tool=None,
        ),
        expected_mission_id=mission.mission_id,
        expected_revision=mission.revision,
    )
    manager.mark_candidate_approved(candidate.candidate_id)
    manager.advance_if_ready()
    release = ReleasePackager(machine).package(
        candidate,
        run_root / "release",
        decision=ReleaseDecision(ReleaseDisposition.RELEASE),
        expected_mission_id=mission.mission_id,
        expected_revision=mission.revision,
    )
    manager.bind_release(candidate.candidate_id, release.sha256)
    _require_current_stage(manager, StageKind.RELEASE)
    stage_gate_log.append(
        _complete_current_stage(
            manager,
            run_root / "workspaces",
            candidate_id=candidate.candidate_id,
        )
    )
    return {
        "run_root": str(run_root),
        "mission_id": mission.mission_id,
        "revision": mission.revision,
        "track": mission.plan.track.value,
        "stages": [stage.kind.value for stage in mission.plan.stages],
        "required_research_assurance": sorted(
            claim.value for claim in mission.plan.required_assurance_claims
        ),
        "foreign_result": foreign_disposition.value,
        "current_result": accepted_disposition.value,
        "inbox_size": manager.inbox_size,
        "candidate_id": candidate.candidate_id,
        "candidate_state": candidate.state.value,
        "mission_completed": mission.completed,
        "stage_gate_log": stage_gate_log,
        "ledger_chain_valid": ledger.verify_chain(),
        "release_package": str(release.path),
        "release_package_sha256": release.sha256,
        "release_disposition": release.decision.disposition.value,
        "demo_limitations": (
            "Engine walkthrough with one executed acceptance check; not an independent "
            "review or proof of complete correctness."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-harness")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run a deterministic end-to-end demonstration")
    demo.add_argument("--root", type=Path, required=True)
    demo.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        report = run_demo(args.root)
        if args.json:
            print(json.dumps(report, sort_keys=True, ensure_ascii=False))
        else:
            print(f"mission: {report['mission_id']}")
            print(f"candidate: {report['candidate_id']}")
            print(f"state: {report['candidate_state']}")
            print(f"release: {report['release_package']}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
