from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from collections.abc import Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


class AuthorityDenied(RuntimeError):
    """Raised when a bounded authority grant cannot authorize an operation."""


@dataclass(frozen=True)
class AuthorityRequest:
    mission_id: str
    revision: int
    task_id: str
    attempt_id: str
    worker_id: str
    workspace_id: str
    candidate_id: str | None
    role: str
    operation: str
    tool: str | None


@dataclass(frozen=True)
class IssuedAuthorityGrant:
    grant_id: str
    token: str
    mission_id: str
    revision: int
    task_id: str
    attempt_id: str
    worker_id: str
    workspace_id: str
    candidate_id: str | None
    role: str
    allowed_operations: frozenset[str]
    allowed_tools: frozenset[str]
    expires_at: datetime
    max_uses: int = 1


@dataclass(frozen=True)
class VerifiedAuthority:
    grant_id: str
    role: str
    mission_id: str
    revision: int
    task_id: str
    attempt_id: str
    worker_id: str
    workspace_id: str
    candidate_id: str | None
    operation: str
    tool: str | None
    use_count: int


class AuthorityStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS authority_grants (
                    grant_id TEXT PRIMARY KEY,
                    token_sha256 TEXT NOT NULL UNIQUE,
                    mission_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    task_id TEXT NOT NULL,
                    attempt_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    candidate_id TEXT,
                    role TEXT NOT NULL,
                    allowed_operations_json TEXT NOT NULL,
                    allowed_tools_json TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    max_uses INTEGER NOT NULL,
                    use_count INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def revoke_issued(self, *, task_id: str, operation: str) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE authority_grants
                SET status = 'REVOKED'
                WHERE task_id = ? AND status = 'ISSUED'
                  AND allowed_operations_json = ?
                """,
                (task_id, json.dumps([operation])),
            )
            return cursor.rowcount

    def issue(
        self,
        *,
        mission_id: str,
        revision: int,
        task_id: str,
        attempt_id: str,
        worker_id: str,
        workspace_id: str,
        candidate_id: str | None,
        role: str,
        allowed_operations: Collection[str],
        allowed_tools: Collection[str],
        expires_at: datetime,
    ) -> IssuedAuthorityGrant:
        if expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")
        if not mission_id or revision < 1 or not task_id or not attempt_id:
            raise ValueError("authority grant bindings must be non-empty")
        if not worker_id or not workspace_id or not role or not allowed_operations:
            raise ValueError("authority grant worker, workspace, role, and operations are required")
        token = secrets.token_urlsafe(32)
        grant_id = f"grant-{secrets.token_hex(16)}"
        operations = frozenset(allowed_operations)
        tools = frozenset(allowed_tools)
        normalized_expiry = expires_at.astimezone(UTC)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO authority_grants (
                    grant_id, token_sha256, mission_id, revision, task_id, attempt_id,
                    worker_id, workspace_id, candidate_id, role,
                    allowed_operations_json, allowed_tools_json, expires_at,
                    max_uses, use_count, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 'ISSUED')
                """,
                (
                    grant_id,
                    self._token_hash(token),
                    mission_id,
                    revision,
                    task_id,
                    attempt_id,
                    worker_id,
                    workspace_id,
                    candidate_id,
                    role,
                    json.dumps(sorted(operations)),
                    json.dumps(sorted(tools)),
                    normalized_expiry.isoformat(),
                ),
            )
        return IssuedAuthorityGrant(
            grant_id=grant_id,
            token=token,
            mission_id=mission_id,
            revision=revision,
            task_id=task_id,
            attempt_id=attempt_id,
            worker_id=worker_id,
            workspace_id=workspace_id,
            candidate_id=candidate_id,
            role=role,
            allowed_operations=operations,
            allowed_tools=tools,
            expires_at=normalized_expiry,
        )

    @staticmethod
    def _require_equal(name: str, actual: object, expected: object) -> None:
        if actual != expected:
            raise AuthorityDenied(f"{name.replace('_', ' ')} binding does not match")

    def consume(self, token: str, request: AuthorityRequest) -> VerifiedAuthority:
        if not token:
            raise AuthorityDenied("authority token is required")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM authority_grants WHERE token_sha256 = ?",
                (self._token_hash(token),),
            ).fetchone()
            if row is None:
                raise AuthorityDenied("authority token is unknown")
            if row["status"] != "ISSUED" or row["use_count"] >= row["max_uses"]:
                raise AuthorityDenied("authority grant was already consumed")
            expires_at = datetime.fromisoformat(str(row["expires_at"]))
            if datetime.now(UTC) >= expires_at:
                raise AuthorityDenied("authority grant expired")

            for name in (
                "mission_id",
                "revision",
                "task_id",
                "attempt_id",
                "worker_id",
                "workspace_id",
                "candidate_id",
                "role",
            ):
                self._require_equal(name, getattr(request, name), row[name])
            operations = frozenset(json.loads(str(row["allowed_operations_json"])))
            tools = frozenset(json.loads(str(row["allowed_tools_json"])))
            if request.operation not in operations:
                raise AuthorityDenied("operation is not allowed by authority grant")
            if request.tool is not None and request.tool not in tools:
                raise AuthorityDenied("tool is not allowed by authority grant")
            if request.tool is None and tools:
                raise AuthorityDenied("tool binding does not match")

            use_count = int(row["use_count"]) + 1
            connection.execute(
                """
                UPDATE authority_grants
                SET use_count = ?, status = 'CONSUMED'
                WHERE grant_id = ? AND status = 'ISSUED' AND use_count = 0
                """,
                (use_count, row["grant_id"]),
            )
            if connection.total_changes != 1:
                raise AuthorityDenied("authority grant was already consumed")
            connection.execute("COMMIT")
            return VerifiedAuthority(
                grant_id=str(row["grant_id"]),
                role=str(row["role"]),
                mission_id=request.mission_id,
                revision=request.revision,
                task_id=request.task_id,
                attempt_id=request.attempt_id,
                worker_id=request.worker_id,
                workspace_id=request.workspace_id,
                candidate_id=request.candidate_id,
                operation=request.operation,
                tool=request.tool,
                use_count=use_count,
            )
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
