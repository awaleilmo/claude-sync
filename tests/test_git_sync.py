"""Tests for `claude_sync.utils.git_sync`."""

from __future__ import annotations

import shutil

from pathlib import Path

import pytest

from claude_sync.utils.git_sync import GitError, GitSync


# Skip the whole module when git isn't installed in the test environment.
pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git executable not available",
)


def _make_initialized(tmp_path: Path) -> Path:
    """Create `.claude-sync/` so GitSync can find a valid working dir."""
    (tmp_path / ".claude-sync").mkdir()
    return tmp_path


def test_init_repo_creates_git_dir(tmp_path: Path) -> None:
    """`init_repo` should make `sync_dir` a real Git repository."""
    root = _make_initialized(tmp_path)
    git = GitSync(project_root=root)

    assert not git.is_repo()
    git.init_repo()

    assert git.is_repo()
    # Bare-minimum layout that Git creates.
    assert (root / ".claude-sync" / ".git").exists()


def test_init_repo_initializes_main_branch_via_init_defaultbranch(tmp_path: Path) -> None:
    """`init -b main` is used so the first commit lands on `main`."""
    root = _make_initialized(tmp_path)
    git = GitSync(project_root=root, branch="main")

    git.init_repo()
    # The repo is now in a state where `main` is the initial branch.
    # We add a commit to verify the branch name resolution works.
    (root / ".claude-sync" / "README.md").write_text("hello\n", encoding="utf-8")
    git.run("add", ".")
    git.run("commit", "-m", "initial")

    status = git.run("branch", "--show-current")
    assert status.stdout.strip() == "main"


def test_run_raises_on_nonzero_exit(tmp_path: Path) -> None:
    """`run` should surface non-zero exit codes as `GitError`."""
    root = _make_initialized(tmp_path)
    git = GitSync(project_root=root)

    with pytest.raises(GitError) as exc_info:
        git.run("this-is-not-a-real-subcommand")
    assert exc_info.value.returncode != 0


def test_is_git_available_returns_bool(tmp_path: Path) -> None:
    """`is_git_available` should return a boolean based on shutil.which."""
    git = GitSync(project_root=tmp_path)
    assert isinstance(git.is_git_available(), bool)


def test_fetch_and_pull_fail_without_remote(tmp_path: Path) -> None:
    """`fetch`/`pull` should raise GitError when no remote is configured."""
    root = _make_initialized(tmp_path)
    git = GitSync(project_root=root)

    git.init_repo()
    # Make a commit so HEAD exists; otherwise `git pull` complains
    # about an unborn branch in addition to the missing remote.
    (root / ".claude-sync" / ".keep").write_text("", encoding="utf-8")
    git.run("add", ".keep")
    git.run("commit", "-m", "initial")

    with pytest.raises(GitError):
        git.fetch()
    with pytest.raises(GitError):
        git.pull()
