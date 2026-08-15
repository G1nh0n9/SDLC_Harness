from __future__ import annotations

from .candidate import Candidate, CandidateState


class InvalidTransition(RuntimeError):
    """Raised when a candidate state transition is not allowed."""


class CandidateStateMachine:
    _allowed: dict[CandidateState, frozenset[CandidateState]] = {
        CandidateState.FROZEN: frozenset({CandidateState.VERIFYING, CandidateState.CORRUPT}),
        CandidateState.VERIFYING: frozenset(
            {CandidateState.REVIEWING, CandidateState.REVIEW_FAILED, CandidateState.CORRUPT}
        ),
        CandidateState.REVIEWING: frozenset(
            {CandidateState.APPROVED, CandidateState.REVIEW_FAILED, CandidateState.CORRUPT}
        ),
        CandidateState.APPROVED: frozenset(
            {CandidateState.PACKAGING, CandidateState.CORRUPT}
        ),
        CandidateState.PACKAGING: frozenset(
            {CandidateState.RELEASE_READY, CandidateState.CORRUPT}
        ),
        CandidateState.RELEASE_READY: frozenset(),
        CandidateState.REVIEW_FAILED: frozenset(),
        CandidateState.CORRUPT: frozenset(),
    }

    def transition(self, candidate: Candidate, target: CandidateState) -> None:
        allowed = self._allowed[candidate.state]
        if target not in allowed:
            raise InvalidTransition(
                f"cannot transition candidate from {candidate.state.value} to {target.value}"
            )
        candidate._transition_state(target)
