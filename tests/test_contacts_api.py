"""Tests for outpost Contacts API layer."""

import httpx
import pytest
import respx

from outpost.api.client import GraphClient
from outpost.api.contacts import list_contacts, search_contacts


GRAPH_BASE = "https://graph.microsoft.com/v1.0"

SAMPLE_CONTACTS = {
    "value": [
        {
            "id": "contact-1",
            "displayName": "Alice Smith",
            "emailAddresses": [{"address": "alice@example.com", "name": "Alice"}],
            "businessPhones": ["+1-555-0100"],
            "mobilePhone": "+1-555-0101",
        },
        {
            "id": "contact-2",
            "displayName": "Bob Jones",
            "emailAddresses": [{"address": "bob@example.com", "name": "Bob"}],
            "businessPhones": [],
            "mobilePhone": None,
        },
    ]
}


@pytest.fixture
def client():
    return GraphClient(token="fake-token")


class TestListContacts:
    def test_list_all(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/contacts").mock(
                return_value=httpx.Response(200, json=SAMPLE_CONTACTS)
            )
            result = list_contacts(client)
        assert len(result) == 2
        assert result[0]["displayName"] == "Alice Smith"
        request_url = str(route.calls[0].request.url)
        assert "orderby" in request_url

    def test_list_with_top(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/contacts").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            list_contacts(client, top=10)
        request_url = str(route.calls[0].request.url)
        assert "top=10" in request_url

    def test_empty_contacts(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/contacts").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            result = list_contacts(client)
        assert result == []


class TestSearchContacts:
    def test_search(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/contacts").mock(
                return_value=httpx.Response(200, json={
                    "value": [SAMPLE_CONTACTS["value"][0]]
                })
            )
            result = search_contacts(client, "Alice")
        assert len(result) == 1
        assert result[0]["displayName"] == "Alice Smith"
        request = route.calls[0].request
        assert request.headers["consistencylevel"] == "eventual"

    def test_search_with_top(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/contacts").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            search_contacts(client, "test", top=5)
        request_url = str(route.calls[0].request.url)
        assert "top=5" in request_url

    def test_search_no_results(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/contacts").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            result = search_contacts(client, "nonexistent")
        assert result == []
