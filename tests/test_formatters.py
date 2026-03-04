"""Tests for outpost output formatters."""

import json

from io import StringIO
from unittest.mock import patch

from rich.console import Console

from outpost.formatters import OutputFormat
from outpost.formatters.table import print_tasks_table, print_events_table
from outpost.formatters.json_fmt import print_json


class TestOutputFormat:
    def test_enum_values(self):
        assert OutputFormat.table.value == "table"
        assert OutputFormat.json.value == "json"

    def test_from_string(self):
        assert OutputFormat("table") == OutputFormat.table
        assert OutputFormat("json") == OutputFormat.json


class TestPrintTasksTable:
    def test_renders_task_data(self):
        buf = StringIO()
        console = Console(file=buf, width=120, force_terminal=True)
        tasks = [
            {
                "id": "abc12345-6789",
                "title": "Buy groceries",
                "dueDateTime": {"dateTime": "2026-03-15T00:00:00"},
                "importance": "high",
                "status": "notStarted",
            },
            {
                "id": "def00000-0000",
                "title": "Review PR",
                "importance": "normal",
                "status": "completed",
            },
        ]
        print_tasks_table(tasks, console=console)
        output = buf.getvalue()
        assert "Buy groceries" in output
        assert "Review PR" in output
        assert "2026-03-15" in output
        assert "done" in output

    def test_empty_list(self):
        buf = StringIO()
        console = Console(file=buf, width=120, force_terminal=True)
        print_tasks_table([], console=console)
        output = buf.getvalue()
        assert "Tasks" in output


class TestPrintEventsTable:
    def test_renders_event_data(self):
        buf = StringIO()
        console = Console(file=buf, width=120, force_terminal=True)
        events = [
            {
                "subject": "Team standup",
                "start": {"dateTime": "2026-03-15T09:00:00"},
                "end": {"dateTime": "2026-03-15T09:30:00"},
                "location": {"displayName": "Room 42"},
            },
        ]
        print_events_table(events, console=console)
        output = buf.getvalue()
        assert "Team standup" in output
        assert "30m" in output
        assert "Room 42" in output


class TestPrintJson:
    def test_outputs_valid_json(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            data = [{"id": "abc", "title": "Test"}]
            print_json(data)
            output = mock_stdout.getvalue()
        parsed = json.loads(output)
        assert parsed == [{"id": "abc", "title": "Test"}]

    def test_outputs_dict(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_json({"status": "ok"})
            output = mock_stdout.getvalue()
        parsed = json.loads(output)
        assert parsed["status"] == "ok"
