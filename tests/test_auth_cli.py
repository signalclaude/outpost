"""Tests for outpost auth/setup CLI commands."""

import json
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from outpost.cli import app


runner = CliRunner()


class TestSetup:
    def test_setup_calls_login(self):
        with patch("outpost.auth.login_interactive", return_value=True) as mock_login:
            result = runner.invoke(app, ["setup"])
        assert result.exit_code == 0
        mock_login.assert_called_once()
        assert "Welcome" in result.output

    def test_setup_no_client_id(self):
        with patch("outpost.auth.DEFAULT_CLIENT_ID", ""):
            result = runner.invoke(app, ["setup"])
        assert result.exit_code == 0
        assert "not configured" in result.output.lower() or "Azure" in result.output


class TestAuthStatus:
    def test_status_not_logged_in(self):
        with patch("outpost.auth.get_auth_status", return_value={"logged_in": False, "username": None}):
            result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "not logged in" in result.output.lower() or "setup" in result.output.lower()

    def test_status_logged_in(self):
        with patch("outpost.auth.get_auth_status", return_value={"logged_in": True, "username": "user@example.com"}):
            result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "user@example.com" in result.output

    def test_status_json_output(self):
        with patch("outpost.auth.get_auth_status", return_value={"logged_in": True, "username": "user@example.com"}):
            result = runner.invoke(app, ["auth", "status", "--output", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["logged_in"] is True
        assert parsed["username"] == "user@example.com"
