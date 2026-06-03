"""`claude-sync import` command.

Restores the contents of `.claude-sync/data/` back into the user's
Claude Code configuration directory. Before touching the destination,
the command takes a timestamped safety backup of whatever currently
lives in `~/.claude`, so a bad restore can always be reverted.

Note: the module is named `import_cmd.py` (not `import.py`) to
avoid clashing with the stdlib `import` keyword.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.config import is_initialized
from claude_sync.utils.exporter import DATA_SUBDIR, EXPORT_SUBDIRS
from claude_sync.utils.importer import ClaudeImporter

console = Console()


def _resolve_root(project_root: Path | None) -> Path:
    """Default to cwd; resolve at call time so chdir-based tests work."""
    return project_root if project_root is not None else Path.cwd()


def run_import(
    project_root: Path | None = None,
    claude_path: Path | None = None,
    no_backup: bool = False,
) -> None:
    """Programmatic entry point used by `pull` and other callers.

    Mirrors the Typer option set on `import_cmd` but takes plain args so
    it can be called from Python code (e.g. `commands/pull.py`) without
    going through the CLI parser.
    """
    # Delegate to the CLI command function. typer.Option defaults on
    # `import_cmd` make it safe to call without any kwargs.
    import_cmd(
        project_root=project_root,
        claude_path=claude_path,
        no_backup=no_backup,
    )


def import_cmd(  # noqa: A001 — Typer binds the public name `import_data`.
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
            "Override the destination Claude directory. By default we "
            "look it up via ClaudeLocator."
        ),
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    no_backup: bool = typer.Option(
        False,
        "--no-backup",
        help="Skip the safety backup. Off by default; only enable in tests/throwaway envs.",
    ),
) -> None:
    """Import Claude Code data from the current sync project."""
    root = _resolve_root(project_root)

    if not is_initialized(root):
        console.print("[red]✗[/red] Project not initialized")
        console.print("  Run [cyan]claude-sync init[/cyan] first.")
        raise typer.Exit(code=1)

    # Resolve destination: explicit flag wins, otherwise locate it.
    if claude_path is None:
        claude_path = ClaudeLocator().find_claude_path()
    if claude_path is None:
        console.print("[red]✗[/red] Claude Path: Not Found")
        console.print("  Pass [cyan]--claude-path[/cyan] to specify a destination.")
        raise typer.Exit(code=1)

    importer = ClaudeImporter(claude_path=claude_path, project_root=root)
    report = importer.import_data(backup=not no_backup)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    if report.file_count == 0 and not report.restored:
        console.print(
            f"[yellow]![/yellow] Nothing to import: {report.data_root} does not exist."
        )
        console.print("  Run [cyan]claude-sync export[/cyan] first.")
        raise typer.Exit(code=1)

    console.print(
        f"[bold]Importing from:[/bold] {report.data_root}\n"
        f"[bold]Importing to:[/bold]   {report.claude_path}\n"
    )

    if report.backup_path is not None:
        console.print(
            f"[green]✓[/green] Backup created: [bold]{report.backup_path}[/bold]\n"
        )

    table = Table(
        title="Import Summary",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Subdir", style="bold")
    table.add_column("Files", justify="right")
    table.add_column("Status", justify="center")

    for name in EXPORT_SUBDIRS:
        if name in report.restored:
            count = report.restored[name]
            table.add_row(name, str(count), "[green]restored[/green]")
        else:
            table.add_row(name, "—", "[yellow]skipped (no data)[/yellow]")

    console.print(table)
    console.print(
        f"\n[bold green]✓[/bold green] Imported {report.file_count} files "
        f"from [bold]{DATA_SUBDIR}/[/bold]"
    )
