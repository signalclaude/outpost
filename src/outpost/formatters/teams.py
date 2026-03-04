"""Rich table formatters for Microsoft Teams output."""

from rich.console import Console
from rich.table import Table


def print_teams_table(teams: list[dict], console: Console | None = None, full_id: bool = False) -> None:
    """Print a list of joined teams as a rich table."""
    console = console or Console()
    table = Table(title="Teams")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Description")

    for t in teams:
        team_id = t.get("id", "") if full_id else t.get("id", "")[:8]
        name = t.get("displayName", "")
        desc = t.get("description", "") or ""
        table.add_row(team_id, name, desc[:60])

    console.print(table)


def print_channels_table(channels: list[dict], console: Console | None = None, full_id: bool = False) -> None:
    """Print a list of channels as a rich table."""
    console = console or Console()
    table = Table(title="Channels")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Type")

    for ch in channels:
        ch_id = ch.get("id", "") if full_id else ch.get("id", "")[:8]
        name = ch.get("displayName", "")
        ch_type = ch.get("membershipType", "standard")
        table.add_row(ch_id, name, ch_type)

    console.print(table)


def print_messages_table(messages: list[dict], console: Console | None = None, full_id: bool = False) -> None:
    """Print a list of channel messages as a rich table."""
    console = console or Console()
    table = Table(title="Messages")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("From", style="bold")
    table.add_column("Message")
    table.add_column("Date")

    for msg in messages:
        msg_id = msg.get("id", "") if full_id else msg.get("id", "")[:8]
        from_user = ""
        if from_info := msg.get("from"):
            if user := from_info.get("user"):
                from_user = user.get("displayName", "")
        body = ""
        if body_info := msg.get("body"):
            body = body_info.get("content", "")[:80]
        date = msg.get("createdDateTime", "")[:16]
        table.add_row(msg_id, from_user, body, date)

    console.print(table)


def print_chats_table(chats: list[dict], console: Console | None = None, full_id: bool = False) -> None:
    """Print a list of chats as a rich table."""
    console = console or Console()
    table = Table(title="Chats")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Type", style="bold")
    table.add_column("Topic / Members")
    table.add_column("Last Updated")

    for chat in chats:
        chat_id = chat.get("id", "") if full_id else chat.get("id", "")[:8]
        chat_type = chat.get("chatType", "")
        topic = chat.get("topic", "") or ""

        if topic:
            display = topic
        else:
            # Show member names from expanded members
            members = chat.get("members", [])
            names = [
                m.get("displayName", "")
                for m in members
                if m.get("displayName")
            ]
            display = ", ".join(names[:4])
            if len(names) > 4:
                display += f" +{len(names) - 4}"

        last_updated = ""
        if preview := chat.get("lastMessagePreview"):
            last_updated = preview.get("createdDateTime", "")[:16]

        table.add_row(chat_id, chat_type, display[:60], last_updated)

    console.print(table)


def print_files_table(files: list[dict], console: Console | None = None) -> None:
    """Print a list of drive items (files/folders) as a rich table."""
    console = console or Console()
    table = Table(title="Files")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Size")
    table.add_column("Modified")

    for item in files:
        item_id = item.get("id", "")[:8]
        name = item.get("name", "")
        item_type = "folder" if "folder" in item else "file"
        size = ""
        if s := item.get("size"):
            if s < 1024:
                size = f"{s} B"
            elif s < 1024 * 1024:
                size = f"{s // 1024} KB"
            else:
                size = f"{s // (1024 * 1024)} MB"
        modified = item.get("lastModifiedDateTime", "")[:16]
        table.add_row(item_id, name, item_type, size, modified)

    console.print(table)
