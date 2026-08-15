from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agent_harness.authority import (
    AuthorityDenied,
    AuthorityRequest,
    AuthorityStore,
)


def bound_request(**changes: object) -> AuthorityRequest:
    values: dict[str, object] = {
        "mission_id": "mis-1",
        "revision": 3,
        "task_id": "task-1",
        "attempt_id": "attempt-1",
        "worker_id": "worker-1",
        "workspace_id": "workspace-1",
        "candidate_id": "cand-1",
        "role": "verification-specialist",
        "operation": "submit-result",
        "tool": "hermes",
    }
    values.update(changes)
    return AuthorityRequest(**values)  # type: ignore[arg-type]


def issue(store: AuthorityStore):  # type: ignore[no-untyped-def]
    return store.issue(
        mission_id="mis-1",
        revision=3,
        task_id="task-1",
        attempt_id="attempt-1",
        worker_id="worker-1",
        workspace_id="workspace-1",
        candidate_id="cand-1",
        role="verification-specialist",
        allowed_operations={"submit-result"},
        allowed_tools={"hermes"},
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mission_id", "mis-other"),
        ("revision", 4),
        ("task_id", "task-other"),
        ("attempt_id", "attempt-other"),
        ("worker_id", "worker-other"),
        ("workspace_id", "workspace-other"),
        ("candidate_id", "cand-other"),
        ("role", "implementation-specialist"),
        ("operation", "approve-candidate"),
        ("tool", "shell"),
    ],
)
def test_authority_grant_is_bound_to_every_security_dimension(
    tmp_path: Path, field: str, value: object
) -> None:
    store = AuthorityStore(tmp_path / "authority.sqlite3")
    grant = issue(store)

    with pytest.raises(AuthorityDenied, match=field.replace("_", " ")):
        store.consume(grant.token, bound_request(**{field: value}))

    verified = store.consume(grant.token, bound_request())
    assert verified.role == "verification-specialist"
    assert verified.use_count == 1


def test_authority_grant_is_one_use_and_replay_is_rejected(tmp_path: Path) -> None:
    store = AuthorityStore(tmp_path / "authority.sqlite3")
    grant = issue(store)

    first = store.consume(grant.token, bound_request())
    assert first.grant_id == grant.grant_id
    with pytest.raises(AuthorityDenied, match="already consumed"):
        store.consume(grant.token, bound_request())


def test_expired_authority_grant_is_rejected_without_becoming_usable(
    tmp_path: Path,
) -> None:
    store = AuthorityStore(tmp_path / "authority.sqlite3")
    grant = store.issue(
        mission_id="mis-1",
        revision=3,
        task_id="task-1",
        attempt_id="attempt-1",
        worker_id="worker-1",
        workspace_id="workspace-1",
        candidate_id=None,
        role="risk-analyst",
        allowed_operations={"submit-result"},
        allowed_tools=set(),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    with pytest.raises(AuthorityDenied, match="expired"):
        store.consume(
            grant.token,
            bound_request(candidate_id=None, tool=None),
        )
