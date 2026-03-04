"""Tests for outpost calendar CLI commands."""

import json
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from outpost.cli import app


runner = CliRunner()

SAMPLE_EVENTS = {
    "value": [
        {
            "id": "evt-1",
            "subject": "Team standup",
            "start": {"dateTime": "2026-03-15T09:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-03-15T09:30:00", "timeZone": "UTC"},
            "location": {"displayName": "Room 42"},
        },
    ]
}


class TestCalAdd:
    def test_add_event_with_end(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {"id": "evt-1", "subject": "Meeting"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "cal", "add", "Meeting",
                "--start", "2026-03-15T09:00:00",
                "--end", "2026-03-15T10:00:00",
            ])

        assert result.exit_code == 0

    def test_add_event_with_duration(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {"id": "evt-1", "subject": "Quick chat"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "cal", "add", "Quick chat",
                "--start", "2026-03-15T14:00:00",
                "--duration", "15",
            ])

        assert result.exit_code == 0

    def test_add_event_json_output(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {"id": "evt-1", "subject": "Test"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "cal", "add", "Test",
                "--start", "2026-03-15T09:00:00",
                "--output", "json",
            ])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["subject"] == "Test"


class TestCalToday:
    def test_today_table(self):
        mock_client = MagicMock()
        mock_client.get_all_pages.return_value = SAMPLE_EVENTS["value"]

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "today"])

        assert result.exit_code == 0
        assert "Team standup" in result.output

    def test_today_json(self):
        mock_client = MagicMock()
        mock_client.get_all_pages.return_value = SAMPLE_EVENTS["value"]

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "today", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 1


class TestCalList:
    def test_list_week(self):
        mock_client = MagicMock()
        mock_client.get_all_pages.return_value = SAMPLE_EVENTS["value"]

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "list", "--week"])

        assert result.exit_code == 0

    def test_list_specific_date(self):
        mock_client = MagicMock()
        mock_client.get_all_pages.return_value = SAMPLE_EVENTS["value"]

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "list", "--date", "2026-03-15"])

        assert result.exit_code == 0

    def test_list_json(self):
        mock_client = MagicMock()
        mock_client.get_all_pages.return_value = SAMPLE_EVENTS["value"]

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "list", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)


class TestCalUpdate:
    def test_update_event_title(self):
        mock_client = MagicMock()
        mock_client.patch.return_value = {"id": "evt-1", "subject": "New Title"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "update", "evt-1", "--title", "New Title"])

        assert result.exit_code == 0

    def test_update_event_json(self):
        mock_client = MagicMock()
        mock_client.patch.return_value = {"id": "evt-1", "subject": "Updated"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "update", "evt-1", "--title", "Updated", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["subject"] == "Updated"


class TestCalDelete:
    def test_delete_event(self):
        mock_client = MagicMock()
        mock_client.delete.return_value = {}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "delete", "evt-1"])

        assert result.exit_code == 0


class TestCalNext:
    def test_next_event(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_EVENTS

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "next"])

        assert result.exit_code == 0

    def test_next_events_with_count(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_EVENTS

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "next", "--count", "3"])

        assert result.exit_code == 0

    def test_next_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_EVENTS

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["cal", "next", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)


class TestCalAddWithAttendee:
    def test_add_with_attendee(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {"id": "evt-1", "subject": "Meeting"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "cal", "add", "Meeting",
                "--start", "2026-03-15T09:00:00",
                "--attendee", "alice@example.com",
            ])

        assert result.exit_code == 0


class TestCalNoAuth:
    def test_cal_today_no_auth(self):
        with patch("outpost.auth.get_token", return_value=None):
            result = runner.invoke(app, ["cal", "today"])
        assert result.exit_code == 1
