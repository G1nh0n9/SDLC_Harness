from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

_CANDIDATE_ID = re.compile(r"^cand-[0-9a-f]{64}$")


class FileRecord(TypedDict):
    input: str
    path: str
    sha256: str
    size: int


class CandidateManifest(TypedDict):
    mission_id: str
    revision: int
    parent_candidate_id: str | None
    created_by_role: str
    input_labels: list[str]
    toolchain: dict[str, str]
    required_evidence: list[str]
    files: list[FileRecord]


class CandidateState(StrEnum):
    FROZEN = "frozen"
    VERIFYING = "verifying"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    PACKAGING = "packaging"
    RELEASE_READY = "release-ready"
    REVIEW_FAILED = "review-failed"
    CORRUPT = "corrupt"


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: str
    mission_id: str
    revision: int
    snapshot_root: Path
    _manifest_json: str
    _manifest_sha256: str
    _parent_candidate_id: str | None
    _created_by_role: str
    _state: CandidateState = CandidateState.FROZEN

    @property
    def manifest(self) -> CandidateManifest:
        return json.loads(self._manifest_json)  # type: ignore[no-any-return]

    @property
    def manifest_sha256(self) -> str:
        return self._manifest_sha256

    @property
    def parent_candidate_id(self) -> str | None:
        return self._parent_candidate_id

    @property
    def created_by_role(self) -> str:
        return self._created_by_role

    @property
    def state(self) -> CandidateState:
        return self._state

    def _transition_state(self, target: CandidateState) -> None:
        object.__setattr__(self, "_state", target)


