"""`claude-sync map` — manual project-path mapping.

When the automatic suffix-matching in Tahap 7C cannot find the right
target folder, the user can explicitly register a mapping with this
command.  The mapping is stored in
``<claude_path>/.claude-sync/project-map.json`` so it survives
across import runs.

Usage::

    claude-sync map --source "...src-enc" --target "...tgt-enc"
    claude-sync map --list
    claude-sync map --clear
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_sync.utils.claude_locator import ClaudeLocator

console = Console()

SYNC_DIR_NAME = ".claude-sync"
PROJECT_MAP_FILENAME = "project-map.json"


def _get_sync_dir(project_root: Path | None) -> Path:
    """Return ``<project_root>/.claude-sync/`` (or cwd fallback)."""
    root = project_root if project_root is not None else Path.cwd()
    return root / SYNC_DIR_NAME


def _load_map(sync_dir: Path) -> dict[str, str]:
    """Read ``project-map.json``, returning {} when absent."""
    map_path = sync_dir / PROJECT_MAP_FILENAME
    if not map_path.is_file():
        return {}
    try:
        return json.loads(map_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_map(sync_dir: Path, mapping: dict[str, str]) -> None:
    """Persist *mapping* to ``project-map.json``."""
    map_path = sync_dir / PROJECT_MAP_FILENAME
    map_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(mapping, indent=2, ensure_ascii=False) + "\n"
    map_path.write_text(content, encoding="utf-8")


def _render_table(mapping: dict[str, str]) -> None:
    """Pretty-print a mapping dict as a Rich table."""
    table = Table(
        title="Project Map",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Source (exported)", style="bold")
    table.add_column("Target (this machine)", style="bold")
    for src, tgt in sorted(mapping.items()):
        table.add_row(src, tgt)
    console.print(table)


def _resolve_claude_path() -> Path:
    """Resolve the target Claude directory.  Exits with an error on failure."""
    claude_path = ClaudeLocator().find_claude_path()
    if claude_path is None:
        console.print(
            "[red]✗[/red] Claude Path: Not Found\n"
            "  Pass [cyan]--claude-path[/cyan] to specify a destination."
        )
        raise typer.Exit(code=1)
    return claude_path


# ------------------------------------------------------------------
# Typer subcommand
# ------------------------------------------------------------------

map_app = typer.Typer(
    name="map",
    help="Manage manual project-path mappings for cross-device import.",
    add_completion=False,
)


@map_app.command()
def add(
    source: str | None = typer.Option(
        None,
        "--source",
        "-s",
        help="Encoded project name from the export side.",
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Encoded project name on this machine.",
    ),
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
    claude_path: Path | None = typer.Option(
        None,
        "--claude-path",
        help="Override the target Claude directory.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Add or update a single source→target mapping."""
    if source is None or target is None:
        console.print("[red]✗[/red] Both --source and --target are required.")
        raise typer.Exit(code=1)

    target_dir = _resolve_claude_path()
    sync_dir = target_dir / SYNC_DIR_NAME
    mapping = _load_map(sync_dir)
    old = mapping.get(source)
    mapping[source] = target
    _save_map(sync_dir, mapping)

    if old is None:
        console.print(f"[green]✓[/green] Added: [bold]{source}[/bold] → [bold]{target}[/bold]")
    else:
        console.print(
            f"[yellow]![/yellow] Updated: [bold]{source}[/bold] {old} → [bold]{target}[/bold]"
        )
    console.print()
    _render_table(mapping)


@map_app.command()
def list_maps(
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
    claude_path: Path | None = typer.Option(
        None,
        "--claude-path",
        help="Override the target Claude directory.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """List all stored manual mappings."""
    target_dir = _resolve_claude_path()
    sync_dir = target_dir / SYNC_DIR_NAME
    mapping = _load_map(sync_dir)
    if not mapping:
        console.print("[yellow]No manual mappings registered.[/yellow]")
        return
    _render_table(mapping)


@map_app.command()
def clear_maps(
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
    claude_path: Path | None = typer.Option(
        None,
        "--claude-path",
        help="Override the target Claude directory.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Remove all manual mappings."""
    target_dir = _resolve_claude_path()
    sync_dir = target_dir / SYNC_DIR_NAME
    map_path = sync_dir / PROJECT_MAP_FILENAME
    if map_path.is_file():
        map_path.unlink()
        console.print("[yellow]![/yellow] All mappings cleared.")
    else:
        console.print("[yellow]No mappings to clear.[/yellow]")
