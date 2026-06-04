"""Tests for `claude_sync.utils.importer`."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from claude_sync.utils.exporter import DATA_SUBDIR
from claude_sync.utils.importer import ClaudeImporter, ImportReport


def _make_data_tree(project_root: Path, layout: dict[str, int]) -> Path:
    """Build a fake `.claude-sync/data/<subdir>/` tree with files."""
    data = project_root / ".claude-sync" / DATA_SUBDIR
    data.mkdir(parents=True)
    for name, count in layout.items():
        subdir = data / name
        subdir.mkdir()
        for i in range(count):
            (subdir / f"f-{i}.txt").write_text("x", encoding="utf-8")
    return data


def _make_claude_dir(root: Path, layout: dict[str, int]) -> Path:
    """Build a fake existing `.claude` dir to be backed up + replaced."""
    claude_dir = root / ".claude"
    claude_dir.mkdir()
    for name, count in layout.items():
        subdir = claude_dir / name
        subdir.mkdir()
        for i in range(count):
            (subdir / f"old-{i}.txt").write_text("old", encoding="utf-8")
    return claude_dir


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_import_restores_all_subdirs_and_reports_count(tmp_path: Path) -> None:
    """A full import should copy every subdir and report per-subdir counts."""
    project = tmp_path / "project"
    _make_data_tree(project, {"sessions": 3, "tasks": 2, "plans": 4, "session-env": 1})

    target = tmp_path / ".claude"  # does not pre-exist; no backup needed
    report = ClaudeImporter(target, project).import_data()

    assert report.backup_path is None
    assert report.restored == {"sessions": 3, "tasks": 2, "plans": 4, "session-env": 1}
    assert report.file_count == 10
    # memory and projects are in EXPORT_SUBDIRS but absent from data/
    assert set(report.skipped) == {"memory", "projects"}
    assert (target / "sessions").is_dir()
    assert (target / "tasks").is_dir()
    assert (target / "plans").is_dir()
    assert (target / "session-env").is_dir()


def test_import_takes_backup_when_target_exists(tmp_path: Path) -> None:
    """When `.claude` already exists, it must be moved aside as a backup."""
    project = tmp_path / "project"
    _make_data_tree(project, {"sessions": 1})

    target = _make_claude_dir(tmp_path, {"sessions": 2, "tasks": 1})

    report = ClaudeImporter(target, project).import_data()

    # Backup exists and has the original layout.
    assert report.backup_path is not None
    assert report.backup_path.is_dir()
    assert report.backup_path.name.startswith(".claude.backup-")
    assert (report.backup_path / "sessions" / "old-0.txt").is_file()
    assert (report.backup_path / "tasks" / "old-0.txt").is_file()
    assert report.backup_existed is True

    # The new target has the imported layout.
    assert (target / "sessions" / "f-0.txt").is_file()
    assert not (target / "tasks").exists()  # not in data
    assert (target / "tasks").is_dir() is False


def test_import_backup_path_uses_timestamped_suffix(tmp_path: Path) -> None:
    """Backup path should match `.claude.backup-YYYYMMDD-HHMMSS[-N]`."""
    project = tmp_path / "project"
    _make_data_tree(project, {"sessions": 1})
    target = _make_claude_dir(tmp_path, {"sessions": 1})

    report = ClaudeImporter(target, project).import_data()

    assert report.backup_path is not None
    pattern = r"^\.claude\.backup-\d{8}-\d{6}(-\d+)?$"
    assert re.match(pattern, report.backup_path.name), report.backup_path.name


def test_import_collision_appends_incrementing_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a backup with the same timestamp already exists, -1, -2, ..."""
    from datetime import datetime

    import claude_sync.utils.importer as importer_mod

    project = tmp_path / "project"
    _make_data_tree(project, {"sessions": 1})
    target = _make_claude_dir(tmp_path, {"sessions": 1})

    # Pin "now" to a known value so the formatter yields a stable
    # timestamp and we can plant a colliding directory.
    fixed = datetime(2025, 1, 2, 3, 4, 5)

    class _FrozenDatetime(datetime):
        """datetime subclass whose `now()` always returns our fixed value."""

        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return fixed

    monkeypatch.setattr(importer_mod, "datetime", _FrozenDatetime)

    parent = target.parent

    # Plant a backup with the same timestamp the importer will pick.
    collision = parent / f".claude.backup-{fixed.strftime('%Y%m%d-%H%M%S')}"
    collision.mkdir()

    report = ClaudeImporter(target, project).import_data()
    assert report.backup_path is not None
    # The importer must have detected the collision and disambiguated.
    assert report.backup_path != collision
    assert re.match(
        r"^\.claude\.backup-\d{8}-\d{6}-\d+$", report.backup_path.name
    ), report.backup_path.name
    # The original collision path is still there (we didn't clobber it).
    assert collision.exists()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_import_with_no_data_is_a_no_op(tmp_path: Path) -> None:
    """If `.claude-sync/data/` doesn't exist, report an empty restore."""
    project = tmp_path / "project"
    (project / ".claude-sync").mkdir(parents=True)  # init dir, but no `data/`

    target = tmp_path / ".claude"
    report = ClaudeImporter(target, project).import_data()

    assert report.file_count == 0
    assert report.restored == {}
    # Target was never created (we don't mkdir an empty target).
    assert not target.exists()
    assert report.backup_path is None


