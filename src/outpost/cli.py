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
mcp_app = typer.Typer(help="MCP server for Claude Desktop integration.", no_args_is_help=True)

app.add_typer(task_app, name="task")
app.add_typer(cal_app, name="cal")
app.add_typer(mail_app, name="mail")
app.add_typer(contact_app, name="contact")
app.add_typer(auth_app, name="auth")
app.add_typer(mcp_app, name="mcp")

stderr = Console(stderr=True)


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
        print_tasks_table(tasks)


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


# ── Calendar commands ────────────────────────────────────────────────────────


@cal_app.command("add")
@handle_errors
def cal_add(
    title: str = typer.Argument(..., help="Event title"),
    start: str = typer.Option(..., "--start", "-s", help="Start time (e.g. 'tomorrow 9am')"),
    end: Optional[str] = typer.Option(None, "--end", "-e", help="End time"),
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="Duration in minutes"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Add a calendar event."""
    from outpost.api.calendar import create_event
    from outpost.utils.dates import parse_natural_datetime
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    start_dt = parse_natural_datetime(start)
    end_dt = parse_natural_datetime(end) if end else None

    result = create_event(client, title, start_dt, end=end_dt, duration=duration)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(result)
    else:
        stderr.print(f"[green]Created event:[/green] {result.get('subject', title)}")


@cal_app.command("today")
@handle_errors
def cal_today(
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
        print_events_table(events)


@cal_app.command("list")
@handle_errors
def cal_list(
    date_str: Optional[str] = typer.Option(None, "--date", help="Show events for a specific date"),
    week: bool = typer.Option(False, "--week", "-w", help="Show this week's events"),
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
        print_events_table(events)


@cal_app.command("update")
@handle_errors
def cal_update(
    event_id: str = typer.Argument(..., help="Event ID to update"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    start: Optional[str] = typer.Option(None, "--start", "-s", help="New start time"),
    end: Optional[str] = typer.Option(None, "--end", "-e", help="New end time"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Update an existing calendar event."""
    from outpost.api.calendar import update_event
    from outpost.utils.dates import parse_natural_datetime
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    start_dt = parse_natural_datetime(start) if start else None
    end_dt = parse_natural_datetime(end) if end else None
    result = update_event(client, event_id, title=title, start=start_dt, end=end_dt)

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
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """List email messages."""
    from outpost.api.mail import list_messages
    from outpost.formatters.mail import print_messages_table
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    messages = list_messages(client, folder=folder, top=top)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(messages)
    else:
        print_messages_table(messages)


@mail_app.command("read")
@handle_errors
def mail_read_cmd(
    message_id: str = typer.Argument(..., help="Message ID to read"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table|json"),
):
    """Read a specific email message."""
    from outpost.api.mail import get_message
    from outpost.formatters.mail import print_message_detail
    from outpost.formatters.json_fmt import print_json

    client = _get_client()
    message = get_message(client, message_id)

    fmt = OutputFormat(output)
    if fmt == OutputFormat.json:
        print_json(message)
    else:
        print_message_detail(message)


@mail_app.command("send")
@handle_errors
def mail_send_cmd(
    to: str = typer.Option(..., "--to", help="Recipient email (comma-separated for multiple)"),
    subject: str = typer.Option(..., "--subject", "-s", help="Email subject"),
    body: str = typer.Option(..., "--body", "-b", help="Email body text"),
    cc: Optional[str] = typer.Option(None, "--cc", help="CC recipients (comma-separated)"),
):
    """Send an email."""
    from outpost.api.mail import send_message

    client = _get_client()
    to_list = [addr.strip() for addr in to.split(",")]
    cc_list = [addr.strip() for addr in cc.split(",")] if cc else None
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


# ── Auth commands ────────────────────────────────────────────────────────────


@app.command()
@handle_errors
def setup():
    """Interactive first-time setup wizard."""
    from outpost.auth import login_interactive

    stderr.print("[bold]Welcome to Outpost![/bold]")
    stderr.print("Let's connect your Microsoft account.\n")
    login_interactive()


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
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio|sse"),
    port: int = typer.Option(8080, "--port", "-p", help="Port for SSE transport"),
):
    """Start the MCP server."""
    from outpost.mcp_server import mcp

    if transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        mcp.run()


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
