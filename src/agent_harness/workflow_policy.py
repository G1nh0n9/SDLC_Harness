from __future__ import annotations

import hashlib
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .methodology import GoalDefinition, StageKind
from .mission import AgentResult, MissionManager, ResultDisposition, WorkTask
from .workflow_state import EventType, WorkflowEventStore, WorkflowProjection


class WorkflowPolicyError(RuntimeError):
    """Raised when a workflow mutation is not valid for the current state."""


class WorkflowPolicyEngine:
    def __init__(self, manager: MissionManager, event_store: WorkflowEventStore) -> None:
        self.manager = manager
        self.event_store = event_store

    @classmethod
    def attach_created(
        cls,
        manager: MissionManager,
        event_store: WorkflowEventStore,
        *,
        command_id: str,
    ) -> WorkflowPolicyEngine:
        policy = cls(manager, event_store)
        mission = manager.current_mission
        event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.MISSION_STARTED,
            payload={"stage": mission.current_stage.value},
        )
        return policy

    @property
    def mission_id(self) -> str:
        return self.manager.current_mission.mission_id

    def issue_task(
        self,
        stage: StageKind,
        role: str,
        candidate_id: str | None = None,
        *,
        command_id: str,
    ) -> WorkTask:
        existing = self.event_store.event_for_command(command_id)
        if existing is not None:
            task_id = str(existing.payload["task_id"])
            try:
                return self.manager.current_mission.tasks[task_id]
            except KeyError as error:
                raise WorkflowPolicyError(
                    "task event exists but mission snapshot has no matching task"
                ) from error
        task = self.manager.issue_task(stage, role, candidate_id)
        mission = self.manager.current_mission
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.TASK_ISSUED,
            payload={
                "task_id": task.task_id,
                "role": task.assignee_role,
                "candidate_id": task.candidate_id,
                "worker_id": task.worker_id,
                "workspace_id": task.workspace_id,
            },
        )
        self.event_store.append(
            command_id=f"{command_id}:attempt-started",
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.ATTEMPT_STARTED,
            payload={"task_id": task.task_id, "attempt_id": task.attempt_id},
        )
        return task

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def record_checkpoint(
        self, task_id: str, artifact_path: Path, *, command_id: str
    ) -> None:
        mission = self.manager.current_mission
        task = mission.tasks[task_id]
        if task.status not in {"issued", "running"}:
            raise WorkflowPolicyError("checkpoint requires an active attempt")
        unresolved = artifact_path.absolute()
        if unresolved.is_symlink():
            raise WorkflowPolicyError("checkpoint artifact cannot be a symbolic link")
        artifact = unresolved.resolve(strict=True)
        if not artifact.is_file():
            raise WorkflowPolicyError("checkpoint artifact must be a regular file")
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.CHECKPOINT_RECORDED,
            payload={
                "task_id": task.task_id,
                "attempt_id": task.attempt_id,
                "checkpoint_id": f"checkpoint-{uuid.uuid4().hex}",
                "artifact_path": str(artifact),
                "artifact_sha256": self._sha256(artifact),
            },
        )

    def interrupt_attempt(self, task_id: str, reason: str, *, command_id: str) -> None:
        if not reason.strip():
            raise WorkflowPolicyError("interruption reason is required")
        mission = self.manager.current_mission
        task = mission.tasks[task_id]
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.ATTEMPT_INTERRUPTED,
            payload={
                "task_id": task.task_id,
                "attempt_id": task.attempt_id,
                "reason": reason,
            },
        )
        task.status = "interrupted"

    def retry_attempt(
        self, task_id: str, retry_class: str, *, command_id: str
    ) -> WorkTask:
        mission = self.manager.current_mission
        task = mission.tasks[task_id]
        existing = self.event_store.event_for_command(command_id)
        if existing is not None:
            new_attempt_id = str(existing.payload["attempt_id"])
            task.attempt_id = new_attempt_id
            task.status = "issued"
            self.event_store.append(
                command_id=f"{command_id}:attempt-started",
                mission_id=mission.mission_id,
                revision=mission.revision,
                event_type=EventType.ATTEMPT_STARTED,
                payload={"task_id": task.task_id, "attempt_id": new_attempt_id},
            )
            return task
        if task.status != "interrupted":
            raise WorkflowPolicyError("only an interrupted attempt can be retried")
        prior_attempt_id = task.attempt_id
        new_attempt_id = f"attempt-{uuid.uuid4().hex}"
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.RETRY_SCHEDULED,
            payload={
                "task_id": task.task_id,
                "prior_attempt_id": prior_attempt_id,
                "attempt_id": new_attempt_id,
                "retry_class": retry_class,
            },
        )
        task.attempt_id = new_attempt_id
        task.status = "issued"
        self.event_store.append(
            command_id=f"{command_id}:attempt-started",
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.ATTEMPT_STARTED,
            payload={"task_id": task.task_id, "attempt_id": new_attempt_id},
        )
        return task

    def receive_result(
        self, result: AgentResult, *, command_id: str
    ) -> ResultDisposition:
        disposition = self.manager.receive_result(result)
        if disposition is ResultDisposition.ACCEPTED_AS_INPUT:
            mission = self.manager.current_mission
            task = mission.tasks[result.task_id]
            self.event_store.append(
                command_id=command_id,
                mission_id=mission.mission_id,
                revision=mission.revision,
                event_type=EventType.RESULT_RECEIVED,
                payload={
                    "task_id": task.task_id,
                    "attempt_id": task.attempt_id,
                    "payload_sha256": result.payload_sha256,
                },
            )
        return disposition

    def advance_if_ready(self, *, command_id: str) -> StageKind | None:
        mission = self.manager.current_mission
        next_stage = self.manager.advance_if_ready()
        if next_stage is None:
            event_type = EventType.MISSION_COMPLETED
            payload: Mapping[str, Any] = {}
        else:
            event_type = EventType.STAGE_ADVANCED
            payload = {"stage": next_stage.value}
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=event_type,
            payload=payload,
        )
        return next_stage

    def apply_user_steering(
        self, goal: GoalDefinition, instruction: str, *, command_id: str
    ) -> None:
        mission = self.manager.apply_user_steering(goal, instruction)
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.REVISION_STARTED,
            payload={"stage": mission.current_stage.value, "reason": instruction},
        )

    def bind_candidate(
        self,
        candidate_id: str,
        candidate_manifest_sha256: str,
        *,
        command_id: str,
    ) -> None:
        mission = self.manager.bind_candidate(
            candidate_id, candidate_manifest_sha256
        )
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.CANDIDATE_FROZEN,
            payload={
                "candidate_id": candidate_id,
                "candidate_manifest_sha256": candidate_manifest_sha256,
            },
        )

    def mark_candidate_approved(self, candidate_id: str, *, command_id: str) -> None:
        mission = self.manager.mark_candidate_approved(candidate_id, command_id)
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.QUALITY_DECIDED,
            payload={"candidate_id": candidate_id, "state": "QUALITY_DECIDED"},
        )

    def bind_release(
        self, candidate_id: str, artifact_sha256: str, *, command_id: str
    ) -> None:
        mission = self.manager.bind_release(candidate_id, artifact_sha256, command_id)
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=EventType.PACKAGE_CREATED,
            payload={
                "candidate_id": candidate_id,
                "artifact_sha256": artifact_sha256,
                "state": "PACKAGE_ELIGIBLE",
            },
        )

    def record_event(
        self,
        event_type: EventType,
        payload: Mapping[str, Any],
        *,
        command_id: str,
    ) -> None:
        mission = self.manager.current_mission
        self.event_store.append(
            command_id=command_id,
            mission_id=mission.mission_id,
            revision=mission.revision,
            event_type=event_type,
            payload=payload,
        )

    def projection(self) -> WorkflowProjection:
        events = self.event_store.events(self.mission_id)
        return WorkflowProjection.rebuild(events)
