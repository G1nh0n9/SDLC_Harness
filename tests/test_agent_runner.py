import sys
from datetime import UTC, datetime, timedelta

import pytest

from agent_harness.agent_runner import (
    AgentExecutionError,
    AgentRunRequest,
    HermesCliRunner,
    RecordingAgentRunner,
)
from agent_harness.authority import AuthorityStore
from agent_harness.methodology import GoalDefinition, StageKind
from agent_harness.mission import MissionManager, ResultDisposition
from agent_harness.result_evidence import build_result_evidence
from agent_harness.workspace import RoleCatalog, WorkspaceBroker


def complete_goal() -> GoalDefinition:
    return GoalDefinition(
        statement="명시된 파일 변환기를 구현한다",
        decision_action="변환기를 배포한다",
        outcome="명세에 맞는 변환 결과",
        population="입력 파일",
        analysis_unit="파일 하나",
        time_horizon="실행 시점",
        constraints=("네트워크 사용 금지",),
        question_type="implementation",
        data_description="고정된 입력·출력 예제",
        decision_threshold="모든 수락 시험 통과",
        field_status={},
        risk_level=1,
        research_artifact=False,
    )


def authority_for(tmp_path, task, tool: str):  # type: ignore[no-untyped-def]
    store = AuthorityStore(tmp_path / f"authority-{tool}.sqlite3")
    grant = store.issue(
        mission_id=task.mission_id,
        revision=task.revision,
        task_id=task.task_id,
        attempt_id=task.attempt_id,
        worker_id=task.worker_id,
        workspace_id=task.workspace_id,
        candidate_id=task.candidate_id,
        role=task.assignee_role,
        allowed_operations={"execute-task"},
        allowed_tools={tool},
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    return store, grant.token


def test_runner_returns_data_result_without_advancing_mission(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = MissionManager()
    mission = manager.create_mission(complete_goal())
    task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")
    catalog = RoleCatalog.default_with_dynamic_role(
        "risk-analyst", can_execute_commands=False, can_approve=False
    )
    workspace = WorkspaceBroker(tmp_path / "runs", catalog).create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=task.task_id,
        role=task.assignee_role,
    )
    artifact = workspace.work / "result.json"
    artifact.write_text('{"gate":"pass"}\n', encoding="utf-8")
    runner = RecordingAgentRunner(
        response=build_result_evidence(
            artifact_path=artifact,
            artifact_root=workspace.work,
            artifact_types=("scope-risk-assessment",),
            claim="task passed",
            gate="pass",
            extra={"risk_level": 1, "stage_decision": "continue"},
        )
    )
    authority_store, authority_token = authority_for(tmp_path, task, "recording-agent")

    result = runner.dispatch(
        AgentRunRequest(
            task=task,
            prompt="Assess scope and risk",
            workspace=workspace,
            authority_store=authority_store,
            authority_token=authority_token,
        )
    )
    disposition = manager.receive_result(result)

    assert disposition is ResultDisposition.ACCEPTED_AS_INPUT
    assert mission.current_stage is StageKind.SCOPE_RISK
    assert task.status == "result-received"
    assert runner.requests[0].workspace.home != runner.requests[0].workspace.work


def test_hermes_runner_starts_tool_free_safe_process(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    script = tmp_path / "fake_hermes.py"
    script.write_text(
        """
import json
import os
import sys

args = sys.argv[1:]
tool_index = args.index("--toolsets")
in_index = args.index("--in")
print(json.dumps({
    "gate": "pass",
    "claims": [{"claim": "runner passed", "evidence": "inline:output"}],
    "assumptions": [],
    "unresolved": [],
    "artifacts": [],
    "safe_mode": "--safe-mode" in args,
    "oneshot": "--oneshot" in args,
    "toolsets": args[tool_index + 1],
    "workdir": args[in_index + 1],
    "secret_present": "HARNESS_TEST_SECRET" in os.environ,
    "path_present": "PATH" in os.environ,
}))
""".strip()
        + "\n",
        encoding="utf-8",
    )
    manager = MissionManager()
    mission = manager.create_mission(complete_goal())
    task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")
    catalog = RoleCatalog.default_with_dynamic_role(
        "risk-analyst", can_execute_commands=True, can_approve=False
    )
    workspace = WorkspaceBroker(tmp_path / "runs", catalog).create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=task.task_id,
        role=task.assignee_role,
    )
    monkeypatch.setattr(
        HermesCliRunner,
        "_discover_command_prefix",
        staticmethod(lambda: (sys.executable, str(script))),
    )
    runner = HermesCliRunner()
    monkeypatch.setenv("HARNESS_TEST_SECRET", "must-not-leak")
    authority_store, authority_token = authority_for(tmp_path, task, "hermes-cli")

    result = runner.dispatch(
        AgentRunRequest(
            task=task,
            prompt="범위와 위험을 판정하라",
            workspace=workspace,
            authority_store=authority_store,
            authority_token=authority_token,
        )
    )

    assert result.payload["safe_mode"] is True
    assert result.payload["oneshot"] is True
    assert result.payload["toolsets"] == ""
    assert result.payload["workdir"] == str(workspace.work)
    assert result.payload["secret_present"] is False
    assert result.payload["path_present"] is False


def test_hermes_runner_enforces_role_and_workspace_binding(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = MissionManager()
    mission = manager.create_mission(complete_goal())
    task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")
    denied_catalog = RoleCatalog.default_with_dynamic_role(
        "risk-analyst", can_execute_commands=False, can_approve=False
    )
    denied_workspace = WorkspaceBroker(tmp_path / "denied", denied_catalog).create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=task.task_id,
        role=task.assignee_role,
    )
    runner = HermesCliRunner()
    authority_store, authority_token = authority_for(tmp_path, task, "hermes-cli")

    with pytest.raises(AgentExecutionError, match="does not allow command execution"):
        runner.dispatch(
            AgentRunRequest(
                task=task,
                prompt="must be denied",
                workspace=denied_workspace,
                authority_store=authority_store,
                authority_token=authority_token,
            )
        )

    allowed_catalog = RoleCatalog.default_with_dynamic_role(
        "risk-analyst", can_execute_commands=True, can_approve=False
    )
    mismatched_workspace = WorkspaceBroker(tmp_path / "mismatch", allowed_catalog).create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id="task-different",
        role=task.assignee_role,
    )
    with pytest.raises(AgentExecutionError, match="does not match task"):
        runner.dispatch(
            AgentRunRequest(
                task=task,
                prompt="must be denied",
                workspace=mismatched_workspace,
                authority_store=authority_store,
                authority_token=authority_token,
            )
        )
