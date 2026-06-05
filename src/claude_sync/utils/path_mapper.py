"""Map project paths to Claude Code project folder names.

Claude Code stores per-project data inside ``~/.claude/projects/<folder>``
where *folder* is derived from the absolute path of the project on the
local machine.  This module provides the forward mapping
(project-path -> Claude folder) used during export/import.

Mapping rules (Claude Code convention)
-------------------------------------

1. Lowercase the drive letter on Windows (e.g. ``D:`` -> ``d:``).
2. Replace **all** path separators (``\\`` and ``/``) with ``-``.
3. Replace ``:`` with ``--`` (Windows drive letters).

Examples
========

Linux::

    /home/awal/workspace/claude-sync
    -> -home-awal-workspace-claude-sync

Windows::

    D:/Project/claude-sync
    -> d--Project-claude-sync

"""

from __future__ import annotations

from pathlib import Path


def project_to_claude_folder(project_path: Path) -> str:
    """Map a project's absolute path to a Claude Code project folder."""
    p = project_path.resolve()
    text = str(p)

    # Lowercase drive letter on Windows.
    if len(text) >= 2 and text[1] == ":":
        text = text[0].lower() + text[1:]

    # Replace separators with dashes.
    result = text.replace("\\", "-").replace("/", "-")

    # Replace drive-colon with double-dash.
    result = result.replace(":", "--")

    return result
