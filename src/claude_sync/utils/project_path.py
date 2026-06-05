"""Project path resolution for Claude Code sync.

This module provides utilities to map a local project path to the
corresponding Claude Code project folder name, and to locate that
folder inside ``~/.claude/projects/``.

Claude Code encodes project paths into folder names by:

1. Replacing path separators (``/``, ``\\``) with ``-``.
2. Lower-casing drive letters on Windows (``D:`` → ``d--``).
3. Replacing ``:`` (drive separator on Windows) with ``--``.

Examples
--------
Linux:   /home/user/project   →  -home-user-project
Windows: D:/Project/foo       →  d--Project-foo

The inverse (Claude → local) is not yet implemented — it will be
needed in Phase 4 (Automatic Path Mapping).
"""

from __future__ import annotations

from pathlib import Path


def project_to_claude_folder(project_path: Path) -> str:
    """Convert a local project path to the Claude Code folder name.

    Algorithm (Claude Code's internal convention):

    1. Get the absolute path string.
    2. On Windows, lower-case the drive letter and replace ``:`` with
       ``--`` so that ``D:\\`` becomes ``d--``.
    3. Replace every path separator with ``-``.

    The resulting string starts with ``-`` for absolute paths,
    which matches Claude Code's naming scheme.
    """
    absolute = project_path.resolve()
    text = str(absolute)

    # --- Windows drive letter handling ---
    # Windows paths like `D:\foo` must become `d--foo`.
    # Linux paths have no drive letter, so this block is a no-op.
    drive, rest = None, text
    if len(text) >= 2 and text[1] == ":":
        drive = text[0].lower()
        rest = text[2:]
    if drive is not None:
        # Replace leading backslash or forward-slash after drive letter.
        if rest.startswith(("\\", "/")):
            rest = rest[1:]

    parts: list[str] = []
    if drive:
        parts.append(f"{drive}--")
    # Split on both separators and flatten.
    parts.extend(rest.replace("\\", "/").split("/"))

    return "-".join(parts)


def locate_claude_project(
    claude_path: Path, project_path: Path
) -> Path | None:
    """Find the Claude Code project folder for a given local project.

    Steps:

    1. Compute the expected folder name via ``project_to_claude_folder``.
    2. Check if that folder exists under ``claude_path / projects/``.

    Returns
    -------
    Path | None
        Absolute path to the project folder, or ``None`` if not found.
    """
    folder_name = project_to_claude_folder(project_path)
    projects_dir = claude_path / "projects"
    candidate = projects_dir / folder_name
    if candidate.is_dir():
        return candidate
    return None
