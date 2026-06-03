"""Tests for the `claude-sync inspect` command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from claude_sync.cli import app
from claude_sync.utils.claude_locator import ClaudeLocator


def _stub_locator(monkeypatch, path: Path | None) -> None:
    """Make ClaudeLocator return a fixed path (or None)."""

    def stub(self: ClaudeLocator) -> Path | None:  # noqa: ARG001
        return path

    monkeypatch.setattr(ClaudeLocator, "find_claude_path", stub)


def _make_claude_tree(root: Path, layout: dict[str, int]) -> Path:
    """Build a fake `.claude` dir with the given per-subdir entry counts."""
    claude_dir = root / ".claude"
    claude_dir.mkdir()
    for name, count in layout.items():
        subdir = claude_dir / name
        subdir.mkdir()
        for i in range(count):
            (subdir / f"entry-{i}").write_text("", encoding="utf-8")
    return claude_dir


def test_inspect_renders_table_for_populated_tree(
    tmp_path: Path, monkeypatch
) -> None:
    """Inspect should print the Claude path, a table, and a summary line.

    Rich may wrap long paths across multiple lines, so we strip
    whitespace before checking for the path.
    """
    claude_dir = _make_claude_tree(
        tmp_path,
        {"sessions": 48, "projects": 12, "tasks": 7, "plans": 10, "session-env": 32},
    )
    _stub_locator(monkeypatch, claude_dir)

    runner = CliRunner()
    result = runner.invoke(app, ["inspect"])

    assert result.exit_code == 0, result.output

    # Header line: the path we stubbed in. Whitespace-strip the
    # output first because Rich may wrap long paths mid-segment.
    assert str(claude_dir) in result.output.replace("\n", "").replace(" ", "")

    # Each tracked subdir appears as a row.
    for name in ("sessions", "projects", "tasks", "plans", "session-env"):
        assert name in result.output

    # Counts should be visible.
    assert "48" in result.output
    assert "12" in result.output
    assert "7" in result.output

    # Summary line uses the documented phrasing.
    assert "summary" in result.output.lower()
    assert "total entries" in result.output.lower()


def test_inspect_reports_missing_subdirs(
    tmp_path: Path, monkeypatch
) -> None:
    """Subdirs that don't exist should appear as 'missing' in the table."""
    claude_dir = _make_claude_tree(tmp_path, {"sessions": 1})
    _stub_locator(monkeypatch, claude_dir)

    runner = CliRunner()
    result = runner.invoke(app, ["inspect"])

    assert result.exit_code == 0, result.output
    # `tasks` etc. should be flagged as missing (case-insensitive).
    output_lower = result.output.lower()
    assert "missing" in output_lower


def test_inspect_handles_no_claude_directory(tmp_path: Path, monkeypatch) -> None:
    """Inspect should report 'Not Found' and exit non-zero when Claude is missing."""
    _stub_locator(monkeypatch, None)

    runner = CliRunner()
    result = runner.invoke(app, ["inspect"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_inspect_with_explicit_claude_path_flag(
    tmp_path: Path, monkeypatch
) -> None:
    """`--claude-path` should override the locator."""
    claude_dir = _make_claude_tree(tmp_path, {"sessions": 5})

    # Locator stub should be ignored because --claude-path wins.
    _stub_locator(monkeypatch, tmp_path / "wrong")

    runner = CliRunner()
    result = runner.invoke(app, ["inspect", "--claude-path", str(claude_dir)])

    assert result.exit_code == 0, result.output
    # Strip whitespace — Rich wraps long paths.
    assert str(claude_dir) in result.output.replace("\n", "").replace(" ", "")
    assert "5" in result.output


def test_inspect_with_no_locate_flag_fails_when_no_path(
    tmp_path: Path, monkeypatch
) -> None:
    """`--no-locate` without `--claude-path` should report Not Found."""
    _stub_locator(monkeypatch, None)

    runner = CliRunner()
    result = runner.invoke(app, ["inspect", "--no-locate"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()
