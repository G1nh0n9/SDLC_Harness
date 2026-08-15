from __future__ import annotations

import json

from hermes_cli.plugins import discover_plugins, get_plugin_manager, get_plugin_toolsets
from tools.registry import registry


def main() -> None:
    discover_plugins(force=True)
    manager = get_plugin_manager()
    toolsets = get_plugin_toolsets()
    expected_tools = {
        "workflow_start",
        "workflow_status",
        "workflow_submit_result",
        "workflow_revise",
        "workflow_freeze_candidate",
        "workflow_record_evidence",
        "workflow_approve_candidate",
        "workflow_package_release",
    }
    entries = {
        name: registry.get_entry(name, scope=manager.scope_key)
        or registry.get_entry(name)
        for name in expected_tools
    }
    missing = sorted(name for name, value in entries.items() if value is None)
    if missing:
        raise RuntimeError(f"workflow tools are not registered: {missing}")
    entry = entries["workflow_start"]
    if entry is None:
        raise AssertionError("workflow_start disappeared after registration check")
    result = json.loads(entry.handler({"goal": "플러그인 런타임 등록을 검증한다"}))
    if not result.get("success"):
        raise RuntimeError(f"workflow_start failed: {result}")
    skill = manager.find_plugin_skill("agent-workflow-harness:workflow")
    if skill is None:
        raise RuntimeError("plugin skill is not registered")
    print(
        json.dumps(
            {
                "plugin": "agent-workflow-harness",
                "toolsets": toolsets,
                "tools": sorted(entries),
                "mission_id": result["mission_id"],
                "current_stage": result["current_stage"],
                "skill": str(skill),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
