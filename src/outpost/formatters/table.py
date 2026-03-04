"""Rich table formatters for outpost CLI output."""

from rich.console import Console
from rich.table import Table


def print_tasks_table(tasks: list[dict], console: Console | None = None, full_id: bool = False) -> None:
    """Print a list of tasks as a rich table."""
    console = console or Console()
    table = Table(title="Tasks")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Due")
    table.add_column("Priority")
    table.add_column("Status")

    for t in tasks:
        task_id = t.get("id", "") if full_id else t.get("id", "")[:8]
        title = t.get("title", "")
        due = ""
        if due_dt := t.get("dueDateTime"):
            due = due_dt.get("dateTime", "")[:10]
        priority_map = {"low": "low", "normal": "", "high": "[red]high[/red]"}
        importance = t.get("importance", "normal")
        priority = priority_map.get(importance, importance)
        status = t.get("status", "")
        if status == "completed":
            status = "[green]done[/green]"
        else:
            status = "pending"
        table.add_row(task_id, title, due, priority, status)

    console.print(table)


def print_events_table(events: list[dict], console: Console | None = None, full_id: bool = False) -> None:
    """Print a list of calendar events as a rich table."""
    console = console or Console()
    table = Table(title="Events")
    if full_id:
        table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Time", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Duration")
    table.add_column("Location")

    for e in events:
        start = e.get("start", {})
        start_str = start.get("dateTime", "")[:16].replace("T", " ")
        title = e.get("subject", "")
        # Calculate duration
        end = e.get("end", {})
        duration = ""
        if start.get("dateTime") and end.get("dateTime"):
            from datetime import datetime

            try:
                s = datetime.fromisoformat(start["dateTime"])
                en = datetime.fromisoformat(end["dateTime"])
                mins = int((en - s).total_seconds() / 60)
                if mins >= 60:
                    duration = f"{mins // 60}h {mins % 60}m" if mins % 60 else f"{mins // 60}h"
                else:
                    duration = f"{mins}m"
            except (ValueError, TypeError):
                pass
        location = e.get("location", {}).get("displayName", "")
        row = []
        if full_id:
            row.append(e.get("id", ""))
        row.extend([start_str, title, duration, location])
        table.add_row(*row)

    console.print(table)


def print_task_lists_table(lists: list[dict], console: Console | None = None, full_id: bool = False) -> None:
    """Print task lists as a rich table."""
    console = console or Console()
    table = Table(title="Task Lists")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Type")

    for lst in lists:
        list_id = lst.get("id", "") if full_id else lst.get("id", "")[:8]
        name = lst.get("displayName", "")
        list_type = "Default" if lst.get("wellknownListName") == "defaultList" else ""
        table.add_row(list_id, name, list_type)

    console.print(table)
