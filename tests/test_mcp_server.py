"""Tests for the MCP server tool functions."""

from unittest.mock import MagicMock, patch

import pytest

from outpost.mcp_server import (
    auth_status,
    cal_add,
    cal_delete,
    cal_list,
    cal_today,
    cal_update,
    contact_list,
    contact_search,
    mail_delete,
    mail_list,
    mail_read,
    mail_reply,
    mail_send,
    task_add,
    task_complete,
    task_delete,
    task_list,
    task_update,
)


# ── Auth error path ─────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value=None)
def test_unauthenticated_raises_runtime_error(mock_token):
    """Tools raise RuntimeError with helpful message when not authenticated."""
    with pytest.raises(RuntimeError, match="Not authenticated"):
        task_list()


# ── task_add ────────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.tasks.add_task")
@patch("outpost.mcp_server.GraphClient")
def test_task_add_basic(mock_client_cls, mock_add_task, mock_token):
    mock_add_task.return_value = {"id": "1", "title": "Buy milk"}
    result = task_add(title="Buy milk")
    mock_add_task.assert_called_once_with(
        mock_client_cls.return_value, "Buy milk", due_date=None, list_name=None, priority="normal"
    )
    assert result == {"id": "1", "title": "Buy milk"}


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.tasks.add_task")
@patch("outpost.mcp_server.GraphClient")
def test_task_add_with_due_and_list(mock_client_cls, mock_add_task, mock_token):
    mock_add_task.return_value = {"id": "2", "title": "Report"}
    result = task_add(title="Report", due="2026-03-15", list_name="Work", priority="high")
    mock_add_task.assert_called_once_with(
        mock_client_cls.return_value, "Report", due_date="2026-03-15", list_name="Work", priority="high"
    )
    assert result["title"] == "Report"


# ── task_list ───────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.tasks.list_tasks")
@patch("outpost.mcp_server.GraphClient")
def test_task_list_no_filter(mock_client_cls, mock_list_tasks, mock_token):
    mock_list_tasks.return_value = [{"id": "1", "title": "Test"}]
    result = task_list()
    mock_list_tasks.assert_called_once_with(
        mock_client_cls.return_value, due_filter=None, list_name=None
    )
    assert len(result) == 1


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.tasks.list_tasks")
@patch("outpost.mcp_server.GraphClient")
def test_task_list_with_due(mock_client_cls, mock_list_tasks, mock_token):
    mock_list_tasks.return_value = []
    result = task_list(due="2026-03-10")
    mock_list_tasks.assert_called_once_with(
        mock_client_cls.return_value, due_filter="2026-03-10", list_name=None
    )
    assert result == []


# ── cal_add ─────────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.calendar.create_event")
@patch("outpost.mcp_server.GraphClient")
def test_cal_add_basic(mock_client_cls, mock_create, mock_token):
    mock_create.return_value = {"id": "e1", "subject": "Meeting"}
    result = cal_add(title="Meeting", start="2026-03-15T09:00")
    assert mock_create.call_count == 1
    call_args = mock_create.call_args
    assert call_args[0][1] == "Meeting"  # title
    assert result["subject"] == "Meeting"


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.calendar.create_event")
@patch("outpost.mcp_server.GraphClient")
def test_cal_add_with_duration(mock_client_cls, mock_create, mock_token):
    mock_create.return_value = {"id": "e2", "subject": "Standup"}
    result = cal_add(title="Standup", start="2026-03-15T09:00", duration=15)
    call_args = mock_create.call_args
    assert call_args[1]["duration"] == 15


# ── cal_today ───────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.calendar.get_today_events")
@patch("outpost.mcp_server.GraphClient")
def test_cal_today(mock_client_cls, mock_today, mock_token):
    mock_today.return_value = [{"subject": "Lunch"}]
    result = cal_today()
    mock_today.assert_called_once_with(mock_client_cls.return_value)
    assert result == [{"subject": "Lunch"}]


# ── cal_list ────────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.calendar.get_week_events")
@patch("outpost.mcp_server.GraphClient")
def test_cal_list_default_week(mock_client_cls, mock_week, mock_token):
    mock_week.return_value = [{"subject": "Weekly"}]
    result = cal_list()
    mock_week.assert_called_once_with(mock_client_cls.return_value)
    assert len(result) == 1


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.calendar.get_calendar_view")
@patch("outpost.mcp_server.GraphClient")
def test_cal_list_specific_date(mock_client_cls, mock_view, mock_token):
    mock_view.return_value = [{"subject": "Birthday"}]
    result = cal_list(date="2026-03-15")
    assert mock_view.call_count == 1
    assert result == [{"subject": "Birthday"}]


# ── auth_status ─────────────────────────────────────────────────────────────


# ── task_update ─────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.tasks.update_task")
@patch("outpost.mcp_server.GraphClient")
def test_task_update(mock_client_cls, mock_update, mock_token):
    mock_update.return_value = {"id": "1", "title": "Updated"}
    result = task_update(task_id="1", title="Updated")
    mock_update.assert_called_once()
    assert result["title"] == "Updated"


