from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypedDict


class EvidenceEvaluation(TypedDict):
    expected_results: list[dict[str, Any]]
    decision_rules: list[dict[str, Any]]
    observations: list[dict[str, Any]]


def build_evidence_evaluation(
    *,
    artifact_path: Path,
    outcome: str,
    expected_owner_role: str = "mission-manager",
) -> EvidenceEvaluation:
    if outcome not in {"pass", "fail", "inconclusive"}:
        raise ValueError("outcome must be pass, fail, or inconclusive")
    digest = hashlib.sha256(artifact_path.resolve(strict=True).read_bytes()).hexdigest()
    return {
        "expected_results": [
            {
                "expected_result_id": "expected-result-1",
                "description": "the evidence artifact records the assigned check result",
                "owner_role": expected_owner_role,
                "decision_rule_ids": ["decision-rule-1"],
            }
        ],
        "decision_rules": [
            {
                "decision_rule_id": "decision-rule-1",
                "description": "the observed check result must satisfy the assigned expectation",
                "owner_role": expected_owner_role,
            }
        ],
        "observations": [
            {
                "observation_id": "observation-1",
                "expected_result_id": "expected-result-1",
                "artifact_sha256": digest,
                "observed_value": outcome,
                "outcome": outcome,
            }
        ],
    }


def build_result_evidence(
    *,
    artifact_path: Path,
    artifact_root: Path,
    artifact_types: Sequence[str],
    claim: str,
    gate: str,
    expected_owner_role: str = "mission-manager",
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if gate not in {"pass", "fail", "inconclusive"}:
        raise ValueError("gate must be pass, fail, or inconclusive")
    if not artifact_types or any(not item.strip() for item in artifact_types):
        raise ValueError("at least one non-empty artifact type is required")
    root = artifact_root.resolve(strict=True)
    artifact = artifact_path.resolve(strict=True)
    try:
        relative_path = artifact.relative_to(root)
    except ValueError as exc:
        raise ValueError("result artifact must be below artifact_root") from exc
    if not artifact.is_file():
        raise ValueError("result artifact must be a regular file")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    evaluation = build_evidence_evaluation(
        artifact_path=artifact,
        outcome=gate,
        expected_owner_role=expected_owner_role,
    )
    observation_id = "observation-1"
    payload: dict[str, Any] = {
        "gate": gate,
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "artifact_sha256s": [digest],
                "observation_ids": [observation_id],
            }
        ],
        **evaluation,
        "decision": {
            "outcome": gate,
            "applied_rule_ids": ["decision-rule-1"],
            "rationale": "the decision follows the independently owned rule and bound observation",
        },
        "assumptions": [],
        "unresolved": [],
        "artifacts": [
            {
                "artifact_type": artifact_type,
                "path": relative_path.as_posix(),
                "sha256": digest,
                "media_type": "application/json",
            }
            for artifact_type in dict.fromkeys(artifact_types)
        ],
    }
    if extra:
        payload.update(dict(extra))
    return payload
