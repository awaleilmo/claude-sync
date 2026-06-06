"""`claude-sync status` command.

Reports:

1. Whether the project is initialized (``.claude-sync/`` + ``manifest.json``).
2. Project identity from ``project.json`` (Project Name, ID, Version).
3. The Claude Code project folder detected for this local project.
4. Whether the Claude Code configuration directory is reachable.
5. Export availability (Phase 3).
6. Package format and availability (Phase 5C).
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
    read_manifest,
)
from claude_sync.utils.project_identity import get_project_metadata_path, read_project_metadata
from claude_sync.utils.project_path import locate_claude_project, project_to_claude_folder

_claudepack_filename = "project.claudepack"

console = Console()


def _resolve_root(project_root: Path | None) -> Path:
    """Resolve the project root, defaulting to cwd."""
    return project_root if project_root is not None else Path.cwd()


def status(
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Project root directory. Defaults to cwd.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    check_mapping: bool = typer.Option(
        False,
        "--check-mapping",
        help="Only print whether Source and Current Claude folders match. "
        "Exits 0 on match, 1 on mismatch.",
    ),
) -> None:
    """Show the initialization status of the current project."""
    root = _resolve_root(project_root)
    sync_dir = get_sync_dir(root)
    manifest_path = get_manifest_path(root)

    if check_mapping:
        _run_mapping_check(root, manifest_path)
        return

    # Section 1: Project initialized?
    if not sync_dir.is_dir():
        console.print("[red]\u2717[/red] Project not initialized")
        console.print(f"  Missing: [bold]{sync_dir.name}[/bold]")
        console.print("  Run [cyan]claude-sync init[/cyan] to initialize.")
        project_ok = False
    else:
        console.print(f"[green]\u2713[/green] Project initialized ({sync_dir.name}/ present)")
        if not manifest_path.is_file():
            console.print(f"[red]\u2717[/red] Manifest missing ({manifest_path.name})")
            project_ok = False
        else:
            console.print(f"[green]\u2713[/green] Manifest found ({manifest_path.name})")
            project_ok = is_initialized(root)

        # Section 1b: Project identity
        project_meta_path = get_project_metadata_path(root)
        meta = read_project_metadata(project_meta_path)
        if meta is not None:
            console.print(f"[dim]\u2022[/dim] Project Name: [bold]{meta.project_name}[/bold]")
            console.print(f"[dim]\u2022[/dim] Project ID:   [bold]{meta.project_id}[/bold]")
            console.print(f"[dim]\u2022[/dim] Version:      {meta.version}")
        else:
            console.print(
                "[dim]\u2022[/dim] [yellow]project.json not found. Run 'claude-sync init'.[/yellow]"
            )

    # Section 1c: Claude project folder detection + Export Available
    console.print()  # blank
    claude_path = ClaudeLocator().find_claude_path()

    # Current Claude Mapping
    current_claude_folder = None
    if claude_path is not None:
        local_project_path = root.resolve()
        claude_project = locate_claude_project(claude_path, local_project_path)
        current_claude_folder = project_to_claude_folder(local_project_path)
        if claude_project is not None:
            console.print(
                f"[green]\u2713[/green] Detected Claude Project Folder: "
                f"[bold]{claude_project.name}[/bold]"
            )
        else:
            console.print(
                "[yellow]![/yellow] Detected Claude Project Folder: [yellow]Not found for this project.[/yellow]"
            )
    else:
        console.print("[dim]\u2022[/dim] Claude path not available, cannot detect project folder.")

    # Export Available
    export_root = sync_dir / "export" / "project"
    if export_root.is_dir():
        subdirs = [p for p in export_root.iterdir() if p.is_dir()]
        if subdirs:
            console.print(
                f"[green]\u2713[/green] Export Available: [bold]YES[/bold] "
                f"({len(subdirs)} project folder(s))"
            )
        else:
            console.print("[yellow]![/yellow] Export Available: [yellow]NO[/yellow] (export/project/ is empty)")
    else:
        console.print("[yellow]![/yellow] Export Available: [yellow]NO[/yellow]")

    # Current Claude Mapping (always show)
    if current_claude_folder:
        console.print(
            f"[dim]\u2022[/dim] Current Claude Folder: [bold]{current_claude_folder}[/bold]"
        )

    # Source Claude Folder (recorded by `export` on the originating machine)
    source_claude_folder = None
    if manifest_path.is_file():
        manifest_data = read_manifest(root) or {}
        source_claude_folder = manifest_data.get("source_claude_project_folder")
    if source_claude_folder:
        if current_claude_folder and source_claude_folder != current_claude_folder:
            console.print(
                f"[dim]\u2022[/dim] Source Claude Folder:  [bold]{source_claude_folder}[/bold] "
                f"[yellow](differs from current)[/yellow]"
            )
        else:
            console.print(
                f"[dim]\u2022[/dim] Source Claude Folder:  [bold]{source_claude_folder}[/bold]"
            )
    else:
        console.print(
            "[dim]\u2022[/dim] Source Claude Folder:  [dim]not recorded (run 'claude-sync export')[/dim]"
        )

    # Package Format (Phase 5C)
    claudepack_path = sync_dir / _claudepack_filename
    if claudepack_path.is_file():
        size_bytes = claudepack_path.stat().st_size
        if size_bytes >= 1_048_576:
            size_str = f"{size_bytes / 1_048_576:.1f} MB"
        else:
            size_str = f"{size_bytes / 1024:.1f} KB"
        console.print(f"[dim]\u2022[/dim] Package Format:     [bold]Claudepack[/bold]")
        console.print(f"[dim]\u2022[/dim] Package Available:  [green]Yes[/green]")
        console.print(f"[dim]\u2022[/dim] Package Size:       [bold]{size_str}[/bold]")
    else:
        console.print(f"[dim]\u2022[/dim] Package Format:     [bold]Folder[/bold]")
        console.print(f"[dim]\u2022[/dim] Package Available:  [yellow]No[/yellow]")
        console.print(f"[dim]\u2022[/dim] Package Size:       [dim]N/A[/dim]")

    # Section 2: Claude Code install status
    console.print()
    if claude_path is not None:
        console.print(f"[green]\u2713[/green] Claude Path: [bold]{claude_path}[/bold]")
        if ClaudeLocator().is_wsl():
            console.print("  [dim]Detected environment: WSL[/dim]")
    else:
        console.print("[yellow]![/yellow] Claude Path: [bold]Not Found[/bold]")
        console.print("  [dim]Install Claude Code so its data can be synced.[/dim]")

    # Exit code
    if not project_ok or claude_path is None:
        raise typer.Exit(code=1)

    console.print("\n[bold green]Everything looks good.[/bold green]")


def _run_mapping_check(root: Path, manifest_path: Path) -> None:
    """Print a mapping check and exit 0 on match, 1 on mismatch.

    Used by ``status --check-mapping`` (and could be wired into a
    future ``doctor`` command). Prints:

    * Source Claude Folder (from manifest)
    * Current Claude Folder (from local project path)
    * A verdict: ✓ Mapping Valid or ⚠ Source and Current Mapping Differ
    """
    manifest_data = read_manifest(root) or {}
    source_folder = manifest_data.get("source_claude_project_folder")
    current_folder = project_to_claude_folder(root.resolve())

    console.print(f"[dim]•[/dim] Source Claude Folder: [bold]{source_folder or 'unknown'}[/bold]")
    console.print(f"[dim]•[/dim] Current Claude Folder: [bold]{current_folder}[/bold]")

    if not source_folder:
        console.print(
            "[yellow]![/yellow] Mapping Check: [yellow]unknown (no source recorded)[/yellow]"
        )
        raise typer.Exit(code=1)

    if source_folder == current_folder:
        console.print("[bold green]✓[/bold green] Mapping Check: [bold green]Valid[/bold green]")
        return

    console.print(
        "[bold yellow]⚠[/bold yellow] Mapping Check: [bold yellow]Source and Current Mapping Differ[/bold yellow]"
    )
    raise typer.Exit(code=1)
