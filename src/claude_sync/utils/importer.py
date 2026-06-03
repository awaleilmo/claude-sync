"""Restore data from a sync project back into a Claude Code directory.

This module is the inverse of `exporter.py`. It mirrors the on-disk
payload from `<project>/.claude-sync/data/` into a target
`.claude` directory, after first creating a timestamped safety
backup of whatever is currently in the target.

Design notes:

* The backup is a sibling of the target (not nested inside it) so
  that `rmtree(target)` cannot possibly reach it.
* "Wipe and rewrite" semantics are reused from the exporter side:
  the target is wiped and recreated on every run. The previous
  contents are always available in the backup directory.
* Time stamps are local-time with second precision — the same
  layout you'd get from `date +%Y%m%d-%H%M%S` — so they sort
  lexically as well as chronologically.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

# Reuse the same set of mirrored subdirs the exporter wrote. The
# constants are kept in `exporter.py` so both sides agree by
# construction; importing from there avoids a duplicate source of
# truth.
from claude_sync.utils.exporter import DATA_SUBDIR, EXPORT_SUBDIRS

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

        Args:
            backup: When False, skip the safety backup entirely. The
                default is True; tests/throwaway envs can opt out.
        """
        restored: dict[str, int] = {}
        skipped: list[str] = []

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

        return ImportReport(
            claude_path=self.claude_path,
            data_root=self.data_root,
            backup_path=backup_path,
            restored=restored,
            skipped=tuple(skipped),
            file_count=file_count,
            backup_existed=backup_existed,
        )

    def _make_backup_path(self) -> Path:
        """Build a unique `claude_path.backup-YYYYMMDD-HHMMSS` path.

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
