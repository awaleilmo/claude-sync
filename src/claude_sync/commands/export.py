"""`claude-sync export` command.

Mirrors a subset of the user's Claude Code configuration into
`.claude-sync/data/` inside the current project. The command is
explicit (no filtering yet) and rewrites the destination on every
run, so deletions in the source propagate to the export.

Side effects:
* Creates `<project>/.claude-sync/data/<subdir>/` for each tracked
  subdir that exists in the source.
* Wipes any pre-existing `<project>/.claude-sync/data/` first.
* Never touches `<home>/.claude/` (the source is read-only).
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.config import is_initialized
from claude_sync.utils.exporter import DATA_SUBDIR, EXPORT_SUBDIRS, ClaudeExporter

console = Console()


def _resolve_root(project_root: Path | None) -> Path:
    """Default to cwd; resolve at call time so tests using chdir work."""
    return project_root if project_root is not None else Path.cwd()


def run_export(
    project_root: Path | None = None,
    claude_path: Path | None = None,
) -> None:
    """Programmatic entry point used by `push` and other callers.

    Mirrors the Typer option set on `export` but takes plain args so it
    can be called from Python code (e.g. `commands/push.py`) without
    going through the CLI parser.
    """
    export(
        project_root=project_root,
        claude_path=claude_path,
    )


def export(
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
        help=(
            "Override the Claude source directory. By default we look it up "
            "via ClaudeLocator."
        ),
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Export Claude Code data into the current sync project."""
    root = _resolve_root(project_root)

    # Refuse to export into an uninitialised project. This matches
    # the `status` command's stance: a project that doesn't even have
    # a manifest shouldn't be written to.
    if not is_initialized(root):
        console.print("[red]✗[/red] Project not initialized")
        console.print("  Run [cyan]claude-sync init[/cyan] first.")
        raise typer.Exit(code=1)

    # Resolve source: explicit flag wins, otherwise locate it.
    if claude_path is None:
        claude_path = ClaudeLocator().find_claude_path()
    if claude_path is None:
        console.print("[red]✗[/red] Claude Path: Not Found")
        console.print("  Install Claude Code or pass [cyan]--claude-path[/cyan].")
        raise typer.Exit(code=1)

    exporter = ClaudeExporter(claude_path=claude_path, project_root=root)
    report = exporter.export()

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    console.print(
        f"[bold]Exporting from:[/bold] {report.claude_path}\n"
        f"[bold]Exporting to:[/bold]   {report.data_root}\n"
    )

    table = Table(
        title="Export Summary",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Subdir", style="bold")
    table.add_column("Files", justify="right")
    table.add_column("Status", justify="center")

    for name in EXPORT_SUBDIRS:
        if name in report.skipped:
            table.add_row(name, "—", "[yellow]skipped (source missing)[/yellow]")
        else:
            count = report.copied[name]
            table.add_row(name, str(count), "[green]copied[/green]")

    console.print(table)
    console.print(
        f"\n[bold green]✓[/bold green] Exported {report.file_count} files "
        f"into [bold]{DATA_SUBDIR}/[/bold]"
    )
