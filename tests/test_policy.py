from collections.abc import Collection
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypedDict

import pytest

from agent_harness.authority import AuthorityRequest, AuthorityStore
from agent_harness.candidate import Candidate, CandidateState, CandidateStore
from agent_harness.evidence import EvidenceLedger, EvidenceRecord
from agent_harness.policy import GateDenied, GatePolicy
from agent_harness.result_evidence import build_evidence_evaluation
from agent_harness.state_machine import CandidateStateMachine


def evidence_artifact(tmp_path: Path, name: str) -> Path:
    artifact = tmp_path / f"{name}.json"
    artifact.write_text(f'{{"name":"{name}"}}\n', encoding="utf-8")
    return artifact


def append_evidence(
    ledger: EvidenceLedger,
    candidate: Candidate,
    tmp_path: Path,
    *,
    evidence_type: str,
    producer_role: str,
    outcome: str,
    name: str,
) -> EvidenceRecord:
    artifact = evidence_artifact(tmp_path, name)
    return ledger.append(
        mission_id=candidate.mission_id,
        revision=candidate.revision,
        candidate_id=candidate.candidate_id,
        evidence_type=evidence_type,
        producer_role=producer_role,
        outcome=outcome,
        artifact_path=artifact,
        **build_evidence_evaluation(artifact_path=artifact, outcome=outcome),
        details={},
    )


def complete_inputs(tmp_path: Path, name: str = "inputs") -> dict[str, Path]:
    inputs = {}
    for label in ("source", "requirements", "design", "build-config", "dependencies"):
        directory = tmp_path / name / label
        directory.mkdir(parents=True)
        (directory / "content.txt").write_text(f"{label}\n", encoding="utf-8")
        inputs[label] = directory
    return inputs


def frozen_candidate(
    tmp_path: Path,
    required_evidence: Collection[str] = ("acceptance-test", "security-review"),
) -> Candidate:
    inputs = complete_inputs(tmp_path)
    source = inputs["source"]
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    return CandidateStore(tmp_path / "candidates").freeze_candidate(
        mission_id="mis-1",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
        required_evidence=required_evidence,
        created_by_role="implementation-specialist",
    )


class ApprovalAuthorityKwargs(TypedDict):
    authority_store: AuthorityStore
    authority_token: str
    authority_request: AuthorityRequest


