"""`claude-sync status` command.

Reports two independent pieces of information:

1. Whether the project is initialized (`.claude-sync/` + `manifest.json`).
2. Whether the Claude Code configuration directory is reachable on
   this machine (so the user can spot "I forgot to install Claude
   on this laptop" before trying to export).
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.config import (
    get_manifest_path,
    get_sync_dir,
    is_initialized,
)

console = Console()


def _resolve_root(project_root: Path | None) -> Path:
    """Resolve the project root, defaulting to the current working directory.

    `Path.cwd()` is captured at function-call time (not module-load time) so
    that tests using `monkeypatch.chdir` behave correctly.
    """
    return project_root if project_root is not None else Path.cwd()


def status(
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
) -> None:
    """Show the initialization status of the current project."""
    root = _resolve_root(project_root)
    sync_dir = get_sync_dir(root)
    manifest_path = get_manifest_path(root)

    # ------------------------------------------------------------------
    # Section 1: claude-sync project status
    # ------------------------------------------------------------------
    if not sync_dir.is_dir():
        console.print("[red]✗[/red] Project not initialized")
        console.print(f"  Missing: [bold]{sync_dir.name}[/bold]")
        console.print("  Run [cyan]claude-sync init[/cyan] to initialize.")
        project_ok = False
    else:
        console.print(f"[green]✓[/green] Project initialized ({sync_dir.name}/ present)")
        if not manifest_path.is_file():
            console.print(
                f"[red]✗[/red] Manifest missing ({manifest_path.name} not found)"
            )
            project_ok = False
        else:
            console.print(f"[green]✓[/green] Manifest found ({manifest_path.name})")
            project_ok = is_initialized(root)

    # ------------------------------------------------------------------
    # Section 2: Claude Code install status (added in Tahap 2)
    # ------------------------------------------------------------------
    console.print()  # blank line between sections
    locator = ClaudeLocator()
    claude_path = locator.find_claude_path()

    if claude_path is not None:
        console.print(f"[green]✓[/green] Claude Path: [bold]{claude_path}[/bold]")
        if locator.is_wsl():
            console.print("  [dim]Detected environment: WSL[/dim]")
    else:
        console.print("[yellow]![/yellow] Claude Path: [bold]Not Found[/bold]")
        console.print("  [dim]Install Claude Code so its data can be synced.[/dim]")

    # ------------------------------------------------------------------
    # Exit code
    # ------------------------------------------------------------------
    # The command fails if EITHER the project is uninitialized OR the
    # Claude install is missing. A non-zero exit makes the command
    # scriptable from CI / shell pipelines.
    if not project_ok or claude_path is None:
        raise typer.Exit(code=1)

    console.print("\n[bold green]Everything looks good.[/bold green]")
