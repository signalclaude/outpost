"""Contacts formatters for outpost CLI output."""

from rich.console import Console
from rich.table import Table


def print_contacts_table(contacts: list[dict], console: Console | None = None) -> None:
    """Print a list of contacts as a rich table."""
    console = console or Console()
    table = Table(title="Contacts")
    table.add_column("Name", style="bold")
    table.add_column("Email")
    table.add_column("Phone")

    for c in contacts:
        name = c.get("displayName", "")
        email = ""
        if addrs := c.get("emailAddresses"):
            email = addrs[0].get("address", "") if addrs else ""
        phone = c.get("mobilePhone", "")
        if not phone:
            phones = c.get("businessPhones", [])
            phone = phones[0] if phones else ""
        table.add_row(name, email, phone)

    console.print(table)
