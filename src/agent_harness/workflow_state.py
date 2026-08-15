from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class EventConflict(RuntimeError):
    """Raised when an idempotency key is reused for a different event."""


class ProjectionError(RuntimeError):
    """Raised when persisted events cannot produce a valid projection."""


class EventType(StrEnum):
    MISSION_STARTED = "MISSION_STARTED"
    REVISION_STARTED = "REVISION_STARTED"
    TASK_ISSUED = "TASK_ISSUED"
    ATTEMPT_STARTED = "ATTEMPT_STARTED"
    CHECKPOINT_RECORDED = "CHECKPOINT_RECORDED"
    ATTEMPT_INTERRUPTED = "ATTEMPT_INTERRUPTED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    RESULT_RECEIVED = "RESULT_RECEIVED"
    STAGE_ADVANCED = "STAGE_ADVANCED"
    CANDIDATE_FROZEN = "CANDIDATE_FROZEN"
    EVIDENCE_RECORDED = "EVIDENCE_RECORDED"
    QUALITY_DECIDED = "QUALITY_DECIDED"
    PACKAGE_CREATED = "PACKAGE_CREATED"
    MISSION_COMPLETED = "MISSION_COMPLETED"
    STALE = "STALE"


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class WorkflowEvent:
    event_id: str
    command_id: str
    mission_id: str
    revision: int
    sequence: int
    event_type: EventType
    payload: Mapping[str, Any]
    created_at: str
    previous_hash: str
    event_hash: str

    def calculated_hash(self) -> str:
        body = {
            "event_id": self.event_id,
            "command_id": self.command_id,
            "mission_id": self.mission_id,
            "revision": self.revision,
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "payload": dict(self.payload),
            "created_at": self.created_at,
            "previous_hash": self.previous_hash,
        }
        return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


class WorkflowEventStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_events (
                    event_id TEXT PRIMARY KEY,
                    command_id TEXT NOT NULL UNIQUE,
                    mission_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    UNIQUE (mission_id, sequence)
                )
                """
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> WorkflowEvent:
        payload = json.loads(str(row["payload_json"]))
        if not isinstance(payload, dict):
            raise ProjectionError("event payload is not an object")
        return WorkflowEvent(
            event_id=str(row["event_id"]),
            command_id=str(row["command_id"]),
            mission_id=str(row["mission_id"]),
            revision=int(row["revision"]),
            sequence=int(row["sequence"]),
            event_type=EventType(str(row["event_type"])),
            payload=payload,
            created_at=str(row["created_at"]),
            previous_hash=str(row["previous_hash"]),
            event_hash=str(row["event_hash"]),
        )

    def append(
        self,
        *,
        command_id: str,
        mission_id: str,
        revision: int,
        event_type: EventType,
        payload: Mapping[str, Any],
    ) -> WorkflowEvent:
        if not command_id or not mission_id or revision < 1:
            raise ValueError("command, mission, and positive revision are required")
        payload_json = _canonical_json(payload)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing_row = connection.execute(
                "SELECT * FROM workflow_events WHERE command_id = ?", (command_id,)
            ).fetchone()
            if existing_row is not None:
                existing = self._from_row(existing_row)
                if (
                    existing.mission_id != mission_id
                    or existing.revision != revision
                    or existing.event_type is not event_type
                    or _canonical_json(existing.payload) != payload_json
                ):
                    raise EventConflict("command id already identifies a different event")
                connection.execute("COMMIT")
                return existing

            previous_row = connection.execute(
                """
                SELECT sequence, event_hash FROM workflow_events
                WHERE mission_id = ? ORDER BY sequence DESC LIMIT 1
                """,
                (mission_id,),
            ).fetchone()
            sequence = 1 if previous_row is None else int(previous_row["sequence"]) + 1
            previous_hash = "0" * 64 if previous_row is None else str(previous_row["event_hash"])
            event = WorkflowEvent(
                event_id=f"event-{uuid.uuid4().hex}",
                command_id=command_id,
                mission_id=mission_id,
                revision=revision,
                sequence=sequence,
                event_type=event_type,
                payload=dict(payload),
                created_at=datetime.now(UTC).isoformat(),
                previous_hash=previous_hash,
                event_hash="",
            )
            event = WorkflowEvent(**{**event.__dict__, "event_hash": event.calculated_hash()})
            connection.execute(
                """
                INSERT INTO workflow_events (
                    event_id, command_id, mission_id, revision, sequence,
                    event_type, payload_json, created_at, previous_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.command_id,
                    event.mission_id,
                    event.revision,
                    event.sequence,
                    event.event_type.value,
                    payload_json,
                    event.created_at,
                    event.previous_hash,
                    event.event_hash,
                ),
            )
            connection.execute("COMMIT")
            return event
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def events(self, mission_id: str) -> tuple[WorkflowEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM workflow_events WHERE mission_id = ? ORDER BY sequence",
                (mission_id,),
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def event_for_command(self, command_id: str) -> WorkflowEvent | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM workflow_events WHERE command_id = ?", (command_id,)
            ).fetchone()
        return None if row is None else self._from_row(row)

    def verify_chain(self, mission_id: str) -> bool:
        previous_hash = "0" * 64
        for expected_sequence, event in enumerate(self.events(mission_id), start=1):
            if event.sequence != expected_sequence:
                return False
            if event.previous_hash != previous_hash:
                return False
            if event.event_hash != event.calculated_hash():
                return False
            previous_hash = event.event_hash
        return True


