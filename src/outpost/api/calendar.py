"""Microsoft Outlook Calendar API operations."""

from datetime import datetime, timedelta

from outpost.api.client import GraphClient
from outpost.utils.dates import to_graph_datetime, today_range


DEFAULT_DURATION_MINUTES = 30


VALID_SHOW_AS = ("free", "tentative", "busy", "oof", "workingElsewhere")


def create_event(
    client: GraphClient,
    title: str,
    start: datetime,
    end: datetime | None = None,
    duration: int | None = None,
    attendees: list[str] | None = None,
    show_as: str | None = None,
    timezone: str = "UTC",
) -> dict:
    """Create a calendar event.

    Args:
        client: GraphClient instance
        title: Event title/subject
        start: Start datetime
        end: End datetime (optional if duration is given)
        duration: Duration in minutes (optional, default 30 if no end)
        attendees: List of attendee email addresses (optional)
        show_as: Free/busy status (free, tentative, busy, oof, workingElsewhere)
        timezone: IANA timezone name (e.g. 'America/New_York')

    Returns: Created event dict from Graph API
    """
    if end is None:
        minutes = duration or DEFAULT_DURATION_MINUTES
        end = start + timedelta(minutes=minutes)

    body: dict = {
        "subject": title,
        "start": to_graph_datetime(start, timezone=timezone),
        "end": to_graph_datetime(end, timezone=timezone),
    }

    if attendees:
        body["attendees"] = [
            {"emailAddress": {"address": email}, "type": "required"}
            for email in attendees
        ]

    if show_as is not None:
        if show_as not in VALID_SHOW_AS:
            raise ValueError(f"Invalid showAs value: {show_as!r}. Must be one of {VALID_SHOW_AS}")
        body["showAs"] = show_as

    return client.post("/me/events", json=body)


def get_calendar_view(
    client: GraphClient,
    start_dt: datetime,
    end_dt: datetime,
) -> list[dict]:
    """Get calendar events within a date range using calendarView."""
    params = {
        "startDateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "endDateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "$orderby": "start/dateTime",
    }
    return client.get_all_pages("/me/calendarview", params=params)


def get_today_events(client: GraphClient) -> list[dict]:
    """Get today's calendar events."""
    start, end = today_range()
    return get_calendar_view(client, start, end)


def get_week_events(client: GraphClient) -> list[dict]:
    """Get this week's calendar events (today through 7 days out)."""
    start, _ = today_range()
    end = start + timedelta(days=7)
    return get_calendar_view(client, start, end)


def get_next_events(client: GraphClient, count: int = 1) -> list[dict]:
    """Get the next upcoming event(s) from now."""
    now = datetime.now()
    end = now + timedelta(days=30)
    params = {
        "startDateTime": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "$orderby": "start/dateTime",
        "$top": str(count),
    }
    result = client.get("/me/calendarview", params=params)
    return result.get("value", [])


def update_event(
    client: GraphClient,
    event_id: str,
    title: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    attendees: list[str] | None = None,
    show_as: str | None = None,
    timezone: str = "UTC",
) -> dict:
    """Update an existing calendar event. Only provided fields are changed."""
    body: dict = {}
    if title is not None:
        body["subject"] = title
    if start is not None:
        body["start"] = to_graph_datetime(start, timezone=timezone)
    if end is not None:
        body["end"] = to_graph_datetime(end, timezone=timezone)
    if attendees is not None:
        body["attendees"] = [
            {"emailAddress": {"address": email}, "type": "required"}
            for email in attendees
        ]
    if show_as is not None:
        if show_as not in VALID_SHOW_AS:
            raise ValueError(f"Invalid showAs value: {show_as!r}. Must be one of {VALID_SHOW_AS}")
        body["showAs"] = show_as
    return client.patch(f"/me/events/{event_id}", json=body)


def delete_event(client: GraphClient, event_id: str) -> dict:
    """Delete a calendar event."""
    return client.delete(f"/me/events/{event_id}")
