"""Tests for outpost config module."""

import json
from pathlib import Path
from unittest.mock import patch

from outpost.config import (
    DEFAULT_CONFIG,
    GRAPH_BASE_URL,
    GRAPH_SCOPES,
    get_config_dir,
    load_config,
    save_config,
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
