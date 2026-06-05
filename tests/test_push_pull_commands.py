"""Tests for the `claude-sync push` and `claude-sync pull` commands.

These tests focus on argument wiring, dependency checks, and basic
non-network happy paths. Network-bound behaviors (real `git push`/
`git pull`) are covered separately by the manual test plan.
"""

from __future__ import annotations

import shutil

from pathlib import Path

import pytest
from typer.testing import CliRunner

from claude_sync.cli import app


pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git executable not available",
)


def test_push_requires_initialized_project(tmp_path: Path, monkeypatch) -> None:
    """`push` should fail clearly when `.claude-sync/` is missing."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["push"])
    assert result.exit_code != 0
    assert "init" in result.output.lower()


def test_pull_requires_initialized_project(tmp_path: Path, monkeypatch) -> None:
    """`pull` should fail clearly when `.claude-sync/` is missing."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["pull"])
    assert result.exit_code != 0
    assert "init" in result.output.lower()


def test_push_with_no_remote_mentions_remote(tmp_path: Path, monkeypatch) -> None:
    """`push` without a remote should print a helpful message about adding one."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # Initialize project + local git repo with no remote.
    runner.invoke(app, ["init"])
    from claude_sync.utils.git_sync import GitSync

    git = GitSync(project_root=tmp_path)
    git.init_repo()
    (tmp_path / ".claude-sync" / ".keep").write_text("", encoding="utf-8")
    git.run("add", ".keep")
    git.run("commit", "-m", "initial")

    # Use --no-export to avoid needing a Claude tree in this test.
    result = runner.invoke(app, ["push", "--no-export"])
    assert result.exit_code != 0
    # Should mention either "remote" or a concrete error from git.
    assert "remote" in result.output.lower() or "git" in result.output.lower()


def test_pull_with_no_remote_warns(tmp_path: Path, monkeypatch) -> None:
    """`pull` without a remote should fail clearly."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["init"])
    from claude_sync.utils.git_sync import GitSync

    git = GitSync(project_root=tmp_path)
    git.init_repo()
    (tmp_path / ".claude-sync" / ".keep").write_text("", encoding="utf-8")
    git.run("add", ".keep")
    git.run("commit", "-m", "initial")

    # pull doesn't call export, so no Claude tree needed.
    result = runner.invoke(app, ["pull"])
    assert result.exit_code != 0
    assert "remote" in result.output.lower() or "git" in result.output.lower()
