from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .candidate import Candidate, CandidateState, CandidateStore
from .state_machine import CandidateStateMachine


@dataclass(frozen=True)
class ReleaseArtifact:
    path: Path
    sha256: str
    decision: ReleaseDecision


class ReleaseDisposition(StrEnum):
    RELEASE = "release"
    LIMITED_RELEASE = "limited-release"
    HOLD = "hold"
    PROHIBITED = "prohibited"


@dataclass(frozen=True)
class ReleaseDecision:
    disposition: ReleaseDisposition
    reasons: tuple[str, ...] = ()
    scope: str | None = None
    expires_at: str | None = None
    rollback_plan: str | None = None
    out_of_scope_controls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.disposition is not ReleaseDisposition.LIMITED_RELEASE:
            return
        required = (
            self.scope,
            self.expires_at,
            self.rollback_plan,
            self.out_of_scope_controls,
        )
        if not all(required):
            raise ValueError(
                "limited release requires scope, expiry, rollback plan, "
                "and out-of-scope controls"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "disposition": self.disposition.value,
            "reasons": list(self.reasons),
            "scope": self.scope,
            "expires_at": self.expires_at,
            "rollback_plan": self.rollback_plan,
            "out_of_scope_controls": list(self.out_of_scope_controls),
        }


class ReleasePackager:
    def __init__(self, state_machine: CandidateStateMachine | None = None) -> None:
        self._state_machine = state_machine or CandidateStateMachine()

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _zip_info(name: str) -> zipfile.ZipInfo:
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        return info

    def package(
        self,
        candidate: Candidate,
        destination: Path,
        *,
        decision: ReleaseDecision,
        expected_mission_id: str,
        expected_revision: int,
    ) -> ReleaseArtifact:
        if decision.disposition in {
            ReleaseDisposition.HOLD,
            ReleaseDisposition.PROHIBITED,
        }:
            raise RuntimeError("release decision does not allow packaging")
        if candidate.mission_id != expected_mission_id:
            raise RuntimeError("candidate does not match current mission")
        if candidate.revision != expected_revision:
            raise RuntimeError("candidate does not match current revision")
        if candidate.state is not CandidateState.APPROVED:
            raise RuntimeError("only an approved candidate can be packaged")
        if not CandidateStore.verify_snapshot(candidate):
            raise RuntimeError("candidate snapshot verification failed before packaging")
        self._state_machine.transition(candidate, CandidateState.PACKAGING)
        destination.mkdir(parents=True, exist_ok=True)
        package_path = destination / f"{candidate.candidate_id}.zip"
        release_manifest = {
            "candidate_id": candidate.candidate_id,
            "mission_id": candidate.mission_id,
            "revision": candidate.revision,
            "parent_candidate_id": candidate.parent_candidate_id,
            "candidate_manifest": candidate.manifest,
            "release_decision": decision.as_dict(),
        }
        with zipfile.ZipFile(package_path, "w") as archive:
            manifest_bytes = (
                json.dumps(release_manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
            ).encode("utf-8")
            archive.writestr(self._zip_info("release-manifest.json"), manifest_bytes)
            for path in sorted(candidate.snapshot_root.rglob("*")):
                if path.is_file():
                    relative = path.relative_to(candidate.snapshot_root).as_posix()
                    archive.writestr(self._zip_info(f"candidate/{relative}"), path.read_bytes())
        self._state_machine.transition(candidate, CandidateState.RELEASE_READY)
        return ReleaseArtifact(
            path=package_path.resolve(),
            sha256=self._sha256(package_path),
            decision=decision,
        )
