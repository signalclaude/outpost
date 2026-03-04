"""Tests for outpost contacts CLI commands."""

import json
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from outpost.cli import app


runner = CliRunner()

SAMPLE_CONTACTS = {
    "value": [
        {
            "id": "contact-1",
            "displayName": "Alice Smith",
            "emailAddresses": [{"address": "alice@example.com"}],
            "businessPhones": ["+1-555-0100"],
            "mobilePhone": "+1-555-0101",
        },
    ]
}


class TestContactList:
    def test_list_table(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_CONTACTS

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["contact", "list"])

        assert result.exit_code == 0
        assert "Alice Smith" in result.output

    def test_list_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_CONTACTS

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["contact", "list", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 1


class TestContactSearch:
    def test_search_table(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_CONTACTS

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["contact", "search", "Alice"])

        assert result.exit_code == 0
        assert "Alice Smith" in result.output

    def test_search_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_CONTACTS

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["contact", "search", "Alice", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 1

    def test_search_no_results(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"value": []}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["contact", "search", "nobody"])

        assert result.exit_code == 0
