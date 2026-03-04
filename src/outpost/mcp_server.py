"""MCP server exposing Outpost operations as tools for Claude Desktop."""

from datetime import datetime, timedelta
from typing import Optional

from fastmcp import FastMCP

from outpost.api.client import GraphClient
from outpost.auth import get_auth_status, get_token
from outpost.utils.dates import (
    parse_natural_date,
    parse_natural_datetime,
    to_graph_date,
    today_range,
)

mcp = FastMCP(
    "outpost",
    instructions="Manage Microsoft Outlook tasks, calendar, email, and contacts via Graph API.",
)


def _get_client() -> GraphClient:
    """Get an authenticated GraphClient or raise RuntimeError."""
    token = get_token()
    if token is None:
        raise RuntimeError(
            "Not authenticated. Run 'outpost setup' in a terminal first to connect your Microsoft account."
        )
    return GraphClient(token=token)


@mcp.tool()
def task_add(
    title: str,
    due: Optional[str] = None,
    list_name: Optional[str] = None,
    priority: str = "normal",
) -> dict:
    """Add a new task to Microsoft To Do.

    Args:
        title: Task title
        due: Due date — natural language ('tomorrow', 'next friday') or ISO ('2026-03-15')
        list_name: Task list name (uses default list if omitted)
        priority: low, normal, or high
    """
    from outpost.api.tasks import add_task

    client = _get_client()
    due_date = to_graph_date(parse_natural_date(due)) if due else None
    return add_task(client, title, due_date=due_date, list_name=list_name, priority=priority)


@mcp.tool()
def task_list(
    due: Optional[str] = None,
    list_name: Optional[str] = None,
) -> list[dict]:
    """List tasks from Microsoft To Do.

    Args:
        due: Filter by due date — natural language or ISO format
        list_name: Task list name (uses default list if omitted)
    """
    from outpost.api.tasks import list_tasks

    client = _get_client()
    due_filter = to_graph_date(parse_natural_date(due)) if due else None
    return list_tasks(client, due_filter=due_filter, list_name=list_name)


@mcp.tool()
def cal_add(
    title: str,
    start: str,
    end: Optional[str] = None,
    duration: Optional[int] = None,
) -> dict:
    """Add a calendar event to Outlook.

    Args:
        title: Event title/subject
        start: Start time — natural language ('tomorrow 9am') or ISO ('2026-03-15T09:00')
        end: End time (optional if duration is given)
        duration: Duration in minutes (default 30 if neither end nor duration given)
    """
    from outpost.api.calendar import create_event

    client = _get_client()
    start_dt = parse_natural_datetime(start)
    end_dt = parse_natural_datetime(end) if end else None
    return create_event(client, title, start_dt, end=end_dt, duration=duration)


@mcp.tool()
def cal_today() -> list[dict]:
    """Get today's calendar events from Outlook."""
    from outpost.api.calendar import get_today_events

    client = _get_client()
    return get_today_events(client)


@mcp.tool()
def cal_list(
    date: Optional[str] = None,
    week: bool = False,
) -> list[dict]:
    """List calendar events from Outlook.

    Args:
        date: Show events for a specific date (natural language or ISO)
        week: If true, show this week's events (default if no date given)
    """
    from outpost.api.calendar import get_calendar_view, get_week_events

    client = _get_client()

    if date:
        d = parse_natural_date(date)
        start = datetime(d.year, d.month, d.day, 0, 0, 0)
        end = start + timedelta(days=1)
        return get_calendar_view(client, start, end)
    else:
        return get_week_events(client)


@mcp.tool()
def task_update(
    task_id: str,
    title: Optional[str] = None,
    due: Optional[str] = None,
    priority: Optional[str] = None,
    list_name: Optional[str] = None,
) -> dict:
    """Update an existing task in Microsoft To Do.

    Args:
        task_id: Task ID to update
        title: New title (optional)
        due: New due date — natural language or ISO format (optional)
        priority: New priority: low, normal, or high (optional)
        list_name: Task list name (uses default list if omitted)
    """
    from outpost.api.tasks import update_task

    client = _get_client()
    due_date = to_graph_date(parse_natural_date(due)) if due else None
    return update_task(client, task_id, list_name=list_name, title=title, due_date=due_date, priority=priority)


