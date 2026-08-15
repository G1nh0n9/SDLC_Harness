from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from agent_harness.evidence import EvidenceLedger, EvidenceStatus
from agent_harness.plugin_service import WorkflowPluginError, WorkflowPluginService
from agent_harness.result_evidence import (
    build_evidence_evaluation,
    build_result_evidence,
)


def _passing_payload(task: dict[str, Any]) -> dict[str, object]:
    artifact = Path(task["workspace"]["work"]) / "stage-result.json"
    artifact.write_text('{"gate":"pass"}\n', encoding="utf-8")
    return build_result_evidence(
        artifact_path=artifact,
        artifact_root=Path(task["workspace"]["work"]),
        artifact_types=task["required_outputs"],
        claim="stage outputs were produced",
        gate="pass",
    )


def _complete_candidate_inputs(tmp_path: Path) -> dict[str, str]:
    inputs = {}
    for label in ("source", "requirements", "design", "build-config", "dependencies"):
        directory = tmp_path / "candidate-inputs" / label
        directory.mkdir(parents=True)
        (directory / "content.txt").write_text(f"{label}\n", encoding="utf-8")
        inputs[label] = str(directory)
    return inputs


def _submit_all_current(
    service: WorkflowPluginService, state: dict[str, Any]
) -> dict[str, Any]:
    current = state
    for task in list(current["tasks"]):
        current = service.submit_result(
            {
                "mission_id": current["mission_id"],
                "revision": current["revision"],
                "task_id": task["task_id"],
                "authority_token": task["authority_grants"]["submit-result"]["token"],
                "candidate_id": task.get("candidate_id"),
                "payload": _passing_payload(task),
            }
        )
    return current


def _reach_stage(
    service: WorkflowPluginService, state: dict[str, Any], stage: str
) -> dict[str, Any]:
    current = state
    for _ in range(20):
        if current["current_stage"] == stage:
            return current
        current = _submit_all_current(service, current)
    raise AssertionError(f"stage not reached: {stage}")


