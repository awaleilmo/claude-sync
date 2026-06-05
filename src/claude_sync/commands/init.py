"""`claude-sync init` command.

Creates the `.claude-sync` folder in the current directory and writes
a `manifest.json` describing the project. Safe to re-run: existing
files are preserved unless explicitly overwritten.

Phase 1: also creates ``.claude-sync/project.json`` with a stable
``project_id`` (UUID4) for project identity.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from claude_sync.utils.config import (
    build_manifest,
    get_manifest_path,
    get_sync_dir,
    is_initialized,
    write_manifest,
)
from claude_sync.utils.project_identity import (
    build_project_metadata,
    get_project_metadata_path,
    read_project_metadata,
    write_project_metadata,
)

console = Console()


def _resolve_root(project_root: Path | None) -> Path:
    """Resolve the project root, defaulting to the current working directory.

    `Path.cwd()` is captured at function-call time (not module-load time) so
    that tests using `monkeypatch.chdir` behave correctly.
    """
    return project_root if project_root is not None else Path.cwd()


def init(
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Project root directory. Defaults to the current working directory.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Re-create the manifest and project metadata even if they already exist.",
    ),
) -> None:
    """Initialize a new claude-sync project in the current directory."""
    root = _resolve_root(project_root)
    sync_dir = get_sync_dir(root)
    manifest_path = get_manifest_path(root)
    project_meta_path = get_project_metadata_path(root)

    # Ensure the sync directory exists. Idempotent: mkdir with exist_ok=True.
    created_dir = not sync_dir.exists()
    sync_dir.mkdir(parents=True, exist_ok=True)

    if created_dir:
        console.print(f"[green]?[/green] Created {sync_dir.name} folder")
    else:
        console.print(f"[yellow]?[/yellow] {sync_dir.name} folder already exists")

    # ---- Write manifest (phase 1+2 identity) ----
    manifest_existed_before = manifest_path.exists()
    manifest_data: dict | None = None
    if manifest_existed_before and not force:
        console.print(f"[yellow]?[/yellow] {manifest_path.name} already exists, skipping")
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest_data = build_manifest(project_name=root.resolve().name)

    # ---- Write project.json (phase 1 identity) ----
    existing_meta = read_project_metadata(project_meta_path)
    if existing_meta is not None and not force:
        console.print(f"[yellow]?[/yellow] {project_meta_path.name} already exists, skipping")
        metadata = existing_meta
    else:
        metadata = build_project_metadata(project_name=root.resolve().name)
        write_project_metadata(project_meta_path, metadata)
        verb = "Re-created" if existing_meta is not None and force else "Created"
        console.print(f"[green]?[/green] {verb} {project_meta_path.name}")

    # ---- Ensure manifest has project fields ----
    if "project_id" not in manifest_data:
        manifest_data["project_id"] = metadata.project_id
    if "source_project_path" not in manifest_data:
        manifest_data["source_project_path"] = str(root.resolve())

    if manifest_existed_before and not force:
        # Only write if we added new fields
        old_json = json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n"
        if manifest_path.read_text(encoding="utf-8") != old_json:
            write_manifest(manifest_path, manifest_data)
            console.print(f"[dim]•[/dim] Updated {manifest_path.name} with project fields")
        else:
            console.print(f"[dim]•[/dim] {manifest_path.name} already up to date")
    else:
        write_manifest(manifest_path, manifest_data)
        verb = "Re-created" if manifest_existed_before and force else "Created"
        console.print(f"[green]?[/green] {verb} {manifest_path.name}")

    # Final status line for quick visual confirmation.
    if is_initialized(root):
        console.print("\n[bold green]Project is ready.[/bold green]")
