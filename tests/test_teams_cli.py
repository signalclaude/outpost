"""Tests for outpost Teams CLI commands."""

import json
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from outpost.cli import app


runner = CliRunner()


def _mock_feature_enabled(feature):
    """Return True for teams feature."""
    return feature == "teams"


def _mock_feature_disabled(feature):
    """Return False for all features."""
    return False


SAMPLE_TEAMS = [
    {"id": "team-1", "displayName": "Engineering", "description": "Eng team"},
    {"id": "team-2", "displayName": "Marketing", "description": ""},
]

SAMPLE_CHANNELS = [
    {"id": "ch-1", "displayName": "General", "membershipType": "standard"},
    {"id": "ch-2", "displayName": "Random", "membershipType": "standard"},
]

SAMPLE_MESSAGES = [
    {
        "id": "msg-1",
        "body": {"content": "Hello world"},
        "from": {"user": {"displayName": "Alice"}},
        "createdDateTime": "2026-03-01T10:00:00Z",
    },
]

SAMPLE_FILES = [
    {"id": "file-1", "name": "doc.pdf", "size": 1024, "lastModifiedDateTime": "2026-03-01T10:00:00Z"},
    {"id": "folder-2", "name": "subfolder", "folder": {"childCount": 3}, "lastModifiedDateTime": "2026-03-01T10:00:00Z"},
]


class TestTeamsList:
    def test_list_table(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"value": SAMPLE_TEAMS}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "list"])

        assert result.exit_code == 0
        assert "Engineering" in result.output

    def test_list_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"value": SAMPLE_TEAMS}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "list", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 2

    def test_list_not_enabled(self):
        with patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_disabled):
            result = runner.invoke(app, ["teams", "list"])

        assert result.exit_code == 1
        assert "not enabled" in result.output


class TestTeamsChannels:
    def test_channels_table(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"value": SAMPLE_CHANNELS}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "channels", "team-1"])

        assert result.exit_code == 0
        assert "General" in result.output

    def test_channels_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"value": SAMPLE_CHANNELS}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "channels", "team-1", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 2


class TestTeamsMessages:
    def test_messages_table(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"value": SAMPLE_MESSAGES}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "messages", "team-1", "ch-1"])

        assert result.exit_code == 0

    def test_messages_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"value": SAMPLE_MESSAGES}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "messages", "team-1", "ch-1", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 1

    def test_messages_not_enabled(self):
        with patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_disabled):
            result = runner.invoke(app, ["teams", "messages", "team-1", "ch-1"])

        assert result.exit_code == 1


class TestTeamsSend:
    def test_send_message(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {"id": "msg-new", "body": {"content": "Hi!"}}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "send", "team-1", "ch-1", "--body", "Hi!"])

        assert result.exit_code == 0

    def test_send_json(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {"id": "msg-new", "body": {"content": "Hi!"}}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "send", "team-1", "ch-1", "--body", "Hi!", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["id"] == "msg-new"


class TestTeamsFiles:
    def test_files_table(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = [
            {"id": "folder-1", "name": "General", "parentReference": {"driveId": "drive-1"}},
            {"value": SAMPLE_FILES},
        ]

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "files", "team-1", "ch-1"])

        assert result.exit_code == 0
        assert "doc.pdf" in result.output

    def test_files_json(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = [
            {"id": "folder-1", "name": "General", "parentReference": {"driveId": "drive-1"}},
            {"value": SAMPLE_FILES},
        ]

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "files", "team-1", "ch-1", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 2


class TestTeamsDownload:
    def test_download_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_client = MagicMock()

        # download_file returns (filename, bytes)
        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled), \
             patch("outpost.api.teams.download_file", return_value=("report.pdf", b"content")):
            result = runner.invoke(app, ["teams", "download", "drive-1", "file-1"])

        assert result.exit_code == 0
        assert (tmp_path / "report.pdf").read_bytes() == b"content"

    def test_download_not_enabled(self):
        with patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_disabled):
            result = runner.invoke(app, ["teams", "download", "drive-1", "file-1"])

        assert result.exit_code == 1
        assert "not enabled" in result.output


class TestTeamsUpload:
    def test_upload_file(self, tmp_path):
        # Create a file to upload
        filepath = tmp_path / "test.txt"
        filepath.write_text("upload content")

        mock_client = MagicMock()
        mock_client.put.return_value = {"id": "item-1", "name": "test.txt"}

        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled), \
             patch("outpost.api.teams.upload_file", return_value={"id": "item-1", "name": "test.txt"}) as mock_upload:
            result = runner.invoke(app, ["teams", "upload", "drive-1", "folder-1", str(filepath)])

        assert result.exit_code == 0
        mock_upload.assert_called_once()

    def test_upload_json(self, tmp_path):
        filepath = tmp_path / "test.txt"
        filepath.write_text("content")

        mock_client = MagicMock()
        with patch("outpost.cli._get_client", return_value=mock_client), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled), \
             patch("outpost.api.teams.upload_file", return_value={"id": "item-1", "name": "test.txt"}):
            result = runner.invoke(app, ["teams", "upload", "drive-1", "folder-1", str(filepath), "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["name"] == "test.txt"

    def test_upload_file_not_found(self):
        with patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "upload", "drive-1", "folder-1", "/nonexistent/file.txt"])

        assert result.exit_code == 1

    def test_upload_not_enabled(self):
        with patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_disabled):
            result = runner.invoke(app, ["teams", "upload", "drive-1", "folder-1", "file.txt"])

        assert result.exit_code == 1
        assert "not enabled" in result.output


class TestTeamsNoAuth:
    def test_teams_list_no_auth(self):
        with patch("outpost.auth.get_token", return_value=None), \
             patch("outpost.config.is_feature_enabled", side_effect=_mock_feature_enabled):
            result = runner.invoke(app, ["teams", "list"])
        assert result.exit_code == 1
