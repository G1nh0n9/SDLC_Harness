from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .plugin_schemas import TOOL_SCHEMAS
from .plugin_service import WorkflowPluginError, WorkflowPluginService


def _data_root() -> Path:
    override = os.environ.get("AGENT_WORKFLOW_DATA", "").strip()
    if override:
        return Path(override).expanduser().resolve(strict=False)
    try:
        from hermes_constants import get_hermes_home  # type: ignore[import-untyped]
    except ImportError:
        home = os.environ.get("HERMES_HOME", "").strip()
        root = Path(home) if home else Path.home() / ".hermes"
    else:
        root = get_hermes_home()
    return root / "workflow-harness"


def _json_response(operation: Callable[[], Mapping[str, Any]]) -> str:
    try:
        result = {"success": True, **dict(operation())}
    except (WorkflowPluginError, TypeError, ValueError, OSError, RuntimeError) as exc:
        result = {"success": False, "error": str(exc)}
    return json.dumps(result, sort_keys=True, ensure_ascii=False)


def _handler(name: str) -> Callable[..., str]:
    def handle(params: Mapping[str, Any], **_: Any) -> str:
        if not isinstance(params, Mapping):
            return json.dumps({"success": False, "error": "parameters must be an object"})
        service = WorkflowPluginService(_data_root())
        if name == "workflow_start":
            return _json_response(lambda: service.start(params))
        if name == "workflow_status":
            return _json_response(lambda: service.status(str(params.get("mission_id", ""))))
        if name == "workflow_submit_result":
            return _json_response(lambda: service.submit_result(params))
        if name == "workflow_record_checkpoint":
            return _json_response(lambda: service.record_checkpoint(params))
        if name == "workflow_interrupt_attempt":
            return _json_response(lambda: service.interrupt_attempt(params))
        if name == "workflow_retry_attempt":
            return _json_response(lambda: service.retry_attempt(params))
        if name == "workflow_revise":
            return _json_response(lambda: service.revise(params))
        if name == "workflow_freeze_candidate":
            return _json_response(lambda: service.freeze_candidate(params))
        if name == "workflow_record_evidence":
            return _json_response(lambda: service.record_evidence(params))
        if name == "workflow_approve_candidate":
            return _json_response(lambda: service.approve_candidate(params))
        if name == "workflow_package_release":
            return _json_response(lambda: service.package_release(params))
        return json.dumps({"success": False, "error": f"unknown operation: {name}"})

    return handle


_HELP = """/workflow — 증거 중심 다중 에이전트 개발 미션

사용법:
  /workflow start <목표>
  /workflow status <mission_id>
  /workflow revise <mission_id> <새 지시>

자세한 목표·위험·연구 산출물 설정은 workflow_start 도구를 사용합니다.
"""


def _handle_command(raw_args: str) -> str:
    text = raw_args.strip()
    if not text or text in {"help", "-h", "--help"}:
        return _HELP
    command, _, remainder = text.partition(" ")
    service = WorkflowPluginService(_data_root())
    if command == "start" and remainder.strip():
        return _json_response(lambda: service.start({"goal": remainder.strip()}))
    if command == "status" and remainder.strip():
        return _json_response(lambda: service.status(remainder.strip()))
    if command == "revise":
        mission_id, separator, instruction = remainder.strip().partition(" ")
        if separator and instruction.strip():
            return _json_response(
                lambda: service.revise(
                    {"mission_id": mission_id, "instruction": instruction.strip()}
                )
            )
    return _HELP


def register(ctx: Any) -> None:
    for schema in TOOL_SCHEMAS:
        name = str(schema["name"])
        ctx.register_tool(
            name=name,
            toolset="agent_workflow",
            schema=schema,
            handler=_handler(name),
            description=str(schema["description"]),
            emoji="🧭",
        )
    ctx.register_command(
        "workflow",
        handler=_handle_command,
        description="증거 중심 다중 에이전트 개발 미션을 시작하고 조회합니다.",
    )
    skill_path = Path(__file__).with_name("plugin_skill") / "SKILL.md"
    ctx.register_skill(
        "workflow",
        skill_path,
        description="증거 중심 다중 에이전트 소프트웨어 개발 절차",
    )
