"""Tests for `claude_sync.utils.exporter`."""

from __future__ import annotations

from pathlib import Path

from claude_sync.utils.exporter import (
    DATA_SUBDIR,
    EXPORT_SUBDIRS,
    ClaudeExporter,
    ExportReport,
    _count_files,
)


def _make_claude_tree(root: Path, layout: dict[str, int]) -> Path:
    """Create a fake `.claude` dir with `count` regular files per subdir."""
    claude_dir = root / ".claude"
    claude_dir.mkdir()
    for name, count in layout.items():
        subdir = claude_dir / name
        subdir.mkdir()
        for i in range(count):
            (subdir / f"file-{i}.txt").write_text("x", encoding="utf-8")
    return claude_dir


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_export_subdirs_excludes_projects() -> None:
    """Verify the canonical export subdirs.

    The set includes the session-related folders that Claude Code
    actually writes into, plus memory for persistence across devices.
    """
    assert "projects" in EXPORT_SUBDIRS  # Tahap 5: now included
    assert "memory" in EXPORT_SUBDIRS   # Tahap 5: now included
    assert "sessions" in EXPORT_SUBDIRS
    assert "tasks" in EXPORT_SUBDIRS
    assert "plans" in EXPORT_SUBDIRS
    assert "session-env" in EXPORT_SUBDIRS


# ---------------------------------------------------------------------------
# _count_files helper
# ---------------------------------------------------------------------------


def test_count_files_returns_zero_for_missing_dir(tmp_path: Path) -> None:
    """A non-existent directory should count as 0, not crash."""
    assert _count_files(tmp_path / "nope") == 0