def test_plugin_requires_candidate_evidence_approval_and_package(tmp_path: Path) -> None:
    root = tmp_path / "data"
    service = WorkflowPluginService(root)
    state = service.start(
        {
            "goal": "작은 라이브러리를 구현한다",
            "decision_action": "출시 여부를 결정한다",
            "outcome": "명세에 맞는 라이브러리",
            "population": "라이브러리 사용자",
            "analysis_unit": "함수 호출",
            "time_horizon": "출시 시점",
            "constraints": ["네트워크 사용 금지"],
            "question_type": "implementation",
            "data_description": "저장소와 인수 기준",
            "decision_threshold": "모든 수락 시험 통과",
            "risk_level": 1,
        }
    )
    state = _reach_stage(service, state, "implementation")
    implementation_task = state["tasks"][0]
    assert implementation_task["permissions"]["can_approve"] is False
    assert implementation_task["permissions"]["can_execute_commands"] is True
    assert Path(implementation_task["workspace"]["work"]).is_dir()
    assert Path(implementation_task["workspace"]["inputs"]).is_dir()

    blocked = _submit_all_current(service, state)
    assert blocked["current_stage"] == "implementation"
    assert blocked["gate_reason"] == "implementation stage requires a frozen candidate"
    implementation_task = blocked["tasks"][0]

    inputs = _complete_candidate_inputs(tmp_path)
    source = Path(inputs["source"])
    (source / "library.py").write_text("VALUE = 1\n", encoding="utf-8")
    frozen = service.freeze_candidate(
        {
            "mission_id": state["mission_id"],
            "revision": state["revision"],
            "task_id": implementation_task["task_id"],
            "authority_token": implementation_task["authority_grants"][
                "freeze-candidate"
            ]["token"],
            "inputs": inputs,
            "toolchain": {"python": "3.11"},
        }
    )
    assert frozen["candidate_state"] == "frozen"

    state = service.status(state["mission_id"])
    state = _submit_all_current(service, state)
    assert state["current_stage"] == "integration-verification"
    assert {task["candidate_id"] for task in state["tasks"]} == {
        frozen["candidate_id"]
    }
    verification_task = state["tasks"][0]
    expected_manifest_sha256 = (
        root
        / "mission-data"
        / state["mission_id"]
        / "candidate-store"
        / "candidates"
        / frozen["candidate_id"]
        / "manifest.sha256"
    ).read_text(encoding="ascii").strip()
    assert (
        verification_task["input_bindings"]["frozen-candidate"]["sha256"]
        == expected_manifest_sha256
    )
    assert verification_task["candidate_snapshot"] is not None
    assert Path(verification_task["candidate_snapshot"]).is_dir()

    evidence_file = tmp_path / "acceptance.json"
    evidence_file.write_text('{"passed": true}\n', encoding="utf-8")
    with pytest.raises(WorkflowPluginError, match="caller-supplied role"):
        service.record_evidence(
            {
                "mission_id": state["mission_id"],
                "revision": state["revision"],
                "task_id": verification_task["task_id"],
                "authority_token": verification_task["authority_grants"][
                    "record-evidence"
                ]["token"],
                "candidate_id": frozen["candidate_id"],
                "evidence_type": "acceptance-test",
                "producer_role": "implementation-specialist",
                "outcome": "pass",
                "artifact_path": str(evidence_file),
                "details": {},
            }
        )
    state = service.record_evidence(
        {
            "mission_id": state["mission_id"],
            "revision": state["revision"],
            "task_id": verification_task["task_id"],
            "authority_token": verification_task["authority_grants"][
                "record-evidence"
            ]["token"],
            "candidate_id": frozen["candidate_id"],
            "evidence_type": "acceptance-test",
            "outcome": "pass",
            "artifact_path": str(evidence_file),
            **build_evidence_evaluation(
                artifact_path=evidence_file, outcome="pass"
            ),
            "details": {},
        }
    )
    state = _submit_all_current(service, state)
    assert state["current_stage"] == "validation"

    blocked = _submit_all_current(service, state)
    assert blocked["current_stage"] == "validation"
    assert blocked["gate_reason"] == "validation stage requires candidate approval"
    validation_task = blocked["tasks"][0]

    evidence_file.write_text('{"passed": false}\n', encoding="utf-8")
    with pytest.raises(WorkflowPluginError, match="artifact verification failed"):
        service.approve_candidate(
            {
                "mission_id": state["mission_id"],
                "revision": state["revision"],
                "task_id": validation_task["task_id"],
                "authority_token": validation_task["authority_grants"][
                    "approve-candidate"
                ]["token"],
                "candidate_id": frozen["candidate_id"],
            }
        )
    evidence_file.write_text('{"passed": true}\n', encoding="utf-8")
    validation_task = service.status(state["mission_id"])["tasks"][0]

    approved = service.approve_candidate(
        {
            "mission_id": state["mission_id"],
            "revision": state["revision"],
            "task_id": validation_task["task_id"],
            "authority_token": validation_task["authority_grants"][
                "approve-candidate"
            ]["token"],
            "candidate_id": frozen["candidate_id"],
        }
    )
    assert approved["candidate_state"] == "approved"
    assert approved["current_stage"] == "release"

    release_task = approved["tasks"][0]
    blocked = service.submit_result(
        {
            "mission_id": approved["mission_id"],
            "revision": approved["revision"],
            "task_id": release_task["task_id"],
            "authority_token": release_task["authority_grants"]["submit-result"][
                "token"
            ],
            "candidate_id": frozen["candidate_id"],
            "payload": _passing_payload(release_task),
        }
    )
    assert blocked["completed"] is False
    assert blocked["gate_reason"] == "release stage requires a release package"
    release_task = blocked["tasks"][0]

    evidence_file.write_text('{"passed": false}\n', encoding="utf-8")
    with pytest.raises(WorkflowPluginError, match="artifact verification failed"):
        service.package_release(
            {
                "mission_id": approved["mission_id"],
                "revision": approved["revision"],
                "task_id": release_task["task_id"],
                "authority_token": release_task["authority_grants"]["package-release"][
                    "token"
                ],
                "candidate_id": frozen["candidate_id"],
                "disposition": "release",
            }
        )
    evidence_file.write_text('{"passed": true}\n', encoding="utf-8")
    release_task = service.status(approved["mission_id"])["tasks"][0]

    packaged = service.package_release(
        {
            "mission_id": approved["mission_id"],
            "revision": approved["revision"],
            "task_id": release_task["task_id"],
            "authority_token": release_task["authority_grants"]["package-release"][
                "token"
            ],
            "candidate_id": frozen["candidate_id"],
            "disposition": "release",
        }
    )
    assert Path(packaged["release_path"]).is_file()
    assert len(packaged["release_sha256"]) == 64

    final_state = service.status(approved["mission_id"])
    final_state = _submit_all_current(service, final_state)
    assert final_state["completed"] is True

    revised = service.revise(
        {
            "mission_id": approved["mission_id"],
            "instruction": "출시 범위를 바꾼다",
            "constraints": ["새 범위만 허용한다"],
        }
    )
    assert revised["revision"] == 2
    assert revised["active_candidate_id"] is None
    with pytest.raises(WorkflowPluginError, match="result revision is not current"):
        service.package_release(
            {
                "mission_id": approved["mission_id"],
                "revision": 1,
                "candidate_id": frozen["candidate_id"],
                "disposition": "release",
            }
        )
    ledger = EvidenceLedger(
        tmp_path
        / "data"
        / "mission-data"
        / approved["mission_id"]
        / "evidence.sqlite3"
    )
    old_record = ledger.records_for(
        approved["mission_id"], 1, frozen["candidate_id"]
    )[0]
    assert ledger.status(old_record.event_id) is EvidenceStatus.STALE


def test_plugin_rejects_rehashed_candidate_manifest_provenance_tamper(
    tmp_path: Path,
) -> None:
    root = tmp_path / "data"
    service = WorkflowPluginService(root)
    state = service.start(
        {
            "goal": "작은 라이브러리를 구현한다",
            "decision_action": "출시 여부를 결정한다",
            "outcome": "명세에 맞는 라이브러리",
            "population": "라이브러리 사용자",
            "analysis_unit": "함수 호출",
            "time_horizon": "출시 시점",
            "constraints": ["네트워크 사용 금지"],
            "question_type": "implementation",
            "data_description": "저장소와 인수 기준",
            "decision_threshold": "모든 수락 시험 통과",
            "risk_level": 1,
        }
    )
    state = _reach_stage(service, state, "implementation")
    blocked = _submit_all_current(service, state)
    task = blocked["tasks"][0]
    frozen = service.freeze_candidate(
        {
            "mission_id": state["mission_id"],
            "revision": state["revision"],
            "task_id": task["task_id"],
            "authority_token": task["authority_grants"]["freeze-candidate"]["token"],
            "inputs": _complete_candidate_inputs(tmp_path),
            "toolchain": {"python": "3.11"},
        }
    )
    candidate_root = (
        root
        / "mission-data"
        / state["mission_id"]
        / "candidate-store"
        / "candidates"
        / frozen["candidate_id"]
    )
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

    with pytest.raises(WorkflowPluginError, match="manifest binding"):
        WorkflowPluginService(root).status(state["mission_id"])
