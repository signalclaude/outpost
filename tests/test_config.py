"""Tests for outpost config module."""

import json
from pathlib import Path
from unittest.mock import patch

from outpost.config import (
    CORE_SCOPES,
    DEFAULT_CONFIG,
    FEATURE_SCOPES,
    GRAPH_BASE_URL,
    GRAPH_SCOPES,
    clean_workspace,
    get_active_scopes,
    get_config_dir,
    get_profile,
    get_workspace_dir,
    is_feature_enabled,
    load_config,
    save_config,
    set_profile,
)


def test_graph_constants():
    assert GRAPH_BASE_URL == "https://graph.microsoft.com/v1.0"
    assert "Tasks.ReadWrite" in GRAPH_SCOPES
    assert "Calendars.ReadWrite" in GRAPH_SCOPES
    assert "User.Read" in GRAPH_SCOPES


def test_get_config_dir_windows():
    with patch("outpost.config.platform.system", return_value="Windows"):
        d = get_config_dir()
        assert d.name == "outpost"
        assert "AppData" in str(d)


def test_get_config_dir_darwin():
    with patch("outpost.config.platform.system", return_value="Darwin"):
        d = get_config_dir()
        assert d.name == "outpost"
        assert "Application Support" in str(d)


def test_get_config_dir_linux():
    with patch("outpost.config.platform.system", return_value="Linux"):
        d = get_config_dir()
        assert d.name == "outpost"
        assert ".config" in str(d)


def test_load_config_defaults(tmp_path):
    with patch("outpost.config.get_config_path", return_value=tmp_path / "nonexistent.json"):
        config = load_config()
    assert config == DEFAULT_CONFIG


def test_save_and_load_config(tmp_path):
    config_path = tmp_path / "outpost" / "config.json"
    with patch("outpost.config.get_config_path", return_value=config_path):
        save_config({"client_id": "test-id", "default_output": "json"})
        loaded = load_config()
    assert loaded["client_id"] == "test-id"
    assert loaded["default_output"] == "json"


def test_load_config_merges_new_defaults(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    # Write a config missing some default keys
    with open(config_path, "w") as f:
        json.dump({"client_id": "my-id"}, f)
    with patch("outpost.config.get_config_path", return_value=config_path):
        loaded = load_config()
    assert loaded["client_id"] == "my-id"
    assert loaded["default_output"] == "table"  # from defaults


def test_set_and_get_profile():
    import outpost.config as cfg
    original = cfg._current_profile
    try:
        set_profile("work")
        assert get_profile() == "work"
    finally:
        cfg._current_profile = original


def test_profile_config_dir():
    import outpost.config as cfg
    original = cfg._current_profile
    try:
        cfg._current_profile = None
        default_dir = get_config_dir()
        set_profile("work")
        profile_dir = get_config_dir()
        assert "profiles" in str(profile_dir)
        assert "work" in str(profile_dir)
        assert str(profile_dir).startswith(str(default_dir.parent))
    finally:
        cfg._current_profile = original


def test_default_profile_no_subdirectory():
    import outpost.config as cfg
    original = cfg._current_profile
    try:
        cfg._current_profile = None
        d = get_config_dir()
        assert "profiles" not in str(d)
    finally:
        cfg._current_profile = original


def test_graph_scopes_is_core_scopes():
    """GRAPH_SCOPES is an alias for CORE_SCOPES for backward compat."""
    assert GRAPH_SCOPES is CORE_SCOPES


def test_feature_scopes_has_teams():
    assert "teams" in FEATURE_SCOPES
    assert "Team.ReadBasic.All" in FEATURE_SCOPES["teams"]


def test_get_active_scopes_core_only():
    config = {"enabled_features": []}
    scopes = get_active_scopes(config)
    assert scopes == CORE_SCOPES


def test_get_active_scopes_with_teams():
    config = {"enabled_features": ["teams"]}
    scopes = get_active_scopes(config)
    assert "Tasks.ReadWrite" in scopes  # core
    assert "Team.ReadBasic.All" in scopes  # teams
    assert len(scopes) == len(CORE_SCOPES) + len(FEATURE_SCOPES["teams"])


def test_get_active_scopes_unknown_feature():
    config = {"enabled_features": ["nonexistent"]}
    scopes = get_active_scopes(config)
    assert scopes == CORE_SCOPES


def test_is_feature_enabled_true():
    config = {"enabled_features": ["teams"]}
    assert is_feature_enabled("teams", config) is True


def test_is_feature_enabled_false():
    config = {"enabled_features": []}
    assert is_feature_enabled("teams", config) is False


def test_is_feature_enabled_no_key():
    config = {}
    assert is_feature_enabled("teams", config) is False


def test_default_config_has_enabled_features():
    assert "enabled_features" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["enabled_features"] == []


def test_get_workspace_dir_creates_dir(tmp_path):
    import outpost.config as cfg
    with patch("outpost.config.tempfile.gettempdir", return_value=str(tmp_path)):
        original = cfg._current_profile
        try:
            cfg._current_profile = None
            d = get_workspace_dir()
            assert d.exists()
            assert "outpost" in str(d)
            assert "workspace" in str(d)
        finally:
            cfg._current_profile = original


def test_get_workspace_dir_profile(tmp_path):
    import outpost.config as cfg
    with patch("outpost.config.tempfile.gettempdir", return_value=str(tmp_path)):
        original = cfg._current_profile
        try:
            set_profile("work")
            d = get_workspace_dir()
            assert "profiles" in str(d)
            assert "work" in str(d)
        finally:
            cfg._current_profile = original


def test_clean_workspace(tmp_path):
    import outpost.config as cfg
    with patch("outpost.config.tempfile.gettempdir", return_value=str(tmp_path)):
        original = cfg._current_profile
        try:
            cfg._current_profile = None
            workspace = get_workspace_dir()
            # Create some files
            (workspace / "file1.txt").write_text("hello")
            (workspace / "file2.txt").write_text("world")
            assert len(list(workspace.iterdir())) == 2
            clean_workspace()
            # Directory should exist but be empty
            assert workspace.exists()
            assert len(list(workspace.iterdir())) == 0
        finally:
            cfg._current_profile = original
