"""Git integration helpers for claude-sync.

This module wraps `git` subprocess calls into a small, testable API.
All commands run in the project root by default; the remote and
branch are configurable.
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

# Sentinel exit code used by tests and callers to detect a clean run.
EXIT_OK = 0


class GitError(RuntimeError):
    """Raised when a Git command fails or is not available.

    The original subprocess output is preserved on `stderr` for callers
    that want to surface it to the user.
    """

    def __init__(self, message: str, *, returncode: int, stderr: str = "") -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


@dataclass(frozen=True)
class GitResult:
    """A successful Git command result.

    Attributes:
        returncode: Process exit code (always 0 for a successful result).
        stdout: Captured standard output, stripped of trailing whitespace.
        stderr: Captured standard error, stripped of trailing whitespace.
        command: The exact argv list that was executed.
    """

    returncode: int
    stdout: str
    stderr: str
    command: Sequence[str]

    @property
    def first_line(self) -> str:
        """Return the first non-empty line of stdout, or '' if none."""
        for line in self.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
        return ""


def _resolve_root(project_root: Path | None) -> Path:
    """Return an absolute project root, defaulting to the current working dir.

    Like other modules, we resolve cwd at call time (not import time) so
    tests that use `monkeypatch.chdir` see the right path.
    """
    root = project_root if project_root is not None else Path.cwd()
    return root.resolve()


def _run(args: Sequence[str], *, cwd: Path, check: bool = True) -> GitResult:
    """Run a git subprocess and return a `GitResult`.

    Args:
        args: Argv list **without** the leading `"git"`, e.g.
            `["status", "--porcelain"]` or `["rev-parse", "--abbrev-ref", "HEAD"]`.
        cwd: Working directory for the command.
        check: If True, raise `GitError` on non-zero exit. If False, return
            the result regardless of exit code (used for read-only probes
            like `git status`).

    Raises:
        GitError: When `check=True` and the command exits non-zero, or when
            the `git` binary is missing.
    """
    argv = ("git", *args)
    try:
        proc = subprocess.run(
            list(argv),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitError(
            "Git is not installed or not on PATH. Install git and retry.",
            returncode=127,
        ) from exc

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    if check and proc.returncode != 0:
        # Quote args so the user can paste them verbatim into a shell.
        quoted = " ".join(shlex.quote(part) for part in args)
        raise GitError(
            f"Git command failed (exit {proc.returncode}): {quoted}",
            returncode=proc.returncode,
            stderr=stderr,
        )

    return GitResult(
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        command=tuple(args),
    )


class GitSync:
    """High-level wrapper for the Git operations claude-sync needs.

    All methods are stateless except for the configured root/remote/branch.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        *,
        remote: str = "origin",
        branch: str = "main",
        sync_dir: Path | None = None,
    ) -> None:
        self.root = _resolve_root(project_root)
        # Backward-compat alias: some callers/tests construct via the
        # keyword `project_root=...` and expect to read it back.
        self.project_root = self.root
        self.remote = remote
        self.branch = branch
        # The directory we treat as the "repo" for git operations. By
        # default this is `.claude-sync/` so commits only track sync data,
        # not the entire project.
        self.sync_dir = (sync_dir or (self.root / ".claude-sync")).resolve()

    # ---- Introspection -------------------------------------------------

    def is_git_available(self) -> bool:
        """Return True if the `git` binary is on PATH and runnable."""
        try:
            self._run(["--version"], cwd=self.root, check=True)
        except GitError:
            return False
        return True

    def is_repo(self) -> bool:
        """Return True if `sync_dir` is inside a Git working tree."""
        result = self._run(
            ["rev-parse", "--is-inside-work-tree"],
            cwd=self.sync_dir,
            check=False,
        )
        return result.returncode == 0 and result.stdout == "true"

    def has_remote(self, name: str | None = None) -> bool:
        """Return True if the named remote is configured (default: `origin`)."""
        remote_name = name or self.remote
        result = self._run(
            ["remote", "get-url", remote_name],
            cwd=self.sync_dir,
            check=False,
        )
        return result.returncode == 0

    def has_uncommitted_changes(self) -> bool:
        """Return True if there are staged/unstaged/untracked changes.

        Uses `git status --porcelain`; non-empty output means dirty.
        """
        result = self._run(
            ["status", "--porcelain"],
            cwd=self.sync_dir,
            check=True,
        )
        return bool(result.stdout)

    # ---- Mutating operations -------------------------------------------

    def init_repo(self) -> GitResult:
        """Initialize a new Git repository in `sync_dir`.

        No-op (still returns a result) if the directory is already a repo.
        """
        if self.is_repo():
            # Re-run a tiny command just to give callers a consistent result.
            return self._run(
                ["rev-parse", "--is-inside-work-tree"],
                cwd=self.sync_dir,
                check=True,
            )
        return self._run(
            ["init", "--initial-branch", self.branch],
            cwd=self.sync_dir,
            check=True,
        )

    def add(self, paths: Sequence[str] = (".",)) -> GitResult:
        """Stage one or more paths. Defaults to staging the whole sync dir."""
        return self._run(
            ["add", "--", *paths],
            cwd=self.sync_dir,
            check=True,
        )

    def commit(self, message: str) -> GitResult:
        """Create a commit. Fails (no-op exit) if nothing is staged."""
        # `--allow-empty` would mask a "nothing to commit" bug, so we
        # intentionally do not pass it. The error message from Git is
        # clear enough for users.
        return self._run(
            ["commit", "-m", message],
            cwd=self.sync_dir,
            check=True,
        )

    def push(
        self,
        *,
        remote: str | None = None,
        branch: str | None = None,
        set_upstream: bool = True,
    ) -> GitResult:
        """Push the current branch to the remote.

        On the first push we pass `-u` so the upstream is configured.
        """
        remote_name = remote or self.remote
        branch_name = branch or self.branch
        args = ["push"]
        if set_upstream:
            args.append("-u")
        args += [remote_name, branch_name]
        return self._run(args, cwd=self.sync_dir, check=True)

    def pull(
        self,
        *,
        remote: str | None = None,
        branch: str | None = None,
    ) -> GitResult:
        """Fetch and fast-forward the configured branch from the remote."""
        remote_name = remote or self.remote
        branch_name = branch or self.branch
        return self._run(
            ["pull", "--ff-only", remote_name, branch_name],
            cwd=self.sync_dir,
            check=True,
        )

    def fetch(
        self,
        *,
        remote: str | None = None,
    ) -> GitResult:
        """Fetch from the remote without merging."""
        remote_name = remote or self.remote
        return self._run(
            ["fetch", remote_name],
            cwd=self.sync_dir,
            check=True,
        )

    # ---- Internals -----------------------------------------------------

    def run(self, *args: str, check: bool = True) -> GitResult:
        """Public alias for the internal `_run` helper.

        Exposes a single positional API (`git.run("add", ".")`) suitable
        for ad-hoc test scaffolding and ad-hoc scripts. The rest of the
        codebase should still use the named methods (add, commit, etc.)
        which provide more specific error reporting.

        Runs in `self.sync_dir` (typically `.claude-sync/`) — that is the
        directory we initialize as the Git repo, so the project root
        itself is *not* the right cwd.
        """
        return self._run(list(args), cwd=self.sync_dir, check=check)

    def _run(self, args: Sequence[str], *, cwd: Path, check: bool) -> GitResult:
        """Thin wrapper kept here so the public API stays self-contained.

        Delegates to the module-level `_run` helper; exists so tests
        subclassing `GitSync` can override it without touching globals.
        """
        return _run(args, cwd=cwd, check=check)