class CandidateStore:
    _safe_input_label = re.compile(r"^[A-Za-z0-9_.-]+$")
    _required_input_labels = frozenset(
        {"source", "requirements", "design", "build-config", "dependencies"}
    )

    def __init__(self, root: Path) -> None:
        self._assert_no_symlink_path(root)
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._candidates: dict[str, Candidate] = {}

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _assert_no_symlink_path(path: Path) -> None:
        absolute = path.absolute()
        for component in (absolute, *absolute.parents):
            if component.is_symlink():
                raise ValueError(f"symbolic links are not allowed: {path}")

    @classmethod
    def _scan_inputs(cls, inputs: Mapping[str, Path]) -> list[FileRecord]:
        records: list[FileRecord] = []
        for label, root in sorted(inputs.items()):
            cls._assert_no_symlink_path(root)
            resolved = root.resolve(strict=True)
            if not resolved.is_dir():
                raise ValueError(f"input {label!r} must be a real directory")
            for path in sorted(resolved.rglob("*")):
                if path.is_symlink():
                    raise ValueError(f"symbolic links are not allowed: {path}")
                if path.is_file():
                    relative = path.relative_to(resolved).as_posix()
                    records.append(
                        {
                            "input": label,
                            "path": relative,
                            "sha256": cls._sha256(path),
                            "size": path.stat().st_size,
                        }
                    )
        return records

    @staticmethod
    def _candidate_id(manifest: CandidateManifest) -> str:
        identity = {
            "input_labels": manifest["input_labels"],
            "toolchain": manifest["toolchain"],
            "required_evidence": manifest["required_evidence"],
            "files": manifest["files"],
        }
        canonical = json.dumps(
            identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        return "cand-" + hashlib.sha256(canonical).hexdigest()

    def freeze_candidate(
        self,
        *,
        mission_id: str,
        revision: int,
        inputs: Mapping[str, Path],
        toolchain: Mapping[str, str],
        required_evidence: Collection[str] = (),
        parent_candidate_id: str | None = None,
        created_by_role: str = "implementation-specialist",
    ) -> Candidate:
        if not inputs:
            raise ValueError("at least one candidate input is required")
        for label in inputs:
            if not self._safe_input_label.fullmatch(label) or label in {".", ".."}:
                raise ValueError(f"unsafe input label: {label!r}")
        missing_inputs = self._required_input_labels - set(inputs)
        if missing_inputs:
            raise ValueError(
                "missing candidate inputs: " + ", ".join(sorted(missing_inputs))
            )
        if not toolchain:
            raise ValueError("candidate toolchain must not be empty")
        if parent_candidate_id is not None:
            self.get(parent_candidate_id)
        manifest: CandidateManifest = {
            "mission_id": mission_id,
            "revision": revision,
            "parent_candidate_id": parent_candidate_id,
            "created_by_role": created_by_role,
            "input_labels": sorted(inputs),
            "toolchain": dict(sorted(toolchain.items())),
            "required_evidence": sorted(set(required_evidence)),
            "files": self._scan_inputs(inputs),
        }
        candidate_id = self._candidate_id(manifest)
        candidate_root = self.root / "candidates" / candidate_id
        snapshot_root = candidate_root / "files"
        if candidate_root.exists():
            raise FileExistsError(f"candidate already exists: {candidate_id}")
        snapshot_root.mkdir(parents=True)
        for label, input_root in sorted(inputs.items()):
            destination = snapshot_root / label
            shutil.copytree(input_root.resolve(strict=True), destination)
        manifest_path = candidate_root / "manifest.json"
        manifest_text = json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        manifest_bytes = manifest_text.encode("utf-8")
        manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
        manifest_path.write_bytes(manifest_bytes)
        (candidate_root / "manifest.sha256").write_text(
            manifest_digest + "\n",
            encoding="ascii",
        )
        (candidate_root / "state.json").write_text(
            json.dumps({"state": CandidateState.FROZEN.value}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        candidate = Candidate(
            candidate_id=candidate_id,
            mission_id=mission_id,
            revision=revision,
            snapshot_root=snapshot_root,
            _manifest_json=json.dumps(manifest, sort_keys=True, ensure_ascii=False),
            _manifest_sha256=manifest_digest,
            _parent_candidate_id=parent_candidate_id,
            _created_by_role=created_by_role,
        )
        self._candidates[candidate_id] = candidate
        return candidate

    def get(self, candidate_id: str) -> Candidate:
        if not _CANDIDATE_ID.fullmatch(candidate_id):
            raise KeyError(candidate_id)
        cached = self._candidates.get(candidate_id)
        if cached is not None:
            return cached
        candidate_root = self.root / "candidates" / candidate_id
        self._assert_no_symlink_path(candidate_root)
        manifest_path = candidate_root / "manifest.json"
        manifest_digest_path = candidate_root / "manifest.sha256"
        state_path = candidate_root / "state.json"
        try:
            manifest_bytes = manifest_path.read_bytes()
            raw_manifest = json.loads(manifest_bytes)
            expected_manifest_digest = manifest_digest_path.read_text(encoding="ascii").strip()
            raw_state = json.loads(state_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, UnicodeError, json.JSONDecodeError) as exc:
            raise KeyError(candidate_id) from exc
        if not isinstance(raw_manifest, dict) or not isinstance(raw_state, dict):
            raise ValueError("candidate metadata must be JSON objects")
        if (
            not re.fullmatch(r"[0-9a-f]{64}", expected_manifest_digest)
            or hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_digest
        ):
            raise ValueError("candidate manifest digest mismatch")
        manifest: CandidateManifest = raw_manifest  # type: ignore[assignment]
        if self._candidate_id(manifest) != candidate_id:
            raise ValueError("candidate manifest does not match candidate_id")
        candidate = Candidate(
            candidate_id=candidate_id,
            mission_id=str(manifest["mission_id"]),
            revision=int(manifest["revision"]),
            snapshot_root=candidate_root / "files",
            _manifest_json=json.dumps(manifest, sort_keys=True, ensure_ascii=False),
            _manifest_sha256=expected_manifest_digest,
            _parent_candidate_id=manifest.get("parent_candidate_id"),
            _created_by_role=str(manifest["created_by_role"]),
            _state=CandidateState(str(raw_state.get("state", ""))),
        )
        self._candidates[candidate_id] = candidate
        return candidate

    def save_state(self, candidate: Candidate) -> None:
        if self.get(candidate.candidate_id) is not candidate:
            self._candidates[candidate.candidate_id] = candidate
        state_path = self.root / "candidates" / candidate.candidate_id / "state.json"
        temporary = state_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps({"state": candidate.state.value}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(state_path)

    @classmethod
    def verify_snapshot(
        cls,
        candidate: Candidate,
        *,
        expected_manifest_sha256: str | None = None,
    ) -> bool:
        try:
            candidate_root = candidate.snapshot_root.parent
            manifest_bytes = (candidate_root / "manifest.json").read_bytes()
            stored_manifest = json.loads(manifest_bytes)
            stored_manifest_digest = (candidate_root / "manifest.sha256").read_text(
                encoding="ascii"
            ).strip()
            manifest = candidate.manifest
            if (
                not isinstance(stored_manifest, dict)
                or not re.fullmatch(r"[0-9a-f]{64}", stored_manifest_digest)
                or hashlib.sha256(manifest_bytes).hexdigest() != stored_manifest_digest
                or stored_manifest_digest != candidate.manifest_sha256
                or (
                    expected_manifest_sha256 is not None
                    and stored_manifest_digest != expected_manifest_sha256
                )
                or stored_manifest != manifest
                or manifest["mission_id"] != candidate.mission_id
                or manifest["revision"] != candidate.revision
                or manifest["parent_candidate_id"] != candidate.parent_candidate_id
                or manifest["created_by_role"] != candidate.created_by_role
                or cls._candidate_id(manifest) != candidate.candidate_id
            ):
                candidate._transition_state(CandidateState.CORRUPT)
                return False
            labels = set(manifest["input_labels"])
            actual = cls._scan_inputs(
                {label: candidate.snapshot_root / label for label in sorted(labels)}
            )
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            candidate._transition_state(CandidateState.CORRUPT)
            return False
        valid = actual == manifest["files"]
        if not valid:
            candidate._transition_state(CandidateState.CORRUPT)
        return valid

    def verify(
        self,
        candidate_id: str,
        *,
        expected_manifest_sha256: str | None = None,
    ) -> bool:
        return self.verify_snapshot(
            self.get(candidate_id),
            expected_manifest_sha256=expected_manifest_sha256,
        )
