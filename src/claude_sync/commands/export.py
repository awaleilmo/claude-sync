"""`claude-sync export` command.

Exports only the Claude Code project folder corresponding to the
current local project into ``.claude-sync/export/project/<folder>/``.

Phase 2 (Project-Based Export):

* No longer exports the entire ``.claude/`` directory.
* Only the project folder (``~/.claude/projects/<current-project>``)
  is copied.
* Output layout::

    .claude-sync/
    ├── project.json
    ├── manifest.json
    └── export/
        └── project/
            └── <current-project-folder>/
                ├── *.jsonl
                └── memory/

Side effects:

* Creates ``<project>/.claude-sync/export/project/<folder>/`` for the
  current project's Claude data.
* Wipes any pre-existing export for that project folder.
* Never touches ``<home>/.claude/`` (the source is read-only).
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.config import (
    get_manifest_path,
    is_initialized,
    read_manifest,
    write_manifest,
)
from claude_sync.utils.exporter import ProjectExporter, ProjectExportReport

console = Console()


def _resolve_root(project_root: Path | None) -> Path:
    """Default to cwd; resolve at call time so tests using chdir work."""
    return project_root if project_root is not None else Path.cwd()


def run_export(
    project_root: Path | None = None,
    claude_path: Path | None = None,
    local_project_path: Path | None = None,
) -> None:
    """Programmatic entry point used by ``push`` and other callers."""
    export(
        project_root=project_root,
        claude_path=claude_path,
        local_project_path=local_project_path,
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
    local_project_path: Path | None = typer.Option(
        None,
        "--local-project-path",
        help=(
            "Override the local project path used to compute the Claude project "
            "folder. By default we use ``cwd.resolve()``."
        ),
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Export Claude Code data for the current project."""
    root = _resolve_root(project_root)

    if not is_initialized(root):
        console.print("[red]✗[/red] Project not initialized")
        console.print("  Run [cyan]claude-sync init[/cyan] first.")
        raise typer.Exit(code=1)

    # Resolve source
    if claude_path is None:
        claude_path = ClaudeLocator().find_claude_path()
    if claude_path is None:
        console.print("[red]✗[/red] Claude Path: Not Found")
        console.print("  Install Claude Code or pass [cyan]--claude-path[/cyan].")
        raise typer.Exit(code=1)

    exporter = ProjectExporter(
        claude_path=claude_path,
        project_root=root,
        local_project_path=local_project_path,
    )

    try:
        report = exporter.export()
    except FileNotFoundError as exc:
        console.print(f"[red]✗[/red] {exc}")
        raise typer.Exit(code=1)

    # Phase 4: record the Claude project folder name of the source
    # machine in the manifest, so the receiving machine can compare it
    # with its own current folder name.
    manifest_path = get_manifest_path(root)
    manifest_data = read_manifest(root) or {}
    manifest_data["source_project_path"] = str(report.source_project_path)
    manifest_data["source_claude_project_folder"] = report.claude_project_folder
    write_manifest(manifest_path, manifest_data)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    console.print(
        f"[bold]Exporting from:[/bold]   {report.claude_path}\n"
        f"[bold]Claude project folder:[/bold] {report.claude_project_folder}\n"
        f"[bold]Exporting to:[/bold]     {report.data_root}\n"
    )

    table = Table(
        title="Export Summary",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Subdir", style="bold")
    table.add_column("Files", justify="right")
    table.add_column("Status", justify="center")

    for name in sorted(report.copied):
        table.add_row(name, str(report.copied[name]), "[green]copied[/green]")

    console.print(table)
    console.print(
        f"\n[bold green]✓[/bold green] Exported {report.file_count} files "
        f"into [bold]export/project/{report.claude_project_folder}/[/bold]"
    )

    if report.claudepack_path is not None:
        console.print(
            f"[bold green]✓[/bold green] Claudepack saved at "
            f"[bold]{report.claudepack_path}[/bold]"
        )
