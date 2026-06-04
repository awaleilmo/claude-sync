"""Tests for ``claude_sync.utils.path_encoder``."""

from __future__ import annotations

from claude_sync.utils.path_encoder import PathEncoder


# ---------------------------------------------------------------------------
# encode
# ---------------------------------------------------------------------------


def test_encode_linux_path() -> None:
    assert PathEncoder.encode("/home/awal/workspace/claude-sync") == (
        "-home-awal-workspace-claude-sync"
    )


def test_encode_linux_single_segment() -> None:
    assert PathEncoder.encode("/app") == "-app"


def test_encode_linux_double_slash_at_root() -> None:
    assert PathEncoder.encode("//home/user/app") == "-home-user-app"


def test_encode_windows_path() -> None:
    """Windows drive:letter + backslash → letter--rest."""
    assert PathEncoder.encode(r"D:\projects\app") == "d--projects-app"


def test_encode_windows_uppercase_drive() -> None:
    """Drive letter is always lowercased."""
    assert PathEncoder.encode(r"D:\projects\app") == "d--projects-app"
    assert PathEncoder.encode(r"d:\projects\app") == "d--projects-app"


def test_encode_windows_forward_slash() -> None:
    """Windows paths with forward slashes also work."""
    assert PathEncoder.encode("D:/projects/app") == "d--projects-app"


def test_encode_path_object() -> None:
    """Accepts pathlib.Path."""
    from pathlib import Path

    result = PathEncoder.encode(Path("/a/b/c"))
    assert result == "-a-b-c"


# ---------------------------------------------------------------------------
# decode_parts
# ---------------------------------------------------------------------------


def test_decode_linux_parts() -> None:
    """decode_parts splits on -, so 'claude-sync' → ['claude', 'sync']."""
    assert PathEncoder.decode_parts("-home-awal-workspace-claude-sync") == [
        "home",
        "awal",
        "workspace",
        "claude",
        "sync",
    ]


def test_decode_windows_parts() -> None:
    assert PathEncoder.decode_parts("d--projects-claude-sync") == [
        "d",
        "",
        "projects",
        "claude",
        "sync",
    ]


def test_decode_single_component() -> None:
    assert PathEncoder.decode_parts("-app") == ["app"]


# ---------------------------------------------------------------------------
# detect_os_from_encoded
# ---------------------------------------------------------------------------


def test_detect_linux_encoded() -> None:
    assert PathEncoder.detect_os_from_encoded("-home-awal") == "linux"


def test_detect_windows_encoded() -> None:
    assert PathEncoder.detect_os_from_encoded("d--projects") == "windows"


def test_detect_windows_uppercase_drive() -> None:
    assert PathEncoder.detect_os_from_encoded("D--projects") == "windows"
