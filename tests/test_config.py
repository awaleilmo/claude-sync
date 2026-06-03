"""Tests for `claude_sync.utils.config`."""

from __future__ import annotations

import json

from pathlib import Path

from claude_sync.utils.config import (
    MANIFEST_VERSION,
    build_manifest,
    get_manifest_path,
    get_sync_dir,
    is_initialized,
    write_manifest,
)


def test_get_sync_dir_default(tmp_path: Path) -> None:
    """Default sync dir should be `<cwd>/.claude-sync`."""
    sync_dir = get_sync_dir(tmp_path)
    assert sync_dir == tmp_path / ".claude-sync"


def test_get_manifest_path(tmp_path: Path) -> None:
    """Manifest path should be `<cwd>/.claude-sync/manifest.json`."""
    manifest = get_manifest_path(tmp_path)
    assert manifest == tmp_path / ".claude-sync" / "manifest.json"


def test_build_manifest() -> None:
    """build_manifest should match the documented schema."""
    manifest = build_manifest("my-project")
    assert manifest == {"project_name": "my-project", "version": MANIFEST_VERSION}


def test_write_manifest_creates_file(tmp_path: Path) -> None:
    """write_manifest should create parent dirs and write valid JSON."""
    manifest_path = tmp_path / ".claude-sync" / "manifest.json"
    write_manifest(manifest_path, {"project_name": "demo", "version": 1})

    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["project_name"] == "demo"
    assert data["version"] == 1


def test_is_initialized_false_when_empty(tmp_path: Path) -> None:
    """Empty project root should report as not initialized."""
    assert is_initialized(tmp_path) is False


def test_is_initialized_true_when_complete(tmp_path: Path) -> None:
    """A complete setup should report as initialized."""
    (tmp_path / ".claude-sync").mkdir()
    (tmp_path / ".claude-sync" / "manifest.json").write_text("{}", encoding="utf-8")
    assert is_initialized(tmp_path) is True
