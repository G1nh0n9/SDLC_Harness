from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from agent_harness.candidate import CandidateState, CandidateStore
from agent_harness.state_machine import CandidateStateMachine, InvalidTransition


def complete_inputs(tmp_path: Path) -> dict[str, Path]:
    inputs = {}
    for label in ("source", "requirements", "design", "build-config", "dependencies"):
        directory = tmp_path / "inputs" / label
        directory.mkdir(parents=True)
        (directory / "content.txt").write_text(f"{label}\n", encoding="utf-8")
        inputs[label] = directory
    return inputs


def test_state_machine_blocks_skips_and_review_failure_requires_child_candidate(
    tmp_path: Path,
) -> None:
    inputs = complete_inputs(tmp_path)
    source = inputs["source"]
    (source / "app.py").write_text("VERSION = 1\n", encoding="utf-8")
    store = CandidateStore(tmp_path / "store")
    parent = store.freeze_candidate(
        mission_id="mis-1",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
    )
    machine = CandidateStateMachine()

    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        parent.state = CandidateState.APPROVED  # type: ignore[misc]
    exposed_manifest = parent.manifest
    exposed_manifest["files"].clear()
    assert parent.manifest["files"]

    with pytest.raises(InvalidTransition):
        machine.transition(parent, CandidateState.APPROVED)

    machine.transition(parent, CandidateState.VERIFYING)
    machine.transition(parent, CandidateState.REVIEWING)
    machine.transition(parent, CandidateState.REVIEW_FAILED)
    assert parent.state is CandidateState.REVIEW_FAILED

    (source / "app.py").write_text("VERSION = 2\n", encoding="utf-8")
    child = store.freeze_candidate(
        mission_id="mis-1",
        revision=1,
        inputs=inputs,
        toolchain={"python": "3.11"},
        parent_candidate_id=parent.candidate_id,
    )
    assert child.candidate_id != parent.candidate_id
    assert child.parent_candidate_id == parent.candidate_id
    assert parent.state is CandidateState.REVIEW_FAILED
