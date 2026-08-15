from pathlib import Path

import pytest

from agent_harness.workspace import AccessDenied, RoleCatalog, WorkspaceBroker


def test_reviewer_cannot_write_product_source_or_escape_workspace(tmp_path: Path) -> None:
    catalog = RoleCatalog.default()
    broker = WorkspaceBroker(tmp_path / "runs", catalog)
    workspace = broker.create(
        mission_id="mis-1",
        revision=1,
        task_id="task-review",
        role="independent-code-reviewer",
    )
    source_file = workspace.inputs / "product-source" / "app.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("VALUE = 1\n", encoding="utf-8")

    with pytest.raises(AccessDenied, match="read-only input"):
        broker.write_text(workspace, source_file, "VALUE = 2\n")
    with pytest.raises(AccessDenied, match="outside role workspace"):
        broker.write_text(workspace, workspace.root.parent / "escaped.txt", "bad")

    finding = workspace.work / "finding.json"
    broker.write_text(workspace, finding, '{"severity":"major"}\n')
    assert finding.read_text(encoding="utf-8").startswith("{")
    assert workspace.profile.can_approve is True
    assert workspace.profile.can_execute_commands is False


def test_workspace_rejects_symbolic_link_write_path(tmp_path: Path) -> None:
    broker = WorkspaceBroker(tmp_path / "runs", RoleCatalog.default())
    workspace = broker.create(
        mission_id="mis-1",
        revision=1,
        task_id="task-implementation",
        role="implementation-specialist",
    )
    target = workspace.work / "target"
    target.mkdir()
    link = workspace.work / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links are not available on this system")

    with pytest.raises(AccessDenied, match="symbolic link"):
        broker.write_text(workspace, link / "result.txt", "blocked")
