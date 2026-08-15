import sqlite3
from pathlib import Path

import pytest

from agent_harness.evidence import EvidenceLedger, EvidenceStatus
from agent_harness.result_evidence import build_evidence_evaluation


def test_evidence_ledger_is_append_only_and_hash_chained(tmp_path: Path) -> None:
    database = tmp_path / "evidence.sqlite3"
    ledger = EvidenceLedger(database)
    acceptance_artifact = tmp_path / "acceptance.json"
    acceptance_artifact.write_text('{"exit_code":0}\n', encoding="utf-8")
    security_artifact = tmp_path / "security.json"
    security_artifact.write_text('{"finding_count":0}\n', encoding="utf-8")
    first = ledger.append(
        mission_id="mis-1",
        revision=1,
        candidate_id="cand-1",
        evidence_type="acceptance-test",
        producer_role="verification-specialist",
        outcome="pass",
        artifact_path=acceptance_artifact,
        **build_evidence_evaluation(artifact_path=acceptance_artifact, outcome="pass"),
        details={"command": "pytest tests/acceptance"},
    )
    ledger.append(
        mission_id="mis-1",
        revision=1,
        candidate_id="cand-1",
        evidence_type="security-review",
        producer_role="security-reviewer",
        outcome="pass",
        artifact_path=security_artifact,
        **build_evidence_evaluation(artifact_path=security_artifact, outcome="pass"),
        details={"finding_count": 0},
    )

    assert ledger.verify_chain() is True
    assert ledger.status(first.event_id) is EvidenceStatus.VALID

    outsider = sqlite3.connect(database)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        outsider.execute(
            "UPDATE evidence_events SET outcome = 'fail' WHERE event_id = ?",
            (first.event_id,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        outsider.execute(
            "UPDATE evidence_artifact_bindings SET revision = 99 "
            "WHERE artifact_sha256 = ?",
            (first.artifact_sha256,),
        )
    outsider.close()

    assert first.artifact_sha256 != "a" * 64
    assert first.details["artifact_path"] == str(acceptance_artifact.resolve())


def test_evidence_requires_a_real_non_symbolic_artifact(tmp_path: Path) -> None:
    ledger = EvidenceLedger(tmp_path / "strict.sqlite3")
    with pytest.raises(FileNotFoundError):
        ledger.append(
            mission_id="mis-1",
            revision=1,
            candidate_id="cand-1",
            evidence_type="acceptance-test",
            producer_role="verification-specialist",
            outcome="pass",
            artifact_path=tmp_path / "missing.json",
            expected_results=[],
            decision_rules=[],
            observations=[],
            details={},
        )

    target = tmp_path / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    link = tmp_path / "link.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symbolic links are not available on this system")
    with pytest.raises(ValueError, match="symbolic links"):
        ledger.append(
            mission_id="mis-1",
            revision=1,
            candidate_id="cand-1",
            evidence_type="acceptance-test",
            producer_role="verification-specialist",
            outcome="pass",
            artifact_path=link,
            expected_results=[],
            decision_rules=[],
            observations=[],
            details={},
        )


def test_evidence_rejects_self_owned_or_unbound_expected_results(tmp_path: Path) -> None:
    artifact = tmp_path / "evidence.json"
    artifact.write_text('{"outcome":"pass"}\n', encoding="utf-8")
    evaluation = build_evidence_evaluation(
        artifact_path=artifact,
        outcome="pass",
        expected_owner_role="verification-specialist",
    )
    with pytest.raises(ValueError, match="independent owner"):
        EvidenceLedger(tmp_path / "ownership.sqlite3").append(
            mission_id="mis-1",
            revision=1,
            candidate_id="cand-1",
            evidence_type="acceptance-test",
            producer_role="verification-specialist",
            outcome="pass",
            artifact_path=artifact,
            **evaluation,
        )

    evaluation = build_evidence_evaluation(artifact_path=artifact, outcome="pass")
    evaluation["observations"][0]["artifact_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="not bound"):
        EvidenceLedger(tmp_path / "binding.sqlite3").append(
            mission_id="mis-1",
            revision=1,
            candidate_id="cand-1",
            evidence_type="acceptance-test",
            producer_role="verification-specialist",
            outcome="pass",
            artifact_path=artifact,
            **evaluation,
        )


def test_evidence_artifact_hash_cannot_be_rebound_to_another_revision(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "acceptance.json"
    artifact.write_text('{"outcome":"pass"}\n', encoding="utf-8")
    evaluation = build_evidence_evaluation(artifact_path=artifact, outcome="pass")
    ledger = EvidenceLedger(tmp_path / "cross-revision.sqlite3")
    ledger.append(
        mission_id="mis-1",
        revision=1,
        candidate_id="cand-content",
        evidence_type="acceptance-test",
        producer_role="verification-specialist",
        outcome="pass",
        artifact_path=artifact,
        **evaluation,
    )

    with pytest.raises(ValueError, match="already bound"):
        ledger.append(
            mission_id="mis-1",
            revision=2,
            candidate_id="cand-content",
            evidence_type="acceptance-test",
            producer_role="verification-specialist",
            outcome="pass",
            artifact_path=artifact,
            **evaluation,
        )
