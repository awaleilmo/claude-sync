"""Inspect the structure of a Claude Code configuration directory.

This module is read-only: it counts entries under well-known subfolders
without copying, mutating, or exporting anything. The numbers it
returns power the `claude-sync inspect` command and (later) the dry
run for `claude-sync export`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Subfolders of `.claude/` that we always inspect, in display order.
# Keeping this as a module-level constant means adding a new tracked
# directory is a one-line change here.
TRACKED_SUBDIRS: tuple[str, ...] = (
    "sessions",
    "projects",
    "tasks",
    "plans",
    "session-env",
)


@dataclass(frozen=True)
class SubdirStat:
    """Counted statistics for a single subdirectory of `.claude/`."""

    name: str
    path: Path
    exists: bool
    entry_count: int

    @property
    def display(self) -> str:
        """Short human-readable summary used in Rich tables."""
        if not self.exists:
            return "—"
        return str(self.entry_count)


@dataclass(frozen=True)
class ClaudeInspectResult:
    """Aggregate result of inspecting a Claude Code directory.

    `total_entries` is the sum across the tracked subdirs that exist,
    not a count of every file under `.claude/`. It is intended to give
    the user a rough "how big is my data" signal.
    """

    claude_path: Path
    stats: tuple[SubdirStat, ...]
    total_entries: int

    def stat_by_name(self, name: str) -> SubdirStat | None:
        """Return the stat for a tracked subdir by name, or None if absent."""
        for stat in self.stats:
            if stat.name == name:
                return stat
        return None


class ClaudeInspector:
    """Read-only inspector for a Claude Code configuration directory.

    The inspector never touches files inside `.claude/` — it only
    reads directory entries to produce counts. If `claude_path` does
    not exist or is not a directory, the returned result still
    contains one `SubdirStat` per tracked subdir, all marked as
    `exists=False`.
    """

    def __init__(self, claude_path: Path | None) -> None:
        self.claude_path = claude_path

    def inspect(self) -> ClaudeInspectResult:
        """Build a `ClaudeInspectResult` for the configured path."""
        stats: list[SubdirStat] = []
        total = 0

        for name in TRACKED_SUBDIRS:
            if self.claude_path is None:
                # No Claude install at all: every tracked subdir is "missing".
                stats.append(
                    SubdirStat(name=name, path=Path(name), exists=False, entry_count=0)
                )
                continue

            subdir = self.claude_path / name
            if not subdir.is_dir():
                stats.append(
                    SubdirStat(name=name, path=subdir, exists=False, entry_count=0)
                )
                continue

            # Count immediate children. `iterdir()` raises on
            # permission errors or vanished entries; we treat that as
            # "we couldn't read this" and report 0.
            try:
                entry_count = sum(1 for _ in subdir.iterdir())
            except OSError:
                entry_count = 0

            stats.append(
                SubdirStat(
                    name=name, path=subdir, exists=True, entry_count=entry_count
                )
            )
            total += entry_count

        # The "path" stored on the result is whatever we were given;
        # a None means Claude is not installed on this machine.
        result_path = self.claude_path if self.claude_path is not None else Path("—")
        return ClaudeInspectResult(
            claude_path=result_path,
            stats=tuple(stats),
            total_entries=total,
        )
