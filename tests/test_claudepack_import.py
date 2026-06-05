"""Tests for .claudepack ZIP import (Phase 5 Part 2)."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from claude_sync.cli import app
from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.exporter import CLAUDEPACK_FILENAME
from claude_sync.utils.importer import ProjectImporter


def _stub_locator(monkeypatch, path: Path | None) -> None:
    def stub(self: ClaudeLocator) -> Path | None:  # noqa: ARG001
        return path

    monkeypatch.setattr(ClaudeLocator, "find_claude_path", stub)


def _expected_folder(project_path: Path) -> str:
    from claude_sync.utils.project_path import project_to_claude_folder
    return project_to_claude_folder(project_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_claudepack(
    project_root: Path,
    folder_name: str,
    files: dict[str, str],
) -> Path:
    """Create a valid .claudepack ZIP inside .claude-sync/."""
    claude_sync_dir = project_root / ".claude-sync"
    claude_sync_dir.mkdir(parents=True, exist_ok=True)
    pack_path = claude_sync_dir / CLAUDEPACK_FILENAME

    # Create a temporary staging directory
    staging = claude_sync_dir / "_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(exist_ok=True)

    project_dir = staging / "project"
    project_dir.mkdir(exist_ok=True)
    for name, content in files.items():
        fpath = project_dir / name
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")

    # Also add a manifest.json at the staging root
    (staging / "manifest.json").write_text(
        json.dumps({"version": 2}), encoding="utf-8"
    )

    # Create ZIP: contains project/ and manifest.json at root
    with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(staging.rglob("*")):
            if item.is_file():
                arcname = str(item.relative_to(staging))
                zf.write(item, arcname)

    # Clean up staging
    shutil.rmtree(staging)
    return pack_path


def _make_corrupt_claudepack(project_root: Path) -> Path:
    """Create a corrupt .claudepack file (not a valid ZIP)."""
    claude_sync_dir = project_root / ".claude-sync"
    claude_sync_dir.mkdir(parents=True, exist_ok=True)
    pack_path = claude_sync_dir / CLAUDEPACK_FILENAME
    pack_path.write_bytes(b"This is not a valid ZIP file\x00\x01")
    return pack_path


# ---------------------------------------------------------------------------
# ProjectImporter ZIP tests
# ---------------------------------------------------------------------------


def test_has_claudepack_returns_true_for_valid_zip(tmp_path: Path) -> None:
    """A valid .claudepack ZIP should be detected."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    pack_path = _make_claudepack(
        project_root,
        "test-folder",
        {"session-1.jsonl": "data"},
    )
    importer = ProjectImporter(
        claude_path=tmp_path / ".claude",
        project_root=project_root,
        local_project_path=project_root,
    )
    assert importer.has_claudepack() is True
    assert pack_path.exists()


def test_has_claudepack_returns_false_for_missing(tmp_path: Path) -> None:
    """No ZIP file means has_claudepack is False."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    importer = ProjectImporter(
        claude_path=tmp_path / ".claude",
        project_root=project_root,
        local_project_path=project_root,
    )
    assert importer.has_claudepack() is False


def test_has_claudepack_returns_false_for_corrupt_zip(tmp_path: Path) -> None:
    """A corrupt ZIP should return False, not crash."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _make_corrupt_claudepack(project_root)
    importer = ProjectImporter(
        claude_path=tmp_path / ".claude",
        project_root=project_root,
        local_project_path=project_root,
    )
    assert importer.has_claudepack() is False


def test_extract_claudepack_restores_files(tmp_path: Path) -> None:
    """Extracting a valid .claudepack should restore the files."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _make_claudepack(
        project_root,
        "test-folder",
        {"session-1.jsonl": "hello", "memory/notes.md": "world"},
    )
    importer = ProjectImporter(
        claude_path=tmp_path / ".claude",
        project_root=project_root,
        local_project_path=project_root,
    )
    extracted = importer.extract_claudepack()
    assert (extracted / "project" / "session-1.jsonl").read_text() == "hello"
    assert (extracted / "project" / "memory" / "notes.md").read_text() == "world"


def test_extract_claudepack_raises_on_corrupt(tmp_path: Path) -> None:
    """Extracting a corrupt ZIP should raise ValueError."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _make_corrupt_claudepack(project_root)
    importer = ProjectImporter(
        claude_path=tmp_path / ".claude",
        project_root=project_root,
        local_project_path=project_root,
    )
    with pytest.raises(ValueError, match="Corrupt .claudepack"):
        importer.extract_claudepack()


