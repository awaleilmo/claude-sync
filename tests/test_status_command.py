"""Tests for the `claude-sync status` command.

Tahap 2 changes:
- `status` now also reports the Claude Code install path.
- `status` exits non-zero if EITHER the project is uninitialized OR
  the Claude install cannot be located.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from claude_sync.cli import app
from claude_sync.utils.claude_locator import ClaudeLocator


def _make_locator_stub(monkeypatch, fake_path: Path | None) -> None:
    """Patch `ClaudeLocator.find_claude_path` to return a deterministic value."""

    def stub(self: ClaudeLocator) -> Path | None:  # noqa: ARG001
        return fake_path

    monkeypatch.setattr(ClaudeLocator, "find_claude_path", stub)


def test_status_fails_when_uninitialized(tmp_path: Path, monkeypatch) -> None:
    """`status` should exit non-zero with a clear message when nothing exists."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    # Pretend Claude is installed so the only failure is project init.
    _make_locator_stub(monkeypatch, tmp_path / ".claude")

    result = runner.invoke(app, ["status"])

    assert result.exit_code != 0
    assert "not initialized" in result.output.lower()


def test_status_succeeds_after_init(tmp_path: Path, monkeypatch) -> None:
    """`status` should report success when project + Claude install are both present."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # Initialize the project.
    init_result = runner.invoke(app, ["init"])
    assert init_result.exit_code == 0, init_result.output

    # Pretend Claude is installed.
    _make_locator_stub(monkeypatch, tmp_path / "fake-home" / ".claude")

    status_result = runner.invoke(app, ["status"])
    assert status_result.exit_code == 0, status_result.output
    assert "initialized" in status_result.output.lower()
    assert "manifest" in status_result.output.lower()
    assert "claude path" in status_result.output.lower()


def test_status_warns_when_manifest_missing(tmp_path: Path, monkeypatch) -> None:
    """`status` should fail clearly if the sync dir exists but manifest is gone."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    _make_locator_stub(monkeypatch, tmp_path / ".claude")

    (tmp_path / ".claude-sync").mkdir()

    result = runner.invoke(app, ["status"])
    assert result.exit_code != 0
    assert "manifest" in result.output.lower()


def test_status_reports_claude_path_when_found(tmp_path: Path, monkeypatch) -> None:
    """`status` should print the discovered Claude path.

    Rich may wrap long paths, so we strip all whitespace from the output
    before comparing — that way line breaks between path segments are
    harmless.
    """
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])  # initialize first

    fake_claude = tmp_path / "home" / ".claude"
    _make_locator_stub(monkeypatch, fake_claude)

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0, result.output
    assert str(fake_claude) in result.output.replace("\n", "").replace(" ", "")


def test_status_reports_claude_path_when_not_found(tmp_path: Path, monkeypatch) -> None:
    """`status` should print 'Not Found' (and exit non-zero) when Claude is missing."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])  # initialize first

    _make_locator_stub(monkeypatch, None)

    result = runner.invoke(app, ["status"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
