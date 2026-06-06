"""Export data from a Claude Code directory into a sync project.

This module contains two exporters:

1. **``ClaudeExporter``** (legacy) — mirrors a subset of ``.claude/``
   into ``<project>/.claude-sync/data/<subdir>/``.  Kept for
   backward-compatibility with ``import_cmd.py`` which still reads
   from the ``data/`` layout.

2. **``ProjectExporter``** (Phase 2) — exports only the Claude Code
   project folder corresponding to the current local project into
   ``<project>/.claude-sync/export/project/<folder>/``.

Constants ``DATA_SUBDIR``, ``EXPORT_SUBDIRS``, and ``EXPORT_FILES``
are re-exported so that ``import_cmd.py`` and existing tests can
continue to import them unchanged.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from claude_sync.utils.project_path import locate_claude_project

# ---------------------------------------------------------------------------
# Legacy constants (re-exported for backward compatibility)
# ---------------------------------------------------------------------------

# Subdirectories of ``.claude/`` that are mirrored by the legacy
# exporter.
EXPORT_SUBDIRS: tuple[str, ...] = (
    "sessions",
    "tasks",
    "plans",
    "session-env",
    "projects",
    "memory",
)

# Individual files at the root of ``.claude/`` mirrored by the legacy
# exporter.
EXPORT_FILES: tuple[str, ...] = (
    "history.jsonl",
    "CLAUDE.md",
    "settings.json",
)

# Default location of the legacy export payload.
DATA_SUBDIR = "data"

# ---------------------------------------------------------------------------
# Project export layout
# ---------------------------------------------------------------------------

# Location of the project-based export payload.
EXPORT_SUBDIR = "export"
PROJECT_EXPORT_SUBDIR = "project"
CLAUDEPACK_FILENAME = "project.claudepack"


@dataclass
class ExportReport:
    """Summary of a legacy export run, intended for display by the command."""

    claude_path: Path
    data_root: Path
    copied: dict[str, int] = field(default_factory=dict)
    skipped: tuple[str, ...] = ()
    file_count: int = 0
    copied_files: dict[str, bool] = field(default_factory=dict)
    skipped_files: tuple[str, ...] = ()

    @property
    def copied_subdirs(self) -> tuple[str, ...]:
        """Subdirs that actually had data to copy, in source order."""
        return tuple(self.copied.keys())


@dataclass
class ProjectExportReport:
    """Summary of a Phase 2 project-based export run."""

    claude_path: Path
    data_root: Path
    source_project_path: Path
    claude_project_folder: str
    file_count: int = 0
    copied: dict[str, int] = field(default_factory=dict)
    skipped: tuple[str, ...] = ()
    claudepack_path: Path | None = None


# ---------------------------------------------------------------------------
# Legacy exporter (kept for backward compat with import_cmd / tests)
# ---------------------------------------------------------------------------


class ClaudeExporter:
    """Mirror a subset of ``.claude/`` into a local sync project.

    This is the **legacy** exporter used by ``import_cmd.py``.  It
    reads from ``.claude/`` subdirectories listed in ``EXPORT_SUBDIRS``
    and writes to ``.claude-sync/data/``.

    Phase 2 users should use ``ProjectExporter`` instead.
    """

    def __init__(
        self,
        claude_path: Path,
        project_root: Path,
        subdirs: Iterable[str] = EXPORT_SUBDIRS,
    ) -> None:
        self.claude_path = claude_path
        self.project_root = project_root
        self.subdirs: tuple[str, ...] = tuple(subdirs)

    @property
    def data_root(self) -> Path:
        """Absolute path to the legacy export destination root."""
        return self.project_root / ".claude-sync" / DATA_SUBDIR

    def export(self) -> ExportReport:
        """Run the legacy export, returning a structured ``ExportReport``."""
        report = ExportReport(
            claude_path=self.claude_path,
            data_root=self.data_root,
        )

        self.data_root.parent.mkdir(parents=True, exist_ok=True)

        if self.data_root.exists():
            shutil.rmtree(self.data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

        total_files = 0
        for name in self.subdirs:
            source = self.claude_path / name
            if not source.is_dir():
                report.skipped = (*report.skipped, name)
                continue

            destination = self.data_root / name
            shutil.copytree(source, destination, dirs_exist_ok=False)
            count = _count_files(source)
            report.copied[name] = count
            total_files += count

        for fname in EXPORT_FILES:
            src_file = self.claude_path / fname
            dst_file = self.data_root / fname
            if src_file.is_file():
                shutil.copy2(src_file, dst_file)
                report.copied_files[fname] = True
                total_files += 1
            else:
                report.skipped_files = (*report.skipped_files, fname)

        report.skipped_files = tuple(set(report.skipped_files))
        report.file_count = total_files
        return report


# ---------------------------------------------------------------------------
# Phase 2: Project-based exporter
# ---------------------------------------------------------------------------


class ProjectExporter:
    """Export only the Claude project folder for the current local project.

    Phase 2 layout (inside ``project_root/.claude-sync/``)::

        export/
        └── project/
            └── <current-project-folder>/
                ├── *.jsonl
                └── memory/
    """

    def __init__(
        self,
        claude_path: Path,
        project_root: Path,
        local_project_path: Path | None = None,
    ) -> None:
        self.claude_path = claude_path
        self.project_root = project_root
        self.local_project_path = (
            local_project_path
            if local_project_path is not None
            else Path.cwd().resolve()
        )

    @property
    def data_root(self) -> Path:
        """Absolute path to the project export destination."""
        return (
            self.project_root
            / ".claude-sync"
            / EXPORT_SUBDIR
            / PROJECT_EXPORT_SUBDIR
        )

    def export(self) -> ProjectExportReport:
        """Export the current project's Claude data.

        Steps:

        1. Determine the Claude Code project folder name from
           ``local_project_path``.
        2. Locate that folder under ``claude_path/projects/``.
        3. Copy only its contents to the export destination.
        """
        claude_project = locate_claude_project(
            self.claude_path, self.local_project_path
        )
        if claude_project is None:
            from claude_sync.utils.project_path import project_to_claude_folder

            folder_name = project_to_claude_folder(self.local_project_path)
            raise FileNotFoundError(
                f"Claude project folder not found: "
                f"{self.claude_path}/projects/{folder_name}"
            )

        folder_name = claude_project.name
        data_root = self.data_root / folder_name
        data_root.parent.mkdir(parents=True, exist_ok=True)

        if data_root.exists():
            shutil.rmtree(data_root)
        data_root.mkdir(parents=True, exist_ok=True)

        total_files = 0
        copied: dict[str, int] = {}
        for item in claude_project.iterdir():
            if item.is_dir():
                dest = data_root / item.name
                shutil.copytree(item, dest, dirs_exist_ok=False)
                count = _count_files(item)
                copied[item.name] = count
                total_files += count
            elif item.is_file():
                shutil.copy2(item, data_root / item.name)
                total_files += 1
                copied[item.name] = 1

        # Build claudepack ZIP package.
        # Import here to avoid circular imports.
        from claude_sync.utils.config import get_manifest_path

        pack_path = build_claudepack(
            project_root=self.project_root,
            source_folder=data_root,
            manifest_path=get_manifest_path(self.project_root),
        )

        # data_root untuk report = export root (bukan project folder)
        report_data_root = self.data_root

        report = ProjectExportReport(
            claude_path=self.claude_path,
            data_root=report_data_root,
            source_project_path=self.local_project_path,
            claude_project_folder=folder_name,
            file_count=total_files,
            copied=copied,
            claudepack_path=pack_path,
        )
        return report


def build_claudepack(
    project_root: Path,
    source_folder: Path,
    manifest_path: Path,
) -> Path:
    """Create a ``project.claudepack`` ZIP from export data.

    Package contents::

        project/
        manifest.json

    ``project.json`` is intentionally excluded — it lives alongside
    the package in ``.claude-sync/``.

    Returns the absolute path to the ``.claudepack`` file.
    """
    sync_dir = project_root / ".claude-sync"
    pack_path = sync_dir / CLAUDEPACK_FILENAME

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # --- Copy source folder as ``project/`` inside ZIP ---
        proj_dir = tmp_path / "project"
        _copy_tree(source_folder, proj_dir)

        # --- Copy manifest ---
        manifest_copy = tmp_path / "manifest.json"
        manifest_copy.write_bytes(manifest_path.read_bytes())

        # --- Write ZIP ---
        with zipfile.ZipFile(
            pack_path, "w", zipfile.ZIP_DEFLATED
        ) as zf:
            for root_dir, dirs, files in os.walk(tmp_path):
                root = Path(root_dir)
                for fname in files:
                    file_path = root / fname
                    arc_name = str(file_path.relative_to(tmp_path))
                    zf.write(file_path, arc_name)

    return pack_path


def _copy_tree(src: Path, dst: Path) -> None:
    """Recursively copy *src* to *dst*.

    Lightweight version of ``shutil.copytree`` that preserves
    permissions via ``copy2``.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            target = dst / item.name
            if item.is_dir():
                _copy_tree(item, target)
            else:
                shutil.copy2(item, target)
    else:
        shutil.copy2(src, dst)


def _count_files(root: Path) -> int:
    """Recursively count files under ``root``.

    Returns 0 if the directory cannot be read.
    """
    count = 0
    try:
        for _ in root.rglob("*"):
            if _.is_file():
                count += 1
    except OSError:
        return 0
    return count
