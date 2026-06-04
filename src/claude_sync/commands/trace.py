"""`claude-sync trace` command.

Investigates which files Claude Code actually touches during a session.

Workflow:
1. Run `claude-sync trace` to take a baseline snapshot.
2. Start a new Claude Code session and perform some work.
3. Run `claude-sync trace --compare` to see what changed.

The output tells you exactly which folders/files are active, so you can
make informed decisions about what to include in export/import.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.trace import (
    SNAPSHOT_FILENAME,
    Diff,
    compare_snapshots,
    take_snapshot,
)

console = Console()


def trace(
    compare: bool = typer.Option(
        False,
        "--compare",
        "-c",
        help="Compare current state against the previous snapshot.",
    ),
    snapshot_path: Path = typer.Option(
        None,
        "--snapshot-path",
        "-s",
        help="Path to store/load the snapshot file. Defaults to current directory.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Take a snapshot of `.claude` or compare against the previous one.

    Without `--compare`: saves a snapshot of the current state.
    With `--compare`: shows files that changed since the last snapshot.
    """
    # Locate Claude directory
    locator = ClaudeLocator()
    claude_path = locator.find_claude_path()

    if claude_path is None:
        console.print("[red]✗[/red] Claude Code not found on this system.")
        console.print("  Run [cyan]claude-sync status[/cyan] for details.")
        raise typer.Exit(code=1)

    # Determine snapshot file location
    snapshot_file = (
        snapshot_path / SNAPSHOT_FILENAME
        if snapshot_path
        else Path.cwd() / SNAPSHOT_FILENAME
    )

    if compare:
        _compare_mode(claude_path, snapshot_file)
    else:
        _snapshot_mode(claude_path, snapshot_file)


def _snapshot_mode(claude_path: Path, snapshot_file: Path) -> None:
    """Take and save a snapshot."""
    console.print(f"📸 Scanning [bold]{claude_path}[/bold]...")

    snapshot = take_snapshot(claude_path)
    snapshot.save(snapshot_file)

    console.print(
        f"[green]✓[/green] Snapshot saved to [bold]{snapshot_file.name}[/bold]"
    )
    console.print(f"  Files tracked: [cyan]{len(snapshot.files)}[/cyan]")
    console.print(f"  Timestamp: [dim]{datetime.fromtimestamp(snapshot.timestamp).isoformat()}[/dim]")
    console.print("\n[dim]Now start a Claude Code session. When done, run:[/dim]")
    console.print(f"  [cyan]claude-sync trace --compare[/cyan]")


def _compare_mode(claude_path: Path, snapshot_file: Path) -> None:
    """Compare current state against the previous snapshot."""
    before_snapshot = Snapshot.load(snapshot_file)

    if before_snapshot is None:
        console.print(
            f"[red]✗[/red] No snapshot found at [bold]{snapshot_file.name}[/bold]"
        )
        console.print("  Run [cyan]claude-sync trace[/cyan] first to create a baseline.")
        raise typer.Exit(code=1)

    console.print(f"🔍 Comparing against snapshot from [dim]{datetime.fromtimestamp(before_snapshot.timestamp).isoformat()}[/dim]...")

    after_snapshot = take_snapshot(claude_path)
    diff = compare_snapshots(before_snapshot, after_snapshot)

    _display_diff(diff)

    # Always save the new snapshot so we can compare incrementally
    after_snapshot.save(snapshot_file)
    console.print(f"\n[dim]Updated snapshot saved to {snapshot_file.name}[/dim]")


def _display_diff(diff: Diff) -> None:
    """Render the diff using Rich tables."""

    if not any([diff.created, diff.modified, diff.deleted]):
        console.print("\n[green]✓[/green] No changes detected.")
        return

    # Created files
    if diff.created:
        console.print("\n[bold green]Created Files[/bold green]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("File", style="cyan")
        table.add_column("Size", justify="right", style="yellow")
        table.add_column("Modified", style="dim")

        for stat in sorted(diff.created, key=lambda s: s.relative_path):
            table.add_row(
                stat.relative_path,
                _format_size(stat.size),
                _format_timestamp(stat.mtime),
            )
        console.print(table)

    # Modified files
    if diff.modified:
        console.print("\n[bold yellow]Modified Files[/bold yellow]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("File", style="cyan")
        table.add_column("Size", justify="right", style="yellow")
        table.add_column("Modified", style="dim")

        for stat in sorted(diff.modified, key=lambda s: s.relative_path):
            table.add_row(
                stat.relative_path,
                _format_size(stat.size),
                _format_timestamp(stat.mtime),
            )
        console.print(table)

    # Deleted files
    if diff.deleted:
        console.print("\n[bold red]Deleted Files[/bold red]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("File", style="red")
        table.add_column("Size", justify="right", style="dim")
        table.add_column("Modified", style="dim")

        for stat in sorted(diff.deleted, key=lambda s: s.relative_path):
            table.add_row(
                stat.relative_path,
                _format_size(stat.size),
                _format_timestamp(stat.mtime),
            )
        console.print(table)

    # Summary
    console.print(
        f"\n[dim]Summary: {len(diff.created)} created, "
        f"{len(diff.modified)} modified, {len(diff.deleted)} deleted.[/dim]"
    )


def _format_size(size: int) -> str:
    """Format a byte count as a human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _format_timestamp(ts: float) -> str:
    """Format a Unix timestamp as a human-readable string."""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# Import Snapshot for type hint
from claude_sync.utils.trace import Snapshot
