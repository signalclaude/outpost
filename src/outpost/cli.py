"""Outpost CLI — main entry point and command groups."""

import functools
import sys
from typing import Optional

import httpx
import typer
from rich.console import Console

from outpost.api.client import GraphAPIError
from outpost.formatters import OutputFormat

app = typer.Typer(
    name="outpost",
    help="A fast CLI for Microsoft Outlook via Microsoft Graph API.",
    no_args_is_help=True,
)

task_app = typer.Typer(help="Manage Microsoft To Do tasks.", no_args_is_help=True)
cal_app = typer.Typer(help="Manage Outlook calendar events.", no_args_is_help=True)
auth_app = typer.Typer(help="Manage authentication.", no_args_is_help=True)

mail_app = typer.Typer(help="Manage Outlook email.", no_args_is_help=True)
contact_app = typer.Typer(help="Search Outlook contacts (read-only).", no_args_is_help=True)
teams_app = typer.Typer(help="Manage Microsoft Teams channels and files.", no_args_is_help=True)
mcp_app = typer.Typer(help="MCP server for Claude Desktop integration.", no_args_is_help=True)

app.add_typer(task_app, name="task")
app.add_typer(cal_app, name="cal")
app.add_typer(mail_app, name="mail")
app.add_typer(contact_app, name="contact")
app.add_typer(teams_app, name="teams")
app.add_typer(auth_app, name="auth")
app.add_typer(mcp_app, name="mcp")

stderr = Console(stderr=True)


# ── Global callback for --profile ─────────────────────────────────────────────


def _version_callback(value: bool):
    if value:
        from outpost import __version__

        typer.echo(f"outpost {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    profile: Optional[str] = typer.Option(None, "--profile", help="Use a named profile for multi-account support"),
    version: Optional[bool] = typer.Option(None, "--version", "-V", callback=_version_callback, is_eager=True, help="Show version and exit"),
):
    """Outpost CLI — Microsoft Outlook from the terminal."""
    if profile:
        from outpost.config import set_profile

        set_profile(profile)

    # Auto-check for updates (only in interactive terminals, never breaks usage)
    try:
        if sys.stderr.isatty():
            from outpost.updater import check_for_update
            from outpost import __version__

            update_info = check_for_update()
            if update_info:
                typer.echo(
                    f"Update available: {__version__} \u2192 {update_info['latest_version']}. "
                    f"Run 'outpost update' to upgrade.",
                    err=True,
                )
    except Exception:
        pass


def _handle_error(exc: Exception) -> None:
    """Print a user-friendly error message and raise typer.Exit."""
    if isinstance(exc, GraphAPIError):
        if exc.status_code == 401:
            msg = "Authentication expired. Run 'outpost setup' to re-authenticate."
        elif exc.status_code == 403:
            msg = "Permission denied. You may need to re-consent. Run 'outpost setup'."
        elif exc.status_code == 429:
            msg = "Rate limited by Microsoft. Please wait a moment and try again."
        else:
            msg = f"Graph API error ({exc.status_code}): {exc.message}"
    elif isinstance(exc, httpx.ConnectError):
        msg = "Network error. Check your internet connection and try again."
    elif isinstance(exc, ValueError):
        msg = f"Invalid input: {exc}"
    else:
        msg = f"Error: {exc}"
    typer.echo(f"Error: {msg}", err=True)
    raise typer.Exit(1)


def handle_errors(func):
    """Decorator that catches exceptions and prints user-friendly error messages."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (typer.Exit, SystemExit):
            raise
        except Exception as exc:
            _handle_error(exc)

    return wrapper


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_client():
    """Get an authenticated GraphClient or exit."""
    from outpost.auth import require_token
    from outpost.api.client import GraphClient

    token = require_token()
    return GraphClient(token=token)


# ── Task commands ────────────────────────────────────────────────────────────


@task_app.command("add")
@handle_errors
def task_add(
    title: str = typer.Argument(..., help="Task title"),
    due: Optional[str] = typer.Option(None, "--due", "-d", help="Due date (e.g. 'tomorrow', '2026-03-15')"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Task list name"),
    priority: str = typer.Option("normal", "--priority", "-p", help="Priority: low|normal|high"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Add a new task to Microsoft To Do."""
    from outpost.api.tasks import add_task
    from outpost.utils.dates import parse_natural_date, to_graph_date
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    due_date = None
    if due:
        due_date = to_graph_date(parse_natural_date(due))

    result = add_task(client, title, due_date=due_date, list_name=list_name, priority=priority)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Created task:[/green] {result.get('title', title)}")
        if due_date:
            stderr.print(f"  Due: {due_date}")


