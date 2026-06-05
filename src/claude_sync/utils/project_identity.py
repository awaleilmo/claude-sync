"""Project identity: unique project metadata for Phase 1.

This module introduces a stable, persistent identifier for each
claude-sync project.  The ``project_id`` is a ``uuid4`` value that is
generated once during ``init`` and never changes.

The data model is a ``dataclass`` (not a raw ``dict``) so callers can
access fields by name and IDE auto-completion works.

Design notes

* ``project.json`` lives inside ``.claude-sync/`` alongside
  ``manifest.json``.  It carries schema version **2** so future
  migrations can detect the old schema.
* The file is created once and preserved on subsequent ``init`` runs
  unless ``--force`` is given.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claude_sync.utils.config import get_sync_dir

# File name inside .claude-sync/ for the new identity file.
PROJECT_METADATA_FILENAME = "project.json"

# Schema version for this file.
PROJECT_METADATA_VERSION = 2


@dataclass(frozen=True)
class ProjectMetadata:
    """Immutable project metadata.

    Attributes:
        project_id: Stable UUID4 generated once at ``init``.
        project_name: Human-readable name from the directory basename.
        version: Schema version (currently always 2).
    """

    project_id: str
    project_name: str
    version: int = PROJECT_METADATA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for ``json.dump``."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectMetadata:
        """Build a ``ProjectMetadata`` from a plain dict."""
        if "project_id" not in data:
            raise ValueError("Missing required field: project_id")
        if "project_name" not in data:
            raise ValueError("Missing required field: project_name")
        if "version" not in data:
            raise ValueError("Missing required field: version")
        return cls(
            project_id=data["project_id"],
            project_name=data["project_name"],
            version=data["version"],
        )


def build_project_metadata(project_name: str) -> ProjectMetadata:
    """Create a new ``ProjectMetadata`` with a fresh UUID4."""
    return ProjectMetadata(
        project_id=str(uuid.uuid4()),
        project_name=project_name,
    )


def get_project_metadata_path(project_root: Path | None = None) -> Path:
    """Return the path to ``project.json`` inside the sync directory."""
    return get_sync_dir(project_root) / PROJECT_METADATA_FILENAME


def read_project_metadata(path: Path) -> ProjectMetadata | None:
    """Read and parse ``project.json``.

    Returns:
        ``ProjectMetadata`` if the file exists and is valid JSON.
        ``None`` if the file does not exist or is malformed.
    """
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProjectMetadata.from_dict(data)
    except (json.JSONDecodeError, ValueError):
        return None


def write_project_metadata(path: Path, metadata: ProjectMetadata) -> None:
    """Write ``ProjectMetadata`` as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(metadata.to_dict(), indent=2, ensure_ascii=False) + "\n"
    path.write_text(content, encoding="utf-8")
