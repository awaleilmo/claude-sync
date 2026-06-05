"""Tests for the `claude-sync init` command."""

from __future__ import annotations

import json

from pathlib import Path

from typer.testing import CliRunner

from claude_sync.cli import app


def test_init_creates_sync_dir_and_manifest(tmp_path: Path, monkeypatch) -> None:
    """`init` should create `.claude-sync/` and `manifest.json` with correct schema."""
    runner = CliRunner()

    # Point the CLI at the temp dir; init's default is cwd.
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0, result.output

    sync_dir = tmp_path / ".claude-sync"
    manifest = sync_dir / "manifest.json"

    assert sync_dir.is_dir()
    assert manifest.is_file()

    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["project_name"] == tmp_path.name
    assert data["version"] == 2


def test_init_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    """Running `init` twice should not fail and should not lose data."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    first = runner.invoke(app, ["init"])
    assert first.exit_code == 0, first.output

    second = runner.invoke(app, ["init"])
    assert second.exit_code == 0, second.output

    manifest = tmp_path / ".claude-sync" / "manifest.json"
    assert manifest.is_file()


def test_init_force_overwrites_manifest(tmp_path: Path, monkeypatch) -> None:
    """`init --force` should regenerate the manifest."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["init"])

    manifest = tmp_path / ".claude-sync" / "manifest.json"
    manifest.write_text('{"project_name": "old", "version": 99}\n', encoding="utf-8")

    result = runner.invoke(app, ["init", "--force"])
    assert result.exit_code == 0, result.output

    data = json.loads(manifest.read_text(encoding="utf-8"))
    # --force restores the default values, replacing the old payload.
    assert data["project_name"] == tmp_path.name
    assert data["version"] == 2