# ── task_complete ──────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.tasks.complete_task")
@patch("outpost.mcp_server.GraphClient")
def test_task_complete(mock_client_cls, mock_complete, mock_token):
    mock_complete.return_value = {"id": "1", "status": "completed"}
    result = task_complete(task_id="1")
    mock_complete.assert_called_once()
    assert result["status"] == "completed"


# ── task_delete ────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.tasks.delete_task")
@patch("outpost.mcp_server.GraphClient")
def test_task_delete(mock_client_cls, mock_del, mock_token):
    mock_del.return_value = {}
    result = task_delete(task_id="1")
    mock_del.assert_called_once()
    assert result == {}


# ── cal_update ─────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.calendar.update_event")
@patch("outpost.mcp_server.GraphClient")
def test_cal_update(mock_client_cls, mock_update, mock_token):
    mock_update.return_value = {"id": "e1", "subject": "Updated"}
    result = cal_update(event_id="e1", title="Updated")
    assert mock_update.call_count == 1
    assert result["subject"] == "Updated"


# ── cal_delete ─────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.calendar.delete_event")
@patch("outpost.mcp_server.GraphClient")
def test_cal_delete(mock_client_cls, mock_del, mock_token):
    mock_del.return_value = {}
    result = cal_delete(event_id="e1")
    mock_del.assert_called_once()
    assert result == {}


# ── mail_list ──────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.mail.list_messages")
@patch("outpost.mcp_server.GraphClient")
def test_mail_list(mock_client_cls, mock_list, mock_token):
    mock_list.return_value = [{"id": "m1", "subject": "Hello"}]
    result = mail_list()
    mock_list.assert_called_once_with(mock_client_cls.return_value, folder="inbox", top=25)
    assert len(result) == 1


# ── mail_read ──────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.mail.get_message")
@patch("outpost.mcp_server.GraphClient")
def test_mail_read(mock_client_cls, mock_get, mock_token):
    mock_get.return_value = {"id": "m1", "subject": "Hello", "body": {"content": "Hi"}}
    result = mail_read(message_id="m1")
    mock_get.assert_called_once_with(mock_client_cls.return_value, "m1")
    assert result["subject"] == "Hello"


# ── mail_send ──────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.mail.send_message")
@patch("outpost.mcp_server.GraphClient")
def test_mail_send(mock_client_cls, mock_send, mock_token):
    mock_send.return_value = {}
    result = mail_send(to="bob@example.com", subject="Test", body="Hi")
    mock_send.assert_called_once_with(
        mock_client_cls.return_value, ["bob@example.com"], "Test", "Hi", cc=None
    )
    assert result == {}


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.mail.send_message")
@patch("outpost.mcp_server.GraphClient")
def test_mail_send_with_cc(mock_client_cls, mock_send, mock_token):
    mock_send.return_value = {}
    mail_send(to="bob@example.com", subject="Test", body="Hi", cc="carol@example.com")
    mock_send.assert_called_once_with(
        mock_client_cls.return_value, ["bob@example.com"], "Test", "Hi", cc=["carol@example.com"]
    )


# ── mail_reply ─────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.mail.reply_message")
@patch("outpost.mcp_server.GraphClient")
def test_mail_reply(mock_client_cls, mock_reply, mock_token):
    mock_reply.return_value = {}
    result = mail_reply(message_id="m1", body="Thanks!")
    mock_reply.assert_called_once_with(mock_client_cls.return_value, "m1", "Thanks!")
    assert result == {}


# ── mail_delete ────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.mail.delete_message")
@patch("outpost.mcp_server.GraphClient")
def test_mail_delete(mock_client_cls, mock_del, mock_token):
    mock_del.return_value = {}
    result = mail_delete(message_id="m1")
    mock_del.assert_called_once_with(mock_client_cls.return_value, "m1")
    assert result == {}


# ── contact_list ───────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.contacts.list_contacts")
@patch("outpost.mcp_server.GraphClient")
def test_contact_list(mock_client_cls, mock_list, mock_token):
    mock_list.return_value = [{"displayName": "Alice"}]
    result = contact_list()
    mock_list.assert_called_once_with(mock_client_cls.return_value, top=50)
    assert len(result) == 1


# ── contact_search ─────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_token", return_value="fake-token")
@patch("outpost.api.contacts.search_contacts")
@patch("outpost.mcp_server.GraphClient")
def test_contact_search(mock_client_cls, mock_search, mock_token):
    mock_search.return_value = [{"displayName": "Alice"}]
    result = contact_search(query="Alice")
    mock_search.assert_called_once_with(mock_client_cls.return_value, "Alice", top=25)
    assert len(result) == 1


# ── auth_status ─────────────────────────────────────────────────────────────


@patch("outpost.mcp_server.get_auth_status")
def test_auth_status_logged_in(mock_status):
    mock_status.return_value = {"logged_in": True, "username": "user@example.com"}
    result = auth_status()
    assert result["logged_in"] is True
    assert result["username"] == "user@example.com"


@patch("outpost.mcp_server.get_auth_status")
def test_auth_status_not_logged_in(mock_status):
    mock_status.return_value = {"logged_in": False, "username": None}
    result = auth_status()
    assert result["logged_in"] is False
