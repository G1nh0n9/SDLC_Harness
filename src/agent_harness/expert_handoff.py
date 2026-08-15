from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .methodology import ExpertProfile, KnowledgeConcept, StageKind


class HandoffKnowledgeError(ValueError):
    """Raised when a handoff does not share issued knowledge or receiver acceptance."""


@dataclass(frozen=True)
class ReceiverAcceptance:
    receiver_expert_id: str
    usable_without_rework: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ExpertHandoff:
    _document: Mapping[str, Any]

    @staticmethod
    def _expert(profile: ExpertProfile) -> dict[str, Any]:
        return {
            "expert_id": profile.expert_id,
            "role": profile.role,
            "responsibility_area": (
                None if profile.responsibility_area is None else profile.responsibility_area.value
            ),
        }

    @classmethod
    def create(
        cls,
        *,
        mission_id: str,
        revision: int,
        task_id: str,
        stage: StageKind,
        candidate_id: str | None,
        sender: ExpertProfile,
        receiver: ExpertProfile,
        shared_foundation: Sequence[str],
        artifacts: Sequence[Mapping[str, str]],
        work_performed: Sequence[str],
        decisions: Sequence[str],
        assumptions: Sequence[str],
        unresolved: Sequence[str],
        next_actions: Sequence[str],
        receiver_acceptance: ReceiverAcceptance,
    ) -> ExpertHandoff:
        shared = set(shared_foundation)
        if not shared.issubset(sender.shared_foundation) or not shared.issubset(
            receiver.shared_foundation
        ):
            raise HandoffKnowledgeError(
                "shared foundation must have been issued to sender and receiver"
            )
        return cls(
            {
                "schema_version": "1.0",
                "document_type": "expert-handoff",
                "mission_id": mission_id,
                "revision": revision,
                "task_id": task_id,
                "stage": stage.value,
                "candidate_id": candidate_id,
                "sender": cls._expert(sender),
                "receiver": cls._expert(receiver),
                "shared_foundation": list(shared_foundation),
                "artifacts": [dict(item) for item in artifacts],
                "work_performed": list(work_performed),
                "decisions": list(decisions),
                "assumptions": list(assumptions),
                "unresolved": list(unresolved),
                "next_actions": list(next_actions),
                "receiver_acceptance": {
                    "receiver_expert_id": receiver_acceptance.receiver_expert_id,
                    "usable_without_rework": receiver_acceptance.usable_without_rework,
                    "reasons": list(receiver_acceptance.reasons),
                },
            }
        )

    def document(self) -> dict[str, Any]:
        return json.loads(json.dumps(self._document))  # type: ignore[no-any-return]


class ExpertHandoffValidator:
    def __init__(self) -> None:
        schema_text = (
            files("agent_harness.schemas")
            .joinpath("expert-handoff.schema.json")
            .read_text(encoding="utf-8")
        )
        self._validator = Draft202012Validator(json.loads(schema_text))

    @staticmethod
    def _assert_no_symlink_path(path: Path) -> None:
        for component in (path.absolute(), *path.absolute().parents):
            if component.is_symlink():
                raise HandoffKnowledgeError(f"artifact path contains a symbolic link: {path}")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def validate_and_verify(
        self,
        document: Mapping[str, Any],
        artifact_root: Path,
        knowledge_base: Mapping[str, KnowledgeConcept],
    ) -> None:
        errors = sorted(
            self._validator.iter_errors(dict(document)),
            key=lambda item: list(item.path),
        )
        if errors:
            raise HandoffKnowledgeError(errors[0].message)
        sender = document["sender"]
        receiver = document["receiver"]
        shared = document["shared_foundation"]
        assert isinstance(sender, Mapping)
        assert isinstance(receiver, Mapping)
        assert isinstance(shared, list)
        for concept_id in shared:
            if concept_id not in knowledge_base:
                raise HandoffKnowledgeError(
                    f"shared foundation concept was not issued: {concept_id}"
                )
        acceptance = document["receiver_acceptance"]
        assert isinstance(acceptance, Mapping)
        if acceptance["receiver_expert_id"] != receiver["expert_id"]:
            raise HandoffKnowledgeError("receiver acceptance identity does not match receiver")
        if acceptance["usable_without_rework"] is not True:
            raise HandoffKnowledgeError("receiver did not accept the handoff as usable")

        self._assert_no_symlink_path(artifact_root)
        root = artifact_root.resolve(strict=True)
        for entry in document["artifacts"]:
            assert isinstance(entry, Mapping)
            relative = Path(str(entry["path"]))
            if relative.is_absolute() or ".." in relative.parts:
                raise HandoffKnowledgeError(f"unsafe artifact path: {relative}")
            unresolved = (root / relative).absolute()
            current = unresolved
            while current != root.parent:
                if current.is_symlink():
                    raise HandoffKnowledgeError(
                        f"artifact path contains a symbolic link: {relative}"
                    )
                if current.parent == current:
                    break
                current = current.parent
            artifact = unresolved.resolve(strict=True)
            try:
                artifact.relative_to(root)
            except ValueError as error:
                raise HandoffKnowledgeError(f"artifact escaped root: {relative}") from error
            if not artifact.is_file():
                raise HandoffKnowledgeError(f"artifact is not a regular file: {relative}")
            if self._sha256(artifact) != str(entry["sha256"]).lower():
                raise HandoffKnowledgeError(f"artifact hash mismatch: {relative}")
