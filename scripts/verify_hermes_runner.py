from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agent_harness.agent_runner import AgentRunRequest, HermesCliRunner
from agent_harness.methodology import StageKind
from agent_harness.mission import WorkTask
from agent_harness.workspace import RoleCatalog, WorkspaceBroker


def main() -> None:
    task = WorkTask(
        task_id="task-runner-verification",
        mission_id="mis-runner-verification",
        revision=1,
        stage=StageKind.INTEGRATION_VERIFICATION,
        assignee_role="verification-specialist",
        candidate_id=None,
    )
    with tempfile.TemporaryDirectory(prefix="agent-harness-hermes-") as temporary:
        catalog = RoleCatalog.default()
        workspace = WorkspaceBroker(Path(temporary), catalog).create(
            mission_id=task.mission_id,
            revision=task.revision,
            task_id=task.task_id,
            role=task.assignee_role,
        )
        result = HermesCliRunner(timeout_seconds=180).dispatch(
            AgentRunRequest(
                task=task,
                prompt=(
                    '{"gate":"pass","claims":[{"claim":"runner verified",'
                    '"evidence":"inline:execution"}],"assumptions":[],"unresolved":[],'
                    '"artifacts":[],"note":"tool-free runner verified"}를 그대로 반환하라.'
                ),
                workspace=workspace,
            )
        )
        print(json.dumps(dict(result.payload), sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
