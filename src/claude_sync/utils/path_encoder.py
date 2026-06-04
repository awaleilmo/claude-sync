"""Path encoding / decoding for Claude Code project folder names.

Claude Code encodes absolute paths into folder names by stripping the
leading ``/`` (or drive letter + ``:\\``) and replacing separators with
``-``.  This module provides the inverse operations so that claude-sync
can remap encoded paths when importing from another machine.
"""

from __future__ import annotations

import re
from pathlib import Path


class PathEncoder:
    """Encode and decode the folder-name representation of an absolute path."""

    @staticmethod
    def encode(path: str | Path) -> str:
        """Encode an absolute path into a Claude Code folder name.

        Linux / WSL::

            /home/awal/workspace/app  →  -home-awal-workspace-app

        Windows::

            D:\\projects\\app  →  d--projects-app
        """
        p = str(path)
        # Check for Windows drive letter first (case-insensitive)
        drive_match = re.match(r"^([a-z]):[/\\]", p, re.IGNORECASE)
        if drive_match:
            drive = drive_match.group(1).lower()
            remainder = p[drive_match.end():]  # everything after "X:\" or "X:/"
            return drive + "--" + remainder.replace("\\", "-").replace("/", "-")
        # Linux / WSL: normalise to forward slashes, strip leading /
        p_norm = p.replace("\\", "/")
        if p_norm.startswith("/"):
            p_norm = p_norm.lstrip("/")
        return "-" + p_norm.replace("/", "-")

    @staticmethod
    def decode_parts(encoded: str) -> list[str]:
        """Split an encoded folder name into path components.

        Examples::

            -home-awal-workspace-claude-sync  →  ['home', 'awal', 'workspace', 'claude', 'sync']
            d--projects-claude-sync           →  ['d', '', 'projects', 'claude', 'sync']
        """
        s = encoded
        if s.startswith("-"):
            # For Linux: "-home-awal" -> "home-awal"
            # For Windows: "d--projects" -> "d--projects" (only strip one dash)
            s = s[1:]
        return s.split("-")

    @staticmethod
    def detect_os_from_encoded(encoded: str) -> str:
        """Detect the originating OS from an encoded folder name.

        * Windows: starts with ``<letter>--`` (e.g. ``d--projects``)
        * Linux:   starts with ``-`` but NOT ``<letter>--`` (e.g. ``-home-awal``)

        Returns ``'windows'`` or ``'linux'``.
        """
        if len(encoded) >= 3 and encoded[1] == "-" and encoded[2] == "-" and encoded[0].isalpha():
            return "windows"
        if encoded.startswith("-"):
            return "linux"
        return "windows"  # fallback to Windows heuristic