@task_app.command("list")
@handle_errors
def task_list(
    due: Optional[str] = typer.Option(None, "--due", "-d", help="Filter by due date (e.g. 'today', 'tomorrow')"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Task list name"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs instead of truncated"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List tasks from Microsoft To Do."""
    from outpost.api.tasks import list_tasks
    from outpost.utils.dates import parse_natural_date, to_graph_date
    from outpost.formatters.table import print_tasks_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    due_filter = None
    if due:
        due_filter = to_graph_date(parse_natural_date(due))

    tasks = list_tasks(client, due_filter=due_filter, list_name=list_name)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(tasks)
    else:
        print_tasks_table(tasks, full_id=full_id)


@task_app.command("update")
@handle_errors
def task_update(
    task_id: str = typer.Argument(..., help="Task ID to update"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    due: Optional[str] = typer.Option(None, "--due", "-d", help="New due date"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="New priority: low|normal|high"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Task list name"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Update an existing task."""
    from outpost.api.tasks import update_task
    from outpost.utils.dates import parse_natural_date, to_graph_date
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    due_date = to_graph_date(parse_natural_date(due)) if due else None
    result = update_task(client, task_id, list_name=list_name, title=title, due_date=due_date, priority=priority)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Updated task:[/green] {result.get('title', task_id)}")


@task_app.command("complete")
@handle_errors
def task_complete_cmd(
    task_id: str = typer.Argument(..., help="Task ID to complete"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Task list name"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Mark a task as completed."""
    from outpost.api.tasks import complete_task
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    result = complete_task(client, task_id, list_name=list_name)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Completed task:[/green] {result.get('title', task_id)}")


@task_app.command("delete")
@handle_errors
def task_delete_cmd(
    task_id: str = typer.Argument(..., help="Task ID to delete"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Task list name"),
):
    """Delete a task."""
    from outpost.api.tasks import delete_task

    client = _get_client()
    delete_task(client, task_id, list_name=list_name)
    stderr.print(f"[green]Deleted task:[/green] {task_id}")


@task_app.command("lists")
@handle_errors
def task_lists_cmd(
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List all task lists."""
    from outpost.api.tasks import get_task_lists
    from outpost.formatters.table import print_task_lists_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    lists = get_task_lists(client)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(lists)
    else:
        print_task_lists_table(lists, full_id=full_id)


@task_app.command("lists-create")
@handle_errors
def task_lists_create_cmd(
    name: str = typer.Argument(..., help="Name for the new task list"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Create a new task list."""
    from outpost.api.tasks import create_task_list
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    result = create_task_list(client, name)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Created task list:[/green] {result.get('displayName', name)}")


@task_app.command("lists-delete")
@handle_errors
def task_lists_delete_cmd(
    list_id: str = typer.Argument(..., help="Task list ID to delete"),
):
    """Delete a task list."""
    from outpost.api.tasks import delete_task_list

    client = _get_client()
    delete_task_list(client, list_id)
    stderr.print(f"[green]Deleted task list:[/green] {list_id}")


# ── Calendar commands ────────────────────────────────────────────────────────


@cal_app.command("add")
@handle_errors
def cal_add(
    title: str = typer.Argument(..., help="Event title"),
    start: str = typer.Option(..., "--start", "-s", help="Start time (e.g. 'tomorrow 9am')"),
    end: Optional[str] = typer.Option(None, "--end", "-e", help="End time"),
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="Duration in minutes"),
    attendee: Optional[list[str]] = typer.Option(None, "--attendee", "-a", help="Attendee email (repeatable)"),
    show_as: Optional[str] = typer.Option(None, "--show-as", help="Status: free|tentative|busy|oof|workingElsewhere"),
    timezone: Optional[str] = typer.Option(None, "--timezone", "--tz", help="IANA timezone (e.g. America/New_York). Defaults to config."),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Add a calendar event."""
    from outpost.api.calendar import create_event
    from outpost.config import load_config
    from outpost.utils.dates import parse_natural_datetime
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    tz = timezone or load_config().get("timezone", "UTC")
    start_dt = parse_natural_datetime(start)
    end_dt = parse_natural_datetime(end) if end else None

    result = create_event(client, title, start_dt, end=end_dt, duration=duration, attendees=attendee, show_as=show_as, timezone=tz)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Created event:[/green] {result.get('subject', title)}")


@cal_app.command("today")
@handle_errors
def cal_today(
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Show today's calendar events."""
    from outpost.api.calendar import get_today_events
    from outpost.formatters.table import print_events_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    events = get_today_events(client)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(events)
    else:
        print_events_table(events, full_id=full_id)


@cal_app.command("list")
@handle_errors
def cal_list(
    date_str: Optional[str] = typer.Option(None, "--date", help="Show events for a specific date"),
    week: bool = typer.Option(False, "--week", "-w", help="Show this week's events"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List calendar events."""
    from datetime import timedelta
    from outpost.api.calendar import get_calendar_view, get_week_events
    from outpost.utils.dates import parse_natural_date, today_range
    from outpost.formatters.table import print_events_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()

    if week:
        events = get_week_events(client)
    elif date_str:
        from datetime import datetime

        d = parse_natural_date(date_str)
        start = datetime(d.year, d.month, d.day, 0, 0, 0)
        end = start + timedelta(days=1)
        events = get_calendar_view(client, start, end)
    else:
        events = get_week_events(client)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(events)
    else:
        print_events_table(events, full_id=full_id)


@cal_app.command("next")
@handle_errors
def cal_next_cmd(
    count: int = typer.Option(1, "--count", "-n", help="Number of upcoming events"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Show the next upcoming calendar event(s)."""
    from outpost.api.calendar import get_next_events
    from outpost.formatters.table import print_events_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    events = get_next_events(client, count=count)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(events)
    else:
        print_events_table(events, full_id=full_id)


@cal_app.command("update")
@handle_errors
def cal_update(
    event_id: str = typer.Argument(..., help="Event ID to update"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    start: Optional[str] = typer.Option(None, "--start", "-s", help="New start time"),
    end: Optional[str] = typer.Option(None, "--end", "-e", help="New end time"),
    attendee: Optional[list[str]] = typer.Option(None, "--attendee", "-a", help="Attendee email (repeatable)"),
    show_as: Optional[str] = typer.Option(None, "--show-as", help="Status: free|tentative|busy|oof|workingElsewhere"),
    timezone: Optional[str] = typer.Option(None, "--timezone", "--tz", help="IANA timezone (e.g. America/New_York). Defaults to config."),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Update an existing calendar event."""
    from outpost.api.calendar import update_event
    from outpost.config import load_config
    from outpost.utils.dates import parse_natural_datetime
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    tz = timezone or load_config().get("timezone", "UTC")
    start_dt = parse_natural_datetime(start) if start else None
    end_dt = parse_natural_datetime(end) if end else None
    result = update_event(client, event_id, title=title, start=start_dt, end=end_dt, attendees=attendee, show_as=show_as, timezone=tz)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Updated event:[/green] {result.get('subject', event_id)}")


@cal_app.command("delete")
@handle_errors
def cal_delete(
    event_id: str = typer.Argument(..., help="Event ID to delete"),
):
    """Delete a calendar event."""
    from outpost.api.calendar import delete_event

    client = _get_client()
    delete_event(client, event_id)
    stderr.print(f"[green]Deleted event:[/green] {event_id}")


# ── Mail commands ────────────────────────────────────────────────────────────


@mail_app.command("list")
@handle_errors
def mail_list_cmd(
    folder: str = typer.Option("inbox", "--folder", "-f", help="Mail folder (inbox, sentitems, drafts, deleteditems)"),
    top: int = typer.Option(25, "--top", "-n", help="Number of messages to show"),
    unread: bool = typer.Option(False, "--unread", "-u", help="Show only unread messages"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List email messages."""
    from outpost.api.mail import list_messages
    from outpost.formatters.mail import print_messages_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    messages = list_messages(client, folder=folder, top=top, unread=unread)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(messages)
    else:
        print_messages_table(messages, full_id=full_id)


@mail_app.command("read")
@handle_errors
def mail_read_cmd(
    message_id: str = typer.Argument(..., help="Message ID to read"),
    download: bool = typer.Option(False, "--download", help="Download attachments to current directory"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Read a specific email message."""
    from outpost.api.mail import get_message, list_attachments, download_attachment
    from outpost.formatters.mail import print_message_detail
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    message = get_message(client, message_id)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(message)
    else:
        print_message_detail(message)

    if download and message.get("hasAttachments"):
        attachments = list_attachments(client, message_id)
        for att in attachments:
            filename, content = download_attachment(client, message_id, att["id"])
            with open(filename, "wb") as f:
                f.write(content)
            stderr.print(f"[green]Downloaded:[/green] {filename} ({len(content)} bytes)")


@mail_app.command("send")
@handle_errors
def mail_send_cmd(
    to: str = typer.Option(..., "--to", help="Recipient email (comma-separated for multiple)"),
    subject: str = typer.Option(..., "--subject", "-s", help="Email subject"),
    body: str = typer.Option(..., "--body", "-b", help="Email body text"),
    cc: Optional[str] = typer.Option(None, "--cc", help="CC recipients (comma-separated)"),
    attach: Optional[list[str]] = typer.Option(None, "--attach", "-a", help="File to attach (repeatable)"),
):
    """Send an email."""
    from outpost.api.mail import send_message, send_message_with_attachments

    client = _get_client()
    to_list = [addr.strip() for addr in to.split(",")]
    cc_list = [addr.strip() for addr in cc.split(",")] if cc else None

    if attach:
        send_message_with_attachments(client, to_list, subject, body, attach, cc=cc_list)
    else:
        send_message(client, to_list, subject, body, cc=cc_list)
    stderr.print(f"[green]Sent email:[/green] {subject}")


@mail_app.command("reply")
@handle_errors
def mail_reply_cmd(
    message_id: str = typer.Argument(..., help="Message ID to reply to"),
    body: str = typer.Option(..., "--body", "-b", help="Reply text"),
):
    """Reply to an email."""
    from outpost.api.mail import reply_message

    client = _get_client()
    reply_message(client, message_id, body)
    stderr.print(f"[green]Replied to message:[/green] {message_id}")


@mail_app.command("delete")
@handle_errors
def mail_delete_cmd(
    message_id: str = typer.Argument(..., help="Message ID to delete"),
):
    """Delete an email."""
    from outpost.api.mail import delete_message

    client = _get_client()
    delete_message(client, message_id)
    stderr.print(f"[green]Deleted message:[/green] {message_id}")


@mail_app.command("search")
@handle_errors
def mail_search_cmd(
    query: str = typer.Argument(..., help="Search query"),
    top: int = typer.Option(25, "--top", "-n", help="Number of results"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Search email messages."""
    from outpost.api.mail import search_messages
    from outpost.formatters.mail import print_messages_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    messages = search_messages(client, query, top=top)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(messages)
    else:
        print_messages_table(messages, full_id=full_id)


# ── Contact commands ────────────────────────────────────────────────────────


@contact_app.command("list")
@handle_errors
def contact_list_cmd(
    top: int = typer.Option(50, "--top", "-n", help="Number of contacts to show"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List contacts."""
    from outpost.api.contacts import list_contacts
    from outpost.formatters.contacts import print_contacts_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    contacts = list_contacts(client, top=top)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(contacts)
    else:
        print_contacts_table(contacts)


@contact_app.command("search")
@handle_errors
def contact_search_cmd(
    query: str = typer.Argument(..., help="Search query (name or email)"),
    top: int = typer.Option(25, "--top", "-n", help="Number of results"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Search contacts by name or email."""
    from outpost.api.contacts import search_contacts
    from outpost.formatters.contacts import print_contacts_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    contacts = search_contacts(client, query, top=top)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(contacts)
    else:
        print_contacts_table(contacts)


# ── Teams commands ───────────────────────────────────────────────────────────


@teams_app.command("list")
@handle_errors
def teams_list_cmd(
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List your joined Microsoft Teams."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import list_teams
    from outpost.formatters.teams import print_teams_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    teams = list_teams(client)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(teams)
    else:
        print_teams_table(teams, full_id=full_id)


@teams_app.command("channels")
@handle_errors
def teams_channels_cmd(
    team_id: str = typer.Argument(..., help="Team ID"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List channels in a team."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import list_channels
    from outpost.formatters.teams import print_channels_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    channels = list_channels(client, team_id)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(channels)
    else:
        print_channels_table(channels, full_id=full_id)


@teams_app.command("messages")
@handle_errors
def teams_messages_cmd(
    team_id: str = typer.Argument(..., help="Team ID"),
    channel_id: str = typer.Argument(..., help="Channel ID"),
    top: int = typer.Option(25, "--top", "-n", help="Number of messages"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Read messages from a Teams channel."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import list_messages
    from outpost.formatters.teams import print_messages_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    messages = list_messages(client, team_id, channel_id, top=top)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(messages)
    else:
        print_messages_table(messages, full_id=full_id)


@teams_app.command("send")
@handle_errors
def teams_send_cmd(
    team_id: str = typer.Argument(..., help="Team ID"),
    channel_id: str = typer.Argument(..., help="Channel ID"),
    body: str = typer.Option(..., "--body", "-b", help="Message content"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Send a message to a Teams channel."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import send_message
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    result = send_message(client, team_id, channel_id, body)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Sent message to channel[/green]")


@teams_app.command("files")
@handle_errors
def teams_files_cmd(
    team_id: str = typer.Argument(..., help="Team ID"),
    channel_id: str = typer.Argument(..., help="Channel ID"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List files in a Teams channel's SharePoint folder."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import get_channel_files_folder, list_files
    from outpost.formatters.teams import print_files_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    folder = get_channel_files_folder(client, team_id, channel_id)
    drive_id = folder["parentReference"]["driveId"]
    item_id = folder["id"]
    files = list_files(client, drive_id, item_id)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(files)
    else:
        print_files_table(files)


@teams_app.command("download")
@handle_errors
def teams_download_cmd(
    drive_id: str = typer.Argument(..., help="Drive ID"),
    item_id: str = typer.Argument(..., help="Item ID"),
):
    """Download a file from Teams/SharePoint."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import download_file

    client = _get_client()
    filename, content = download_file(client, drive_id, item_id)
    with open(filename, "wb") as f:
        f.write(content)
    stderr.print(f"[green]Downloaded:[/green] {filename} ({len(content)} bytes)")


@teams_app.command("upload")
@handle_errors
def teams_upload_cmd(
    drive_id: str = typer.Argument(..., help="Drive ID"),
    parent_item_id: str = typer.Argument(..., help="Parent folder item ID"),
    filepath: str = typer.Argument(..., help="Local file path to upload"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Upload a local file to Teams/SharePoint."""
    from pathlib import Path
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import upload_file
    from outpost.formatters.json_fmt import print_json

    path = Path(filepath)
    if not path.exists():
        typer.echo(f"Error: File not found: {filepath}", err=True)
        raise typer.Exit(1)

    client = _get_client()
    content = path.read_bytes()
    result = upload_file(client, drive_id, parent_item_id, path.name, content)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Uploaded:[/green] {path.name} ({len(content)} bytes)")


@teams_app.command("chats")
@handle_errors
def teams_chats_cmd(
    top: int = typer.Option(25, "--top", "-n", help="Number of chats to show"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List your recent Teams chats (1:1, group, and meeting)."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import list_chats
    from outpost.formatters.teams import print_chats_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    chats = list_chats(client, top=top)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(chats)
    else:
        print_chats_table(chats, full_id=full_id)


@teams_app.command("chat-messages")
@handle_errors
def teams_chat_messages_cmd(
    chat_id: str = typer.Argument(..., help="Chat ID"),
    top: int = typer.Option(25, "--top", "-n", help="Number of messages"),
    full_id: bool = typer.Option(False, "--full-id", help="Show full IDs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Read messages from a Teams chat."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import list_chat_messages
    from outpost.formatters.teams import print_messages_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    messages = list_chat_messages(client, chat_id, top=top)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(messages)
    else:
        print_messages_table(messages, full_id=full_id)


@teams_app.command("chat-send")
@handle_errors
def teams_chat_send_cmd(
    chat_id: str = typer.Argument(..., help="Chat ID"),
    body: str = typer.Option(..., "--body", "-b", help="Message content"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Send a message to a Teams chat."""
    from outpost.config import is_feature_enabled

    if not is_feature_enabled("teams"):
        typer.echo(
            "Error: The 'teams' feature is not enabled. "
            "Run 'outpost setup' and enable it to use this command.",
            err=True,
        )
        raise typer.Exit(1)

    from outpost.api.teams import send_chat_message
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    result = send_chat_message(client, chat_id, body)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Sent message to chat[/green]")


# ── Auth commands ────────────────────────────────────────────────────────────


def require_feature(feature: str):
    """Decorator that exits with a helpful error if a feature is not enabled."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from outpost.config import is_feature_enabled

            if not is_feature_enabled(feature):
                typer.echo(
                    f"Error: The '{feature}' feature is not enabled. "
                    f"Run 'outpost setup' and enable it to use this command.",
                    err=True,
                )
                raise typer.Exit(1)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.command()
@handle_errors
def setup():
    """Interactive first-time setup wizard."""
    from outpost.auth import login_interactive
    from outpost.config import load_config, save_config, get_active_scopes, get_workspace_dir

    stderr.print("[bold]Welcome to Outpost![/bold]")
    stderr.print("Let's connect your Microsoft account.\n")

    config = load_config()
    enabled = list(config.get("enabled_features", []))

    # Prompt for optional features
    stderr.print("[bold]Optional features[/bold] (require additional permissions):")
    stderr.print("  Microsoft Teams — read/send channel messages, browse channel files\n")

    teams_current = "teams" in enabled
    prompt = "Enable Teams access?"
    if teams_current:
        prompt += " (currently enabled) [Y/n]"
    else:
        prompt += " (your admin may need to approve) [y/N]"

    answer = typer.prompt(prompt, default="y" if teams_current else "n")
    if answer.lower().startswith("y"):
        if "teams" not in enabled:
            enabled.append("teams")
    else:
        if "teams" in enabled:
            enabled.remove("teams")

    # Prompt for timezone
    current_tz = config.get("timezone", "UTC")
    stderr.print(f"\n[bold]Timezone[/bold] (used for calendar events):")
    stderr.print("  Enter an IANA timezone name, e.g. America/New_York, Europe/London, Asia/Tokyo")
    stderr.print(f"  See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones\n")
    tz_answer = typer.prompt(f"Timezone", default=current_tz)
    config["timezone"] = tz_answer

    config["enabled_features"] = enabled
    save_config(config)

    # Ensure workspace directory exists for MCP filesystem server
    get_workspace_dir()

    scopes = get_active_scopes(config)
    success = login_interactive(scopes=scopes)

    if success:
        if "teams" in enabled:
            stderr.print("[green]Teams access:[/green] enabled")
        else:
            stderr.print("[dim]Teams access:[/dim] disabled")


@auth_app.command("status")
@handle_errors
def auth_status(
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Show current authentication status."""
    from outpost.auth import get_auth_status
    from outpost.formatters.json_fmt import print_json

    status = get_auth_status()
    fmt = OutputFormat(output)

    if fmt == OutputFormat.json:
        print_json(status)
    else:
        if status["logged_in"]:
            stderr.print(f"[green]Logged in[/green] as [bold]{status['username']}[/bold]")
        else:
            stderr.print("[yellow]Not logged in.[/yellow] Run [bold]outpost setup[/bold] to connect.")


# ── MCP commands ────────────────────────────────────────────────────────────


@mcp_app.command("serve")
def mcp_serve(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio|sse|streamable-http"),
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="Host to bind (use 0.0.0.0 for LAN access)"),
    port: int = typer.Option(8080, "--port", "-p", help="Port for network transports"),
):
    """Start the MCP server."""
    from outpost.mcp_server import mcp, create_mcp_server

    if transport in ("sse", "streamable-http"):
        from outpost.config import get_mcp_api_key

        key = get_mcp_api_key()

        from fastmcp.server.auth import StaticTokenVerifier

        auth = StaticTokenVerifier(
            tokens={key: {"client_id": "outpost-remote", "scopes": ["all"]}},
        )
        server = create_mcp_server(auth=auth)
        stderr.print(f"Starting MCP server ({transport}) on {host}:{port}")
        stderr.print(f"API key required — run [bold]outpost mcp key[/bold] to view")
        server.run(transport=transport, host=host, port=port)
    else:
        mcp.run()


@mcp_app.command("key")
@handle_errors
def mcp_key(
    regenerate: bool = typer.Option(False, "--regenerate", help="Generate a new API key"),
):
    """Display or regenerate the MCP API key for remote access."""
    from outpost.config import get_mcp_api_key, generate_mcp_api_key

    if regenerate:
        key = generate_mcp_api_key()
        stderr.print(f"[green]New API key generated.[/green]")
    else:
        key = get_mcp_api_key()

    stderr.print(f"\nAPI key: [bold]{key}[/bold]")
    stderr.print(f"\nUse as Bearer token in the Authorization header.")
    stderr.print(f"For Claude connectors, paste this key during connector setup.")


# ── Update command ───────────────────────────────────────────────────────────


@app.command()
@handle_errors
def update(
    check: bool = typer.Option(False, "--check", help="Only check for updates, don't install"),
    force: bool = typer.Option(False, "--force", help="Ignore cache, check GitHub now"),
):
    """Check for updates and self-update outpost."""
    from outpost import __version__
    from outpost.updater import check_for_update, perform_update

    stderr.print(f"Current version: [bold]{__version__}[/bold]")

    update_info = check_for_update(force=force)

    if not update_info:
        stderr.print("[green]You're up to date![/green]")
        return

    stderr.print(f"Latest version:  [bold]{update_info['latest_version']}[/bold]")

    if check:
        stderr.print(f"\nRun [bold]outpost update[/bold] to upgrade.")
        return

    stderr.print(f"\nInstalling update...")
    success = perform_update(update_info["download_url"])

    if success:
        stderr.print(f"[green]Updated to {update_info['latest_version']}![/green]")
    else:
        stderr.print("[red]Update failed.[/red] Try manually:")
        stderr.print(f"  pip install --upgrade {update_info['download_url']}")
        raise typer.Exit(1)


# ── Entry point with error handling ──────────────────────────────────────────


def app_entry():
    """Entry point that wraps the Typer app with error handling."""
    try:
        app()
    except SystemExit:
        raise
    except GraphAPIError as exc:
        if exc.status_code == 401:
            stderr.print("[red]Authentication expired.[/red] Run [bold]outpost setup[/bold] to re-authenticate.")
        elif exc.status_code == 403:
            stderr.print("[red]Permission denied.[/red] You may need to re-consent. Run [bold]outpost setup[/bold].")
        elif exc.status_code == 429:
            stderr.print("[yellow]Rate limited by Microsoft.[/yellow] Please wait a moment and try again.")
        else:
            stderr.print(f"[red]Graph API error ({exc.status_code}):[/red] {exc.message}")
        sys.exit(1)
    except httpx.ConnectError:
        stderr.print("[red]Network error.[/red] Check your internet connection and try again.")
        sys.exit(1)
    except ValueError as exc:
        stderr.print(f"[red]Invalid input:[/red] {exc}")
        sys.exit(1)
    except Exception as exc:
        stderr.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)
