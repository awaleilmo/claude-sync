"""Tests for the `claude-sync import` command (Phase 3 + Phase 4)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from claude_sync.cli import app
from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.config import get_manifest_path, write_manifest
from claude_sync.utils.project_path import project_to_claude_folder


def _stub_locator(monkeypatch, path: Path | None) -> None:
    def stub(self: ClaudeLocator) -> Path | None:  # noqa: ARG001
        return path

    monkeypatch.setattr(ClaudeLocator, "find_claude_path", stub)


def _make_export_tree(
    project_root: Path, folder_name: str, files: dict[str, str]
) -> Path:
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
    """Build a fake existing Claude project directory."""
    projects_dir = claude_path / "projects"
    target = projects_dir / folder_name
    target.mkdir(parents=True)
    for name, content in files.items():
        fpath = target / name
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
    return target


def _expected_folder(project_path: Path) -> str:
    """Compute the expected Claude folder name for a project path."""
    return project_to_claude_folder(project_path)


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
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    # Create export data so we pass the export check
    _make_export_tree(project, "-some-folder", {"file.txt": "data"})

    _stub_locator(monkeypatch, None)

    result = runner.invoke(app, ["import"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_import_fails_when_no_export_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If there's no export data, abort with a clear message."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()
    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(app, ["import"])
    assert result.exit_code != 0
    assert "no export" in result.output.lower()


def test_import_restores_project_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: init, create export data, import, verify target."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    # Compute the expected folder name from the project path
    folder = _expected_folder(project)

    # Create export data with any name (importer will find it and copy to computed target)
    _make_export_tree(
        project,
        "-source-folder",
        {"session-1.jsonl": "session-data", "memory/notes.md": "notes"},
    )

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()
    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(
        app,
        ["import", "--local-project-path", str(project)],
    )
    assert result.exit_code == 0, result.output

    # Verify files are at the expected target location
    target = claude_dest / "projects" / folder
    assert target.is_dir()
    assert (target / "session-1.jsonl").read_text() == "session-data"
    assert (target / "memory" / "notes.md").read_text() == "notes"


def test_import_creates_backup_of_existing_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`import` must take a timestamped backup of the target project folder."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    folder = _expected_folder(project)

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()

    # Create existing Claude project with old data at the expected target location
    _make_claude_projects_dir(
        claude_dest,
        folder,
        {"old-session.jsonl": "old-data"},
    )

    # Create export data (source folder name differs from target)
    _make_export_tree(
        project,
        "-source-folder",
        {"new-session.jsonl": "new-data"},
    )

    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(
        app,
        ["import", "--local-project-path", str(project)],
    )
    assert result.exit_code == 0, result.output

    # Backup should exist
    backups_dir = claude_dest / "backups"
    assert backups_dir.is_dir()
    backups = list(backups_dir.iterdir())
    assert len(backups) == 1
    assert backups[0].name.startswith(f"{folder}-")
    assert (backups[0] / "old-session.jsonl").read_text() == "old-data"

    # Target has new data
    target = claude_dest / "projects" / folder
    assert (target / "new-session.jsonl").read_text() == "new-data"

    assert "Backup created" in result.output


def test_import_no_backup_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--no-backup` should not create a backup directory."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    folder = _expected_folder(project)

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()

    _make_claude_projects_dir(claude_dest, folder, {"old.txt": "old"})
    _make_export_tree(project, "-source-folder", {"new.txt": "new"})

    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(
        app,
        ["import", "--no-backup", "--local-project-path", str(project)],
    )
    assert result.exit_code == 0, result.output

    # No backups
    assert not (claude_dest / "backups").exists()

    # Target has new data
    target = claude_dest / "projects" / folder
    assert (target / "new.txt").read_text() == "new"


def test_import_does_not_touch_other_projects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Import must not modify other Claude project folders."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    folder = _expected_folder(project)

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()

    # Other projects that must remain untouched
    _make_claude_projects_dir(
        claude_dest, "-home-user-project-a", {"a.txt": "data-a"}
    )
    _make_claude_projects_dir(
        claude_dest, "-home-user-project-b", {"b.txt": "data-b"}
    )
    # Target project
    _make_claude_projects_dir(claude_dest, folder, {"old.txt": "old"})

    _make_export_tree(project, "-source-folder", {"new.txt": "new"})

    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(
        app,
        ["import", "--local-project-path", str(project)],
    )
    assert result.exit_code == 0, result.output

    # Other projects untouched
    assert (claude_dest / "projects" / "-home-user-project-a" / "a.txt").read_text() == "data-a"
    assert (claude_dest / "projects" / "-home-user-project-b" / "b.txt").read_text() == "data-b"


def test_import_with_explicit_claude_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--claude-path` overrides the locator."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    folder = _expected_folder(project)

    _make_export_tree(project, "-source-folder", {"file.txt": "data"})

    dest = tmp_path / "explicit-dest"
    dest.mkdir()
    _stub_locator(monkeypatch, tmp_path / "wrong")  # ignored

    result = runner.invoke(
        app,
        [
            "import",
            "--claude-path", str(dest),
            "--local-project-path", str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (dest / "projects" / folder / "file.txt").exists()


# ---------------------------------------------------------------------------
# Phase 4: Validation warnings (warn but do not abort)
# ---------------------------------------------------------------------------


def test_import_warns_on_project_name_mismatch_but_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If project.json's project_name differs from the current folder,
    import must warn but still complete successfully."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    # Tamper with project.json so project_name != current folder
    from claude_sync.utils.project_identity import get_project_metadata_path, write_project_metadata
    from claude_sync.utils.project_identity import ProjectMetadata

    meta_path = get_project_metadata_path(project)
    write_project_metadata(
        meta_path,
        ProjectMetadata(
            project_name="stale-name-from-another-machine",
            project_id="abc",
            version=2,
        ),
    )

    folder = _expected_folder(project)
    _make_export_tree(project, "-source-folder", {"file.txt": "data"})

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()
    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(
        app,
        ["import", "--local-project-path", str(project)],
    )

    # Must still succeed
    assert result.exit_code == 0, result.output
    # And warn
    assert "Mapping Mismatch" in result.output
    assert "stale-name-from-another-machine" in result.output
    assert folder in result.output
    # Files still restored at current folder
    assert (claude_dest / "projects" / folder / "file.txt").exists()


def test_import_warns_on_source_manifest_mismatch_but_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the manifest's source folder differs from the current folder,
    import must warn but still complete successfully."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    # Write a manifest with a source folder that differs from the current
    manifest_path = get_manifest_path(project)
    write_manifest(
        manifest_path,
        {
            "project_name": project.name,
            "version": 2,
            "source_project_path": "/home/other-machine/project",
            "source_claude_project_folder": "-home-other-machine-project",
        },
    )

    folder = _expected_folder(project)
    _make_export_tree(project, "-source-folder", {"file.txt": "data"})

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()
    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(
        app,
        ["import", "--local-project-path", str(project)],
    )

    assert result.exit_code == 0, result.output
    assert "Source folder" in result.output
    assert "-home-other-machine-project" in result.output
    assert folder in result.output
    # Files still restored at current folder
    assert (claude_dest / "projects" / folder / "file.txt").exists()


def test_import_silent_when_mapping_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If project.json's project_name matches the current folder, no warning."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    runner = CliRunner()
    runner.invoke(app, ["init"])

    folder = _expected_folder(project)

    # Manually rewrite project.json with the current folder name as project_name
    from claude_sync.utils.project_identity import (
        ProjectMetadata,
        get_project_metadata_path,
        write_project_metadata,
    )

    meta_path = get_project_metadata_path(project)
    write_project_metadata(
        meta_path,
        ProjectMetadata(
            project_name=folder,
            project_id="abc",
            version=2,
        ),
    )

    # Manifest source matches current
    manifest_path = get_manifest_path(project)
    write_manifest(
        manifest_path,
        {
            "project_name": folder,
            "version": 2,
            "source_project_path": str(project),
            "source_claude_project_folder": folder,
        },
    )

    _make_export_tree(project, folder, {"file.txt": "data"})

    claude_dest = tmp_path / ".claude"
    claude_dest.mkdir()
    _stub_locator(monkeypatch, claude_dest)

    result = runner.invoke(
        app,
        ["import", "--local-project-path", str(project)],
    )

    assert result.exit_code == 0, result.output
    assert "Mapping Mismatch" not in result.output
    assert "Source folder" not in result.output or folder in result.output
    assert "differs" not in result.output
