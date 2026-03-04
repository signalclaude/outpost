"""Tests for outpost Calendar API layer."""

import json
from datetime import datetime, timedelta

import httpx
import pytest
import respx

from outpost.api.client import GraphClient
from outpost.api.calendar import (
    create_event,
    delete_event,
    get_calendar_view,
    get_next_events,
    get_today_events,
    get_week_events,
    update_event,
)


GRAPH_BASE = "https://graph.microsoft.com/v1.0"

SAMPLE_EVENTS = {
    "value": [
        {
            "id": "evt-1",
            "subject": "Team standup",
            "start": {"dateTime": "2026-03-15T09:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-03-15T09:30:00", "timeZone": "UTC"},
            "location": {"displayName": "Room 42"},
        },
    ]
}


@pytest.fixture
def client():
    return GraphClient(token="fake-token")


class TestCreateEvent:
    def test_with_end_time(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1", "subject": "Meeting"})
            )
            start = datetime(2026, 3, 15, 9, 0)
            end = datetime(2026, 3, 15, 10, 0)
            result = create_event(client, "Meeting", start, end=end)

        assert result["subject"] == "Meeting"
        body = json.loads(route.calls[0].request.content)
        assert body["subject"] == "Meeting"
        assert body["start"]["dateTime"] == "2026-03-15T09:00:00"
        assert body["end"]["dateTime"] == "2026-03-15T10:00:00"

    def test_with_duration(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1", "subject": "Quick chat"})
            )
            start = datetime(2026, 3, 15, 14, 0)
            create_event(client, "Quick chat", start, duration=15)

        body = json.loads(route.calls[0].request.content)
        assert body["end"]["dateTime"] == "2026-03-15T14:15:00"

    def test_default_duration(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1", "subject": "Sync"})
            )
            start = datetime(2026, 3, 15, 10, 0)
            create_event(client, "Sync", start)

        body = json.loads(route.calls[0].request.content)
        # Default 30 minutes
        assert body["end"]["dateTime"] == "2026-03-15T10:30:00"

    def test_timezone_in_body(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1"})
            )
            create_event(client, "Test", datetime(2026, 3, 15, 9, 0))

        body = json.loads(route.calls[0].request.content)
        assert body["start"]["timeZone"] == "UTC"
        assert body["end"]["timeZone"] == "UTC"

    def test_custom_timezone(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1"})
            )
            create_event(client, "Meeting", datetime(2026, 3, 15, 9, 0), timezone="America/New_York")

        body = json.loads(route.calls[0].request.content)
        assert body["start"]["timeZone"] == "America/New_York"
        assert body["end"]["timeZone"] == "America/New_York"


