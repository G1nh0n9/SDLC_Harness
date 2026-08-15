from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class EvidenceStatus(StrEnum):
    VALID = "valid"
    STALE = "stale"
    REJECTED = "rejected"


@dataclass(frozen=True)
class EvidenceRecord:
    event_id: str
    event_type: str
    subject_id: str | None
    mission_id: str
    revision: int
    candidate_id: str
    evidence_type: str
    producer_role: str
    outcome: str
    artifact_sha256: str
    details: Mapping[str, Any]
    previous_hash: str
    record_hash: str

    def has_bound_evaluation(self) -> bool:
        return all(
            isinstance(self.details.get(field), list) and bool(self.details[field])
            for field in ("expected_results", "decision_rules", "observations")
        )


class EvidenceLedger:
    _sha256_pattern = re.compile(r"^[0-9a-f]{64}$")

    def __init__(self, database: Path) -> None:
        self.database = database.resolve()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS evidence_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    subject_id TEXT,
                    mission_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    candidate_id TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    producer_role TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    artifact_sha256 TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS evidence_artifact_bindings (
                    artifact_sha256 TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    candidate_id TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS evidence_events_no_update
                BEFORE UPDATE ON evidence_events
                BEGIN
                    SELECT RAISE(ABORT, 'evidence ledger is append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS evidence_events_no_delete
                BEFORE DELETE ON evidence_events
                BEGIN
                    SELECT RAISE(ABORT, 'evidence ledger is append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS evidence_artifact_bindings_no_update
                BEFORE UPDATE ON evidence_artifact_bindings
                BEGIN
                    SELECT RAISE(ABORT, 'evidence artifact bindings are append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS evidence_artifact_bindings_no_delete
                BEFORE DELETE ON evidence_artifact_bindings
                BEGIN
                    SELECT RAISE(ABORT, 'evidence artifact bindings are append-only');
                END;
                """
            )
            event_rows = connection.execute(
                """
                SELECT artifact_sha256, mission_id, revision, candidate_id
                FROM evidence_events
                WHERE event_type = 'evidence'
                ORDER BY sequence
                """
            ).fetchall()
            event_bindings: dict[str, tuple[str, int, str]] = {}
            for row in event_rows:
                artifact_sha256 = str(row["artifact_sha256"])
                target = (
                    str(row["mission_id"]),
                    int(row["revision"]),
                    str(row["candidate_id"]),
                )
                existing = event_bindings.setdefault(artifact_sha256, target)
                if existing != target:
                    raise ValueError(
                        "existing evidence artifact hash is bound to multiple targets"
                    )
            stored_rows = connection.execute(
                """
                SELECT artifact_sha256, mission_id, revision, candidate_id
                FROM evidence_artifact_bindings
                """
            ).fetchall()
            stored_bindings = {
                str(row["artifact_sha256"]): (
                    str(row["mission_id"]),
                    int(row["revision"]),
                    str(row["candidate_id"]),
                )
                for row in stored_rows
            }
            if any(
                digest not in event_bindings or event_bindings[digest] != target
                for digest, target in stored_bindings.items()
            ):
                raise ValueError("evidence artifact binding table does not match events")
            for digest, target in event_bindings.items():
                if digest not in stored_bindings:
                    connection.execute(
                        """
                        INSERT INTO evidence_artifact_bindings (
                            artifact_sha256, mission_id, revision, candidate_id
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (digest, *target),
                    )

    @staticmethod
    def _hash_payload(payload: Mapping[str, Any], previous_hash: str) -> str:
        envelope = {"payload": payload, "previous_hash": previous_hash}
        canonical = json.dumps(
            envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def _append_event(
        self,
        *,
        event_type: str,
        subject_id: str | None,
        mission_id: str,
        revision: int,
        candidate_id: str,
        evidence_type: str,
        producer_role: str,
        outcome: str,
        artifact_sha256: str,
        details: Mapping[str, Any],
    ) -> EvidenceRecord:
        if not self._sha256_pattern.fullmatch(artifact_sha256.lower()):
            raise ValueError("artifact_sha256 must be a 64-character hex digest")
        event_id = f"ev-{uuid.uuid4().hex}"
        details_dict = dict(details)
        payload: dict[str, Any] = {
            "event_id": event_id,
            "event_type": event_type,
            "subject_id": subject_id,
            "mission_id": mission_id,
            "revision": revision,
            "candidate_id": candidate_id,
            "evidence_type": evidence_type,
            "producer_role": producer_role,
            "outcome": outcome,
            "artifact_sha256": artifact_sha256,
            "details": details_dict,
        }
        with self._connect() as connection:
            if event_type == "evidence":
                binding = connection.execute(
                    """
                    SELECT mission_id, revision, candidate_id
                    FROM evidence_artifact_bindings
                    WHERE artifact_sha256 = ?
                    """,
                    (artifact_sha256,),
                ).fetchone()
                expected_binding = (mission_id, revision, candidate_id)
                if binding is None:
                    connection.execute(
                        """
                        INSERT INTO evidence_artifact_bindings (
                            artifact_sha256, mission_id, revision, candidate_id
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (artifact_sha256, *expected_binding),
                    )
                elif (
                    str(binding["mission_id"]),
                    int(binding["revision"]),
                    str(binding["candidate_id"]),
                ) != expected_binding:
                    raise ValueError(
                        "evidence artifact hash is already bound to another target"
                    )
            last = connection.execute(
                "SELECT record_hash FROM evidence_events ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previous_hash = "0" * 64 if last is None else str(last["record_hash"])
            record_hash = self._hash_payload(payload, previous_hash)
            connection.execute(
                """
                INSERT INTO evidence_events (
                    event_id, event_type, subject_id, mission_id, revision,
                    candidate_id, evidence_type, producer_role, outcome,
                    artifact_sha256, details_json, previous_hash, record_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event_type,
                    subject_id,
                    mission_id,
                    revision,
                    candidate_id,
                    evidence_type,
                    producer_role,
                    outcome,
                    artifact_sha256,
                    json.dumps(details_dict, sort_keys=True, ensure_ascii=False),
                    previous_hash,
                    record_hash,
                ),
            )
        return EvidenceRecord(
            event_id=event_id,
            event_type=event_type,
            subject_id=subject_id,
            mission_id=mission_id,
            revision=revision,
            candidate_id=candidate_id,
            evidence_type=evidence_type,
            producer_role=producer_role,
            outcome=outcome,
            artifact_sha256=artifact_sha256,
            details=details_dict,
            previous_hash=previous_hash,
            record_hash=record_hash,
        )

    def append(
        self,
        *,
        mission_id: str,
        revision: int,
        candidate_id: str,
        evidence_type: str,
        producer_role: str,
        outcome: str,
        artifact_path: Path,
        expected_results: Sequence[Mapping[str, Any]],
        decision_rules: Sequence[Mapping[str, Any]],
        observations: Sequence[Mapping[str, Any]],
        details: Mapping[str, Any] | None = None,
    ) -> EvidenceRecord:
        unresolved = artifact_path.absolute()
        current = unresolved
        while current.parent != current:
            if current.is_symlink():
                raise ValueError("evidence artifact path must not contain symbolic links")
            current = current.parent
        resolved = unresolved.resolve(strict=True)
        if not resolved.is_file():
            raise ValueError("evidence artifact must be a regular file")
        artifact_sha256 = hashlib.sha256(resolved.read_bytes()).hexdigest()
        expected_list = [dict(item) for item in expected_results]
        rule_list = [dict(item) for item in decision_rules]
        observation_list = [dict(item) for item in observations]
        self._validate_evaluation(
            producer_role=producer_role,
            outcome=outcome,
            artifact_sha256=artifact_sha256,
            expected_results=expected_list,
            decision_rules=rule_list,
            observations=observation_list,
        )
        return self._append_event(
            event_type="evidence",
            subject_id=None,
            mission_id=mission_id,
            revision=revision,
            candidate_id=candidate_id,
            evidence_type=evidence_type,
            producer_role=producer_role,
            outcome=outcome,
            artifact_sha256=artifact_sha256,
            details={
                **dict(details or {}),
                "artifact_path": str(resolved),
                "expected_results": expected_list,
                "decision_rules": rule_list,
                "observations": observation_list,
            },
        )

    @staticmethod
    def _validate_evaluation(
        *,
        producer_role: str,
        outcome: str,
        artifact_sha256: str,
        expected_results: Sequence[Mapping[str, Any]],
        decision_rules: Sequence[Mapping[str, Any]],
        observations: Sequence[Mapping[str, Any]],
    ) -> None:
        if not expected_results or not decision_rules or not observations:
            raise ValueError(
                "evidence requires expected results, decision rules, and observations"
            )
        rules = {str(item.get("decision_rule_id", "")): item for item in decision_rules}
        expected = {
            str(item.get("expected_result_id", "")): item for item in expected_results
        }
        if "" in rules or len(rules) != len(decision_rules):
            raise ValueError("decision rule IDs must be non-empty and unique")
        if "" in expected or len(expected) != len(expected_results):
            raise ValueError("expected result IDs must be non-empty and unique")
        for item in (*expected_results, *decision_rules):
            if str(item.get("owner_role", "")) in {"", producer_role}:
                raise ValueError(
                    "expected results and decision rules require an independent owner"
                )
        for item in expected_results:
            rule_ids = item.get("decision_rule_ids")
            if not isinstance(rule_ids, list) or not rule_ids:
                raise ValueError("expected result has no decision rule")
            if any(str(rule_id) not in rules for rule_id in rule_ids):
                raise ValueError("expected result references an unknown decision rule")
        observed_expected: set[str] = set()
        for observation in observations:
            expected_id = str(observation.get("expected_result_id", ""))
            if expected_id not in expected:
                raise ValueError("observation references an unknown expected result")
            observed_expected.add(expected_id)
            if str(observation.get("artifact_sha256", "")).lower() != artifact_sha256:
                raise ValueError("observation is not bound to the evidence artifact")
        if set(expected) != observed_expected:
            raise ValueError("every expected result must have an observation")
        if outcome == "pass" and any(
            str(item.get("outcome", "")) != "pass" for item in observations
        ):
            raise ValueError("passing evidence requires passing observations")

    def invalidate(self, event_id: str, *, producer_role: str, reason: str) -> EvidenceRecord:
        original = self.get(event_id)
        return self._append_event(
            event_type="invalidation",
            subject_id=event_id,
            mission_id=original.mission_id,
            revision=original.revision,
            candidate_id=original.candidate_id,
            evidence_type=original.evidence_type,
            producer_role=producer_role,
            outcome="stale",
            artifact_sha256=original.artifact_sha256,
            details={"reason": reason},
        )

    def get(self, event_id: str) -> EvidenceRecord:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM evidence_events WHERE event_id = ?", (event_id,)
            ).fetchone()
        if row is None:
            raise KeyError(event_id)
        return self._row_to_record(row)

    def status(self, event_id: str) -> EvidenceStatus:
        original = self.get(event_id)
        if original.event_type != "evidence":
            raise ValueError("status is defined for evidence events only")
        with self._connect() as connection:
            invalidation = connection.execute(
                """
                SELECT 1 FROM evidence_events
                WHERE event_type = 'invalidation' AND subject_id = ?
                LIMIT 1
                """,
                (event_id,),
            ).fetchone()
        if invalidation is not None:
            return EvidenceStatus.STALE
        return EvidenceStatus.VALID if original.outcome == "pass" else EvidenceStatus.REJECTED

    def records_for(
        self, mission_id: str, revision: int, candidate_id: str
    ) -> list[EvidenceRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM evidence_events
                WHERE event_type = 'evidence'
                  AND mission_id = ? AND revision = ? AND candidate_id = ?
                ORDER BY sequence
                """,
                (mission_id, revision, candidate_id),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> EvidenceRecord:
        return EvidenceRecord(
            event_id=str(row["event_id"]),
            event_type=str(row["event_type"]),
            subject_id=None if row["subject_id"] is None else str(row["subject_id"]),
            mission_id=str(row["mission_id"]),
            revision=int(row["revision"]),
            candidate_id=str(row["candidate_id"]),
            evidence_type=str(row["evidence_type"]),
            producer_role=str(row["producer_role"]),
            outcome=str(row["outcome"]),
            artifact_sha256=str(row["artifact_sha256"]),
            details=json.loads(str(row["details_json"])),
            previous_hash=str(row["previous_hash"]),
            record_hash=str(row["record_hash"]),
        )

    def verify_chain(self) -> bool:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM evidence_events ORDER BY sequence"
            ).fetchall()
        previous_hash = "0" * 64
        for row in rows:
            record = self._row_to_record(row)
            payload: dict[str, Any] = {
                "event_id": record.event_id,
                "event_type": record.event_type,
                "subject_id": record.subject_id,
                "mission_id": record.mission_id,
                "revision": record.revision,
                "candidate_id": record.candidate_id,
                "evidence_type": record.evidence_type,
                "producer_role": record.producer_role,
                "outcome": record.outcome,
                "artifact_sha256": record.artifact_sha256,
                "details": dict(record.details),
            }
            expected = self._hash_payload(payload, previous_hash)
            if record.previous_hash != previous_hash or record.record_hash != expected:
                return False
            previous_hash = record.record_hash
        return True
