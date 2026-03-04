"""Microsoft Outlook Calendar API operations."""

from datetime import datetime, timedelta

from outpost.api.client import GraphClient
from outpost.utils.dates import to_graph_datetime, today_range


DEFAULT_DURATION_MINUTES = 30


def create_event(
    client: GraphClient,
    title: str,
    start: datetime,
    end: datetime | None = None,
    duration: int | None = None,
) -> dict:
    """Create a calendar event.

    Args:
        client: GraphClient instance
        title: Event title/subject
        start: Start datetime
        end: End datetime (optional if duration is given)
        duration: Duration in minutes (optional, default 30 if no end)

    Returns: Created event dict from Graph API
    """
    if end is None:
        minutes = duration or DEFAULT_DURATION_MINUTES
        end = start + timedelta(minutes=minutes)

    body = {
        "subject": title,
        "start": to_graph_datetime(start),
        "end": to_graph_datetime(end),
    }

    return client.post("/me/events", json=body)


def get_calendar_view(
    client: GraphClient,
    start_dt: datetime,
    end_dt: datetime,
) -> list[dict]:
    """Get calendar events within a date range using calendarView.

    Args:
        client: GraphClient instance
        start_dt: Start of the range
        end_dt: End of the range

    Returns: List of event dicts
    """
    params = {
        "startDateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "endDateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "$orderby": "start/dateTime",
    }
    result = client.get("/me/calendarview", params=params)
    return result.get("value", [])


def get_today_events(client: GraphClient) -> list[dict]:
    """Get today's calendar events."""
    start, end = today_range()
    return get_calendar_view(client, start, end)


def get_week_events(client: GraphClient) -> list[dict]:
    """Get this week's calendar events (today through 7 days out)."""
    start, _ = today_range()
    end = start + timedelta(days=7)
    return get_calendar_view(client, start, end)


def update_event(
    client: GraphClient,
    event_id: str,
    title: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict:
    """Update an existing calendar event. Only provided fields are changed."""
    body: dict = {}
    if title is not None:
        body["subject"] = title
    if start is not None:
        body["start"] = to_graph_datetime(start)
    if end is not None:
        body["end"] = to_graph_datetime(end)
    return client.patch(f"/me/events/{event_id}", json=body)


def delete_event(client: GraphClient, event_id: str) -> dict:
    """Delete a calendar event."""
    return client.delete(f"/me/events/{event_id}")
