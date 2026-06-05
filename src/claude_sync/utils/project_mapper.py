"""Automatic project path remapping across machines.

When a project is exported from machine A (Linux) and imported on
machine B (Windows), the encoded folder name will differ even though
the *project name* (last path component) is the same.  This module
implements fuzzy matching so that `claude-sync import` can
automatically rename the ``projects/`` folder on the target machine.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from claude_sync.utils.path_encoder import PathEncoder

SYNC_DIR_NAME = ".claude-sync"
PROJECT_MAP_FILENAME = "project-map.json"


@dataclass
class ProjectMapper:
    """Map encoded project names between two machines.

    Args:
        data_root: Root of the *source* sync project (the one we are
            importing *from*).
        claude_path: Root of the *target* Claude Code directory
            (the one we are importing *into*).
    """

    data_root: Path
    claude_path: Path

    # -- public helpers --

    def get_source_projects(self) -> list[str]:
        """Return encoded folder names inside ``<data_root>/projects/``."""
        projects_dir = self.data_root / "projects"
        if not projects_dir.is_dir():
            return []
        return sorted(
            e.name for e in projects_dir.iterdir() if e.is_dir()
        )

    def get_target_projects(self) -> list[str]:
        """Return encoded folder names inside ``<claude_path>/projects/``."""
        projects_dir = self.claude_path / "projects"
        if not projects_dir.is_dir():
            return []
        return sorted(
            e.name for e in projects_dir.iterdir() if e.is_dir()
        )

    def find_matching_project(self, source_encoded: str) -> str | None:
        """Find the target project that best matches *source_encoded*.

        Strategy 1 — Exact match::

            source: -home-awal-workspace-claude-sync
            target has the same folder? -> return as-is

        Strategy 2 — Suffix match::

            source parts:  ['home', 'awal', 'workspace', 'claude-sync']
            target parts:  ['d', 'projects', 'claude-sync']
            match suffix:  ['claude-sync'] -> project name matches

            If multiple candidates tie on suffix length, pick the one
            with the longest total suffix match.

        Strategy 3 — Manual mapping from ``.claude-sync/project-map.json``.

        Returns ``None`` when no candidate is found.
        """
        target_projects = self.get_target_projects()

        # Strategy 1: exact match
        if source_encoded in target_projects:
            return source_encoded

        # Strategy 2: suffix match (case-insensitive)
        source_parts = PathEncoder.decode_parts(source_encoded)
        source_parts_lower = [p.lower() for p in source_parts]

        best_target: str | None = None
        best_suffix_len = 0

        for target_enc in target_projects:
            # Skip self-matches when source and target dirs are the same
            if target_enc == source_encoded:
                continue

            target_parts = PathEncoder.decode_parts(target_enc)
            target_parts_lower = [p.lower() for p in target_parts]

            # Count matching suffix (case-insensitive)
            match_len = 0
            for s, t in zip(reversed(source_parts_lower), reversed(target_parts_lower)):
                if s == t:
                    match_len += 1
                else:
                    break

            if match_len > best_suffix_len:
                best_suffix_len = match_len
                best_target = target_enc
            elif match_len == best_suffix_len and match_len > 0 and best_target is not None:
                # Tie-break: prefer the candidate with more total parts
                # in the matched suffix
                if match_len > len(PathEncoder.decode_parts(best_target)):
                    best_target = target_enc

        if best_target is not None and best_suffix_len > 0:
            return best_target

        # Strategy 3: manual mapping
        manual = self._load_manual_mapping()
        return manual.get(source_encoded)

    def build_remap_plan(self) -> dict[str, str | None]:
        """Build a full remapping plan.

        Returns::

            { source_encoded: target_encoded | None }

        ``None`` means no partner was found on the target machine.
        """
        source_projects = self.get_source_projects()
        plan: dict[str, str | None] = {}
        for src in source_projects:
            plan[src] = self.find_matching_project(src)
        return plan

    # -- internal helpers --

    def _project_map_path(self) -> Path:
        """Path to ``.claude-sync/project-map.json`` inside the **target**."""
        return self.claude_path / SYNC_DIR_NAME / PROJECT_MAP_FILENAME

    @staticmethod
    def _load_mapping_file(path: Path) -> dict[str, str]:
        """Read a JSON mapping file, returning an empty dict when absent."""
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _load_manual_mapping(self) -> dict[str, str]:
        """Load the manual override map from the target machine."""
        return self._load_mapping_file(self._project_map_path())

    def save_manual_mapping(self, mapping: dict[str, str]) -> None:
        """Persist a manual mapping to ``project-map.json`` on the target."""
        path = self._project_map_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(mapping, indent=2, ensure_ascii=False) + "\n"
        path.write_text(content, encoding="utf-8")
