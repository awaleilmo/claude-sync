"""Tests for the `claude-sync export` command.

Phase 2: export is now project-based — it only copies the single
Claude project folder that corresponds to the current local project.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from claude_sync.cli import app
from claude_sync.utils.claude_locator import ClaudeLocator


def _stub_locator(monkeypatch, path: Path | None) -> None:
    def stub(self: ClaudeLocator) -> Path | None:  # noqa: ARG001
        return path

    monkeypatch.setattr(ClaudeLocator, "find_claude_path", stub)


def _make_claude_tree(root: Path, layout: dict[str, int]) -> Path:
    """Create a fake ``.claude/`` directory.

    For Phase 2 we must also create a ``projects/`` sub-directory
    whose name matches the *local project path* that tests will
    compute via ``project_to_claude_folder``.

    Args:
        root: Temp directory used by ``tmp_path``.
        layout: Mapping ``subdir -> num_files``.

    Returns:
        Path to the ``.claude`` directory.
    """
    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True)
    for name, count in layout.items():
        subdir = claude_dir / name
        subdir.mkdir()
        for i in range(count):
            (subdir / f"f-{i}.txt").write_text("x", encoding="utf-8")
    return claude_dir


def _make_project_claude_tree(
    root: Path, local_project_path: Path
) -> Path:
    """Create a Claude directory with a matching project folder.

    Phase 2 export looks for ``~/.claude/projects/<computed_folder_name>``
    where the folder name is derived from ``local_project_path``.

    Args:
        root: Temp directory.
        local_project_path: The *local* project path used to compute
            the expected Claude project folder name.

    Returns:
        Path to the ``.claude`` directory.
    """
    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True)

    # Compute what Claude project folder name the exporter will look for.
    from claude_sync.utils.project_path import project_to_claude_folder

    folder_name = project_to_claude_folder(local_project_path)

    projects_dir = claude_dir / "projects" / folder_name
    projects_dir.mkdir(parents=True)

    # Add a couple of session files inside the project folder.
    for i in range(3):
        (projects_dir / f"session-{i}.jsonl").write_text("x", encoding="utf-8")
    # Also add a memory subdir.
    mem_dir = projects_dir / "memory"
    mem_dir.mkdir()
    (mem_dir / "session.md").write_text("mem", encoding="utf-8")

    return claude_dir


def test_export_fails_when_project_not_initialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`export` must refuse to write into an uninitialised project."""
    _stub_locator(monkeypatch, tmp_path / ".claude")
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["export"])

    assert result.exit_code != 0
    assert "not initialized" in result.output.lower()


def test_export_fails_when_claude_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`export` should exit non-zero if Claude can't be located."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])

    _stub_locator(monkeypatch, None)
    result = runner.invoke(app, ["export"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_export_copies_project_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: init, export, verify the project folder is exported."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    # Set up Claude with matching project folder.
    claude = _make_project_claude_tree(tmp_path, project)
    _stub_locator(monkeypatch, claude)

    runner = CliRunner()
    init_result = runner.invoke(app, ["init"])
    assert init_result.exit_code == 0, init_result.output

    export_result = runner.invoke(app, ["export"], input="test123\n")
    assert export_result.exit_code == 0, export_result.output

    # Verify project folder exists in export destination.
    expected = project / ".claude-sync" / "export" / "project"
    assert expected.is_dir()

    from claude_sync.utils.project_path import project_to_claude_folder

    folder_name = project_to_claude_folder(project)
    project_export = expected / folder_name
    assert project_export.is_dir()

    # Check files were copied.
    files = list(project_export.rglob("*"))
    file_count = sum(1 for f in files if f.is_file())
    assert file_count == 4  # 3 session files + 1 memory file

    # Verify the output messages.
    assert "Exported" in export_result.output
    assert folder_name in export_result.output


def test_export_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second export should replace the previous data, not merge."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    claude = _make_project_claude_tree(tmp_path, project)
    _stub_locator(monkeypatch, claude)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    runner.invoke(app, ["export"], input="test123\n")

    # Plant a stale file in the destination.
    from claude_sync.utils.project_path import project_to_claude_folder

    folder_name = project_to_claude_folder(project)
    stale = (
        project
        / ".claude-sync"
        / "export"
        / "project"
        / folder_name
        / "stale.txt"
    )
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("stale", encoding="utf-8")

    runner.invoke(app, ["export"], input="test123\n")

    assert not stale.exists(), "stale file should have been wiped"


def test_export_with_explicit_claude_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--claude-path` overrides the locator."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    # Set up a Claude directory in a *different* root path.
    other_root = tmp_path / "other_claude_root"
    claude = _make_project_claude_tree(other_root, project)
    # Make sure the locator returns the *wrong* path (which should be ignored).
    _stub_locator(monkeypatch, tmp_path / "wrong")

    runner = CliRunner()
    runner.invoke(app, ["init"])

    result = runner.invoke(
        app, ["export", "--claude-path", str(claude)], input="test123\n"
    )
    assert result.exit_code == 0, result.output

    from claude_sync.utils.project_path import project_to_claude_folder

    folder_name = project_to_claude_folder(project)
    exported = project / ".claude-sync" / "export" / "project" / folder_name
    assert exported.is_dir()
