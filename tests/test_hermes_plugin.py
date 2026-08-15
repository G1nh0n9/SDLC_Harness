from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agent_harness.hermes_plugin import register
from agent_harness.plugin_service import WorkflowPluginError, WorkflowPluginService
from agent_harness.result_evidence import build_result_evidence


def _passing_payload(task: dict[str, Any]) -> dict[str, object]:
    artifact = Path(task["workspace"]["work"]) / "stage-result.json"
    artifact.write_text('{"gate":"pass"}\n', encoding="utf-8")
    return build_result_evidence(
        artifact_path=artifact,
        artifact_root=Path(task["workspace"]["work"]),
        artifact_types=task["required_outputs"],
        claim="stage outputs were produced",
        gate="pass",
        extra={"findings": []},
    )


class FakePluginContext:
    def __init__(self) -> None:
        self.tools: dict[str, tuple[dict[str, Any], Any]] = {}
        self.commands: dict[str, Any] = {}
        self.skills: dict[str, Path] = {}

    def register_tool(
        self,
        *,
        name: str,
        toolset: str,
        schema: dict[str, Any],
        handler: Any,
        **kwargs: Any,
    ) -> None:
        assert toolset == "agent_workflow"
        self.tools[name] = (schema, handler)

    def register_command(
        self, name: str, *, handler: Any, description: str
    ) -> None:
        del description
        self.commands[name] = handler

    def register_skill(
        self,
        name: str,
        path: str | Path,
        description: str = "",
        **kwargs: Any,
    ) -> None:
        del description, kwargs
        self.skills[name] = Path(path)


def test_plugin_registers_tools_command_and_skill(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AGENT_WORKFLOW_DATA", str(tmp_path / "data"))
    context = FakePluginContext()

    register(context)

    assert {
        "workflow_start",
        "workflow_status",
        "workflow_submit_result",
        "workflow_record_checkpoint",
        "workflow_interrupt_attempt",
        "workflow_retry_attempt",
        "workflow_revise",
        "workflow_freeze_candidate",
        "workflow_record_evidence",
        "workflow_approve_candidate",
        "workflow_package_release",
    } <= context.tools.keys()
    assert "workflow" in context.commands
    assert context.skills["workflow"].name == "SKILL.md"
    assert context.skills["workflow"].is_file()


def test_plugin_service_persists_and_advances_mission(tmp_path: Path) -> None:
    root = tmp_path / "plugin-data"
    first = WorkflowPluginService(root)
    started = first.start(
        {
            "goal": "인증 기능을 추가한다",
            "decision_action": "배포 여부를 결정한다",
            "outcome": "승인된 사용자의 로그인",
            "population": "로그인 사용자",
            "analysis_unit": "로그인 시도",
            "time_horizon": "배포 시점",
            "question_type": "implementation",
            "data_description": "현재 저장소와 인수 기준",
            "decision_threshold": "모든 수락 시험 통과",
            "constraints": ["비밀번호를 로그에 남기지 않는다"],
            "risk_level": 2,
        }
    )

    assert started["mission_id"].startswith("mis-")
    assert started["current_stage"] == "scope-risk"
    assert {task["role"] for task in started["tasks"]} == {"risk-analyst"}

    # A new service instance simulates a Hermes process restart.
    second = WorkflowPluginService(root)
    status = second.status(started["mission_id"])
    assert status["revision"] == 1
    task = status["tasks"][0]

    rejected = second.submit_result(
        {
            "mission_id": started["mission_id"],
            "revision": 1,
            "task_id": task["task_id"],
            "authority_token": task["authority_grants"]["submit-result"]["token"],
            "payload": {
                    **_passing_payload(task),
                "artifacts": [
                    {
                        "path": "missing.json",
                        "sha256": "0" * 64,
                        "media_type": "application/json",
                    }
                ],
            },
        }
    )
    assert rejected["disposition"] == "rejected-invalid-payload"
    assert rejected["current_stage"] == "scope-risk"
    task = rejected["tasks"][0]

    submitted = second.submit_result(
        {
            "mission_id": started["mission_id"],
            "revision": 1,
            "task_id": task["task_id"],
            "authority_token": task["authority_grants"]["submit-result"]["token"],
            "payload": _passing_payload(task),
        }
    )

    assert submitted["disposition"] == "accepted-as-input"
    assert submitted["current_stage"] == "requirements"
    assert submitted["tasks"][0]["role"] == "requirements-specialist"
    requirement_task = submitted["tasks"][0]
    assert set(requirement_task["input_bindings"]) == set(
        requirement_task["required_inputs"]
    )
    assert all(
        len(binding["sha256"]) == 64
        for binding in requirement_task["input_bindings"].values()
    )
    on_disk = json.loads((root / "missions" / f"{started['mission_id']}.json").read_text("utf-8"))
    assert on_disk["current_stage_index"] == 1


def test_checkpoint_interruption_and_retry_survive_service_restart(
    tmp_path: Path,
) -> None:
    root = tmp_path / "plugin-data"
    service = WorkflowPluginService(root)
    state = service.start(
        {
            "goal": "중단 가능한 변환 작업을 구현한다",
            "decision_action": "출시 여부를 결정한다",
            "outcome": "검증된 변환 결과",
            "population": "입력 파일",
            "analysis_unit": "파일 하나",
            "time_horizon": "출시 시점",
            "question_type": "implementation",
            "data_description": "고정 입력과 기대값",
            "decision_threshold": "모든 수락 시험 통과",
        }
    )
    task = state["tasks"][0]
    first_attempt = task["attempt_id"]
    checkpoint = Path(task["workspace"]["work"]) / "checkpoint.json"
    checkpoint.write_text('{"cursor":3}\n', encoding="utf-8")

    state = service.record_checkpoint(
        {
            "mission_id": state["mission_id"],
            "revision": state["revision"],
            "task_id": task["task_id"],
            "authority_token": task["authority_grants"]["record-checkpoint"]["token"],
            "artifact_path": str(checkpoint),
        }
    )
    task = state["tasks"][0]
    state = service.interrupt_attempt(
        {
            "mission_id": state["mission_id"],
            "revision": state["revision"],
            "task_id": task["task_id"],
            "authority_token": task["authority_grants"]["interrupt-attempt"]["token"],
            "reason": "worker timeout",
        }
    )
    interrupted = state["tasks"][0]
    assert interrupted["status"] == "interrupted"
    assert set(interrupted["authority_grants"]) == {"retry-attempt"}

    restarted = WorkflowPluginService(root)
    state = restarted.status(state["mission_id"])
    interrupted = state["tasks"][0]
    retry_token = interrupted["authority_grants"]["retry-attempt"]["token"]
    state = restarted.retry_attempt(
        {
            "mission_id": state["mission_id"],
            "revision": state["revision"],
            "task_id": interrupted["task_id"],
            "authority_token": retry_token,
            "retry_class": "safe-retry",
        }
    )
    retried = state["tasks"][0]
    assert retried["attempt_id"] != first_attempt
    assert retried["status"] == "issued"
    assert state["workflow_event_chain_valid"] is True

    with pytest.raises(WorkflowPluginError, match="not authorized|already consumed"):
        restarted.retry_attempt(
            {
                "mission_id": state["mission_id"],
                "revision": state["revision"],
                "task_id": retried["task_id"],
                "authority_token": retry_token,
                "retry_class": "safe-retry",
            }
        )
