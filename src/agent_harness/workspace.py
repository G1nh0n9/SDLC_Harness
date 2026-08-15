from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class AccessDenied(PermissionError):
    """Raised when a role requests an unauthorized workspace operation."""


@dataclass(frozen=True)
class RoleProfile:
    name: str
    tools: frozenset[str]
    writable_areas: frozenset[str]
    network_allowed: bool
    can_execute_commands: bool
    can_approve: bool


class RoleCatalog:
    def __init__(self, profiles: Mapping[str, RoleProfile]) -> None:
        self._profiles = dict(profiles)

    def __getitem__(self, role: str) -> RoleProfile:
        try:
            return self._profiles[role]
        except KeyError as error:
            raise KeyError(f"unknown role profile: {role}") from error

    @classmethod
    def default(cls) -> RoleCatalog:
        reviewer = RoleProfile(
            name="independent-code-reviewer",
            tools=frozenset({"read-file", "search", "write-finding"}),
            writable_areas=frozenset({"work"}),
            network_allowed=False,
            can_execute_commands=False,
            can_approve=True,
        )
        profiles = {
            reviewer.name: reviewer,
            "implementation-specialist": RoleProfile(
                name="implementation-specialist",
                tools=frozenset({"read-file", "write-file", "run-tests"}),
                writable_areas=frozenset({"work", "build", "tmp"}),
                network_allowed=False,
                can_execute_commands=True,
                can_approve=False,
            ),
            "oracle-specialist": RoleProfile(
                name="oracle-specialist",
                tools=frozenset({"read-spec", "write-oracle"}),
                writable_areas=frozenset({"work"}),
                network_allowed=False,
                can_execute_commands=True,
                can_approve=False,
            ),
            "verification-specialist": RoleProfile(
                name="verification-specialist",
                tools=frozenset({"read-candidate", "run-tests", "write-evidence"}),
                writable_areas=frozenset({"work", "build", "tmp"}),
                network_allowed=False,
                can_execute_commands=True,
                can_approve=False,
            ),
            "mission-manager": RoleProfile(
                name="mission-manager",
                tools=frozenset({"dispatch", "read-evidence", "transition"}),
                writable_areas=frozenset({"work"}),
                network_allowed=False,
                can_execute_commands=False,
                can_approve=False,
            ),
            "release-specialist": RoleProfile(
                name="release-specialist",
                tools=frozenset({"read-approved-candidate", "package", "write-manifest"}),
                writable_areas=frozenset({"work", "build"}),
                network_allowed=False,
                can_execute_commands=True,
                can_approve=False,
            ),
            "security-reviewer": RoleProfile(
                name="security-reviewer",
                tools=frozenset({"read-candidate", "write-finding"}),
                writable_areas=frozenset({"work"}),
                network_allowed=False,
                can_execute_commands=False,
                can_approve=False,
            ),
        }
        return cls(profiles)

    @classmethod
    def default_with_dynamic_role(
        cls,
        role: str,
        *,
        can_execute_commands: bool,
        can_approve: bool,
    ) -> RoleCatalog:
        catalog = cls.default()
        if role not in catalog._profiles:
            catalog._profiles[role] = RoleProfile(
                name=role,
                tools=frozenset({"read-input", "write-result"}),
                writable_areas=frozenset({"work", "tmp"}),
                network_allowed=False,
                can_execute_commands=can_execute_commands,
                can_approve=can_approve,
            )
        return catalog

    def register_dynamic_role(
        self,
        role: str,
        *,
        can_execute_commands: bool,
        can_approve: bool,
    ) -> None:
        if role not in self._profiles:
            self._profiles[role] = RoleProfile(
                name=role,
                tools=frozenset({"read-input", "write-result"}),
                writable_areas=frozenset({"work", "tmp"}),
                network_allowed=False,
                can_execute_commands=can_execute_commands,
                can_approve=can_approve,
            )


@dataclass(frozen=True)
class RoleWorkspace:
    root: Path
    work: Path
    build: Path
    tmp: Path
    home: Path
    inputs: Path
    profile: RoleProfile
    mission_id: str
    revision: int
    task_id: str


class WorkspaceBroker:
    _safe_component_pattern = re.compile(r"^[A-Za-z0-9_.-]+$")

    def __init__(self, root: Path, catalog: RoleCatalog | None = None) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.catalog = catalog or RoleCatalog.default()

    @classmethod
    def _safe_component(cls, value: str) -> str:
        if not value or not cls._safe_component_pattern.fullmatch(value):
            raise ValueError(f"unsafe path component: {value!r}")
        return value

    def create(
        self, *, mission_id: str, revision: int, task_id: str, role: str
    ) -> RoleWorkspace:
        mission = self._safe_component(mission_id)
        task = self._safe_component(task_id)
        role_name = self._safe_component(role)
        profile = self.catalog[role]
        workspace_root = (
            self.root / "missions" / mission / f"rev-{revision}" / "tasks" / task / role_name
        ).resolve()
        try:
            workspace_root.relative_to(self.root)
        except ValueError as error:
            raise AccessDenied("workspace path escaped harness root") from error
        areas = {name: workspace_root / name for name in ("work", "build", "tmp", "home", "inputs")}
        for area in areas.values():
            area.mkdir(parents=True, exist_ok=True)
        return RoleWorkspace(
            root=workspace_root,
            work=areas["work"],
            build=areas["build"],
            tmp=areas["tmp"],
            home=areas["home"],
            inputs=areas["inputs"],
            profile=profile,
            mission_id=mission_id,
            revision=revision,
            task_id=task_id,
        )

    @staticmethod
    def _inside(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True

    @staticmethod
    def _has_symbolic_component(path: Path, root: Path) -> bool:
        current = path
        boundary = root.parent
        while current != boundary:
            if current.is_symlink():
                return True
            if current.parent == current:
                break
            current = current.parent
        return False

    def write_text(self, workspace: RoleWorkspace, destination: Path, content: str) -> None:
        unresolved = destination.absolute()
        if self._has_symbolic_component(unresolved, workspace.root):
            raise AccessDenied("symbolic link write paths are forbidden")
        resolved = destination.resolve(strict=False)
        if not self._inside(resolved, workspace.root):
            raise AccessDenied("write target is outside role workspace")
        if self._inside(resolved, workspace.inputs):
            raise AccessDenied("write target is a read-only input")
        allowed_roots = [
            getattr(workspace, area) for area in workspace.profile.writable_areas
        ]
        if not any(self._inside(resolved, root) for root in allowed_roots):
            raise AccessDenied("role profile does not allow this write area")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
