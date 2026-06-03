"""Tests for the `claude-sync export` command."""

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
    claude_dir = root / ".claude"
    claude_dir.mkdir()
    for name, count in layout.items():
        subdir = claude_dir / name
        subdir.mkdir()
        for i in range(count):
            (subdir / f"f-{i}.txt").write_text("x", encoding="utf-8")
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
    runner.invoke(app, ["init"])  # initialise first

    _stub_locator(monkeypatch, None)
    result = runner.invoke(app, ["export"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_export_copies_data_and_reports_file_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: init, export, verify the destination tree and the count."""
    claude = _make_claude_tree(
        tmp_path, {"sessions": 3, "tasks": 2, "plans": 1, "session-env": 4}
    )
    _stub_locator(monkeypatch, claude)

    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    init_result = runner.invoke(app, ["init"])
    assert init_result.exit_code == 0, init_result.output

    export_result = runner.invoke(app, ["export"])
    assert export_result.exit_code == 0, export_result.output

    data = project / ".claude-sync" / "data"
    assert data.is_dir()
    for name, count in {"sessions": 3, "tasks": 2, "plans": 1, "session-env": 4}.items():
        target = data / name
        assert target.is_dir()
        assert sum(1 for p in target.rglob("*") if p.is_file()) == count

    # Summary line: total file count is 10.
    assert "10" in export_result.output
    assert "Exported" in export_result.output


def test_export_rewrites_destination_on_second_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second export must replace, not merge, the previous data."""
    claude = _make_claude_tree(tmp_path, {"sessions": 2})
    _stub_locator(monkeypatch, claude)

    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    runner.invoke(app, ["export"])

    # Plant a stale file in the destination.
    stale = project / ".claude-sync" / "data" / "sessions" / "stale.txt"
    stale.write_text("stale", encoding="utf-8")

    runner.invoke(app, ["export"])

    assert not stale.exists(), "stale file should have been wiped"


def test_export_with_explicit_claude_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--claude-path` overrides the locator."""
    claude = _make_claude_tree(tmp_path, {"sessions": 1})
    _stub_locator(monkeypatch, tmp_path / "wrong")  # ignored

    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    result = runner.invoke(
        app, ["export", "--claude-path", str(claude)]
    )
    assert result.exit_code == 0, result.output
    assert (project / ".claude-sync" / "data" / "sessions").is_dir()
