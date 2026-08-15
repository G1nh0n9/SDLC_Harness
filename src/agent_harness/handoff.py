from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class SchemaViolation(ValueError):
    """Raised when a handoff document does not satisfy its JSON Schema."""


class ArtifactMismatch(ValueError):
    """Raised when a handoff artifact path or digest cannot be verified."""


class HandoffValidator:
    def __init__(self) -> None:
        schema_text = files("agent_harness.schemas").joinpath("handoff.schema.json").read_text(
            encoding="utf-8"
        )
        self._validator = Draft202012Validator(json.loads(schema_text))

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _assert_no_symlink_path(path: Path) -> None:
        absolute = path.absolute()
        for component in (absolute, *absolute.parents):
            if component.is_symlink():
                raise ArtifactMismatch(f"artifact root contains a symbolic link: {path}")

    def validate_and_verify(self, document: Mapping[str, Any], artifact_root: Path) -> None:
        errors = sorted(
            self._validator.iter_errors(dict(document)),
            key=lambda item: list(item.path),
        )
        if errors:
            raise SchemaViolation(errors[0].message)
        self._assert_no_symlink_path(artifact_root)
        root = artifact_root.resolve(strict=True)
        artifacts = document["artifacts"]
        if not isinstance(artifacts, list):
            raise SchemaViolation("artifacts must be an array")
        verified_hashes: set[str] = set()
        artifact_types: set[str] = set()
        for entry in artifacts:
            if not isinstance(entry, dict):
                raise SchemaViolation("artifact entries must be objects")
            raw_path = Path(str(entry["path"]))
            if raw_path.is_absolute() or ".." in raw_path.parts:
                raise ArtifactMismatch(f"unsafe artifact path: {raw_path}")
            unresolved = (root / raw_path).absolute()
            current = unresolved
            while current != root.parent:
                if current.is_symlink():
                    raise ArtifactMismatch(
                        f"artifact path contains a symbolic link: {raw_path}"
                    )
                if current.parent == current:
                    break
                current = current.parent
            artifact = unresolved.resolve(strict=True)
            try:
                artifact.relative_to(root)
            except ValueError as error:
                raise ArtifactMismatch(f"artifact escaped root: {raw_path}") from error
            if not artifact.is_file():
                raise ArtifactMismatch(f"artifact is not a regular file: {raw_path}")
            actual = self._sha256(artifact)
            if actual.lower() != str(entry["sha256"]).lower():
                raise ArtifactMismatch(f"artifact hash mismatch: {raw_path}")
            verified_hashes.add(actual.lower())
            artifact_types.add(str(entry["artifact_type"]))
        if len(artifact_types) != len(artifacts):
            raise SchemaViolation("artifact_type values must be unique")
        self._verify_evidence_links(document, verified_hashes)

    @staticmethod
    def _indexed(
        document: Mapping[str, Any], field: str, identifier: str
    ) -> dict[str, Mapping[str, Any]]:
        entries = document[field]
        if not isinstance(entries, list):
            raise SchemaViolation(f"{field} must be an array")
        indexed: dict[str, Mapping[str, Any]] = {}
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise SchemaViolation(f"{field} entries must be objects")
            key = str(entry[identifier])
            if key in indexed:
                raise SchemaViolation(f"duplicate {identifier}: {key}")
            indexed[key] = entry
        return indexed

    def _verify_evidence_links(
        self, document: Mapping[str, Any], verified_hashes: set[str]
    ) -> None:
        sender_role = str(document["sender_role"])
        expected = self._indexed(
            document, "expected_results", "expected_result_id"
        )
        rules = self._indexed(document, "decision_rules", "decision_rule_id")
        observations = self._indexed(document, "observations", "observation_id")
        claims = self._indexed(document, "claims", "claim_id")

        for entry in expected.values():
            if str(entry["owner_role"]) == sender_role:
                raise SchemaViolation(
                    "expected results must be owned independently of the sender"
                )
            for rule_id in entry["decision_rule_ids"]:
                if str(rule_id) not in rules:
                    raise SchemaViolation(
                        f"expected result references unknown decision rule: {rule_id}"
                    )
        for rule in rules.values():
            if str(rule["owner_role"]) == sender_role:
                raise SchemaViolation(
                    "decision rules must be owned independently of the sender"
                )
        observed_expected: set[str] = set()
        for observation in observations.values():
            expected_id = str(observation["expected_result_id"])
            if expected_id not in expected:
                raise SchemaViolation(
                    f"observation references unknown expected result: {expected_id}"
                )
            observed_expected.add(expected_id)
            artifact_hash = str(observation["artifact_sha256"]).lower()
            if artifact_hash not in verified_hashes:
                raise SchemaViolation(
                    "observation does not reference a verified artifact hash"
                )
        missing_observations = set(expected) - observed_expected
        if missing_observations:
            raise SchemaViolation(
                "expected results lack observations: "
                + ", ".join(sorted(missing_observations))
            )
        for claim in claims.values():
            for artifact_hash in claim["artifact_sha256s"]:
                if str(artifact_hash).lower() not in verified_hashes:
                    raise SchemaViolation("claim references an unverified artifact hash")
            for observation_id in claim["observation_ids"]:
                if str(observation_id) not in observations:
                    raise SchemaViolation(
                        f"claim references unknown observation: {observation_id}"
                    )
        decision = document["decision"]
        if not isinstance(decision, Mapping):
            raise SchemaViolation("decision must be an object")
        for rule_id in decision["applied_rule_ids"]:
            if str(rule_id) not in rules:
                raise SchemaViolation(f"decision references unknown rule: {rule_id}")
        if str(decision["outcome"]) == "pass":
            if document["unresolved"]:
                raise SchemaViolation("passing handoffs must not contain unresolved items")
            if any(
                str(observation["outcome"]) != "pass"
                for observation in observations.values()
            ):
                raise SchemaViolation(
                    "passing handoffs require passing observations for every expected result"
                )