def approval_authority(
    tmp_path: Path, candidate: Candidate, role: str
) -> ApprovalAuthorityKwargs:
    store = AuthorityStore(tmp_path / "approval-authority.sqlite3")
    grant = store.issue(
        mission_id=candidate.mission_id,
        revision=candidate.revision,
        task_id="task-approval",
        attempt_id="attempt-approval",
        worker_id=f"expert:validation:{role}",
        workspace_id="workspace-approval",
        candidate_id=candidate.candidate_id,
        role=role,
        allowed_operations={"approve-candidate"},
        allowed_tools=set(),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    return {
        "authority_store": store,
        "authority_token": grant.token,
        "authority_request": AuthorityRequest(
            mission_id=candidate.mission_id,
            revision=candidate.revision,
            task_id="task-approval",
            attempt_id="attempt-approval",
            worker_id=f"expert:validation:{role}",
            workspace_id="workspace-approval",
            candidate_id=candidate.candidate_id,
            role=role,
            operation="approve-candidate",
            tool=None,
        ),
    }


def test_stale_evidence_and_self_approval_are_blocked(tmp_path: Path) -> None:
    candidate = frozen_candidate(tmp_path)
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite3")
    acceptance_record = append_evidence(
        ledger,
        candidate,
        tmp_path,
        evidence_type="acceptance-test",
        producer_role="verification-specialist",
        outcome="pass",
        name="acceptance-1",
    )
    security = append_evidence(
        ledger,
        candidate,
        tmp_path,
        evidence_type="security-review",
        producer_role="security-reviewer",
        outcome="pass",
        name="security-1",
    )
    ledger.invalidate(security.event_id, producer_role="mission-manager", reason="source changed")
    policy = GatePolicy()
    machine = CandidateStateMachine()
    machine.transition(candidate, CandidateState.VERIFYING)
    machine.transition(candidate, CandidateState.REVIEWING)

    with pytest.raises(GateDenied, match="security-review"):
        policy.approve(
            candidate,
            ledger,
            **approval_authority(tmp_path, candidate, "independent-code-reviewer"),
            expected_mission_id=candidate.mission_id,
            expected_revision=candidate.revision,
        )
    assert candidate.state is CandidateState.REVIEWING

    append_evidence(
        ledger,
        candidate,
        tmp_path,
        evidence_type="security-review",
        producer_role="security-reviewer",
        outcome="pass",
        name="security-2",
    )
    with pytest.raises(GateDenied, match="self-approval"):
        policy.approve(
            candidate,
            ledger,
            **approval_authority(tmp_path, candidate, "implementation-specialist"),
            expected_mission_id=candidate.mission_id,
            expected_revision=candidate.revision,
        )

    decision = policy.approve(
        candidate,
        ledger,
        **approval_authority(tmp_path, candidate, "independent-code-reviewer"),
        expected_mission_id=candidate.mission_id,
        expected_revision=candidate.revision,
    )
    assert decision.candidate_id == candidate.candidate_id
    assert ledger.status(acceptance_record.event_id).value == "valid"


def test_approval_requires_reviewing_state_even_with_complete_evidence(tmp_path: Path) -> None:
    candidate = frozen_candidate(tmp_path, {"acceptance-test"})
    ledger = EvidenceLedger(tmp_path / "gate.sqlite3")
    append_evidence(
        ledger,
        candidate,
        tmp_path,
        evidence_type="acceptance-test",
        producer_role="verification-specialist",
        outcome="pass",
        name="acceptance-2",
    )

    with pytest.raises(GateDenied, match="reviewing"):
        GatePolicy().approve(
            candidate,
            ledger,
            **approval_authority(tmp_path, candidate, "independent-code-reviewer"),
            expected_mission_id=candidate.mission_id,
            expected_revision=candidate.revision,
        )

    machine = CandidateStateMachine()
    machine.transition(candidate, CandidateState.VERIFYING)
    machine.transition(candidate, CandidateState.REVIEWING)
    GatePolicy().approve(
        candidate,
        ledger,
        **approval_authority(tmp_path, candidate, "independent-code-reviewer"),
        expected_mission_id=candidate.mission_id,
        expected_revision=candidate.revision,
    )
    assert candidate.state is CandidateState.APPROVED


def test_candidate_bound_evidence_requirement_cannot_be_dropped(tmp_path: Path) -> None:
    inputs = complete_inputs(tmp_path, "bound-inputs")
    source = inputs["source"]
    (source / "analysis.py").write_text("VALUE = 1\n", encoding="utf-8")
    candidate = CandidateStore(tmp_path / "bound-store").freeze_candidate(
        mission_id="mis-research",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
        required_evidence={"acceptance-test", "scope-purity"},
    )
    ledger = EvidenceLedger(tmp_path / "bound-evidence.sqlite3")
    append_evidence(
        ledger,
        candidate,
        tmp_path,
        evidence_type="acceptance-test",
        producer_role="verification-specialist",
        outcome="pass",
        name="acceptance-3",
    )
    machine = CandidateStateMachine()
    machine.transition(candidate, CandidateState.VERIFYING)
    machine.transition(candidate, CandidateState.REVIEWING)

    with pytest.raises(GateDenied, match="scope-purity"):
        GatePolicy(machine).approve(
            candidate,
            ledger,
            **approval_authority(tmp_path, candidate, "independent-code-reviewer"),
            expected_mission_id=candidate.mission_id,
            expected_revision=candidate.revision,
        )


def test_latest_failure_overrides_earlier_passing_evidence(tmp_path: Path) -> None:
    candidate = frozen_candidate(tmp_path, {"acceptance-test"})
    ledger = EvidenceLedger(tmp_path / "latest.sqlite3")
    for outcome in ("pass", "fail"):
        append_evidence(
            ledger,
            candidate,
            tmp_path,
            evidence_type="acceptance-test",
            producer_role="verification-specialist",
            outcome=outcome,
            name=f"acceptance-{outcome}",
        )
    machine = CandidateStateMachine()
    machine.transition(candidate, CandidateState.VERIFYING)
    machine.transition(candidate, CandidateState.REVIEWING)

    with pytest.raises(GateDenied, match="acceptance-test"):
        GatePolicy(machine).approve(
            candidate,
            ledger,
            **approval_authority(tmp_path, candidate, "independent-code-reviewer"),
            expected_mission_id=candidate.mission_id,
            expected_revision=candidate.revision,
        )


@pytest.mark.parametrize(
    ("producer_role", "reviewer_role", "message"),
    [
        ("implementation-specialist", "independent-code-reviewer", "acceptance-test"),
        ("unregistered-producer", "independent-code-reviewer", "acceptance-test"),
        ("verification-specialist", "verification-specialist", "not allowed to approve"),
        ("verification-specialist", "unknown-reviewer", "not registered"),
    ],
)
def test_approval_enforces_registered_separated_roles(
    tmp_path: Path,
    producer_role: str,
    reviewer_role: str,
    message: str,
) -> None:
    candidate = frozen_candidate(tmp_path, {"acceptance-test"})
    ledger = EvidenceLedger(tmp_path / f"roles-{producer_role}.sqlite3")
    append_evidence(
        ledger,
        candidate,
        tmp_path,
        evidence_type="acceptance-test",
        producer_role=producer_role,
        outcome="pass",
        name=f"roles-{producer_role}",
    )
    machine = CandidateStateMachine()
    machine.transition(candidate, CandidateState.VERIFYING)
    machine.transition(candidate, CandidateState.REVIEWING)

    with pytest.raises(GateDenied, match=message):
        GatePolicy(machine).approve(
            candidate,
            ledger,
            **approval_authority(tmp_path, candidate, reviewer_role),
            expected_mission_id=candidate.mission_id,
            expected_revision=candidate.revision,
        )
