"""JSON output formatter for outpost CLI."""

import json
import sys


def print_json(data: list[dict] | dict) -> None:
    """Print data as formatted JSON to stdout."""
    json.dump(data, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
