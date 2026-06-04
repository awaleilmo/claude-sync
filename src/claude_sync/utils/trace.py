"""Filesystem tracing utility for detecting Claude Code session activity.

This module provides tools to:
1. Take a snapshot of all files in a directory (size, mtime, inode)
2. Compare two snapshots to find created/modified/deleted files
3. Store snapshots persistently for later comparison

The snapshot format is a simple JSON file that maps relative file paths
to their metadata. This is deliberately lightweight — no hashing, no
content inspection, just filesystem stat data. This makes it fast and
safe to run on large `.claude` directories.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Snapshot file stored in project root: .claude-sync-trace.json
SNAPSHOT_FILENAME = ".claude-sync-trace.json"


@dataclass
class FileStat:
    """Lightweight stat data for a single file."""

    size: int
    mtime: float  # Unix timestamp
    relative_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "mtime": self.mtime,
            "relative_path": self.relative_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileStat:
        return cls(
            size=data["size"],
            mtime=data["mtime"],
            relative_path=data["relative_path"],
        )


@dataclass
class Snapshot:
    """Snapshot of a directory at a point in time."""

    root: Path
    timestamp: float
    files: dict[str, FileStat] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "timestamp": self.timestamp,
            "files": {p: f.to_dict() for p, f in self.files.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Snapshot:
        files = {
            p: FileStat.from_dict(f) for p, f in data.get("files", {}).items()
        }
        return cls(root=Path(data["root"]), timestamp=data["timestamp"], files=files)

    @classmethod
    def load(cls, path: Path) -> Snapshot | None:
        """Load a snapshot from a JSON file. Returns None if file doesn't exist."""
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def save(self, path: Path) -> None:
        """Save this snapshot to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def take_snapshot(root: Path) -> Snapshot:
    """Scan a directory recursively and record stat data for all files.

    This is deliberately fast and lightweight: no hashing, no content
    inspection, just `stat` calls. On a typical `.claude` directory
    (~50k files) this completes in a few seconds.

    Args:
        root: The directory to scan.

    Returns:
        A Snapshot object containing metadata for all files found.
    """
    timestamp = datetime.now().timestamp()
    files: dict[str, FileStat] = {}

    for entry in root.rglob("*"):
        if entry.is_file():
            stat = entry.stat()
            relative = entry.relative_to(root)
            files[str(relative)] = FileStat(
                size=stat.st_size,
                mtime=stat.st_mtime,
                relative_path=str(relative),
            )

    return Snapshot(root=root, timestamp=timestamp, files=files)


@dataclass
class Diff:
    """Difference between two snapshots."""

    created: list[FileStat] = field(default_factory=list)
    modified: list[FileStat] = field(default_factory=list)
    deleted: list[FileStat] = field(default_factory=list)


def compare_snapshots(before: Snapshot, after: Snapshot) -> Diff:
    """Compare two snapshots and return the differences.

    A file is considered:
    - Created if it exists in `after` but not in `before`.
    - Deleted if it exists in `before` but not in `after`.
    - Modified if it exists in both but size or mtime changed.

    Args:
        before: Snapshot taken before the activity.
        after: Snapshot taken after the activity.

    Returns:
        A Diff object containing the changes.
    """
    diff = Diff()

    before_paths = set(before.files.keys())
    after_paths = set(after.files.keys())

    # Files created
    for path in after_paths - before_paths:
        diff.created.append(after.files[path])

    # Files deleted
    for path in before_paths - after_paths:
        diff.deleted.append(before.files[path])

    # Files modified
    for path in before_paths & after_paths:
        before_stat = before.files[path]
        after_stat = after.files[path]
        if (
            before_stat.size != after_stat.size
            or before_stat.mtime != after_stat.mtime
        ):
            diff.modified.append(after_stat)

    return diff