def test_import_from_claudepack(tmp_path: Path) -> None:
    """Importing from a .claudepack should restore files correctly."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    _make_claudepack(
        project_root,
        "test-folder",
        {"session-1.jsonl": "clouddata", "memory/notes.md": "notes"},
    )

    folder = _expected_folder(project_root)
    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=project_root,
    )
    report = importer.import_data()

    assert report.file_count == 2
    assert report.claude_project_folder == folder
    assert report.source_type == "claudepack"
    assert report.backup_path is None

    # Verify files
    target = claude_path / "projects" / folder
    assert (target / "session-1.jsonl").read_text() == "clouddata"
    assert (target / "memory" / "notes.md").read_text() == "notes"


def test_import_from_claudepack_with_backup(tmp_path: Path) -> None:
    """Import from .claudepack should backup existing target."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    # Create existing target
    folder = _expected_folder(project_root)
    target = claude_path / "projects" / folder
    target.mkdir(parents=True)
    (target / "old-session.jsonl").write_text("old", encoding="utf-8")

    # Create .claudepack with new data
    _make_claudepack(
        project_root,
        "test-folder",
        {"new-session.jsonl": "new"},
    )

    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=project_root,
    )
    report = importer.import_data()

    assert report.backup_path is not None
    assert report.backup_existed is True
    target = claude_path / "projects" / folder
    assert (target / "new-session.jsonl").read_text() == "new"
    assert not (target / "old-session.jsonl").exists()


def test_import_fallback_to_folder_when_no_claudepack(tmp_path: Path) -> None:
    """When no .claudepack exists, fallback to folder export."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    # Create folder export (no ZIP)
    export_dir = (
        project_root / ".claude-sync" / "export" / "project" / "test-folder"
    )
    export_dir.mkdir(parents=True)
    (export_dir / "session-1.jsonl").write_text("folder-data", encoding="utf-8")

    folder = _expected_folder(project_root)
    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=project_root,
    )
    report = importer.import_data()

    assert report.source_type == "folder"
    assert report.file_count == 1
    target = claude_path / "projects" / folder
    assert (target / "session-1.jsonl").read_text() == "folder-data"


def test_import_claudepack_takes_priority_over_folder(tmp_path: Path) -> None:
    """When both .claudepack and folder export exist, ZIP wins."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    claude_path = tmp_path / ".claude"
    claude_path.mkdir()

    # Create folder export
    export_dir = (
        project_root / ".claude-sync" / "export" / "project" / "test-folder"
    )
    export_dir.mkdir(parents=True)
    (export_dir / "session-1.jsonl").write_text("folder-data", encoding="utf-8")

    # Create .claudepack with different data
    _make_claudepack(
        project_root,
        "test-folder",
        {"session-1.jsonl": "zip-data"},
    )

    folder = _expected_folder(project_root)
    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=project_root,
        local_project_path=project_root,
    )
    report = importer.import_data()

    assert report.source_type == "claudepack"
    target = claude_path / "projects" / folder
    assert (target / "session-1.jsonl").read_text() == "zip-data"


# ---------------------------------------------------------------------------
# import_cmd CLI tests
# ---------------------------------------------------------------------------


def test_import_claudepack_via_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: CLI import using .claudepack."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()
    _stub_locator(monkeypatch, claude_dest)

    folder = _expected_folder(project)
    _make_claudepack(
        project,
        "test-folder",
        {"session-1.jsonl": "zip-data", "memory/notes.md": "notes"},
    )

    result = runner.invoke(
        app,
        ["import", "--local-project-path", str(project)],
    )
    assert result.exit_code == 0, result.output
    assert "Using .claudepack format" in result.output
    assert "ZIP (.claudepack)" in result.output

    # Verify files restored
    target = claude_dest / "projects" / folder
    assert (target / "session-1.jsonl").read_text() == "zip-data"
    assert (target / "memory" / "notes.md").read_text() == "notes"


def test_import_corrupt_claudepack_via_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Corrupt .claudepack should abort with clear error."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    _make_corrupt_claudepack(project)
    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()
    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(app, ["import"])
    assert result.exit_code != 0
    assert "Corrupt .claudepack" in result.output


def test_import_fallback_folder_via_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no .claudepack, should fallback to folder format."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    export_dir = (
        project / ".claude-sync" / "export" / "project" / "test-folder"
    )
    export_dir.mkdir(parents=True)
    (export_dir / "session-1.jsonl").write_text("folder-data", encoding="utf-8")

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()
    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(
        app,
        ["import", "--local-project-path", str(project)],
    )
    assert result.exit_code == 0, result.output
    assert "Using legacy folder format" in result.output
    assert "folder" in result.output.lower()
