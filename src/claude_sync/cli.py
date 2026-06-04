"""CLI entry point for claude-sync.

This module wires the subcommands into a single Typer app. The
`console_scripts` entry in `pyproject.toml` points at `claude_sync.cli:app`,
so `claude-sync ...` is dispatched here.
"""

from __future__ import annotations

import typer
from rich.console import Console

from claude_sync import __version__
from claude_sync.commands import export as export_cmd
from claude_sync.commands import import_cmd as import_cmd
from claude_sync.commands import init as init_cmd
from claude_sync.commands import inspect as inspect_cmd
from claude_sync.commands import pull as pull_cmd
from claude_sync.commands import push as push_cmd
from claude_sync.commands import status as status_cmd
from claude_sync.commands import trace as trace_cmd

# Single Typer app shared by all subcommands. `no_args_is_help=True`
# makes `claude-sync` alone print the help screen, which is the
# conventional behavior for well-behaved CLIs.
app = typer.Typer(
    name="claude-sync",
    help="Sync Claude Code sessions across devices using Git.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


def _version_callback(value: bool) -> None:
    """Print version and exit when --version is passed."""
    if value:
        console.print(f"claude-sync [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """claude-sync root command (callback runs before subcommands)."""


# Register subcommands. Each command module exposes a function with
# the same name as the command; we attach it here as a Typer command.
app.command(name="init")(init_cmd.init)
app.command(name="status")(status_cmd.status)
app.command(name="inspect")(inspect_cmd.inspect)
app.command(name="export")(export_cmd.export)
app.command(name="import")(import_cmd.import_cmd)
app.command(name="push")(push_cmd.push)
app.command(name="pull")(pull_cmd.pull)
app.command(name="trace")(trace_cmd.trace)


if __name__ == "__main__":
    # Allow `python -m claude_sync` as a fallback entry point.
    app()
