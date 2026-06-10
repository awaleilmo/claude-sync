"""Restore data from a sync project back into a Claude Code directory.

This module contains two importers:

1. **``ClaudeImporter``** (legacy) — restores the entire ``.claude/``
   directory from ``<project>/.claude-sync/data/``. Kept for backward
   compatibility.

2. **``ProjectImporter``** (Phase 3) — restores only the current
   project's Claude data from ``.claude-sync/export/project/<folder>/``
   into ``~/.claude/projects/<current-project>/``.

Phase 6C (Decrypt Import):

* Supports importing from encrypted ``.claudepack`` files.
* Password is requested interactively and never stored.
* Decryption uses ``decrypt_bytes()`` from crypto.py.
* AES-256-GCM authenticated decryption validates package integrity.

Design notes:

* Backups are siblings of the target (not nested) so that
  ``rmtree(target)`` cannot reach them.
* "Wipe and rewrite" semantics: the target is wiped and recreated on
  every run. The previous contents are always in the backup directory.
* Timestamps are local-time with second precision.
* Temporary extraction directory is cleaned up after import (success or failure).
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

# Reuse the same set of mirrored subdirs and files the exporter wrote.
# The constants are kept in `exporter.py` so both sides agree by
# construction; importing from there avoids a duplicate source of
# truth.
from claude_sync.utils.crypto import decrypt_bytes
from claude_sync.utils.exporter import (
    CLAUDEPACK_FILENAME,
    DATA_SUBDIR,
    EXPORT_FILES,
    EXPORT_SUBDIRS,
)

# Filename suffix appended to the backup directory. The dash makes
# the boundary between the original name and the timestamp obvious.
BACKUP_SUFFIX_FORMAT = "%Y%m%d-%H%M%S"


@dataclass
class ImportReport:
    """Summary of an import run, intended for display by the command."""

    claude_path: Path
    data_root: Path
    backup_path: Path | None
    restored: dict[str, int]
    skipped: tuple[str, ...] = ()
    file_count: int = 0
    backup_existed: bool = False
    source_type: str = ""
    # Added in Tahap 7C: project path remapping results.
    remapped_projects: dict[str, str] = field(default_factory=dict)
    unmatched_projects: tuple[str, ...] = ()
    restored_files: tuple[str, ...] = ()
    skipped_files: tuple[str, ...] = ()
    # Added in Tahap 7C: project path remapping results.
    remapped_projects: dict[str, str] = field(default_factory=dict)
    unmatched_projects: tuple[str, ...] = ()

    @property
    def restored_subdirs(self) -> tuple[str, ...]:
        """Subdirs that were actually restored, in source order."""
        return tuple(self.restored.keys())


class ClaudeImporter:
    """Restore `.claude-sync/data/` into a Claude Code directory.

    One instance, one `import_data()` call, one `ImportReport`.
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
        """Source data directory inside the sync project."""
        return self.project_root / ".claude-sync" / DATA_SUBDIR

    def import_data(self, backup: bool = True) -> ImportReport:
        """Run the import, returning a structured `ImportReport`.

        The algorithm is:

        1. Bail with an empty `restored` map if the source data dir
           is missing — there is nothing to import.
        2. Move the existing `claude_path` aside as
           `claude_path.backup-<timestamp>`. If the path does not
           exist OR `backup` is False, skip the backup.
        3. Create a fresh `claude_path` and copy every subdir from
           `data_root` into it.
        4. Copy individual files from `data_root` into the root of
           `claude_path`.
        5. Remap ``projects/`` folder names via ``ProjectMapper``
           (Tahap 7C).

        Args:
            backup: When False, skip the safety backup entirely. The
                default is True; tests/throwaway envs can opt out.
        """
        restored: dict[str, int] = {}
        skipped: list[str] = []
        restored_files: list[str] = []
        skipped_files: list[str] = []

        # Bail early if there's nothing to import. The command layer
        # is expected to gate on this case, but we handle it here so
        # the importer is safe to call directly.
        if not self.data_root.is_dir():
            return ImportReport(
                claude_path=self.claude_path,
                data_root=self.data_root,
                backup_path=None,
                restored={},
                skipped=(),
                file_count=0,
            )

        # Step 1: backup (or no-op if target is missing / disabled).
        backup_path: Path | None = None
        backup_existed = self.claude_path.exists()
        if backup and backup_existed:
            backup_path = self._make_backup_path()
            # `shutil.move` is a rename when source/dest are on the
            # same filesystem — which they always are for a backup
            # sitting next to the original. Falls back to copy+delete
            # across filesystems, but we don't rely on that here.
            shutil.move(str(self.claude_path), str(backup_path))
        elif not backup and backup_existed:
            # Without a backup, the user has opted in to losing the
            # old contents. Wipe the target so the fresh copy below
            # is the only thing under `.claude/`.
            shutil.rmtree(self.claude_path)

        # Step 2: recreate the target and copy data in.
        # `exist_ok=True` because the path is absent after a backup
        # OR after the rmtree above; in either case mkdir is a no-op.
        self.claude_path.mkdir(parents=True, exist_ok=True)
        file_count = 0
        for name in self.subdirs:
            source = self.data_root / name
            if not source.is_dir():
                skipped.append(name)
                continue

            destination = self.claude_path / name
            shutil.copytree(source, destination, dirs_exist_ok=False)

            count = _count_files(source)
            restored[name] = count
            file_count += count

        # Step 3: copy individual files from data_root to claude_path root.
        for filename in EXPORT_FILES:
            source = self.data_root / filename
            if not source.is_file():
                skipped_files.append(filename)
                continue

            destination = self.claude_path / filename
            shutil.copy2(source, destination)
            restored_files.append(filename)
            file_count += 1

        # Step 4: remap projects/ folder names (Tahap 7C).
        remapped_projects: dict[str, str] = {}
        unmatched_projects: list[str] = []
        if "projects" in restored:
            # Build the remap plan based on what's in data_root/projects/
            # (which was just copied into claude_path/projects/).
            from claude_sync.utils.project_mapper import ProjectMapper

            mapper = ProjectMapper(
                data_root=self.data_root,
                claude_path=self.claude_path,
            )
            plan = mapper.build_remap_plan()
            projects_dir = self.claude_path / "projects"

            for source_encoded, target_encoded in plan.items():
                src_folder = projects_dir / source_encoded
                if target_encoded is not None and target_encoded != source_encoded:
                    dst_folder = projects_dir / target_encoded
                    if src_folder.exists():
                        src_folder.rename(dst_folder)
                        remapped_projects[source_encoded] = target_encoded
                elif target_encoded is None:
                    unmatched_projects.append(source_encoded)

        return ImportReport(
            claude_path=self.claude_path,
            data_root=self.data_root,
            backup_path=backup_path,
            restored=restored,
            skipped=tuple(skipped),
            file_count=file_count,
            backup_existed=backup_existed,
            restored_files=tuple(restored_files),
            skipped_files=tuple(skipped_files),
            remapped_projects=remapped_projects,
            unmatched_projects=tuple(unmatched_projects),
        )

    def _make_backup_path(self) -> Path:
        """Build a unique `claude_path.backup-YYYYMMDD-HHMMSS[-N]` path.

        If a backup with the default timestamp already exists, we
        fall back to appending `-<n>` until we find a free name. This
        makes back-to-back imports (e.g. from CI) safe.
        """
        stem = f"{self.claude_path.name}.backup-{datetime.now().strftime(BACKUP_SUFFIX_FORMAT)}"
        parent = self.claude_path.parent
        candidate = parent / stem
        suffix_n = 0
        while candidate.exists():
            suffix_n += 1
            candidate = parent / f"{stem}-{suffix_n}"
        return candidate


