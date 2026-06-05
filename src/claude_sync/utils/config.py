"""Configuration helpers: paths and manifest handling.

This module is the single source of truth for filesystem locations
used by the ``init`` and ``status`` commands.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Folder name created inside the user's project directory.
SYNC_DIR_NAME = ".claude-sync"

# Manifest file written inside the sync directory.
MANIFEST_FILENAME = "manifest.json"

# Current manifest schema version.
MANIFEST_VERSION = 2


def get_sync_dir(project_root: Path | None = None) -> Path:
    """Return the path to the ``.claude-sync`` directory.

    Args:
        project_root: Base directory. Defaults to the current working directory.

    Returns:
        Absolute path to the sync directory (may not exist yet).
    """
    root = project_root if project_root is not None else Path.cwd()
    return root / SYNC_DIR_NAME


def get_manifest_path(project_root: Path | None = None) -> Path:
    """Return the path to ``manifest.json`` inside the sync directory."""
    return get_sync_dir(project_root) / MANIFEST_FILENAME


def build_manifest(project_name: str) -> dict[str, Any]:
    """Build the default manifest payload for a given project name."""
    return {
        "project_name": project_name,
        "version": MANIFEST_VERSION,
    }


def read_manifest(project_root: Path | None = None) -> dict[str, Any] | None:
    """Read the manifest from the sync dir; return None if missing or invalid."""
    manifest_path = get_manifest_path(project_root)
    if not manifest_path.is_file():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    """Write the manifest as pretty-printed JSON.

    Uses UTF-8 encoding and a trailing newline for friendly diffs.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    manifest_path.write_text(content, encoding="utf-8")


def is_initialized(project_root: Path | None = None) -> bool:
    """Return True only if both the sync dir and manifest exist."""
    sync_dir = get_sync_dir(project_root)
    manifest = get_manifest_path(project_root)
    return sync_dir.is_dir() and manifest.is_file()
