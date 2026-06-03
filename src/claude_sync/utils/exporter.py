"""Export data from a Claude Code directory into a sync project.

This module performs the read+copy half of a sync round-trip: it
walks well-known subdirectories under `.claude/` and mirrors them
into `<project>/.claude-sync/data/<subdir>/`.

Design notes:

* We deliberately use `shutil.copytree` rather than walking files
  ourselves. It handles symlinks, directories, and platform quirks
  for us, and its `dirs_exist_ok` flag is exactly the lever we need
  for "wipe and rewrite" semantics.
* "Wipe and rewrite" is implemented by removing the *target* root
  before re-copying. We never touch the *source* under `.claude/`.
* The number of files copied is computed from a dry-run walk BEFORE
  we start copying, so the user gets a count even if a copy fails
  partway through. We return a stable dataclass instead of printing,
  leaving presentation to the command layer.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# Subdirectories of `.claude/` that are mirrored during export.
# Note: `projects` is intentionally excluded here — it is inspected
# in `inspector.py` (TRACKED_SUBDIRS) but exporting it would copy
# potentially huge, project-specific state we don't yet know how to
# merge. We can revisit once project filtering lands in Tahap 5+.
EXPORT_SUBDIRS: tuple[str, ...] = (
    "sessions",
    "tasks",
    "plans",
    "session-env",
)

# Default location of the exported payload, relative to the sync
# project root. Kept as a single constant so future changes (e.g.
# versioning the layout) only touch one place.
DATA_SUBDIR = "data"


@dataclass
class ExportReport:
    """Summary of an export run, intended for display by the command."""

    claude_path: Path
    data_root: Path
    copied: dict[str, int] = field(default_factory=dict)
    skipped: tuple[str, ...] = ()
    file_count: int = 0

    @property
    def copied_subdirs(self) -> tuple[str, ...]:
        """Subdirs that actually had data to copy, in source order."""
        return tuple(self.copied.keys())


class ClaudeExporter:
    """Mirror a subset of `.claude/` into a local sync project.

    The exporter is single-shot: one instance, one `export()` call,
    one `ExportReport`. It is intentionally not a long-lived object;
    there is no per-instance mutable state worth keeping around.
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
        """Absolute path to the export destination root."""
        return self.project_root / ".claude-sync" / DATA_SUBDIR

    def export(self) -> ExportReport:
        """Run the export, returning a structured `ExportReport`.

        Behaviour:
        * For each tracked subdir, if the source is missing -> recorded
          as `skipped` and otherwise left alone.
        * The destination root is wiped and recreated on every run, so
          deleted files in the source do NOT linger in the export.
        """
        report = ExportReport(
            claude_path=self.claude_path,
            data_root=self.data_root,
        )

        # `shutil.copytree` will create `data_root` for us, so the
        # only prep work is making sure the parent exists.
        self.data_root.parent.mkdir(parents=True, exist_ok=True)

        # Wipe and recreate the destination. Doing this once at the
        # top is simpler than per-subdir checks and guarantees no
        # stale files from a previous export survive.
        if self.data_root.exists():
            shutil.rmtree(self.data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

        # Pre-walk to count files. We use the same recursive count
        # for every subdir so partial progress numbers stay honest
        # even if we later add a "report after each subdir" feature.
        total_files = 0
        for name in self.subdirs:
            source = self.claude_path / name
            if not source.is_dir():
                report.skipped = (*report.skipped, name)
                continue

            destination = self.data_root / name
            # `dirs_exist_ok=False` is safe because we just wiped
            # `data_root` above; the per-subdir dest cannot pre-exist.
            shutil.copytree(source, destination, dirs_exist_ok=False)

            count = _count_files(source)
            report.copied[name] = count
            total_files += count

        report.file_count = total_files
        return report


def _count_files(root: Path) -> int:
    """Recursively count files under `root`.

    Returns 0 if the directory cannot be read (permission errors,
    vanished entries, etc.). A zero count is a useful signal in the
    report ("empty or unreadable") rather than a crash.
    """
    count = 0
    try:
        for _ in root.rglob("*"):
            # `rglob` yields both files and directories; only files
            # count toward the report.
            if _.is_file():
                count += 1
    except OSError:
        return 0
    return count
