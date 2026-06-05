"""Tests for `claude_sync.utils.importer.ProjectImporter` (Phase 3)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from claude_sync.utils.importer import ProjectImporter, ProjectImportReport


def _make_export_tree(project_root: Path, folder_name: str, files: dict[str, str]) -> Path:
    """Build a fake `.claude-sync/export/project/<folder>/` tree."""
    export_dir = project_root / ".claude-sync" / "export" / "project" / folder_name
    export_dir.mkdir(parents=True)
    for name, content in files.items():
        fpath = export_dir / name
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
    return export_dir


def _make_claude_projects_dir(
    claude_path: Path, folder_name: str, files: dict[str, str]
) -> Path:
    """Build a fake existing Claude project directory to be backed up."""
    projects_dir = claude_path / "projects"
    target = projects_dir / folder_name
    target.mkdir(parents=True)
    for name, content in files.items():
        fpath = target / name
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_import_restores_project_folder(tmp_path: Path) -> None:
    """Project import should copy exported data to the correct Claude project folder."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    _make_export_tree(
        project_root,
        "-home-user-myproject",
        {"session-1.jsonl": "data1", "memory/notes.md": "notes"},
    )

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=Path("/home/user/myproject"),
    )
    report = importer.import_data()

    assert report.file_count == 2
    assert report.claude_project_folder == "-home-user-myproject"
    assert report.backup_path is None
    assert report.backup_existed is False

    # Verify files on disk
    target = claude_path / "projects" / "-home-user-myproject"
    assert (target / "session-1.jsonl").read_text() == "data1"
    assert (target / "memory" / "notes.md").read_text() == "notes"


def test_import_with_existing_target_creates_backup(tmp_path: Path) -> None:
    """When target project exists, it should be backed up before restore."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    # Create existing Claude project with old data
    _make_claude_projects_dir(
        claude_path,
        "-home-user-myproject",
        {"old-session.jsonl": "old-data"},
    )

    # Create export data
    _make_export_tree(
        project_root,
        "-home-user-myproject",
        {"new-session.jsonl": "new-data"},
    )

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=Path("/home/user/myproject"),
    )
    report = importer.import_data()

    assert report.file_count == 1
    assert report.backup_path is not None
    assert report.backup_existed is True

    # Backup should have old data
    assert report.backup_path.name.startswith("-home-user-myproject-")
    assert (report.backup_path / "old-session.jsonl").read_text() == "old-data"

    # Target should have new data
    target = claude_path / "projects" / "-home-user-myproject"
    assert (target / "new-session.jsonl").read_text() == "new-data"
    assert not (target / "old-session.jsonl").exists()


def test_import_backup_in_correct_location(tmp_path: Path) -> None:
    """Backup should be in ~/.claude/backups/, not next to the project folder."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    _make_claude_projects_dir(
        claude_path, "-home-user-myproject", {"old.txt": "old"}
    )
    _make_export_tree(
        project_root, "-home-user-myproject", {"new.txt": "new"}
    )

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=Path("/home/user/myproject"),
    )
    report = importer.import_data()

    assert report.backup_path is not None
    # Backup must be under .claude/backups/
    assert "backups" in str(report.backup_path)
    assert report.backup_path.parent == claude_path / "backups"


def test_import_does_not_touch_other_projects(tmp_path: Path) -> None:
    """Import should never modify other project folders."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    # Create OTHER projects that should remain untouched
    other_project = _make_claude_projects_dir(
        claude_path, "-home-user-otherproject", {"other.txt": "other-data"}
    )
    another_project = _make_claude_projects_dir(
        claude_path, "-home-user-thirdproject", {"third.txt": "third-data"}
    )

    # Create target project
    _make_claude_projects_dir(
        claude_path, "-home-user-myproject", {"old.txt": "old"}
    )
    _make_export_tree(
        project_root, "-home-user-myproject", {"new.txt": "new"}
    )

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=Path("/home/user/myproject"),
    )
    importer.import_data()

    # Other projects untouched
    assert (other_project / "other.txt").read_text() == "other-data"
    assert (another_project / "third.txt").read_text() == "third-data"


def test_import_no_backup_flag(tmp_path: Path) -> None:
    """--no-backup should not create backup."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    _make_claude_projects_dir(
        claude_path, "-home-user-myproject", {"old.txt": "old"}
    )
    _make_export_tree(
        project_root, "-home-user-myproject", {"new.txt": "new"}
    )

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=Path("/home/user/myproject"),
    )
    report = importer.import_data(backup=False)

    assert report.backup_path is None
    # Old data is gone
    target = claude_path / "projects" / "-home-user-myproject"
    assert (target / "new.txt").read_text() == "new"
    assert not (target / "old.txt").exists()

    # No backups directory
    assert not (claude_path / "backups").exists()


def test_import_no_export_data_returns_empty_report(tmp_path: Path) -> None:
    """If no export data exists, return empty report."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=Path("/home/user/myproject"),
    )
    report = importer.import_data()

    assert report.file_count == 0
    assert report.claude_project_folder == ""
    assert report.backup_path is None


def test_import_preserves_file_contents(tmp_path: Path) -> None:
    """Bytes should round-trip unchanged through export and import."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    payload = "round-trip test with special chars: \\n\\t\\r\\n"
    _make_export_tree(
        project_root,
        "-home-user-myproject",
        {"session.jsonl": payload},
    )

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=Path("/home/user/myproject"),
    )
    report = importer.import_data()

    target = claude_path / "projects" / "-home-user-myproject"
    assert (target / "session.jsonl").read_text() == payload


def test_import_creates_projects_dir_if_missing(tmp_path: Path) -> None:
    """Import should create ~/.claude/projects/ if it doesn't exist."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()
    # Note: no projects/ dir created

    _make_export_tree(
        project_root, "-home-user-myproject", {"file.txt": "data"}
    )

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=Path("/home/user/myproject"),
    )
    report = importer.import_data()

    assert report.file_count == 1
    assert (claude_path / "projects").is_dir()
    assert (claude_path / "projects" / "-home-user-myproject" / "file.txt").exists()


def test_import_report_dataclass_shape() -> None:
    """ProjectImportReport has expected fields."""
    r = ProjectImportReport(
        claude_path=Path("/c"),
        data_root=Path("/d"),
        target_project_path=Path("/t"),
        claude_project_folder="-home-user-test",
        backup_path=None,
        file_count=5,
    )
    assert r.file_count == 5
    assert r.claude_project_folder == "-home-user-test"
    assert r.backup_path is None