@mcp.tool()
def task_complete(task_id: str, list_name: Optional[str] = None) -> dict:
    """Mark a task as completed in Microsoft To Do.

    Args:
        task_id: Task ID to complete
        list_name: Task list name (uses default list if omitted)
    """
    from outpost.api.tasks import complete_task

    client = _get_client()
    return complete_task(client, task_id, list_name=list_name)


@mcp.tool()
def task_delete(task_id: str, list_name: Optional[str] = None) -> dict:
    """Delete a task from Microsoft To Do.

    Args:
        task_id: Task ID to delete
        list_name: Task list name (uses default list if omitted)
    """
    from outpost.api.tasks import delete_task

    client = _get_client()
    return delete_task(client, task_id, list_name=list_name)


@mcp.tool()
def cal_update(
    event_id: str,
    title: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> dict:
    """Update an existing calendar event in Outlook.

    Args:
        event_id: Event ID to update
        title: New title (optional)
        start: New start time — natural language or ISO format (optional)
        end: New end time — natural language or ISO format (optional)
    """
    from outpost.api.calendar import update_event

    client = _get_client()
    start_dt = parse_natural_datetime(start) if start else None
    end_dt = parse_natural_datetime(end) if end else None
    return update_event(client, event_id, title=title, start=start_dt, end=end_dt)


@mcp.tool()
def cal_delete(event_id: str) -> dict:
    """Delete a calendar event from Outlook.

    Args:
        event_id: Event ID to delete
    """
    from outpost.api.calendar import delete_event

    client = _get_client()
    return delete_event(client, event_id)


@mcp.tool()
def mail_list(folder: str = "inbox", top: int = 25) -> list[dict]:
    """List email messages from Outlook.

    Args:
        folder: Mail folder (inbox, sentitems, drafts, deleteditems)
        top: Maximum number of messages to return
    """
    from outpost.api.mail import list_messages

    client = _get_client()
    return list_messages(client, folder=folder, top=top)


@mcp.tool()
def mail_read(message_id: str) -> dict:
    """Read a specific email message from Outlook.

    Args:
        message_id: Message ID to read
    """
    from outpost.api.mail import get_message

    client = _get_client()
    return get_message(client, message_id)


@mcp.tool()
def mail_send(to: str, subject: str, body: str, cc: Optional[str] = None) -> dict:
    """Send an email via Outlook.

    Args:
        to: Recipient email address (comma-separated for multiple)
        subject: Email subject
        body: Email body text
        cc: CC recipients (comma-separated, optional)
    """
    from outpost.api.mail import send_message

    client = _get_client()
    to_list = [addr.strip() for addr in to.split(",")]
    cc_list = [addr.strip() for addr in cc.split(",")] if cc else None
    return send_message(client, to_list, subject, body, cc=cc_list)


@mcp.tool()
def mail_reply(message_id: str, body: str) -> dict:
    """Reply to an email in Outlook.

    Args:
        message_id: Message ID to reply to
        body: Reply text
    """
    from outpost.api.mail import reply_message

    client = _get_client()
    return reply_message(client, message_id, body)


@mcp.tool()
def mail_delete(message_id: str) -> dict:
    """Delete an email from Outlook.

    Args:
        message_id: Message ID to delete
    """
    from outpost.api.mail import delete_message

    client = _get_client()
    return delete_message(client, message_id)


@mcp.tool()
def contact_list(top: int = 50) -> list[dict]:
    """List contacts from Outlook.

    Args:
        top: Maximum number of contacts to return
    """
    from outpost.api.contacts import list_contacts

    client = _get_client()
    return list_contacts(client, top=top)


@mcp.tool()
def contact_search(query: str, top: int = 25) -> list[dict]:
    """Search contacts in Outlook by name or email.

    Args:
        query: Search query (name or email)
        top: Maximum number of results
    """
    from outpost.api.contacts import search_contacts

    client = _get_client()
    return search_contacts(client, query, top=top)


@mcp.tool()
def auth_status() -> dict:
    """Check if the user is authenticated with Microsoft."""
    return get_auth_status()


def main():
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
