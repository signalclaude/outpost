"""Output formatting for outpost CLI."""

from enum import Enum


class OutputFormat(str, Enum):
    """Output format for CLI commands."""

    table = "table"
    json = "json"
