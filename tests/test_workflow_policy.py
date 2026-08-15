import hashlib
from pathlib import Path

from agent_harness.methodology import GoalDefinition, StageKind
from agent_harness.mission import MissionManager
from agent_harness.workflow_policy import WorkflowPolicyEngine
from agent_harness.workflow_state import EventType, WorkflowEventStore


def goal() -> GoalDefinition:
    return GoalDefinition(
        statement="implement a bounded converter",
        decision_action="decide whether to release",
        outcome="correct converted files",
        population="input files",
        analysis_unit="one file",
        time_horizon="one release",
        constraints=("no network",),
        question_type="implementation",
        data_description="fixed fixtures",
        decision_threshold="all acceptance criteria pass",
        field_status={},
        risk_level=1,
        research_artifact=False,
    )


def test_policy_engine_records_task_attempt_checkpoint_interruption_and_retry(
    tmp_path: Path,
) -> None:
    manager = MissionManager()
    mission = manager.create_mission(goal())
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    policy = WorkflowPolicyEngine.attach_created(manager, store, command_id="cmd-start")
    task = policy.issue_task(
        StageKind.SCOPE_RISK,
        "risk-analyst",
        command_id="cmd-task",
    )
    artifact = tmp_path / "checkpoint.json"
    artifact.write_text('{"partial":true}\n', encoding="utf-8")

    policy.record_checkpoint(task.task_id, artifact, command_id="cmd-checkpoint")
    old_attempt = task.attempt_id
    policy.interrupt_attempt(task.task_id, "timeout", command_id="cmd-interrupt")
    policy.retry_attempt(task.task_id, "safe-retry", command_id="cmd-retry")

    projection = policy.projection()
    assert projection.mission_id == mission.mission_id
    assert projection.attempts[old_attempt].status == "interrupted"
    assert projection.attempts[old_attempt].checkpoint_ids
    assert projection.attempts[task.attempt_id].retry_of == old_attempt
    assert projection.attempts[task.attempt_id].status == "running"
    events = store.events(mission.mission_id)
    assert [event.event_type for event in events] == [
        EventType.MISSION_STARTED,
        EventType.TASK_ISSUED,
        EventType.ATTEMPT_STARTED,
        EventType.CHECKPOINT_RECORDED,
        EventType.ATTEMPT_INTERRUPTED,
        EventType.RETRY_SCHEDULED,
        EventType.ATTEMPT_STARTED,
    ]
    checkpoint = events[3]
    assert checkpoint.payload["artifact_sha256"] == hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()
    assert store.verify_chain(mission.mission_id)


def test_retry_command_is_idempotent_and_does_not_create_a_third_attempt(
    tmp_path: Path,
) -> None:
    manager = MissionManager()
    manager.create_mission(goal())
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    policy = WorkflowPolicyEngine.attach_created(manager, store, command_id="cmd-start")
    task = policy.issue_task(
        StageKind.SCOPE_RISK,
        "risk-analyst",
        command_id="cmd-task",
    )
    policy.interrupt_attempt(task.task_id, "timeout", command_id="cmd-interrupt")

    first = policy.retry_attempt(task.task_id, "safe-retry", command_id="cmd-retry")
    second = policy.retry_attempt(task.task_id, "safe-retry", command_id="cmd-retry")

    assert second.attempt_id == first.attempt_id
    assert len(policy.projection().attempts) == 2