@dataclass(frozen=True)
class AttemptProjection:
    attempt_id: str
    task_id: str
    status: str
    checkpoint_ids: tuple[str, ...] = ()
    retry_of: str | None = None


@dataclass(frozen=True)
class TaskProjection:
    task_id: str
    role: str
    active_attempt_id: str | None = None


@dataclass
class WorkflowProjection:
    mission_id: str
    revision: int
    current_stage: str | None = None
    completed: bool = False
    tasks: dict[str, TaskProjection] = field(default_factory=dict)
    attempts: dict[str, AttemptProjection] = field(default_factory=dict)
    last_sequence: int = 0

    @classmethod
    def rebuild(cls, events: Sequence[WorkflowEvent]) -> WorkflowProjection:
        if not events:
            raise ProjectionError("cannot rebuild a workflow from no events")
        first = events[0]
        projection = cls(mission_id=first.mission_id, revision=first.revision)
        previous_hash = "0" * 64
        for expected_sequence, event in enumerate(events, start=1):
            if event.mission_id != projection.mission_id:
                raise ProjectionError("event mission changed during projection")
            if event.sequence != expected_sequence or event.previous_hash != previous_hash:
                raise ProjectionError("event sequence or previous hash is invalid")
            if event.calculated_hash() != event.event_hash:
                raise ProjectionError("event hash is invalid")
            projection._apply(event)
            projection.last_sequence = event.sequence
            previous_hash = event.event_hash
        return projection

    def _apply(self, event: WorkflowEvent) -> None:
        payload = event.payload
        if event.event_type in {EventType.MISSION_STARTED, EventType.REVISION_STARTED}:
            self.revision = event.revision
            self.current_stage = str(payload["stage"])
            self.completed = False
        elif event.event_type is EventType.TASK_ISSUED:
            task_id = str(payload["task_id"])
            self.tasks[task_id] = TaskProjection(task_id, str(payload["role"]))
        elif event.event_type is EventType.ATTEMPT_STARTED:
            task_id = str(payload["task_id"])
            attempt_id = str(payload["attempt_id"])
            previous = self.attempts.get(attempt_id)
            self.attempts[attempt_id] = AttemptProjection(
                attempt_id=attempt_id,
                task_id=task_id,
                status="running",
                checkpoint_ids=() if previous is None else previous.checkpoint_ids,
                retry_of=None if previous is None else previous.retry_of,
            )
            task = self.tasks[task_id]
            self.tasks[task_id] = TaskProjection(task.task_id, task.role, attempt_id)
        elif event.event_type is EventType.CHECKPOINT_RECORDED:
            attempt_id = str(payload["attempt_id"])
            attempt = self.attempts[attempt_id]
            checkpoint = str(payload["checkpoint_id"])
            self.attempts[attempt_id] = AttemptProjection(
                attempt.attempt_id,
                attempt.task_id,
                attempt.status,
                (*attempt.checkpoint_ids, checkpoint),
                attempt.retry_of,
            )
        elif event.event_type is EventType.ATTEMPT_INTERRUPTED:
            attempt_id = str(payload["attempt_id"])
            attempt = self.attempts[attempt_id]
            self.attempts[attempt_id] = AttemptProjection(
                attempt.attempt_id,
                attempt.task_id,
                "interrupted",
                attempt.checkpoint_ids,
                attempt.retry_of,
            )
        elif event.event_type is EventType.RETRY_SCHEDULED:
            attempt_id = str(payload["attempt_id"])
            self.attempts[attempt_id] = AttemptProjection(
                attempt_id,
                str(payload["task_id"]),
                "scheduled",
                (),
                str(payload["prior_attempt_id"]),
            )
        elif event.event_type is EventType.RESULT_RECEIVED:
            attempt_id = str(payload["attempt_id"])
            attempt = self.attempts[attempt_id]
            self.attempts[attempt_id] = AttemptProjection(
                attempt.attempt_id,
                attempt.task_id,
                "completed",
                attempt.checkpoint_ids,
                attempt.retry_of,
            )
        elif event.event_type is EventType.STAGE_ADVANCED:
            self.current_stage = str(payload["stage"])
        elif event.event_type is EventType.MISSION_COMPLETED:
            self.completed = True
            self.current_stage = None
