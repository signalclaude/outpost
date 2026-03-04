"""Tests for outpost CLI error handling."""

from unittest.mock import patch, MagicMock

import httpx
from typer.testing import CliRunner

from outpost.api.client import GraphAPIError
from outpost.cli import app


runner = CliRunner()


class TestErrorHandling:
    def test_401_error(self):
        mock_client = MagicMock()
        error = GraphAPIError(401, "InvalidAuthenticationToken", "Token expired")
        mock_client.get.side_effect = error
        mock_client.get_all_pages.side_effect = error

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "today"])

        assert result.exit_code == 1
        assert "expired" in result.output.lower() or "setup" in result.output.lower()

    def test_403_error(self):
        mock_client = MagicMock()
        error = GraphAPIError(403, "Forbidden", "Insufficient privileges")
        mock_client.get.side_effect = error
        mock_client.get_all_pages.side_effect = error

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "today"])

        assert result.exit_code == 1
        assert "permission" in result.output.lower() or "denied" in result.output.lower()

    def test_429_error(self):
        mock_client = MagicMock()
        error = GraphAPIError(429, "TooManyRequests", "Rate limited")
        mock_client.get.side_effect = error
        mock_client.get_all_pages.side_effect = error

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "today"])

        assert result.exit_code == 1
        assert "rate" in result.output.lower() or "wait" in result.output.lower()

    def test_500_error(self):
        mock_client = MagicMock()
        error = GraphAPIError(500, "InternalServerError", "Something broke")
        mock_client.get.side_effect = error
        mock_client.get_all_pages.side_effect = error

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "today"])

        assert result.exit_code == 1
        assert "500" in result.output or "broke" in result.output.lower()

    def test_network_error(self):
        mock_client = MagicMock()
        error = httpx.ConnectError("Connection refused")
        mock_client.get.side_effect = error
        mock_client.get_all_pages.side_effect = error

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "today"])

        assert result.exit_code == 1
        assert "network" in result.output.lower() or "connection" in result.output.lower()

    def test_value_error_bad_date(self):
        with patch("outpost.cli._get_client", return_value=MagicMock()):
            result = runner.invoke(app, ["task", "add", "Test", "--due", "xyzzy nonsense gibberish"])

        assert result.exit_code == 1
        assert "parse" in result.output.lower() or "invalid" in result.output.lower()
