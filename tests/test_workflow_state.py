import json
import sqlite3
from pathlib import Path

import pytest

from agent_harness.workflow_state import (
    EventConflict,
    EventType,
    WorkflowEventStore,
    WorkflowProjection,
)


def test_event_store_is_idempotent_by_command_and_rejects_changed_duplicate(
    tmp_path: Path,
) -> None:
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    first = store.append(
        command_id="cmd-1",
        mission_id="mis-1",
        revision=1,
        event_type=EventType.MISSION_STARTED,
        payload={"stage": "scope-risk"},
    )
    duplicate = store.append(
        command_id="cmd-1",
        mission_id="mis-1",
        revision=1,
        event_type=EventType.MISSION_STARTED,
        payload={"stage": "scope-risk"},
    )

    assert duplicate == first
    assert len(store.events("mis-1")) == 1
    with pytest.raises(EventConflict, match="different event"):
        store.append(
            command_id="cmd-1",
            mission_id="mis-1",
            revision=1,
            event_type=EventType.STAGE_ADVANCED,
            payload={"stage": "requirements"},
        )


def test_projection_rebuilds_attempt_checkpoint_interruption_and_retry(
    tmp_path: Path,
) -> None:
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    events = [
        ("cmd-1", EventType.MISSION_STARTED, {"stage": "scope-risk"}),
        (
            "cmd-2",
            EventType.TASK_ISSUED,
            {"task_id": "task-1", "role": "risk-analyst"},
        ),
        (
            "cmd-3",
            EventType.ATTEMPT_STARTED,
            {"task_id": "task-1", "attempt_id": "attempt-1"},
        ),
        (
            "cmd-4",
            EventType.CHECKPOINT_RECORDED,
            {
                "task_id": "task-1",
                "attempt_id": "attempt-1",
                "checkpoint_id": "checkpoint-1",
                "artifact_sha256": "a" * 64,
            },
        ),
        (
            "cmd-5",
            EventType.ATTEMPT_INTERRUPTED,
            {"task_id": "task-1", "attempt_id": "attempt-1", "reason": "timeout"},
        ),
        (
            "cmd-6",
            EventType.RETRY_SCHEDULED,
            {
                "task_id": "task-1",
                "prior_attempt_id": "attempt-1",
                "attempt_id": "attempt-2",
                "retry_class": "safe-retry",
            },
        ),
        (
            "cmd-7",
            EventType.ATTEMPT_STARTED,
            {"task_id": "task-1", "attempt_id": "attempt-2"},
        ),
    ]
    for command_id, event_type, payload in events:
        store.append(
            command_id=command_id,
            mission_id="mis-1",
            revision=1,
            event_type=event_type,
            payload=payload,
        )

    projection = WorkflowProjection.rebuild(store.events("mis-1"))

    assert projection.current_stage == "scope-risk"
    assert projection.tasks["task-1"].active_attempt_id == "attempt-2"
    assert projection.attempts["attempt-1"].status == "interrupted"
    assert projection.attempts["attempt-1"].checkpoint_ids == ("checkpoint-1",)
    assert projection.attempts["attempt-2"].status == "running"
    assert projection.attempts["attempt-2"].retry_of == "attempt-1"


def test_event_hash_chain_detects_persisted_payload_tampering(tmp_path: Path) -> None:
    path = tmp_path / "workflow.sqlite3"
    store = WorkflowEventStore(path)
    store.append(
        command_id="cmd-1",
        mission_id="mis-1",
        revision=1,
        event_type=EventType.MISSION_STARTED,
        payload={"stage": "scope-risk"},
    )
    store.append(
        command_id="cmd-2",
        mission_id="mis-1",
        revision=1,
        event_type=EventType.STAGE_ADVANCED,
        payload={"stage": "requirements"},
    )
    assert store.verify_chain("mis-1")

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE workflow_events SET payload_json = ? WHERE sequence = 1",
            (json.dumps({"stage": "release"}),),
        )

    assert not store.verify_chain("mis-1")