def _count_files(root: Path) -> int:
    """Recursive file count, mirroring the exporter's helper."""
    count = 0
    try:
        for entry in root.rglob("*"):
            if entry.is_file():
                count += 1
    except OSError:
        return 0
    return count


# ---------------------------------------------------------------------------
# Phase 3: Project-based importer
# ---------------------------------------------------------------------------

# Backup subdirectory inside ~/.claude/
BACKUP_SUBDIR = "backups"


@dataclass
class ProjectImportReport:
    """Summary of a Phase 3 project-based import run."""

    claude_path: Path
    data_root: Path
    target_project_path: Path
    claude_project_folder: str
    backup_path: Path | None
    file_count: int = 0
    backup_existed: bool = False
    source_type: str = ""
    # Added in Tahap 7C: project path remapping results.
    remapped_projects: dict[str, str] = field(default_factory=dict)
    unmatched_projects: tuple[str, ...] = ()


class ProjectImporter:
    """Restore only the current project's Claude data.

    Source: ``<project>/.claude-sync/export/project/<folder>/``
    Target: ``<claude_path>/projects/<current-project-folder>/``
    Backup: ``<claude_path>/backups/<folder>-YYYYMMDD-HHMMSS``

    Phase 6C: Supports encrypted ``.claudepack`` files with password
    prompt. Password is never stored or cached.

    This importer never touches other projects in ``~/.claude/projects/``.
    """

    def __init__(
        self,
        claude_path: Path,
        project_root: Path,
        local_project_path: Path | None = None,
        password: str | None = None,
    ) -> None:
        self.claude_path = claude_path
        self.project_root = project_root
        self.local_project_path = (
            local_project_path
            if local_project_path is not None
            else Path.cwd().resolve()
        )
        self.password = password

    @property
    def export_root(self) -> Path:
        """Root of the project export data."""
        return self.project_root / ".claude-sync" / "export" / "project"

    def _resolve_claude_folder(self) -> str:
        """Compute the Claude project folder name for the local path."""
        from claude_sync.utils.project_path import project_to_claude_folder
        return project_to_claude_folder(self.local_project_path)

    def _find_export_source(self) -> Path | None:
        """Find the exported project folder in .claude-sync/export/project/.

        There should be exactly one subfolder. Returns None if no export exists.
        """
        if not self.export_root.is_dir():
            return None
        subdirs = [p for p in self.export_root.iterdir() if p.is_dir()]
        if not subdirs:
            return None
        # Return the first (and should be only) project folder
        return subdirs[0]

    def _make_project_backup(self, target: Path) -> Path:
        """Create a timestamped backup of the project folder.

        Backup location: ``<claude_path>/backups/<folder>-YYYYMMDD-HHMMSS``
        """
        backup_dir = self.claude_path / BACKUP_SUBDIR
        backup_dir.mkdir(parents=True, exist_ok=True)

        stem = f"{target.name}-{datetime.now().strftime(BACKUP_SUFFIX_FORMAT)}"
        candidate = backup_dir / stem
        suffix_n = 0
        while candidate.exists():
            suffix_n += 1
            candidate = backup_dir / f"{stem}-{suffix_n}"

        shutil.copytree(target, candidate, dirs_exist_ok=False)
        # Remove the original after successful backup copy
        shutil.rmtree(target)
        return candidate

    # ------------------------------------------------------------------
    # Phase 5 Part 2: .claudepack (ZIP) support
    # ------------------------------------------------------------------

    @property
    def claudepack_path(self) -> Path:
        """Path to the ``.claudepack`` ZIP file."""
        return self.project_root / ".claude-sync" / CLAUDEPACK_FILENAME

    def has_claudepack(self) -> bool:
        """Return True if a valid ``.claudepack`` ZIP exists."""
        path = self.claudepack_path
        if not path.is_file():
            return False
        try:
            with zipfile.ZipFile(path, "r") as zf:
                zf.testzip()
            return True
        except zipfile.BadZipFile:
            return False

    def _is_encrypted_claudepack(self) -> bool:
        """Check if the .claudepack is encrypted (not a plain ZIP)."""
        path = self.claudepack_path
        if not path.is_file():
            return False
        try:
            with open(path, "rb") as f:
                magic = f.read(4)
            return magic != b"PK\x03\x04"
        except OSError:
            return False

    def _extract_plain_zip(self, extracted_dir: Path, password: str | None = None) -> None:
        """Extract ZIP, optionally decrypting if encrypted."""
        path = self.claudepack_path
        
        if password and self._is_encrypted_claudepack():
            with open(path, "rb") as f:
                encrypted = f.read()
            try:
                zip_bytes = decrypt_bytes(encrypted, password)
            except ValueError as exc:
                shutil.rmtree(extracted_dir)
                raise ValueError(
                    f"Failed to decrypt .claudepack:\n"
                    f"  Wrong password or corrupted package."
                )
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                zip_temp = tmp_path / "package.zip"
                zip_temp.write_bytes(zip_bytes)
                with zipfile.ZipFile(zip_temp, "r") as zf:
                    zf.extractall(extracted_dir)
        else:
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(extracted_dir)
            except zipfile.BadZipFile:
                shutil.rmtree(extracted_dir)
                raise ValueError(
                    f"Corrupt .claudepack file: {path}\n"
                    "  The file may be incomplete or damaged. "
                    "Please re-export."
                )

    def extract_claudepack(self, password: str | None = None) -> Path:
        """Extract ``.claudepack`` into a sub-directory of ``.claude-sync/``.

        If *password* is provided and the package is encrypted, attempts
        AES-256-GCM decryption before extracting.

        Returns the path to the extracted contents.
        Raises ``ValueError`` if the ZIP is corrupt or password is wrong.
        """
        path = self.claudepack_path
        extracted_dir = self.project_root / ".claude-sync" / ".extracted"
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir)
        extracted_dir.mkdir(parents=True, exist_ok=True)

        self._extract_plain_zip(extracted_dir, password)

        return extracted_dir

    def _find_claudepack_source(self) -> tuple[Path | None, str]:
        """Determine the import source.

        Returns ``(source_path, source_type)`` where:
        * ``source_path`` is the directory to import from
        * ``source_type`` is ``"claudepack"`` or ``"folder"`` or ``None``

        Priority: .claudepack > folder export.
        """
        if self.has_claudepack():
            return self.extract_claudepack(self.password), "claudepack"

        source = self._find_export_source()
        if source is not None:
            return source, "folder"

        return None, ""

    def import_data(self, backup: bool = True) -> ProjectImportReport:
        """Run the project-based import.

        Steps:
        1. Determine import source (.claudepack ZIP or folder export).
        2. If no source, return empty report.
        3. Determine current machine's Claude project folder name.
        4. If target folder exists, back it up (only the project folder).
        5. Restore imported data to target folder.

        Args:
            backup: When False, skip the safety backup. Default True.
        """
        # Step 1: Find import source (ZIP first, then folder)
        source, source_type = self._find_claudepack_source()
        if source is None:
            return ProjectImportReport(
                claude_path=self.claude_path,
                data_root=self.export_root,
                target_project_path=self.claude_path,
                claude_project_folder="",
                backup_path=None,
                file_count=0,
            )

        # Step 2: Resolve current machine's Claude folder name
        claude_folder = self._resolve_claude_folder()
        projects_dir = self.claude_path / "projects"
        target = projects_dir / claude_folder

        # Step 3: Backup existing target (only the project folder)
        backup_path: Path | None = None
        backup_existed = target.exists()
        if backup and backup_existed:
            backup_path = self._make_project_backup(target)
        elif not backup and backup_existed:
            shutil.rmtree(target)

        # Step 4: Restore
        projects_dir.mkdir(parents=True, exist_ok=True)
        actual_source = source / "project" if source_type == "claudepack" else source
        shutil.copytree(actual_source, target, dirs_exist_ok=False)

        # Clean up extracted directory if using .claudepack
        if source_type == "claudepack":
            extracted_dir = self.project_root / ".claude-sync" / ".extracted"
            if extracted_dir.exists():
                shutil.rmtree(extracted_dir)

        file_count = _count_files(target)

        return ProjectImportReport(
            claude_path=self.claude_path,
            data_root=self.export_root,
            target_project_path=target,
            claude_project_folder=claude_folder,
            backup_path=backup_path,
            file_count=file_count,
            backup_existed=backup_existed,
            source_type=source_type,
        )
