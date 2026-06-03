"""`claude-sync inspect` command.

Read-only view of the structure inside the user's Claude Code
configuration directory. Shows entry counts for the well-known
subfolders (`sessions`, `projects`, `tasks`, `plans`, `session-env`)
using a Rich table. Does NOT copy, move, or modify any files.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.inspector import ClaudeInspector, TRACKED_SUBDIRS

console = Console()


def inspect(
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
    no_located: bool = typer.Option(
        False,
        "--no-locate",
        help=(
            "Skip the Claude directory lookup and inspect a path provided "
            "via --claude-path (or fail if neither is given)."
        ),
    ),
    claude_path: Path | None = typer.Option(
        None,
        "--claude-path",
        help=(
            "Override the Claude directory to inspect. By default we look "
            "it up via ClaudeLocator (Linux/Windows/WSL)."
        ),
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Inspect the structure of the Claude Code configuration directory."""
    # --claude-path wins; otherwise locate the directory; otherwise
    # `None` is passed to the inspector, which renders all rows as
    # "missing".
    if claude_path is not None:
        target = claude_path
    elif no_located:
        target = None
    else:
        target = ClaudeLocator().find_claude_path()

    inspector = ClaudeInspector(target)
    result = inspector.inspect()

    # ------------------------------------------------------------------
    # Header: which Claude directory are we looking at?
    # ------------------------------------------------------------------
    if result.claude_path == Path("—"):
        console.print("[bold]Claude Path:[/bold] Not Found")
    else:
        console.print(f"[bold]Claude Path:[/bold] {result.claude_path}")

    # ------------------------------------------------------------------
    # Rich table: one row per tracked subdir.
    # ------------------------------------------------------------------
    table = Table(
        title="Claude Code Directory Structure",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Subdirectory", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Entries", justify="right")
    table.add_column("Path", style="dim", overflow="fold")

    for stat in result.stats:
        if not stat.exists:
            status = "[yellow]missing[/yellow]"
        else:
            status = "[green]present[/green]"

        # Show the absolute path only when we actually have one. For
        # missing subdirs we display a hyphen so the column is never
        # blank and the table stays aligned.
        path_display = str(stat.path) if stat.exists else "—"

        table.add_row(stat.name, status, stat.display, path_display)

    console.print()
    console.print(table)
    console.print()

    # ------------------------------------------------------------------
    # Summary line — handy for piping into other tools.
    # ------------------------------------------------------------------
    present = sum(1 for s in result.stats if s.exists)
    console.print(
        f"[bold]Summary:[/bold] {present}/{len(TRACKED_SUBDIRS)} tracked subdirs present, "
        f"{result.total_entries} total entries."
    )

    # Non-zero exit if Claude is missing entirely, mirroring `status`.
    if result.claude_path == Path("—"):
        raise typer.Exit(code=1)