def test_count_files_recursive(tmp_path: Path) -> None:
    """Files in nested subdirs should be counted."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "c.txt").write_text("", encoding="utf-8")
    (tmp_path / "a" / "b" / "d.txt").write_text("", encoding="utf-8")
    (tmp_path / "a" / "top.txt").write_text("", encoding="utf-8")
    assert _count_files(tmp_path) == 3


# ---------------------------------------------------------------------------
# ClaudeExporter
# ---------------------------------------------------------------------------


def test_export_creates_data_root_and_copies_subdirs(tmp_path: Path) -> None:
    """A full export should mirror every present subdir and report counts."""
    claude = _make_claude_tree(
        tmp_path, {"sessions": 3, "tasks": 2, "plans": 4, "session-env": 1, "memory": 2, "projects": 5}
    )

    project = tmp_path / "project"
    project.mkdir()

    report = ClaudeExporter(claude, project).export()

    # Counts.
    assert report.copied == {"sessions": 3, "tasks": 2, "plans": 4, "session-env": 1, "memory": 2, "projects": 5}
    assert report.file_count == 17
    assert report.skipped == ()

    # Files on disk.
    data = project / ".claude-sync" / DATA_SUBDIR
    assert data.is_dir()
    for name, count in report.copied.items():
        target = data / name
        assert target.is_dir()
        assert _count_files(target) == count


def test_export_skips_missing_source_subdirs(tmp_path: Path) -> None:
    """Subdirs absent in the source should be reported as skipped, not error."""
    claude = _make_claude_tree(tmp_path, {"sessions": 2})  # others missing
    project = tmp_path / "project"
    project.mkdir()

    report = ClaudeExporter(claude, project).export()

    assert report.copied == {"sessions": 2}
    # The other five were skipped.
    assert set(report.skipped) == {"tasks", "plans", "session-env", "memory", "projects"}
    assert report.file_count == 2

    # The destination only has `sessions/`.
    data = project / ".claude-sync" / DATA_SUBDIR
    assert (data / "sessions").is_dir()
    assert not (data / "tasks").exists()
    assert not (data / "plans").exists()
    assert not (data / "session-env").exists()
    assert not (data / "memory").exists()
    assert not (data / "projects").exists()


def test_export_wipes_previous_data(tmp_path: Path) -> None:
    """A second run must NOT keep stale files from the first."""
    claude = _make_claude_tree(tmp_path, {"sessions": 2, "tasks": 1, "memory": 1})

    project = tmp_path / "project"
    project.mkdir()

    # First export.
    ClaudeExporter(claude, project).export()
    data = project / ".claude-sync" / DATA_SUBDIR
    assert _count_files(data / "sessions") == 2

    # Add a file in the source, remove a different one, re-export.
    (claude / "sessions" / "extra.txt").write_text("y", encoding="utf-8")
    (claude / "tasks" / "file-0.txt").unlink()
    (claude / "plans").mkdir()  # a brand-new subdir appears
    (claude / "plans" / "p.txt").write_text("p", encoding="utf-8")
    (claude / "projects").mkdir()  # another new subdir
    (claude / "projects" / "proj.txt").write_text("proj", encoding="utf-8")

    report = ClaudeExporter(claude, project).export()
    assert report.copied["sessions"] == 3  # was 2, +extra
    assert report.copied["tasks"] == 0  # was 1, -file-0
    assert report.copied["memory"] == 1  # unchanged
    assert report.copied["plans"] == 1  # new
    assert report.copied["projects"] == 1  # new
    # `session-env` was missing in BOTH runs; first run skipped it,
    # and it's still skipped here (we don't switch a subdir from
    # skipped -> copied on a re-run).
    assert "session-env" in report.skipped

    # No stale files from the first run.
    sessions_files = sorted(p.name for p in (data / "sessions").iterdir())
    assert sessions_files == ["extra.txt", "file-0.txt", "file-1.txt"]
    assert (data / "tasks").is_dir() and list((data / "tasks").iterdir()) == []


def test_export_handles_empty_source_subdirs(tmp_path: Path) -> None:
    """An empty subdir in the source should be created empty in the dest."""
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "sessions").mkdir()  # exists, empty

    project = tmp_path / "project"
    project.mkdir()

    report = ClaudeExporter(claude, project).export()

    assert report.copied == {"sessions": 0}
    assert report.file_count == 0
    assert (project / ".claude-sync" / DATA_SUBDIR / "sessions").is_dir()


def test_export_preserves_file_contents(tmp_path: Path) -> None:
    """Bytes should round-trip unchanged for the files we copy."""
    claude = tmp_path / ".claude"
    claude.mkdir()
    sessions = claude / "sessions"
    sessions.mkdir()
    payload = "hello\nworld\n"
    (sessions / "a.txt").write_text(payload, encoding="utf-8")

    project = tmp_path / "project"
    project.mkdir()

    ClaudeExporter(claude, project).export()

    copied = project / ".claude-sync" / DATA_SUBDIR / "sessions" / "a.txt"
    assert copied.read_text(encoding="utf-8") == payload


def test_export_does_not_touch_source(tmp_path: Path) -> None:
    """Running export multiple times must not modify the source tree."""
    claude = _make_claude_tree(tmp_path, {"sessions": 2})
    before = sorted(p.name for p in claude.rglob("*") if p.is_file())
    project = tmp_path / "project"
    project.mkdir()

    ClaudeExporter(claude, project).export()
    ClaudeExporter(claude, project).export()

    after = sorted(p.name for p in claude.rglob("*") if p.is_file())
    assert before == after


def test_export_creates_data_dir_under_existing_sync_dir(tmp_path: Path) -> None:
    """The parent `.claude-sync/` may pre-exist (init ran first)."""
    claude = _make_claude_tree(tmp_path, {"sessions": 1})
    project = tmp_path / "project"
    (project / ".claude-sync" / "manifest.json").parent.mkdir(parents=True)
    (project / ".claude-sync" / "manifest.json").write_text("{}", encoding="utf-8")

    ClaudeExporter(claude, project).export()

    data = project / ".claude-sync" / DATA_SUBDIR
    assert data.is_dir()
    # Manifest was not deleted.
    assert (project / ".claude-sync" / "manifest.json").is_file()


def test_export_report_dataclass_shape() -> None:
    """`ExportReport.copied_subdirs` returns the keys in insertion order.

    `file_count` is a plain field the exporter fills in; constructing the
    dataclass by hand does not recompute it, so we set it explicitly.
    """
    r = ExportReport(
        claude_path=Path("/c"),
        data_root=Path("/d"),
        copied={"sessions": 1, "tasks": 2},
        file_count=3,
        copied_files=(),
        skipped_files=(),
    )
    assert r.copied_subdirs == ("sessions", "tasks")
    assert r.file_count == 3
    assert r.copied_files == ()
    assert r.skipped_files == ()
