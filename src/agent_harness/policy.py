from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass

from .authority import AuthorityDenied, AuthorityRequest, AuthorityStore
from .candidate import Candidate, CandidateState
from .evidence import EvidenceLedger, EvidenceStatus
from .state_machine import CandidateStateMachine
from .workspace import RoleCatalog


class GateDenied(RuntimeError):
    """Raised when candidate approval requirements are not satisfied."""


@dataclass(frozen=True)
class GateDecision:
    candidate_id: str
    reviewer_role: str
    evidence_types: frozenset[str]
    authority_grant_id: str


class GatePolicy:
    _default_evidence_roles: Mapping[str, Collection[str]] = {
        "acceptance-test": {"verification-specialist", "oracle-specialist"},
        "security-review": {
            "independent-code-reviewer",
            "independent-spec-reviewer",
            "security-reviewer",
        },
    }

    def __init__(
        self,
        state_machine: CandidateStateMachine | None = None,
        *,
        role_catalog: RoleCatalog | None = None,
        evidence_roles: Mapping[str, Collection[str]] | None = None,
    ) -> None:
        self._state_machine = state_machine or CandidateStateMachine()
        self._role_catalog = role_catalog or RoleCatalog.default()
        self._evidence_roles = evidence_roles or self._default_evidence_roles

    def approve(
        self,
        candidate: Candidate,
        ledger: EvidenceLedger,
        *,
        authority_store: AuthorityStore,
        authority_token: str,
        authority_request: AuthorityRequest,
        expected_mission_id: str,
        expected_revision: int,
    ) -> GateDecision:
        if authority_request.operation != "approve-candidate":
            raise GateDenied("authority operation does not allow candidate approval")
        if authority_request.candidate_id != candidate.candidate_id:
            raise GateDenied("authority candidate does not match reviewed candidate")
        if authority_request.mission_id != expected_mission_id:
            raise GateDenied("authority mission does not match current mission")
        if authority_request.revision != expected_revision:
            raise GateDenied("authority revision does not match current revision")
        try:
            authority = authority_store.consume(authority_token, authority_request)
        except AuthorityDenied as error:
            raise GateDenied(str(error)) from error
        reviewer_role = authority.role
        if candidate.mission_id != expected_mission_id:
            raise GateDenied("candidate does not match current mission")
        if candidate.revision != expected_revision:
            raise GateDenied("candidate does not match current revision")
        if candidate.state is CandidateState.CORRUPT:
            raise GateDenied("corrupt candidate cannot be approved")
        if candidate.state is not CandidateState.REVIEWING:
            raise GateDenied("candidate must be in reviewing state before approval")
        try:
            reviewer_profile = self._role_catalog[reviewer_role]
        except KeyError as error:
            raise GateDenied("reviewer role is not registered") from error
        if reviewer_role == candidate.created_by_role:
            raise GateDenied("self-approval is forbidden")
        if not reviewer_profile.can_approve:
            raise GateDenied("reviewer role is not allowed to approve")
        required_evidence = frozenset(candidate.manifest["required_evidence"])
        if not required_evidence:
            raise GateDenied("candidate has no bound evidence requirements")
        if not ledger.verify_chain():
            raise GateDenied("evidence ledger hash chain is invalid")

        records = ledger.records_for(
            candidate.mission_id, candidate.revision, candidate.candidate_id
        )
        latest_by_type = {}
        for record in records:
            latest_by_type[record.evidence_type] = record
        registered_producers = set()
        for record in latest_by_type.values():
            try:
                self._role_catalog[record.producer_role]
            except KeyError:
                continue
            registered_producers.add(record.producer_role)
        incomplete = {
            evidence_type
            for evidence_type in required_evidence
            if evidence_type in latest_by_type
            and not latest_by_type[evidence_type].has_bound_evaluation()
        }
        if incomplete:
            raise GateDenied(
                "evidence lacks expected results and bound observations: "
                + ", ".join(sorted(incomplete))
            )
        fresh_passes = {
            evidence_type
            for evidence_type, record in latest_by_type.items()
            if record.outcome == "pass"
            and ledger.status(record.event_id) is EvidenceStatus.VALID
            and record.producer_role in registered_producers
            and record.producer_role != candidate.created_by_role
            and record.producer_role in self._evidence_roles.get(evidence_type, ())
        }
        missing = set(required_evidence) - fresh_passes
        if missing:
            joined = ", ".join(sorted(missing))
            raise GateDenied(f"missing fresh passing evidence: {joined}")

        self._state_machine.transition(candidate, CandidateState.APPROVED)
        return GateDecision(
            candidate_id=candidate.candidate_id,
            reviewer_role=reviewer_role,
            evidence_types=frozenset(required_evidence),
            authority_grant_id=authority.grant_id,
        )
