"""`claude-sync import` command.

Restores only the current project\'s Claude Code data from
``.claude-sync/export/project/<folder>/`` into
``~/.claude/projects/<current-project-folder>/``.

Phase 3 (Project-Based Import):

* No longer restores the entire ``~/.claude`` directory.
* Only the current project folder is restored.
* Backup is per-project (not the whole ``~/.claude``).
* Other projects in ``~/.claude/projects/`` are never touched.

Safety validations (abort before any restore if any fail):

* ``project.json`` exists.
* Export folder exists.
* Claude path exists.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_sync.utils.claude_locator import ClaudeLocator
from claude_sync.utils.config import get_manifest_path, is_initialized, read_manifest
from claude_sync.utils.importer import ProjectImporter
from claude_sync.utils.project_identity import (
    get_project_metadata_path,
    read_project_metadata,
)
from claude_sync.utils.project_path import project_to_claude_folder

console = Console()


def _resolve_root(project_root: Path | None) -> Path:
    """Default to cwd; resolve at call time so chdir-based tests work."""
    return project_root if project_root is not None else Path.cwd()


def run_import(
    project_root: Path | None = None,
    claude_path: Path | None = None,
    no_backup: bool = False,
) -> None:
    """Programmatic entry point used by `pull` and other callers."""
    import_cmd(
        project_root=project_root,
        claude_path=claude_path,
        no_backup=no_backup,
    )


def import_cmd(  # noqa: A001
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
            "Override the Claude directory. By default we "
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
    """Import Claude Code data for the current project."""
    root = _resolve_root(project_root)

    if not is_initialized(root):
        console.print("[red]\u2717[/red] Project not initialized")
        console.print("  Run [cyan]claude-sync init[/cyan] first.")
        raise typer.Exit(code=1)

    # --- Safety validations ---
    meta_path = get_project_metadata_path(root)
    meta = read_project_metadata(meta_path)
    if meta is None:
        console.print("[red]\u2717[/red] project.json not found")
        console.print("  Run [cyan]claude-sync init[/cyan] first.")
        raise typer.Exit(code=1)

    # Resolve Claude path first (needed before export check)
    if claude_path is None:
        claude_path = ClaudeLocator().find_claude_path()
    if claude_path is None:
        console.print("[red]\u2717[/red] Claude Path: Not Found")
        console.print("  Pass [cyan]--claude-path[/cyan] to specify a destination.")
        raise typer.Exit(code=1)

    # Phase 5 Part 2: Check for .claudepack ZIP first
    from claude_sync.utils.exporter import CLAUDEPACK_FILENAME

    claudepack_file = root / ".claude-sync" / CLAUDEPACK_FILENAME
    use_claudepack = claudepack_file.is_file()

    # Validate .claudepack if it exists
    if use_claudepack:
        importer = ProjectImporter(
            claude_path=claude_path,
            project_root=root,
            local_project_path=local_project_path,
        )
        try:
            if not importer.has_claudepack():
                console.print(
                    f"[red]\u2717[/red] Corrupt .claudepack: {claudepack_file}"
                )
                console.print(
                    "  The file may be damaged. Please re-export."
                )
                raise typer.Exit(code=1)
        except ValueError as exc:
            console.print(f"[red]\u2717[/red] {exc}")
            raise typer.Exit(code=1)
        console.print(
            f"[cyan]![/cyan] Using .claudepack format: {CLAUDEPACK_FILENAME}"
        )
    else:
        # Fallback: check folder export
        export_root = root / ".claude-sync" / "export" / "project"
        if not export_root.is_dir():
            console.print(
                f"[yellow]![/yellow] No export data found: {export_root}"
            )
            console.print("  Run [cyan]claude-sync export[/cyan] first.")
            raise typer.Exit(code=1)
        console.print(
            "[cyan]![/cyan] Using legacy folder format"
        )

    # --- Phase 4: Validation warning (do not abort) ---

    # --- Phase 4: Validation warning (do not abort) ---
    # If the project_name in project.json doesn't match the current
    # machine's computed Claude folder name, warn the user but still
    # proceed with the import.
    local_path_for_validation = (
        local_project_path if local_project_path is not None else root.resolve()
    )
    current_claude_folder = project_to_claude_folder(local_path_for_validation)
    if meta.project_name and meta.project_name != current_claude_folder:
        console.print(
            f"[yellow]![/yellow] Mapping Mismatch: project.json says "
            f"[bold]{meta.project_name}[/bold] but current folder is "
            f"[bold]{current_claude_folder}[/bold]."
        )
        console.print(
            "  [yellow]Importing anyway. "
            "Data will be restored using the current folder name.[/yellow]"
        )
        console.print()

    # Also surface any source vs current difference recorded in the manifest.
    manifest_path = get_manifest_path(root)
    if manifest_path.is_file():
        manifest_data = read_manifest(root) or {}
        source_folder = manifest_data.get("source_claude_project_folder")
        if source_folder and source_folder != current_claude_folder:
            console.print(
                f"[yellow]![/yellow] Source folder "
                f"[bold]{source_folder}[/bold] differs from current "
                f"[bold]{current_claude_folder}[/bold]. "
                "Data will be restored under the current folder name."
            )
            console.print()

    # Create importer (reused for format check above and for import)
    importer = ProjectImporter(
        claude_path=claude_path,
        project_root=root,
        local_project_path=local_project_path,
    )
    report = importer.import_data(backup=not no_backup)

    # --- Output ---
    if report.file_count == 0 and not report.claude_project_folder:
        console.print(
            f"[yellow]![/yellow] Nothing to import: {report.data_root} does not exist or is empty."
        )
        console.print("  Run [cyan]claude-sync export[/cyan] first.")
        raise typer.Exit(code=1)

    source_label = "ZIP (.claudepack)" if report.source_type == "claudepack" else "folder"
    console.print(
        f"[bold]Source type:[/bold]          {source_label}\n"
        f"[bold]Importing from:[/bold]     {report.data_root}\n"
        f"[bold]Claude project folder:[/bold] {report.claude_project_folder}\n"
        f"[bold]Importing to:[/bold]       {report.target_project_path}\n"
    )

    if report.backup_path is not None:
        console.print(
            f"[green]\u2713[/green] Backup created: [bold]{report.backup_path}[/bold]\n"
        )

    table = Table(
        title="Import Summary",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Claude project folder", report.claude_project_folder)
    table.add_row("Files restored", str(report.file_count))
    table.add_row(
        "Backup",
        str(report.backup_path) if report.backup_path else "N/A",
    )

    console.print(table)
    console.print(
        f"\n[bold green]\u2713[/bold green] Imported {report.file_count} files "
        f"into [bold]projects/{report.claude_project_folder}/[/bold]"
    )

    # ---- Tahap 7C: Project Path Remapping table ----
    if report.remapped_projects or report.unmatched_projects:
        console.print("\n[bold]Project Path Remapping[/bold]")
        remap_table = Table(show_header=True, header_style="bold cyan")
        remap_table.add_column("Source (exported)", style="bold")
        remap_table.add_column("Target (this machine)", justify="right")
        remap_table.add_column("Status", justify="center")

        # Show remapped projects first
        for source_enc, target_enc in sorted(report.remapped_projects.items()):
            if source_enc != target_enc:
                remap_table.add_row(
                    source_enc,
                    target_enc,
                    "[green]remapped[/green]",
                )

        # Show unmatched projects
        for source_enc in sorted(report.unmatched_projects):
            remap_table.add_row(
                source_enc,
                "(not found)",
                "[yellow]kept as-is[/yellow]",
            )

        console.print(remap_table)
