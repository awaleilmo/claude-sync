"""`claude-sync init` command.

Creates the `.claude-sync` folder in the current directory and writes
a `manifest.json` describing the project. Safe to re-run: existing
files are preserved unless explicitly overwritten.
"""

from __future__ import annotations

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
        help="Re-create the manifest even if one already exists.",
    ),
) -> None:
    """Initialize a new claude-sync project in the current directory."""
    root = _resolve_root(project_root)
    sync_dir = get_sync_dir(root)
    manifest_path = get_manifest_path(root)

    # Ensure the sync directory exists. Idempotent: mkdir with exist_ok=True.
    created_dir = not sync_dir.exists()
    sync_dir.mkdir(parents=True, exist_ok=True)

    if created_dir:
        console.print(f"[green]✓[/green] Created {sync_dir.name} folder")
    else:
        console.print(f"[yellow]•[/yellow] {sync_dir.name} folder already exists")

    # Write manifest unless one is already there (unless --force is given).
    manifest_existed_before = manifest_path.exists()
    if manifest_existed_before and not force:
        console.print(f"[yellow]•[/yellow] {manifest_path.name} already exists, skipping")
    else:
        manifest = build_manifest(project_name=root.resolve().name)
        write_manifest(manifest_path, manifest)
        verb = "Re-created" if manifest_existed_before and force else "Created"
        console.print(f"[green]✓[/green] {verb} {manifest_path.name}")

    # Final status line for quick visual confirmation.
    if is_initialized(root):
        console.print("\n[bold green]Project is ready.[/bold green]")
