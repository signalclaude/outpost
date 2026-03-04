"""Tests for outpost mail CLI commands."""

import json
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from outpost.cli import app


runner = CliRunner()

SAMPLE_MESSAGES = {
    "value": [
        {
            "id": "msg-1",
            "subject": "Hello",
            "from": {"emailAddress": {"address": "alice@example.com"}},
            "receivedDateTime": "2026-03-01T10:00:00Z",
            "isRead": False,
            "bodyPreview": "Hi there",
        },
    ]
}

SAMPLE_MESSAGE_DETAIL = {
    "id": "msg-1",
    "subject": "Hello",
    "from": {"emailAddress": {"address": "alice@example.com"}},
    "toRecipients": [{"emailAddress": {"address": "me@example.com"}}],
    "ccRecipients": [],
    "receivedDateTime": "2026-03-01T10:00:00Z",
    "body": {"contentType": "text", "content": "Hi there"},
    "isRead": True,
}


class TestMailList:
    def test_list_table(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_MESSAGES

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["mail", "list"])

        assert result.exit_code == 0
        assert "Hello" in result.output

    def test_list_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_MESSAGES

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["mail", "list", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 1

    def test_list_with_folder(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"value": []}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["mail", "list", "--folder", "sentitems"])

        assert result.exit_code == 0


class TestMailRead:
    def test_read_table(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_MESSAGE_DETAIL

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["mail", "read", "msg-1"])

        assert result.exit_code == 0
        assert "Hello" in result.output

    def test_read_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_MESSAGE_DETAIL

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["mail", "read", "msg-1", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["subject"] == "Hello"


class TestMailSend:
    def test_send(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "mail", "send",
                "--to", "bob@example.com",
                "--subject", "Test",
                "--body", "Hello Bob",
            ])

        assert result.exit_code == 0

    def test_send_with_cc(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "mail", "send",
                "--to", "bob@example.com",
                "--subject", "Test",
                "--body", "Hi",
                "--cc", "carol@example.com",
            ])

        assert result.exit_code == 0


class TestMailReply:
    def test_reply(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "mail", "reply", "msg-1", "--body", "Thanks!",
            ])

        assert result.exit_code == 0


class TestMailDelete:
    def test_delete(self):
        mock_client = MagicMock()
        mock_client.delete.return_value = {}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["mail", "delete", "msg-1"])

        assert result.exit_code == 0
