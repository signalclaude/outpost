"""Mail formatters for outpost CLI output."""

import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def print_messages_table(messages: list[dict], console: Console | None = None) -> None:
    """Print a list of messages as a rich table."""
    console = console or Console()
    table = Table(title="Messages")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("From")
    table.add_column("Subject", style="bold")
    table.add_column("Date")
    table.add_column("Status")

    for msg in messages:
        msg_id = msg.get("id", "")[:8]
        from_addr = ""
        if from_field := msg.get("from"):
            from_addr = from_field.get("emailAddress", {}).get("address", "")
        subject = msg.get("subject", "")
        date = msg.get("receivedDateTime", "")[:16].replace("T", " ")
        status = "Read" if msg.get("isRead") else "[bold]Unread[/bold]"
        table.add_row(msg_id, from_addr, subject, date, status)

    console.print(table)


def _strip_html(html: str) -> str:
    """Strip HTML tags for plain text display."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def print_message_detail(message: dict, console: Console | None = None) -> None:
    """Print a single message with full body."""
    console = console or Console()

    from_addr = ""
    if from_field := message.get("from"):
        from_addr = from_field.get("emailAddress", {}).get("address", "")

    to_addrs = ", ".join(
        r.get("emailAddress", {}).get("address", "")
        for r in message.get("toRecipients", [])
    )
    cc_addrs = ", ".join(
        r.get("emailAddress", {}).get("address", "")
        for r in message.get("ccRecipients", [])
    )

    subject = message.get("subject", "")
    date = message.get("receivedDateTime", "")[:19].replace("T", " ")

    header = f"[bold]Subject:[/bold] {subject}\n"
    header += f"[bold]From:[/bold]    {from_addr}\n"
    header += f"[bold]To:[/bold]      {to_addrs}\n"
    if cc_addrs:
        header += f"[bold]CC:[/bold]      {cc_addrs}\n"
    header += f"[bold]Date:[/bold]    {date}"

    console.print(Panel(header, title="Message"))

    body = message.get("body", {})
    content = body.get("content", "")
    if body.get("contentType") == "html":
        content = _strip_html(content)

    if content:
        console.print(Panel(content, title="Body"))
