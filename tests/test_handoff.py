import hashlib
from pathlib import Path

import pytest

from agent_harness.handoff import ArtifactMismatch, HandoffValidator, SchemaViolation


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_document(
    artifact: Path,
    *,
    artifact_name: str | None = None,
    sender_role: str = "architecture-specialist",
    stage: str = "design",
) -> dict[str, object]:
    artifact_hash = sha256(artifact)
    return {
        "schema_version": "2.0",
        "document_type": "work-order-result",
        "mission_id": "mis-1",
        "revision": 1,
        "task_id": "task-1",
        "stage": stage,
        "candidate_id": None,
        "sender_role": sender_role,
        "receiver_role": "mission-manager",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "the expected result was observed",
                "artifact_sha256s": [artifact_hash],
                "observation_ids": ["observation-1"],
            }
        ],
        "expected_results": [
            {
                "expected_result_id": "expected-1",
                "description": "the artifact contains the selected design",
                "owner_role": "requirements-specialist",
                "decision_rule_ids": ["rule-1"],
            }
        ],
        "decision_rules": [
            {
                "decision_rule_id": "rule-1",
                "description": "the selected design is recorded",
                "owner_role": "requirements-specialist",
            }
        ],
        "observations": [
            {
                "observation_id": "observation-1",
                "expected_result_id": "expected-1",
                "artifact_sha256": artifact_hash,
                "observed_value": "selected design recorded",
                "outcome": "pass",
            }
        ],
        "decision": {
            "outcome": "pass",
            "applied_rule_ids": ["rule-1"],
            "rationale": "the verified artifact satisfies the independently owned rule",
        },
        "assumptions": [],
        "unresolved": [],
        "artifacts": [
            {
                "artifact_type": "design-baseline",
                "path": artifact_name or artifact.name,
                "sha256": artifact_hash,
                "media_type": "application/json",
            }
        ],
    }


def test_handoff_requires_schema_and_matching_artifact_hash(tmp_path: Path) -> None:
    artifact = tmp_path / "design.json"
    artifact.write_text('{"decision":"queue"}\n', encoding="utf-8")
    document = evidence_document(artifact)
    validator = HandoffValidator()

    validator.validate_and_verify(document, tmp_path)

    incomplete = dict(document)
    incomplete.pop("claims")
    with pytest.raises(SchemaViolation, match="claims"):
        validator.validate_and_verify(incomplete, tmp_path)

    artifact.write_text('{"decision":"tampered"}\n', encoding="utf-8")
    with pytest.raises(ArtifactMismatch, match="design.json"):
        validator.validate_and_verify(document, tmp_path)


def test_handoff_rejects_unverified_claims_and_self_owned_decision_rules(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "result.json"
    artifact.write_text('{"result":"pass"}\n', encoding="utf-8")
    document = evidence_document(artifact)

    unsupported = dict(document)
    unsupported["claims"] = [
        {
            "claim_id": "claim-1",
            "claim": "unsupported completion",
            "artifact_sha256s": ["a" * 64],
            "observation_ids": ["observation-1"],
        }
    ]
    with pytest.raises(SchemaViolation, match="unverified artifact"):
        HandoffValidator().validate_and_verify(unsupported, tmp_path)

    self_owned = dict(document)
    self_owned["decision_rules"] = [
        {
            "decision_rule_id": "rule-1",
            "description": "the sender says the work is complete",
            "owner_role": "architecture-specialist",
        }
    ]
    with pytest.raises(SchemaViolation, match="independently"):
        HandoffValidator().validate_and_verify(self_owned, tmp_path)


def test_handoff_rejects_symbolic_link_artifact(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text('{"result":"pass"}\n', encoding="utf-8")
    link = tmp_path / "linked.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symbolic links are not available on this system")
    document = evidence_document(
        target,
        artifact_name="linked.json",
        sender_role="verification-specialist",
        stage="integration-verification",
    )

    with pytest.raises(ArtifactMismatch, match="symbolic link"):
        HandoffValidator().validate_and_verify(document, tmp_path)


def test_handoff_rejects_symlinked_artifact_root(tmp_path: Path) -> None:
    real_root = tmp_path / "real-root"
    real_root.mkdir()
    artifact = real_root / "result.json"
    artifact.write_text("{}\n", encoding="utf-8")
    linked_root = tmp_path / "linked-root"
    try:
        linked_root.symlink_to(real_root, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are not available")
    document = evidence_document(
        artifact,
        sender_role="verification-specialist",
        stage="integration-verification",
    )
    document["mission_id"] = "mis-root-link"
    document["task_id"] = "task-root-link"

    with pytest.raises(ArtifactMismatch, match="artifact root contains a symbolic link"):
        HandoffValidator().validate_and_verify(document, linked_root)


def test_handoff_rejects_symlinked_intermediate_directory(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifact-root"
    real_directory = tmp_path / "real-directory"
    artifact_root.mkdir()
    real_directory.mkdir()
    artifact = real_directory / "result.json"
    artifact.write_text('{"result":"pass"}\n', encoding="utf-8")
    linked_directory = artifact_root / "linked-directory"
    try:
        linked_directory.symlink_to(real_directory, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are not available")
    document = evidence_document(
        artifact,
        artifact_name="linked-directory/result.json",
        sender_role="verification-specialist",
        stage="integration-verification",
    )

    with pytest.raises(ArtifactMismatch, match="artifact path contains a symbolic link"):
        HandoffValidator().validate_and_verify(document, artifact_root)
