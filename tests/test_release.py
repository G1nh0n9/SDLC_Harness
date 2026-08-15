import json
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agent_harness.authority import AuthorityRequest, AuthorityStore
from agent_harness.candidate import CandidateState, CandidateStore
from agent_harness.evidence import EvidenceLedger
from agent_harness.policy import GatePolicy
from agent_harness.release import (
    ReleaseDecision,
    ReleaseDisposition,
    ReleasePackager,
)
from agent_harness.result_evidence import build_evidence_evaluation
from agent_harness.state_machine import CandidateStateMachine


def complete_inputs(tmp_path: Path) -> dict[str, Path]:
    inputs = {}
    for label in ("source", "requirements", "design", "build-config", "dependencies"):
        directory = tmp_path / "inputs" / label
        directory.mkdir(parents=True)
        (directory / "content.txt").write_text(f"{label}\n", encoding="utf-8")
        inputs[label] = directory
    return inputs


def approved_candidate(tmp_path: Path):  # type: ignore[no-untyped-def]
    inputs = complete_inputs(tmp_path)
    source = inputs["source"]
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    candidate = CandidateStore(tmp_path / "store").freeze_candidate(
        mission_id="mis-1",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
        required_evidence={"acceptance-test"},
    )
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite3")
    evidence_artifact = tmp_path / "acceptance.json"
    evidence_artifact.write_text('{"outcome":"pass"}\n', encoding="utf-8")
    ledger.append(
        mission_id=candidate.mission_id,
        revision=candidate.revision,
        candidate_id=candidate.candidate_id,
        evidence_type="acceptance-test",
        producer_role="verification-specialist",
        outcome="pass",
        artifact_path=evidence_artifact,
        **build_evidence_evaluation(artifact_path=evidence_artifact, outcome="pass"),
        details={},
    )
    machine = CandidateStateMachine()
    machine.transition(candidate, CandidateState.VERIFYING)
    machine.transition(candidate, CandidateState.REVIEWING)
    authority_store = AuthorityStore(tmp_path / "authority.sqlite3")
    grant = authority_store.issue(
        mission_id=candidate.mission_id,
        revision=candidate.revision,
        task_id="task-approval",
        attempt_id="attempt-approval",
        worker_id="expert:validation:independent-code-reviewer",
        workspace_id="workspace-approval",
        candidate_id=candidate.candidate_id,
        role="independent-code-reviewer",
        allowed_operations={"approve-candidate"},
        allowed_tools=set(),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    GatePolicy(machine).approve(
        candidate,
        ledger,
        authority_store=authority_store,
        authority_token=grant.token,
        authority_request=AuthorityRequest(
            mission_id=candidate.mission_id,
            revision=candidate.revision,
            task_id="task-approval",
            attempt_id="attempt-approval",
            worker_id="expert:validation:independent-code-reviewer",
            workspace_id="workspace-approval",
            candidate_id=candidate.candidate_id,
            role="independent-code-reviewer",
            operation="approve-candidate",
            tool=None,
        ),
        expected_mission_id=candidate.mission_id,
        expected_revision=candidate.revision,
    )
    return candidate, machine


def test_release_rechecks_snapshot_after_approval(tmp_path: Path) -> None:
    candidate, machine = approved_candidate(tmp_path)
    (candidate.snapshot_root / "source" / "app.py").write_text(
        "VALUE = 999\n", encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="snapshot"):
        ReleasePackager(machine).package(
            candidate,
            tmp_path / "release",
            decision=ReleaseDecision(ReleaseDisposition.RELEASE),
            expected_mission_id=candidate.mission_id,
            expected_revision=candidate.revision,
        )
    assert candidate.state is CandidateState.CORRUPT
    assert not (tmp_path / "release" / f"{candidate.candidate_id}.zip").exists()


@pytest.mark.parametrize(
    "disposition", [ReleaseDisposition.HOLD, ReleaseDisposition.PROHIBITED]
)
def test_non_release_decisions_do_not_create_package(
    tmp_path: Path, disposition: ReleaseDisposition
) -> None:
    candidate, machine = approved_candidate(tmp_path)

    with pytest.raises(RuntimeError, match="does not allow packaging"):
        ReleasePackager(machine).package(
            candidate,
            tmp_path / "release",
            decision=ReleaseDecision(disposition),
            expected_mission_id=candidate.mission_id,
            expected_revision=candidate.revision,
        )
    assert not (tmp_path / "release").exists()


def test_limited_release_requires_and_records_all_limits(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="limited release requires"):
        ReleaseDecision(ReleaseDisposition.LIMITED_RELEASE, scope="pilot users")

    candidate, machine = approved_candidate(tmp_path)
    decision = ReleaseDecision(
        ReleaseDisposition.LIMITED_RELEASE,
        scope="pilot users",
        expires_at="2026-09-01T00:00:00Z",
        rollback_plan="restore the previous package",
        out_of_scope_controls=("deny non-pilot accounts",),
    )
    artifact = ReleasePackager(machine).package(
        candidate,
        tmp_path / "release",
        decision=decision,
        expected_mission_id=candidate.mission_id,
        expected_revision=candidate.revision,
    )

    with zipfile.ZipFile(artifact.path) as archive:
        manifest = json.loads(archive.read("release-manifest.json"))
    assert manifest["release_decision"]["disposition"] == "limited-release"
    assert manifest["release_decision"]["scope"] == "pilot users"