def test_import_can_skip_backup(tmp_path: Path) -> None:
    """`backup=False` must NOT create a backup even when target exists."""
    project = tmp_path / "project"
    _make_data_tree(project, {"sessions": 1})
    target = _make_claude_dir(tmp_path, {"sessions": 1})

    report = ClaudeImporter(target, project).import_data(backup=False)

    assert report.backup_path is None
    # Original target content is gone (we wiped and replaced it).
    assert not (target / "sessions" / "old-0.txt").exists()
    assert (target / "sessions" / "f-0.txt").is_file()


def test_import_skips_subdirs_missing_from_data(tmp_path: Path) -> None:
    """A subdir that exists in the target but not in data/ is dropped silently."""
    project = tmp_path / "project"
    _make_data_tree(project, {"sessions": 1})  # only sessions
    target = _make_claude_dir(tmp_path, {"sessions": 1, "tasks": 1, "plans": 1})

    report = ClaudeImporter(target, project).import_data()

    # `tasks`, `plans`, `session-env`, `memory`, and `projects` are absent
    # from data/ and were wiped with the old target, so they're not in the
    # report at all (the spec is silent on restoring empty placeholders;
    # we keep it simple).
    assert report.restored == {"sessions": 1}
    assert set(report.skipped) == {"tasks", "plans", "session-env", "memory", "projects"}
    assert (target / "sessions" / "f-0.txt").is_file()
    assert not (target / "tasks").exists()


def test_import_preserves_file_contents(tmp_path: Path) -> None:
    """Bytes should round-trip unchanged."""
    project = tmp_path / "project"
    data = project / ".claude-sync" / DATA_SUBDIR
    data.mkdir(parents=True)
    sessions = data / "sessions"
    sessions.mkdir()
    payload = "round-trip\n"
    (sessions / "a.txt").write_text(payload, encoding="utf-8")

    target = tmp_path / ".claude"
    ClaudeImporter(target, project).import_data()

    copied = target / "sessions" / "a.txt"
    assert copied.read_text(encoding="utf-8") == payload


def test_import_report_dataclass_shape(tmp_path: Path) -> None:
    """`ImportReport.restored_subdirs` returns keys in insertion order."""
    r = ImportReport(
        claude_path=Path("/c"),
        data_root=Path("/d"),
        backup_path=None,
        restored={"sessions": 1, "tasks": 2},
    )
    assert r.restored_subdirs == ("sessions", "tasks")
    assert r.file_count == 0  # we didn't set it; default is 0
