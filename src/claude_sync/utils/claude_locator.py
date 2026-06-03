"""Locate the Claude Code configuration directory across platforms.

The directory we look for is the one Claude Code uses to store its
runtime data: sessions, projects, tasks, plans, session-env, etc.
By convention on every supported platform it is a folder named
`.claude` inside the user's home directory.

Search order (first match wins):

1. Linux    — ``$HOME/.claude`` (also covers WSL)
2. Windows  — ``%USERPROFILE%\\.claude``

The result is whatever the OS actually uses; we do not silently
substitute one for the other, since syncing the wrong one would
mangle the user's data.
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Callable

# Folder name used by Claude Code on every supported platform.
CLAUDE_DIR_NAME = ".claude"


class ClaudeLocator:
    """Resolve the path to the user's Claude Code configuration directory.

    The locator is intentionally side-effect free: it does not read or
    mutate the filesystem beyond checking `is_dir()`. A `None` return
    value from `find_claude_path()` means "Claude Code is not installed
    (or has never been run) on this machine".
    """

    # Pluggable platform resolvers. The dict is keyed by
    # `platform.system()` (lowercased) and holds a function that
    # returns the candidate path or `None`. Exposed as a class
    # attribute so tests can override individual entries without
    # having to subclass the whole locator.
    resolvers: dict[str, Callable[[], Path | None]] = {}

    def __init__(self) -> None:
        # Lazily populate the default resolver table on first use so
        # tests that override `resolvers` are not clobbered.
        if not ClaudeLocator.resolvers:
            ClaudeLocator.resolvers = {
                "linux": _linux_candidate,
                "darwin": _linux_candidate,  # macOS uses the same layout
                "windows": _windows_candidate,
            }

    def find_claude_path(self) -> Path | None:
        """Return the absolute path to the Claude config directory, or None.

        Returns:
            The path to `.claude` if it exists and is a directory.
            `None` if the directory cannot be found on the current system.
        """
        system = platform.system().lower()
        resolver = ClaudeLocator.resolvers.get(system)

        # Unknown platforms: try the Linux layout as a best effort
        # (e.g. FreeBSD, other Unixes with $HOME semantics).
        if resolver is None:
            resolver = _linux_candidate

        candidate = resolver()
        if candidate is not None and candidate.is_dir():
            return candidate
        return None

    # Convenience aliases mirroring the same data in different forms.

    def exists(self) -> bool:
        """Return True if the Claude config directory is present."""
        return self.find_claude_path() is not None

    def is_wsl(self) -> bool:
        """Return True when running inside Windows Subsystem for Linux."""
        return _is_wsl()


# ---------------------------------------------------------------------------
# Platform-specific candidate resolvers
# ---------------------------------------------------------------------------


def _linux_candidate() -> Path | None:
    """Resolve `$HOME/.claude`, returning None if `$HOME` is unset."""
    home = os.environ.get("HOME")
    if not home:
        return None
    return Path(home) / CLAUDE_DIR_NAME


def _windows_candidate() -> Path | None:
    """Resolve `%USERPROFILE%/.claude` (or `%HOME%` as a fallback)."""
    # On Windows, the user profile is conventionally exposed via
    # USERPROFILE. Some shells (MSYS, Git Bash) also export HOME,
    # so we accept either — preferring USERPROFILE for fidelity.
    profile = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not profile:
        return None
    return Path(profile) / CLAUDE_DIR_NAME


def _is_wsl() -> bool:
    """Heuristically detect WSL by looking at /proc/version."""
    if not sys.platform.startswith("linux"):
        return False
    try:
        proc_version = Path("/proc/version").read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "microsoft" in proc_version.lower() or "wsl" in proc_version.lower()
