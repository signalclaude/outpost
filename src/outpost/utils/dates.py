"""Natural language date/time parsing utilities for outpost."""

from datetime import date, datetime, time, timedelta

import parsedatetime


_cal = parsedatetime.Calendar()


def parse_natural_date(text: str) -> date:
    """Parse natural language or ISO date string into a date.

    Accepts: "tomorrow", "next friday", "2026-03-15", etc.
    Raises ValueError if the text cannot be parsed.
    """
    # Try ISO format first
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass

    result, status = _cal.parseDT(text)
    if status == 0:
        raise ValueError(f"Could not parse date: {text!r}")
    return result.date()


def parse_natural_datetime(text: str) -> datetime:
    """Parse natural language or ISO datetime string into a datetime.

    Accepts: "tomorrow 9am", "next friday 2pm", "2026-03-15T09:00", etc.
    Raises ValueError if the text cannot be parsed.
    """
    # Try ISO format first
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass

    result, status = _cal.parseDT(text)
    if status == 0:
        raise ValueError(f"Could not parse datetime: {text!r}")
    return result


def parse_time_string(text: str) -> time:
    """Parse a time string into a time object.

    Accepts: "9am", "14:00", "2:30pm", etc.
    Raises ValueError if the text cannot be parsed.
    """
    result, status = _cal.parseDT(text)
    if status == 0:
        raise ValueError(f"Could not parse time: {text!r}")
    return result.time()


def to_graph_datetime(dt: datetime) -> dict:
    """Format a datetime for the Microsoft Graph API.

    Returns: {"dateTime": "2026-03-15T09:00:00", "timeZone": "UTC"}
    """
    return {
        "dateTime": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "timeZone": "UTC",
    }


def to_graph_date(d: date) -> str:
    """Format a date for the Microsoft Graph API (ISO 8601 date string)."""
    return d.isoformat()


def today_range() -> tuple[datetime, datetime]:
    """Return the start and end of today as datetimes."""
    now = datetime.now()
    start = datetime(now.year, now.month, now.day, 0, 0, 0)
    end = start + timedelta(days=1)
    return start, end
