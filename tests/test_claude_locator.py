"""Tests for `claude_sync.utils.claude_locator`."""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_sync.utils.claude_locator import (
    CLAUDE_DIR_NAME,
    ClaudeLocator,
    _is_wsl,
    _linux_candidate,
    _windows_candidate,
)


# ---------------------------------------------------------------------------
# Candidate resolvers
# ---------------------------------------------------------------------------


def test_linux_candidate_uses_home_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Linux resolver should expand $HOME and append `.claude`."""
    monkeypatch.setenv("HOME", str(tmp_path))
    assert _linux_candidate() == tmp_path / CLAUDE_DIR_NAME


def test_linux_candidate_returns_none_when_home_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unset $HOME must not crash; it should yield None."""
    monkeypatch.delenv("HOME", raising=False)
    assert _linux_candidate() is None


def test_windows_candidate_prefers_userprofile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """USERPROFILE wins over HOME on Windows."""
    other = tmp_path / "home-fallback"
    other.mkdir()
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(other))
    assert _windows_candidate() == tmp_path / CLAUDE_DIR_NAME


def test_windows_candidate_falls_back_to_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Without USERPROFILE, HOME is the fallback (MSYS / Git Bash)."""
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert _windows_candidate() == tmp_path / CLAUDE_DIR_NAME


def test_windows_candidate_returns_none_when_neither_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No USERPROFILE and no HOME -> None, no exception."""
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.delenv("HOME", raising=False)
    assert _windows_candidate() is None


# ---------------------------------------------------------------------------
# ClaudeLocator
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_claude_dir(tmp_path: Path) -> Path:
    """Create a fake `.claude` directory for the locator to find."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "sessions").mkdir()
    return claude_dir


def test_find_claude_path_returns_existing_directory(
    monkeypatch: pytest.MonkeyPatch, fake_claude_dir: Path
) -> None:
    """If $HOME/.claude exists, return it as an absolute path."""
    monkeypatch.setenv("HOME", str(fake_claude_dir.parent))
    # Force the linux resolver to be used regardless of host platform.
    monkeypatch.setattr(ClaudeLocator, "resolvers", {"linux": _linux_candidate})

    locator = ClaudeLocator()
    found = locator.find_claude_path()

    assert found == fake_claude_dir
    assert found is not None
    assert found.is_dir()


def test_find_claude_path_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If the candidate path does not exist, return None."""
    # HOME points somewhere with no `.claude` subdir.
    empty_home = tmp_path / "empty-home"
    empty_home.mkdir()
    monkeypatch.setenv("HOME", str(empty_home))
    monkeypatch.setattr(ClaudeLocator, "resolvers", {"linux": _linux_candidate})

    locator = ClaudeLocator()
    assert locator.find_claude_path() is None
    assert locator.exists() is False


def test_locator_uses_darwin_resolver_on_macos(
    monkeypatch: pytest.MonkeyPatch, fake_claude_dir: Path
) -> None:
    """macOS (Darwin) should reuse the linux-style $HOME layout."""
    monkeypatch.setenv("HOME", str(fake_claude_dir.parent))
    monkeypatch.setattr(
        ClaudeLocator,
        "resolvers",
        {"linux": _linux_candidate, "darwin": _linux_candidate},
    )
    monkeypatch.setattr("claude_sync.utils.claude_locator.platform.system", lambda: "Darwin")

    locator = ClaudeLocator()
    assert locator.find_claude_path() == fake_claude_dir


def test_locator_falls_back_to_linux_on_unknown_platform(
    monkeypatch: pytest.MonkeyPatch, fake_claude_dir: Path
) -> None:
    """On an unrecognised platform we still try the $HOME layout."""
    monkeypatch.setenv("HOME", str(fake_claude_dir.parent))
    monkeypatch.setattr(ClaudeLocator, "resolvers", {})  # no resolvers at all
    monkeypatch.setattr("claude_sync.utils.claude_locator.platform.system", lambda: "Plan9")

    locator = ClaudeLocator()
    assert locator.find_claude_path() == fake_claude_dir


def test_locator_uses_windows_resolver_on_windows(
    monkeypatch: pytest.MonkeyPatch, fake_claude_dir: Path
) -> None:
    """When platform.system() reports Windows, the windows resolver wins."""
    monkeypatch.setenv("USERPROFILE", str(fake_claude_dir.parent))
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.setattr(ClaudeLocator, "resolvers", {"windows": _windows_candidate})
    monkeypatch.setattr(
        "claude_sync.utils.claude_locator.platform.system", lambda: "Windows"
    )

    locator = ClaudeLocator()
    assert locator.find_claude_path() == fake_claude_dir


def test_locator_wsl_detection_returns_bool(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`_is_wsl` returns a bool and never raises.

    The exact value depends on the host running the tests, so we only
    assert that the function returns a bool without crashing.
    """
    result = _is_wsl()
    assert isinstance(result, bool)
