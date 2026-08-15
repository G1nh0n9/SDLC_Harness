import json
import uuid
from pathlib import Path

import pytest

from agent_harness.methodology import GoalDefinition, StageKind
from agent_harness.mission import (
    AgentResult,
    MissionManager,
    ResultDisposition,
    StageGateDenied,
)
from agent_harness.result_evidence import build_result_evidence


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


def result_payload(root: Path, gate: str) -> dict[str, object]:
    artifact_name = f"result-{uuid.uuid4().hex}.json"
    artifact = root / artifact_name
    artifact.write_text(json.dumps({"gate": gate}) + "\n", encoding="utf-8")
    return build_result_evidence(
        artifact_path=artifact,
        artifact_root=root,
        artifact_types=("scope-risk-assessment",),
        claim=f"gate is {gate}",
        gate=gate,
    )


def test_foreign_mission_result_is_quarantined_without_advancing_current_state(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = MissionManager()
    current = manager.create_mission(complete_goal())
    task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")
    before_stage = current.current_stage

    result = AgentResult.create(
        mission_id="mission-from-another-session",
        revision=current.revision,
        task_id=task.task_id,
        stage=task.stage,
        sender_role=task.assignee_role,
        candidate_id=None,
        payload=result_payload(tmp_path, "pass"),
        artifact_root=tmp_path,
    )
    disposition = manager.receive_result(result)

    assert disposition is ResultDisposition.QUARANTINED_FOREIGN_MISSION
    assert manager.current_mission.current_stage is before_stage
    assert manager.inbox_size == 1
    assert task.status == "issued"


def test_user_steering_increments_revision_and_quarantines_old_result(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = MissionManager()
    mission = manager.create_mission(complete_goal())
    old_task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")

    old_result = AgentResult.create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=old_task.task_id,
        stage=old_task.stage,
        sender_role=old_task.assignee_role,
        candidate_id=None,
        payload=result_payload(tmp_path, "pass"),
        artifact_root=tmp_path,
    )
    updated_goal = complete_goal()
    manager.apply_user_steering(updated_goal, "연구 논문의 핵심 산출물로 사용한다")

    disposition = manager.receive_result(old_result)

    assert manager.current_mission.revision == 2
    assert old_task.status == "stale"
    assert disposition is ResultDisposition.QUARANTINED_STALE_REVISION
    assert manager.current_mission.current_stage is StageKind.SCOPE_RISK


def test_stage_advances_only_after_all_required_roles_return_pass(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = MissionManager()
    mission = manager.create_mission(complete_goal())
    task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")

    with pytest.raises(StageGateDenied, match="missing passing result"):
        manager.advance_if_ready()

    failed = AgentResult.create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=task.task_id,
        stage=task.stage,
        sender_role=task.assignee_role,
        candidate_id=None,
        payload=result_payload(tmp_path, "fail"),
        artifact_root=tmp_path,
    )
    manager.receive_result(failed)
    with pytest.raises(StageGateDenied, match="failed result"):
        manager.advance_if_ready()
    assert mission.current_stage is StageKind.SCOPE_RISK

    retry = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")
    passed = AgentResult.create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=retry.task_id,
        stage=retry.stage,
        sender_role=retry.assignee_role,
        candidate_id=None,
        payload=result_payload(tmp_path, "pass"),
        artifact_root=tmp_path,
    )
    manager.receive_result(passed)
    manager.advance_if_ready()

    assert mission.current_stage.value == StageKind.REQUIREMENTS.value
    assert retry.status == "completed"


def test_result_without_valid_handoff_is_rejected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = MissionManager()
    mission = manager.create_mission(complete_goal())
    task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")
    malformed = AgentResult.create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=task.task_id,
        stage=task.stage,
        sender_role=task.assignee_role,
        candidate_id=None,
        payload={"gate": "pass"},
        artifact_root=tmp_path,
    )

    assert manager.receive_result(malformed) is ResultDisposition.REJECTED_INVALID_PAYLOAD
    assert task.status == "issued"


def test_stage_cannot_advance_with_a_valid_but_wrong_output_type(tmp_path: Path) -> None:
    manager = MissionManager()
    mission = manager.create_mission(complete_goal())
    task = manager.issue_task(StageKind.SCOPE_RISK, "risk-analyst")
    artifact = tmp_path / "unrelated.json"
    artifact.write_text('{"gate":"pass"}\n', encoding="utf-8")
    result = AgentResult.create(
        mission_id=mission.mission_id,
        revision=mission.revision,
        task_id=task.task_id,
        stage=task.stage,
        sender_role=task.assignee_role,
        candidate_id=None,
        payload=build_result_evidence(
            artifact_path=artifact,
            artifact_root=tmp_path,
            artifact_types=("unrelated-output",),
            claim="an unrelated artifact exists",
            gate="pass",
        ),
        artifact_root=tmp_path,
    )

    assert manager.receive_result(result) is ResultDisposition.ACCEPTED_AS_INPUT
    with pytest.raises(StageGateDenied, match="scope-risk-assessment"):
        manager.advance_if_ready()
    assert "scope-risk-assessment" not in mission.output_bindings
