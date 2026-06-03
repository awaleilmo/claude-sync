"""Tests for `claude_sync.utils.inspector`."""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_sync.utils.inspector import (
    TRACKED_SUBDIRS,
    ClaudeInspector,
    SubdirStat,
)


def _make_claude_tree(root: Path, layout: dict[str, int]) -> Path:
    """Create a fake `.claude` directory with the given entry counts.

    `layout` maps subdir name -> number of dummy entries to create.
    Any name in TRACKED_SUBDIRS that is missing from `layout` will
    simply not be created, mimicking "subdir not yet present".
    """
    claude_dir = root / ".claude"
    claude_dir.mkdir()
    for name, count in layout.items():
        subdir = claude_dir / name
        subdir.mkdir()
        for i in range(count):
            (subdir / f"entry-{i}").write_text("", encoding="utf-8")
    return claude_dir


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------


def test_tracked_subdirs_are_the_documented_set() -> None:
    """The tracked set must match the spec exactly, in the documented order."""
    assert TRACKED_SUBDIRS == (
        "sessions",
        "projects",
        "tasks",
        "plans",
        "session-env",
    )


def test_subdir_stat_display_for_missing(tmp_path: Path) -> None:
    """A missing subdir should display as an em-dash."""
    stat = SubdirStat(name="sessions", path=tmp_path, exists=False, entry_count=0)
    assert stat.display == "—"


def test_subdir_stat_display_for_present(tmp_path: Path) -> None:
    """A present subdir should display its entry count as a string."""
    stat = SubdirStat(name="sessions", path=tmp_path, exists=True, entry_count=42)
    assert stat.display == "42"


# ---------------------------------------------------------------------------
# Inspector behaviour
# ---------------------------------------------------------------------------


def test_inspect_none_path_reports_all_missing() -> None:
    """Inspector with None path must not raise; all subdirs are missing."""
    result = ClaudeInspector(None).inspect()
    assert result.claude_path == Path("—")
    assert len(result.stats) == len(TRACKED_SUBDIRS)
    assert all(not s.exists for s in result.stats)
    assert result.total_entries == 0


def test_inspect_existing_path_counts_entries(tmp_path: Path) -> None:
    """A populated tree should produce per-subdir counts and a total."""
    claude_dir = _make_claude_tree(
        tmp_path,
        {"sessions": 48, "projects": 12, "session-env": 32},
    )

    result = ClaudeInspector(claude_dir).inspect()

    assert result.claude_path == claude_dir
    # All subdirs in the spec are present in the result, in spec order.
    assert [s.name for s in result.stats] == list(TRACKED_SUBDIRS)

    sessions = result.stat_by_name("sessions")
    assert sessions is not None
    assert sessions.exists is True
    assert sessions.entry_count == 48

    projects = result.stat_by_name("projects")
    assert projects is not None
    assert projects.entry_count == 12

    session_env = result.stat_by_name("session-env")
    assert session_env is not None
    assert session_env.entry_count == 32

    # Total reflects only the subdirs that actually exist.
    assert result.total_entries == 48 + 12 + 32


def test_inspect_handles_partial_tree(tmp_path: Path) -> None:
    """If some subdirs are absent, only the present ones contribute to total."""
    claude_dir = _make_claude_tree(tmp_path, {"sessions": 5, "projects": 2})
    # `tasks`, `plans`, `session-env` intentionally not created.

    result = ClaudeInspector(claude_dir).inspect()

    assert result.stat_by_name("sessions").exists is True  # type: ignore[union-attr]
    assert result.stat_by_name("projects").exists is True  # type: ignore[union-attr]
    assert result.stat_by_name("tasks").exists is False
    assert result.stat_by_name("plans").exists is False
    assert result.stat_by_name("session-env").exists is False
    assert result.total_entries == 5 + 2


def test_inspect_with_nonexistent_path_marks_all_missing(tmp_path: Path) -> None:
    """A path that does not exist should look identical to None."""
    ghost = tmp_path / "no-such-claude"
    result = ClaudeInspector(ghost).inspect()
    assert all(not s.exists for s in result.stats)
    assert result.total_entries == 0


def test_inspect_handles_unreadable_subdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a subdir raises OSError on iterdir, treat it as zero entries."""
    claude_dir = _make_claude_tree(tmp_path, {"sessions": 3})

    def boom(_self: Path):
        raise PermissionError("nope")

    monkeypatch.setattr(Path, "iterdir", boom)

    result = ClaudeInspector(claude_dir).inspect()
    stat = result.stat_by_name("sessions")
    # The subdir itself exists, we just couldn't read it: count is 0.
    assert stat is not None
    assert stat.exists is True
    assert stat.entry_count == 0
