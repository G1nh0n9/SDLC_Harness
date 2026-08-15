from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .authority import AuthorityDenied, AuthorityRequest, AuthorityStore
from .mission import AgentResult, WorkTask
from .workspace import RoleWorkspace


class AgentExecutionError(RuntimeError):
    """Raised when an agent process request violates execution policy or fails."""


@dataclass(frozen=True)
class AgentRunRequest:
    task: WorkTask
    prompt: str
    workspace: RoleWorkspace
    authority_store: AuthorityStore
    authority_token: str


def _consume_authority(request: AgentRunRequest, tool: str) -> None:
    task = request.task
    try:
        request.authority_store.consume(
            request.authority_token,
            AuthorityRequest(
                mission_id=task.mission_id,
                revision=task.revision,
                task_id=task.task_id,
                attempt_id=task.attempt_id,
                worker_id=task.worker_id,
                workspace_id=task.workspace_id,
                candidate_id=task.candidate_id,
                role=task.assignee_role,
                operation="execute-task",
                tool=tool,
            ),
        )
    except AuthorityDenied as error:
        raise AgentExecutionError(str(error)) from error


class AgentRunner(Protocol):
    def dispatch(self, request: AgentRunRequest) -> AgentResult: ...


@dataclass
class RecordingAgentRunner:
    response: Mapping[str, Any]
    requests: list[AgentRunRequest] = field(default_factory=list)

    def dispatch(self, request: AgentRunRequest) -> AgentResult:
        _consume_authority(request, "recording-agent")
        self.requests.append(request)
        return AgentResult.create(
            mission_id=request.task.mission_id,
            revision=request.task.revision,
            task_id=request.task.task_id,
            stage=request.task.stage,
            sender_role=request.task.assignee_role,
            candidate_id=request.task.candidate_id,
            payload=dict(self.response),
            artifact_root=request.workspace.work,
        )


class HermesCliRunner:
    _environment_allowlist = frozenset(
        {
            "APPDATA",
            "COMSPEC",
            "HERMES_HOME",
            "HOMEDRIVE",
            "HOMEPATH",
            "LANG",
            "LC_ALL",
            "LOCALAPPDATA",
            "PATHEXT",
            "PROGRAMDATA",
            "PROGRAMFILES",
            "PROGRAMFILES(X86)",
            "REQUESTS_CA_BUNDLE",
            "SSL_CERT_FILE",
            "SYSTEMROOT",
            "USERPROFILE",
            "WINDIR",
        }
    )

    def __init__(
        self,
        timeout_seconds: int = 900,
    ) -> None:
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _discover_command_prefix() -> tuple[str, ...]:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates = (
                Path(local_app_data)
                / "hermes"
                / "hermes-agent"
                / "venv"
                / "Scripts"
                / "hermes.exe",
                Path(local_app_data) / "hermes" / "hermes-agent" / "bin" / "hermes.exe",
            )
            for candidate in candidates:
                if candidate.is_file():
                    return (str(candidate),)
        raise AgentExecutionError("Hermes executable was not found")

    def dispatch(self, request: AgentRunRequest) -> AgentResult:
        task = request.task
        workspace = request.workspace
        if not workspace.profile.can_execute_commands:
            raise AgentExecutionError(
                f"role {workspace.profile.name} does not allow command execution"
            )
        bindings = (
            (workspace.mission_id, task.mission_id, "mission"),
            (workspace.revision, task.revision, "revision"),
            (workspace.task_id, task.task_id, "task"),
            (workspace.profile.name, task.assignee_role, "role"),
        )
        for actual, expected, name in bindings:
            if actual != expected:
                raise AgentExecutionError(
                    f"workspace {name} does not match task: {actual!r} != {expected!r}"
                )
        _consume_authority(request, "hermes-cli")
        context = {
            "mission_id": request.task.mission_id,
            "revision": request.task.revision,
            "task_id": request.task.task_id,
            "stage": request.task.stage.value,
            "role": request.task.assignee_role,
            "candidate_id": request.task.candidate_id,
            "instruction": request.prompt,
            "result_format": (
                "Return one JSON object with gate, claims, assumptions, unresolved, and "
                "artifacts; do not issue state-transition commands. Artifact paths must be "
                "relative to the assigned work directory and include SHA-256 values."
            ),
        }
        prompt = json.dumps(context, sort_keys=True, ensure_ascii=False)
        environment = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in self._environment_allowlist
        }
        environment.update(
            {
                "HOME": str(request.workspace.home),
                "TMP": str(request.workspace.tmp),
                "TEMP": str(request.workspace.tmp),
                "HERMES_MISSION_ID": request.task.mission_id,
                "HERMES_MISSION_REVISION": str(request.task.revision),
            }
        )
        command_prefix = self._discover_command_prefix()
        command = [
            *command_prefix,
            "--safe-mode",
            "--toolsets",
            "",
            "--oneshot",
            prompt,
            "--in",
            str(request.workspace.work),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=request.workspace.work,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AgentExecutionError(f"Hermes agent execution failed: {error}") from error
        if completed.returncode != 0:
            raise AgentExecutionError(
                f"Hermes agent exited with {completed.returncode}: {completed.stderr.strip()}"
            )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise AgentExecutionError("Hermes agent output was not one JSON object") from error
        if not isinstance(payload, dict):
            raise AgentExecutionError("Hermes agent output must be a JSON object")
        return AgentResult.create(
            mission_id=request.task.mission_id,
            revision=request.task.revision,
            task_id=request.task.task_id,
            stage=request.task.stage,
            sender_role=request.task.assignee_role,
            candidate_id=request.task.candidate_id,
            payload=payload,
            artifact_root=request.workspace.work,
        )