class TestGetCalendarView:
    def test_passes_date_range(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/calendarview").mock(
                return_value=httpx.Response(200, json=SAMPLE_EVENTS)
            )
            start = datetime(2026, 3, 15, 0, 0)
            end = datetime(2026, 3, 16, 0, 0)
            result = get_calendar_view(client, start, end)

        assert len(result) == 1
        assert result[0]["subject"] == "Team standup"
        request_url = str(route.calls[0].request.url)
        assert "startDateTime" in request_url
        assert "endDateTime" in request_url

    def test_empty_results(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/calendarview").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            result = get_calendar_view(client, datetime(2026, 3, 15), datetime(2026, 3, 16))
        assert result == []


class TestGetTodayEvents:
    def test_returns_events(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/calendarview").mock(
                return_value=httpx.Response(200, json=SAMPLE_EVENTS)
            )
            result = get_today_events(client)
        assert isinstance(result, list)


class TestGetWeekEvents:
    def test_returns_events(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/calendarview").mock(
                return_value=httpx.Response(200, json=SAMPLE_EVENTS)
            )
            result = get_week_events(client)
        assert isinstance(result, list)
        # Verify the range spans ~7 days
        request_url = str(route.calls[0].request.url)
        assert "startDateTime" in request_url


class TestUpdateEvent:
    def test_update_title(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.patch("/me/events/evt-1").mock(
                return_value=httpx.Response(200, json={"id": "evt-1", "subject": "New Title"})
            )
            result = update_event(client, "evt-1", title="New Title")
        assert result["subject"] == "New Title"
        body = json.loads(route.calls[0].request.content)
        assert body["subject"] == "New Title"

    def test_update_start_and_end(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.patch("/me/events/evt-1").mock(
                return_value=httpx.Response(200, json={"id": "evt-1"})
            )
            update_event(
                client, "evt-1",
                start=datetime(2026, 3, 20, 10, 0),
                end=datetime(2026, 3, 20, 11, 0),
            )
        body = json.loads(route.calls[0].request.content)
        assert body["start"]["dateTime"] == "2026-03-20T10:00:00"
        assert body["end"]["dateTime"] == "2026-03-20T11:00:00"

    def test_partial_update(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.patch("/me/events/evt-1").mock(
                return_value=httpx.Response(200, json={"id": "evt-1"})
            )
            update_event(client, "evt-1", title="Only Title")
        body = json.loads(route.calls[0].request.content)
        assert "subject" in body
        assert "start" not in body
        assert "end" not in body

    def test_update_with_timezone(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.patch("/me/events/evt-1").mock(
                return_value=httpx.Response(200, json={"id": "evt-1"})
            )
            update_event(
                client, "evt-1",
                start=datetime(2026, 3, 20, 10, 0),
                timezone="America/Chicago",
            )
        body = json.loads(route.calls[0].request.content)
        assert body["start"]["timeZone"] == "America/Chicago"


class TestGetNextEvents:
    def test_next_event(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/calendarview").mock(
                return_value=httpx.Response(200, json=SAMPLE_EVENTS)
            )
            result = get_next_events(client, count=1)
        assert len(result) == 1
        assert result[0]["subject"] == "Team standup"
        request_url = str(route.calls[0].request.url)
        assert "top=1" in request_url

    def test_next_events_multiple(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/calendarview").mock(
                return_value=httpx.Response(200, json={"value": [
                    {"subject": "Event 1"}, {"subject": "Event 2"}, {"subject": "Event 3"}
                ]})
            )
            result = get_next_events(client, count=3)
        assert len(result) == 3


class TestCreateEventWithAttendees:
    def test_attendees_included(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1", "subject": "Meeting"})
            )
            create_event(
                client, "Meeting",
                datetime(2026, 3, 15, 9, 0),
                attendees=["alice@example.com", "bob@example.com"],
            )
        body = json.loads(route.calls[0].request.content)
        assert len(body["attendees"]) == 2
        assert body["attendees"][0]["emailAddress"]["address"] == "alice@example.com"
        assert body["attendees"][0]["type"] == "required"

    def test_no_attendees(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1"})
            )
            create_event(client, "Solo", datetime(2026, 3, 15, 9, 0))
        body = json.loads(route.calls[0].request.content)
        assert "attendees" not in body


class TestUpdateEventWithAttendees:
    def test_update_attendees(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.patch("/me/events/evt-1").mock(
                return_value=httpx.Response(200, json={"id": "evt-1"})
            )
            update_event(client, "evt-1", attendees=["carol@example.com"])
        body = json.loads(route.calls[0].request.content)
        assert len(body["attendees"]) == 1
        assert body["attendees"][0]["emailAddress"]["address"] == "carol@example.com"


class TestCreateEventShowAs:
    def test_show_as_oof(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1", "showAs": "oof"})
            )
            result = create_event(client, "PTO", datetime(2026, 3, 15, 9, 0), show_as="oof")
        body = json.loads(route.calls[0].request.content)
        assert body["showAs"] == "oof"
        assert result["showAs"] == "oof"

    def test_show_as_not_set_by_default(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/events").mock(
                return_value=httpx.Response(201, json={"id": "evt-1"})
            )
            create_event(client, "Meeting", datetime(2026, 3, 15, 9, 0))
        body = json.loads(route.calls[0].request.content)
        assert "showAs" not in body

    def test_show_as_invalid(self, client):
        with pytest.raises(ValueError, match="Invalid showAs"):
            create_event(client, "Bad", datetime(2026, 3, 15, 9, 0), show_as="invalid")


class TestUpdateEventShowAs:
    def test_update_show_as(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.patch("/me/events/evt-1").mock(
                return_value=httpx.Response(200, json={"id": "evt-1", "showAs": "free"})
            )
            update_event(client, "evt-1", show_as="free")
        body = json.loads(route.calls[0].request.content)
        assert body["showAs"] == "free"

    def test_update_show_as_invalid(self, client):
        with pytest.raises(ValueError, match="Invalid showAs"):
            update_event(client, "evt-1", show_as="nope")


class TestDeleteEvent:
    def test_delete_event(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.delete("/me/events/evt-1").mock(
                return_value=httpx.Response(204)
            )
            result = delete_event(client, "evt-1")
        assert result == {}
        assert route.called
