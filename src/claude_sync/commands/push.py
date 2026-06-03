"""`claude-sync push` command.

Pipeline:
    1. Run `export` (unless `--no-export`).
    2. Ensure `.claude-sync/` is a Git repo (auto-init on first push).
    3. `git add` + `git commit` the changes.
    4. `git push` to the configured remote/branch (defaults: `origin`/`main`).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from claude_sync.commands.export import run_export
from claude_sync.utils.config import is_initialized
from claude_sync.utils.git_sync import GitError, GitSync

console = Console()

DEFAULT_COMMIT_PREFIX = "chore(sync): update claude data"


def _resolve_root(project_root: Path | None) -> Path:
    """Return an absolute project root, defaulting to the current working dir."""
    return project_root if project_root is not None else Path.cwd()


def _default_message() -> str:
    """Build a deterministic-ish commit message with a UTC timestamp."""
    return f"{DEFAULT_COMMIT_PREFIX} @ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}"


def push(
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Project root directory. Defaults to the current working directory.",
    ),
    message: str = typer.Option(
        None,
        "--message",
        "-m",
        help="Commit message. Defaults to a timestamped sync message.",
    ),
    remote: str = typer.Option(
        "origin",
        "--remote",
        "-r",
        help="Remote name to push to.",
    ),
    branch: str = typer.Option(
        "main",
        "--branch",
        "-b",
        help="Branch name to push to.",
    ),
    no_export: bool = typer.Option(
        False,
        "--no-export",
        help="Skip the export step (use existing data in .claude-sync/).",
    ),
    no_init: bool = typer.Option(
        False,
        "--no-init",
        help="Do not auto-init a Git repo. Fail if none exists.",
    ),
    skip_empty: bool = typer.Option(
        True,
        "--skip-empty/--no-skip-empty",
        help="If there are no changes, exit 0 without creating a commit.",
    ),
) -> None:
    """Export Claude data, commit it, and push to the remote."""
    root = _resolve_root(project_root)

    if not is_initialized(root):
        console.print(
            "[red]✗[/red] Project not initialized. "
            "Run [cyan]claude-sync init[/cyan] first."
        )
        raise typer.Exit(code=1)

    if not no_export:
        # `run_export` already prints a summary; we just trust it.
        run_export(project_root=root)

    git = GitSync(project_root=root, remote=remote, branch=branch)

    if not git.is_git_available():
        console.print("[red]✗[/red] Git is not installed. Install git and retry.")
        raise typer.Exit(code=1)

    if not git.is_repo():
        if no_init:
            console.print(
                f"[red]✗[/red] {git.sync_dir} is not a Git repo. "
                "Re-run without --no-init, or run `git init` manually."
            )
            raise typer.Exit(code=1)
        console.print(f"[blue]•[/blue] Initializing Git repo in {git.sync_dir.name}/")
        try:
            git.init_repo()
        except GitError as exc:
            console.print(f"[red]✗[/red] git init failed: {exc}")
            if exc.stderr:
                console.print(f"  {exc.stderr}")
            raise typer.Exit(code=1)

    if not git.has_remote():
        console.print(
            f"[red]✗[/red] No remote named [bold]{remote}[/bold] is configured.\n"
            f"  Add one with: "
            f"[cyan]git -C {git.sync_dir} remote add {remote} <url>[/cyan]"
        )
        raise typer.Exit(code=1)

    if skip_empty and not git.has_uncommitted_changes():
        console.print(
            "[yellow]•[/yellow] No changes to commit; skipping push "
            "(use --no-skip-empty to override)."
        )
        raise typer.Exit(code=0)

    try:
        git.add()
    except GitError as exc:
        console.print(f"[red]✗[/red] git add failed: {exc}")
        if exc.stderr:
            console.print(f"  {exc.stderr}")
        raise typer.Exit(code=1)

    commit_message = message or _default_message()
    try:
        git.commit(commit_message)
    except GitError as exc:
        # "nothing to commit" is informational, not fatal: surface and stop.
        console.print(f"[yellow]•[/yellow] {exc.stderr or exc}")
        raise typer.Exit(code=0)

    try:
        git.push()
    except GitError as exc:
        console.print(f"[red]✗[/red] git push failed: {exc}")
        if exc.stderr:
            console.print(f"  {exc.stderr}")
        raise typer.Exit(code=1)

    console.print(
        f"[bold green]✓[/bold green] Pushed to [cyan]{remote}/{branch}[/cyan]"
    )
