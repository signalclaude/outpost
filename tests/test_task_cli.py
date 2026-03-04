"""Tests for outpost task CLI commands."""

import json
from unittest.mock import patch, MagicMock

import httpx
import respx
from typer.testing import CliRunner

from outpost.cli import app


GRAPH_BASE = "https://graph.microsoft.com/v1.0"

runner = CliRunner()

SAMPLE_LISTS = {
    "value": [
        {"id": "list-default", "displayName": "Tasks", "wellknownListName": "defaultList"},
    ]
}


def _mock_auth(token="fake-token"):
    """Return a patch context that makes require_token return a fake token."""
    return patch("outpost.cli.require_token" if False else "outpost.auth.require_token", return_value=token)


# We need to patch at the point of import in cli.py
def _patch_require_token():
    return patch("outpost.cli._get_client")


class TestTaskAdd:
    def test_add_basic_task(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.post.return_value = {"id": "task-1", "title": "Buy milk"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "add", "Buy milk"])

        assert result.exit_code == 0

    def test_add_task_with_due(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.post.return_value = {"id": "task-1", "title": "Review PR"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "add", "Review PR", "--due", "2026-03-15"])

        assert result.exit_code == 0

    def test_add_task_with_priority(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.post.return_value = {"id": "task-1", "title": "Urgent"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "add", "Urgent", "--priority", "high"])

        assert result.exit_code == 0

    def test_add_task_json_output(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.post.return_value = {"id": "task-1", "title": "Test"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "add", "Test", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["title"] == "Test"


class TestTaskList:
    def test_list_tasks_table(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = [
            SAMPLE_LISTS,  # get_task_lists call
            {"value": [{"id": "t1", "title": "Task 1", "status": "notStarted", "importance": "normal"}]},
        ]

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 0
        assert "Task 1" in result.output

    def test_list_tasks_json(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = [
            SAMPLE_LISTS,
            {"value": [{"id": "t1", "title": "Task 1"}]},
        ]

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "list", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert len(parsed) == 1

    def test_list_tasks_with_due_filter(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = [
            SAMPLE_LISTS,
            {"value": []},
        ]

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "list", "--due", "2026-03-15"])

        assert result.exit_code == 0


class TestTaskUpdate:
    def test_update_task_title(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.patch.return_value = {"id": "task-1", "title": "New Title"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "update", "task-1", "--title", "New Title"])

        assert result.exit_code == 0

    def test_update_task_json_output(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.patch.return_value = {"id": "task-1", "title": "Updated"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "update", "task-1", "--title", "Updated", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["title"] == "Updated"


class TestTaskComplete:
    def test_complete_task(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.patch.return_value = {"id": "task-1", "title": "Done", "status": "completed"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "complete", "task-1"])

        assert result.exit_code == 0

    def test_complete_task_json(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.patch.return_value = {"id": "task-1", "status": "completed"}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "complete", "task-1", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["status"] == "completed"


class TestTaskDelete:
    def test_delete_task(self):
        mock_client = MagicMock()
        mock_client.get.return_value = SAMPLE_LISTS
        mock_client.delete.return_value = {}

        with patch("outpost.cli._get_client", return_value=mock_client):
            result = runner.invoke(app, ["task", "delete", "task-1"])

        assert result.exit_code == 0


class TestTaskNoAuth:
    def test_task_add_no_auth(self):
        with patch("outpost.auth.get_token", return_value=None):
            result = runner.invoke(app, ["task", "add", "Test"])
        assert result.exit_code == 1
