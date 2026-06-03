"""Tests for the `claude-sync import` command."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from claude_sync.cli import app
from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.exporter import DATA_SUBDIR


def _stub_locator(monkeypatch, path: Path | None) -> None:
    def stub(self: ClaudeLocator) -> Path | None:  # noqa: ARG001
        return path

    monkeypatch.setattr(ClaudeLocator, "find_claude_path", stub)


def _make_data_tree(project_root: Path, layout: dict[str, int]) -> None:
    data = project_root / ".claude-sync" / DATA_SUBDIR
    data.mkdir(parents=True)
    for name, count in layout.items():
        subdir = data / name
        subdir.mkdir()
        for i in range(count):
            (subdir / f"f-{i}.txt").write_text("x", encoding="utf-8")


def _make_existing_claude(root: Path, layout: dict[str, int]) -> Path:
    claude = root / ".claude"
    claude.mkdir()
    for name, count in layout.items():
        sub = claude / name
        sub.mkdir()
        for i in range(count):
            (sub / f"old-{i}.txt").write_text("old", encoding="utf-8")
    return claude


def test_import_fails_when_project_not_initialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`import` should refuse to write into an uninitialised project."""
    _stub_locator(monkeypatch, tmp_path / ".claude")
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["import"])

    assert result.exit_code != 0
    assert "not initialized" in result.output.lower()


def test_import_fails_when_claude_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`import` should exit non-zero if no destination can be resolved."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])  # project exists, but no data
    _stub_locator(monkeypatch, None)

    result = runner.invoke(app, ["import"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_import_fails_when_data_dir_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If there's no `.claude-sync/data/`, we have nothing to import."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])

    # Use a destination that does not pre-exist (no backup needed).
    dest = tmp_path / "claude-dest"
    _stub_locator(monkeypatch, dest)

    result = runner.invoke(app, ["import"])
    assert result.exit_code != 0
    assert "nothing to import" in result.output.lower()


def test_import_restores_files_and_reports_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: init, plant data, import, verify destination + count."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    _make_data_tree(project, {"sessions": 3, "tasks": 2, "plans": 1, "session-env": 4})

    dest = tmp_path / "claude-dest"
    _stub_locator(monkeypatch, dest)

    result = runner.invoke(app, ["import"])
    assert result.exit_code == 0, result.output

    # Files on disk.
    for name, count in {"sessions": 3, "tasks": 2, "plans": 1, "session-env": 4}.items():
        target = dest / name
        assert target.is_dir()
        assert sum(1 for p in target.rglob("*") if p.is_file()) == count

    # Summary line: total file count is 10.
    assert "10" in result.output
    assert "Imported" in result.output


def test_import_creates_backup_when_destination_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`import` must take a timestamped backup before overwriting."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    _make_data_tree(project, {"sessions": 1})

    # Existing destination with old data.
    dest = _make_existing_claude(tmp_path, {"sessions": 2})
    _stub_locator(monkeypatch, dest)

    result = runner.invoke(app, ["import"])
    assert result.exit_code == 0, result.output

    # Find the backup directory.
    backups = [p for p in tmp_path.iterdir() if p.name.startswith(".claude.backup-")]
    assert len(backups) == 1
    backup = backups[0]
    assert re.match(r"^\.claude\.backup-\d{8}-\d{6}(-\d+)?$", backup.name)

    # Backup has the old data; destination has the new data.
    assert (backup / "sessions" / "old-0.txt").is_file()
    assert (dest / "sessions" / "f-0.txt").is_file()
    assert not (dest / "sessions" / "old-0.txt").exists()

    # Backup path is mentioned in the output.
    assert "Backup created" in result.output


def test_import_no_backup_flag_skips_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--no-backup` should not create a backup directory."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    _make_data_tree(project, {"sessions": 1})

    dest = _make_existing_claude(tmp_path, {"sessions": 2})
    _stub_locator(monkeypatch, dest)

    result = runner.invoke(app, ["import", "--no-backup"])
    assert result.exit_code == 0, result.output

    # No backup directories.
    backups = [p for p in tmp_path.iterdir() if p.name.startswith(".claude.backup-")]
    assert backups == []

    # Destination has the imported data, not the old data.
    assert (dest / "sessions" / "f-0.txt").is_file()
    assert not (dest / "sessions" / "old-0.txt").exists()


def test_import_with_explicit_claude_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--claude-path` overrides the locator."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    _make_data_tree(project, {"sessions": 2})

    dest = tmp_path / "explicit-dest"
    _stub_locator(monkeypatch, tmp_path / "wrong")  # ignored

    result = runner.invoke(
        app, ["import", "--claude-path", str(dest), "--no-backup"]
    )
    assert result.exit_code == 0, result.output
    assert (dest / "sessions" / "f-0.txt").is_file()
    assert (dest / "sessions" / "f-1.txt").is_file()
