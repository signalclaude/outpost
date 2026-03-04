"""Tests for remote MCP access — API key management and server factory."""

import json
from unittest.mock import patch, MagicMock

import pytest

from outpost.config import get_mcp_api_key, generate_mcp_api_key


# ── API key generation ───────────────────────────────────────────────────────


def test_get_mcp_api_key_generates_if_missing(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"enabled_features": []}))

    with patch("outpost.config.get_config_path", return_value=config_file):
        key = get_mcp_api_key()
        assert key
        assert len(key) > 20

        # Should be persisted
        saved = json.loads(config_file.read_text())
        assert saved["mcp_api_key"] == key


def test_get_mcp_api_key_returns_existing(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mcp_api_key": "existing-key-123"}))

    with patch("outpost.config.get_config_path", return_value=config_file):
        key = get_mcp_api_key()
        assert key == "existing-key-123"


def test_get_mcp_api_key_from_config_dict():
    config = {"mcp_api_key": "my-key"}
    with patch("outpost.config.load_config", return_value=config):
        key = get_mcp_api_key(config=config)
        assert key == "my-key"


def test_generate_mcp_api_key_creates_new(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mcp_api_key": "old-key"}))

    with patch("outpost.config.get_config_path", return_value=config_file):
        new_key = generate_mcp_api_key()
        assert new_key != "old-key"
        assert len(new_key) > 20

        saved = json.loads(config_file.read_text())
        assert saved["mcp_api_key"] == new_key


def test_generate_mcp_api_key_unique():
    keys = set()
    with patch("outpost.config.get_config_path") as mock_path, \
         patch("outpost.config.save_config"):
        mock_path.return_value = MagicMock()
        with patch("outpost.config.load_config", return_value={}):
            for _ in range(10):
                keys.add(generate_mcp_api_key())
    assert len(keys) == 10


# ── Server factory ───────────────────────────────────────────────────────────


def test_create_mcp_server_no_auth_returns_default():
    from outpost.mcp_server import mcp, create_mcp_server

    server = create_mcp_server(auth=None)
    assert server is mcp


def test_create_mcp_server_with_auth_returns_new_instance():
    from outpost.mcp_server import mcp, create_mcp_server
    from fastmcp.server.auth import StaticTokenVerifier

    auth = StaticTokenVerifier(
        tokens={"test-key": {"client_id": "test", "scopes": ["all"]}},
    )
    server = create_mcp_server(auth=auth)
    assert server is not mcp
    assert server.auth is auth


# ── CLI wiring ───────────────────────────────────────────────────────────────


def test_mcp_key_display(tmp_path):
    from typer.testing import CliRunner
    from outpost.cli import app

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mcp_api_key": "test-display-key"}))

    runner = CliRunner()
    with patch("outpost.config.get_config_path", return_value=config_file):
        result = runner.invoke(app, ["mcp", "key"])
        assert result.exit_code == 0
        assert "test-display-key" in result.output


def test_mcp_key_regenerate(tmp_path):
    from typer.testing import CliRunner
    from outpost.cli import app

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mcp_api_key": "old-key"}))

    runner = CliRunner()
    with patch("outpost.config.get_config_path", return_value=config_file):
        result = runner.invoke(app, ["mcp", "key", "--regenerate"])
        assert result.exit_code == 0
        assert "New API key generated" in result.output
        # Should not be the old key
        saved = json.loads(config_file.read_text())
        assert saved["mcp_api_key"] != "old-key"
