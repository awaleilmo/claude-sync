"""`claude-sync pull` command.

Pipeline:
    1. Ensure `.claude-sync/` is a Git repo (auto-init when missing).
    2. `git fetch` + `git pull --ff-only` from the remote.
    3. Run `import` to restore data into `~/.claude/`.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from claude_sync.commands.import_cmd import run_import
from claude_sync.utils.config import is_initialized
from claude_sync.utils.git_sync import GitError, GitSync

console = Console()


def _resolve_root(project_root: Path | None) -> Path:
    """Return an absolute project root, defaulting to the current working dir."""
    return project_root if project_root is not None else Path.cwd()


def pull(
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Project root directory. Defaults to the current working directory.",
    ),
    remote: str = typer.Option(
        "origin",
        "--remote",
        "-r",
        help="Remote name to pull from.",
    ),
    branch: str = typer.Option(
        "main",
        "--branch",
        "-b",
        help="Branch name to pull from.",
    ),
    no_import: bool = typer.Option(
        False,
        "--no-import",
        help="Skip the import step (just sync the .claude-sync/ tree).",
    ),
    no_init: bool = typer.Option(
        False,
        "--no-init",
        help="Do not auto-init a Git repo. Fail if none exists.",
    ),
) -> None:
    """Fetch from the remote and import the synced data locally."""
    root = _resolve_root(project_root)

    if not is_initialized(root):
        console.print(
            "[red]✗[/red] Project not initialized. "
            "Run [cyan]claude-sync init[/cyan] first."
        )
        raise typer.Exit(code=1)

    git = GitSync(project_root=root, remote=remote, branch=branch)

    if not git.is_git_available():
        console.print("[red]✗[/red] Git is not installed. Install git and retry.")
        raise typer.Exit(code=1)

    if not git.is_repo():
        if no_init:
            console.print(
                f"[red]✗[/red] {git.sync_dir} is not a Git repo. "
                "Re-run without --no-init."
            )
            raise typer.Exit(code=1)
        console.print(f"[blue]•[/blue] Initializing Git repo in {git.sync_dir.name}/")
        try:
            git.init_repo()
        except GitError as exc:
            console.print(f"[red]✗[/red] git init failed: {exc}")
            raise typer.Exit(code=1)

    if not git.has_remote():
        console.print(
            f"[red]✗[/red] No remote named [bold]{remote}[/bold] is configured.\n"
            f"  Add one with: "
            f"[cyan]git -C {git.sync_dir} remote add {remote} <url>[/cyan]"
        )
        raise typer.Exit(code=1)

    try:
        git.fetch()
    except GitError as exc:
        console.print(f"[red]✗[/red] git fetch failed: {exc}")
        if exc.stderr:
            console.print(f"  {exc.stderr}")
        raise typer.Exit(code=1)

    try:
        git.pull()
    except GitError as exc:
        # `--ff-only` is strict: a non-fast-forward is a normal failure mode
        # (e.g. divergent histories) and we want to surface it clearly.
        console.print(f"[red]✗[/red] git pull failed: {exc}")
        if exc.stderr:
            console.print(f"  {exc.stderr}")
        raise typer.Exit(code=1)

    if not no_import:
        run_import(project_root=root)

    console.print(
        f"[bold green]✓[/bold green] Pulled from [cyan]{remote}/{branch}[/cyan] "
        "and restored data."
    )
