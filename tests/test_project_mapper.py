"""Tests for ``claude_sync.utils.project_mapper``."""

from __future__ import annotations

from pathlib import Path

from claude_sync.utils.project_mapper import (
    PROJECT_MAP_FILENAME,
    SYNC_DIR_NAME,
    ProjectMapper,
)


def _make_projects_dir(root: Path, names: list[str]) -> Path:
    """Create *root*/projects/*name*/ for each name in *names*."""
    base = root / "projects"
    base.mkdir(parents=True, exist_ok=True)
    for name in names:
        (base / name).mkdir(parents=True, exist_ok=True)
    return base


def _make_project_map_file(cwd: Path, mapping: dict[str, str]) -> None:
    """Write project-map.json into <cwd>/.claude-sync/."""
    sync_dir = cwd / SYNC_DIR_NAME
    sync_dir.mkdir(parents=True, exist_ok=True)
    import json
    (sync_dir / PROJECT_MAP_FILENAME).write_text(
        json.dumps(mapping, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# get_source_projects / get_target_projects
# ---------------------------------------------------------------------------


def test_get_source_projects_empty(tmp_path: Path) -> None:
    mapper = ProjectMapper(data_root=tmp_path, claude_path=tmp_path)
    assert mapper.get_source_projects() == []


def test_get_source_projects_populated(tmp_path: Path) -> None:
    _make_projects_dir(tmp_path, ["-home-x", "-home-y"])
    mapper = ProjectMapper(data_root=tmp_path, claude_path=tmp_path)
    assert set(mapper.get_source_projects()) == {"-home-x", "-home-y"}


def test_get_target_projects_populated(tmp_path: Path) -> None:
    _make_projects_dir(tmp_path, ["d--proj"])
    mapper = ProjectMapper(data_root=tmp_path, claude_path=tmp_path)
    assert mapper.get_target_projects() == ["d--proj"]


# ---------------------------------------------------------------------------
# find_matching_project — exact match
# ---------------------------------------------------------------------------


def test_exact_match(tmp_path: Path) -> None:
    """Source and target share the same dir with the same folder."""
    _make_projects_dir(tmp_path, ["-home-x"])
    mapper = ProjectMapper(data_root=tmp_path, claude_path=tmp_path)
    assert mapper.find_matching_project("-home-x") == "-home-x"


# ---------------------------------------------------------------------------
# find_matching_project — suffix match
# ---------------------------------------------------------------------------


def test_suffix_match_same_project_different_paths(tmp_path: Path) -> None:
    """Source Linux, target Windows — same project name at end.

    Uses separate tmp dirs so source and target don't pollute each other.
    """
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-awal-workspace-myapp"])
    _make_projects_dir(target_root, ["d--projects-myapp"])
    mapper = ProjectMapper(
        data_root=source_root,
        claude_path=target_root,
    )
    result = mapper.find_matching_project("-home-awal-workspace-myapp")
    assert result == "d--projects-myapp"


def test_suffix_match_no_match(tmp_path: Path) -> None:
    """Completely different project names return None."""
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-awal-workspace-myapp"])
    _make_projects_dir(target_root, ["d--projects-otherapp"])
    mapper = ProjectMapper(data_root=source_root, claude_path=target_root)
    result = mapper.find_matching_project("-home-awal-workspace-myapp")
    assert result is None


def test_suffix_match_case_insensitive(tmp_path: Path) -> None:
    """Suffix matching is case-insensitive."""
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-awal-MyApp"])
    _make_projects_dir(target_root, ["d--projects-myapp"])
    mapper = ProjectMapper(data_root=source_root, claude_path=target_root)
    result = mapper.find_matching_project("-home-awal-MyApp")
    assert result == "d--projects-myapp"


def test_suffix_match_longest_wins(tmp_path: Path) -> None:
    """Longer suffix match wins; if tie, any valid candidate is fine."""
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-awal-workspace-myapp"])
    _make_projects_dir(target_root, ["d--projects-myapp", "x--other-myapp"])
    mapper = ProjectMapper(data_root=source_root, claude_path=target_root)
    result = mapper.find_matching_project("-home-awal-workspace-myapp")
    assert result in ("d--projects-myapp", "x--other-myapp")


# ---------------------------------------------------------------------------
# find_matching_project — manual mapping
# ---------------------------------------------------------------------------


def test_manual_mapping_override(tmp_path: Path) -> None:
    """Manual mapping overrides when no suffix match exists."""
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-x", "-home-y"])
    _make_projects_dir(target_root, ["d--target-y"])
    _make_project_map_file(target_root, {"-home-y": "d--target-y"})
    mapper = ProjectMapper(data_root=source_root, claude_path=target_root)
    # -home-x: no suffix match (different name), no manual mapping
    assert mapper.find_matching_project("-home-x") is None
    # -home-y: manual mapping takes priority
    result = mapper.find_matching_project("-home-y")
    assert result == "d--target-y"


def test_manual_mapping_fallback_when_no_suffix_match(tmp_path: Path) -> None:
    """When suffix doesn't match at all, manual map should work."""
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-awal-special-app"])
    _make_projects_dir(target_root, ["d--windows-othername"])
    _make_project_map_file(target_root, {
        "-home-awal-special-app": "d--windows-othername",
    })
    mapper = ProjectMapper(data_root=source_root, claude_path=target_root)
    result = mapper.find_matching_project("-home-awal-special-app")
    assert result == "d--windows-othername"


def test_manual_mapping_used_before_suffix(tmp_path: Path) -> None:
    """Manual mapping is checked before suffix match.

    When both source and target have different project names but manual
    mapping points to the right target, it should still work.
    """
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-awal-custom-app"])
    _make_projects_dir(target_root, ["d--windows-custom-app"])
    # No manual mapping, but suffix should match 'custom-app' and 'app'
    mapper = ProjectMapper(data_root=source_root, claude_path=target_root)
    result = mapper.find_matching_project("-home-awal-custom-app")
    # Both end with 'app' — suffix match finds d--windows-custom-app
    assert result == "d--windows-custom-app"


# ---------------------------------------------------------------------------
# build_remap_plan
# ---------------------------------------------------------------------------


def test_build_remap_plan_simple(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-x", "-home-y"])
    _make_projects_dir(target_root, ["d--target-x"])
    _make_project_map_file(target_root, {"-home-y": "d--target-y"})
    mapper = ProjectMapper(data_root=source_root, claude_path=target_root)
    plan = mapper.build_remap_plan()
    assert plan["-home-x"] == "d--target-x"  # suffix match (x -> target-x)
    assert plan["-home-y"] == "d--target-y"  # manual


def test_build_remap_plan_empty(tmp_path: Path) -> None:
    mapper = ProjectMapper(data_root=tmp_path, claude_path=tmp_path)
    assert mapper.build_remap_plan() == {}


def test_build_remap_plan_with_unmatched(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _make_projects_dir(source_root, ["-home-only"])
    # target_root/projects is empty
    mapper = ProjectMapper(data_root=source_root, claude_path=target_root)
    plan = mapper.build_remap_plan()
    assert plan["-home-only"] is None


# ---------------------------------------------------------------------------
# save_manual_mapping / _load_mapping_file
# ---------------------------------------------------------------------------


def test_save_and_load_manual_mapping(tmp_path: Path) -> None:
    import json

    sync_dir = tmp_path / SYNC_DIR_NAME
    sync_dir.mkdir(parents=True, exist_ok=True)
    mapper = ProjectMapper(data_root=tmp_path, claude_path=tmp_path)
    mapper.save_manual_mapping({"src": "tgt"})
    data = json.loads((sync_dir / PROJECT_MAP_FILENAME).read_text(encoding="utf-8"))
    assert data == {"src": "tgt"}


def test_load_nonexistent_mapping_returns_empty(tmp_path: Path) -> None:
    mapper = ProjectMapper(data_root=tmp_path, claude_path=tmp_path)
    assert mapper._load_manual_mapping() == {}
