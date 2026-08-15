import hashlib
import json
from pathlib import Path

import pytest

from agent_harness.candidate import CandidateState, CandidateStore


def complete_inputs(tmp_path: Path) -> dict[str, Path]:
    inputs: dict[str, Path] = {}
    for label in ("source", "requirements", "design", "build-config", "dependencies"):
        directory = tmp_path / "inputs" / label
        directory.mkdir(parents=True)
        (directory / "content.txt").write_text(f"{label}\n", encoding="utf-8")
        inputs[label] = directory
    return inputs


def test_frozen_candidate_detects_snapshot_tampering(tmp_path: Path) -> None:
    inputs = complete_inputs(tmp_path)
    source = inputs["source"]
    requirements = inputs["requirements"]
    (source / "main.py").write_text("print('approved')\n", encoding="utf-8")
    (requirements / "acceptance.md").write_text("must print approved\n", encoding="utf-8")

    store = CandidateStore(tmp_path / "store")
    candidate = store.freeze_candidate(
        mission_id="mis-1",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
    )

    assert candidate.state is CandidateState.FROZEN
    assert store.verify(candidate.candidate_id) is True

    frozen_file = candidate.snapshot_root / "source" / "main.py"
    frozen_file.write_text("print('tampered')\n", encoding="utf-8")

    assert store.verify(candidate.candidate_id) is False
    assert store.get(candidate.candidate_id).state is CandidateState.CORRUPT


@pytest.mark.parametrize("label", ["..", "source/../../escape", "C:/outside"])
def test_candidate_rejects_unsafe_input_labels(tmp_path: Path, label: str) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "main.py").write_text("VALUE = 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unsafe input label"):
        CandidateStore(tmp_path / "store").freeze_candidate(
            mission_id="mis-1",
            revision=1,
            inputs={label: source},
            toolchain={"python": "3.11"},
        )


def test_candidate_requires_all_baseline_inputs(tmp_path: Path) -> None:
    inputs = complete_inputs(tmp_path)
    inputs.pop("dependencies")

    with pytest.raises(ValueError, match="missing candidate inputs: dependencies"):
        CandidateStore(tmp_path / "store").freeze_candidate(
            mission_id="mis-1",
            revision=1,
            inputs=inputs,
            toolchain={"python": "3.11"},
        )


def test_candidate_id_is_content_identity_not_mission_identity(tmp_path: Path) -> None:
    inputs = complete_inputs(tmp_path)
    first = CandidateStore(tmp_path / "first-store").freeze_candidate(
        mission_id="mis-first",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
        required_evidence={"acceptance-test"},
        created_by_role="implementation-specialist",
    )
    second = CandidateStore(tmp_path / "second-store").freeze_candidate(
        mission_id="mis-second",
        revision=99,
        inputs=inputs,
        toolchain={"python": "3.11"},
        required_evidence={"acceptance-test"},
        created_by_role="another-implementation-role",
    )

    assert first.candidate_id == second.candidate_id


def test_candidate_rejects_top_level_input_symlink(tmp_path: Path) -> None:
    inputs = complete_inputs(tmp_path)
    linked_source = tmp_path / "linked-source"
    try:
        linked_source.symlink_to(inputs["source"], target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are not available")
    inputs["source"] = linked_source

    with pytest.raises(ValueError, match="symbolic links"):
        CandidateStore(tmp_path / "store").freeze_candidate(
            mission_id="mis-symlink-root",
            revision=1,
            inputs=inputs,
            toolchain={"python": "3.11"},
            required_evidence={"acceptance-test"},
        )


def test_candidate_detects_manifest_provenance_tamper(tmp_path: Path) -> None:
    inputs = complete_inputs(tmp_path)
    candidate = CandidateStore(tmp_path / "store").freeze_candidate(
        mission_id="mis-manifest",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
        required_evidence={"acceptance-test"},
    )
    manifest_path = candidate.snapshot_root.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["revision"] = 999
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert CandidateStore.verify_snapshot(candidate) is False
    assert candidate.state is CandidateState.CORRUPT


def test_candidate_store_rejects_symlinked_storage_root(tmp_path: Path) -> None:
    real_store = tmp_path / "real-store"
    real_store.mkdir()
    linked_store = tmp_path / "linked-store"
    try:
        linked_store.symlink_to(real_store, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are not available")

    with pytest.raises(ValueError, match="symbolic links"):
        CandidateStore(linked_store)


def test_candidate_get_rejects_symlinked_candidate_directory(tmp_path: Path) -> None:
    inputs = complete_inputs(tmp_path)
    source_store = CandidateStore(tmp_path / "source-store")
    candidate = source_store.freeze_candidate(
        mission_id="mis-symlink-candidate",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
    )
    receiving_root = tmp_path / "receiving-store"
    candidate_link = receiving_root / "candidates" / candidate.candidate_id
    candidate_link.parent.mkdir(parents=True)
    try:
        candidate_link.symlink_to(
            candidate.snapshot_root.parent, target_is_directory=True
        )
    except OSError:
        pytest.skip("directory symlinks are not available")

    with pytest.raises(ValueError, match="symbolic links"):
        CandidateStore(receiving_root).get(candidate.candidate_id)


def test_candidate_rejects_rehashed_manifest_provenance_tamper(tmp_path: Path) -> None:
    inputs = complete_inputs(tmp_path)
    store_root = tmp_path / "store"
    candidate = CandidateStore(store_root).freeze_candidate(
        mission_id="mis-manifest-bound",
        revision=2,
        inputs=inputs,
        toolchain={"python": "3.11"},
        required_evidence={"acceptance-test"},
    )
    expected_manifest_sha256 = candidate.manifest_sha256
    candidate_root = candidate.snapshot_root.parent
    manifest_path = candidate_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["revision"] = 999
    manifest_bytes = (
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    (candidate_root / "manifest.sha256").write_text(
        hashlib.sha256(manifest_bytes).hexdigest() + "\n", encoding="ascii"
    )

    restarted = CandidateStore(store_root)
    assert (
        restarted.verify(
            candidate.candidate_id,
            expected_manifest_sha256=expected_manifest_sha256,
        )
        is False
    )
    assert restarted.get(candidate.candidate_id).state is CandidateState.CORRUPT
