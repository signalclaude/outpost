"""Tests for outpost Mail API layer."""

import json

import httpx
import pytest
import respx

from outpost.api.client import GraphClient
from outpost.api.mail import (
    delete_message,
    get_message,
    list_messages,
    reply_message,
    send_message,
)


GRAPH_BASE = "https://graph.microsoft.com/v1.0"

SAMPLE_MESSAGES = {
    "value": [
        {
            "id": "msg-1",
            "subject": "Hello",
            "from": {"emailAddress": {"address": "alice@example.com", "name": "Alice"}},
            "receivedDateTime": "2026-03-01T10:00:00Z",
            "isRead": False,
            "bodyPreview": "Hi there",
        },
        {
            "id": "msg-2",
            "subject": "Meeting notes",
            "from": {"emailAddress": {"address": "bob@example.com", "name": "Bob"}},
            "receivedDateTime": "2026-03-01T09:00:00Z",
            "isRead": True,
            "bodyPreview": "Notes from today",
        },
    ]
}

SAMPLE_MESSAGE_DETAIL = {
    "id": "msg-1",
    "subject": "Hello",
    "from": {"emailAddress": {"address": "alice@example.com", "name": "Alice"}},
    "toRecipients": [{"emailAddress": {"address": "me@example.com"}}],
    "ccRecipients": [],
    "receivedDateTime": "2026-03-01T10:00:00Z",
    "body": {"contentType": "text", "content": "Hi there, how are you?"},
    "isRead": True,
}


@pytest.fixture
def client():
    return GraphClient(token="fake-token")


class TestListMessages:
    def test_list_inbox(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/mailFolders/inbox/messages").mock(
                return_value=httpx.Response(200, json=SAMPLE_MESSAGES)
            )
            result = list_messages(client)
        assert len(result) == 2
        assert result[0]["subject"] == "Hello"
        request_url = str(route.calls[0].request.url)
        assert "orderby" in request_url

    def test_list_sentitems(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/mailFolders/sentitems/messages").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            result = list_messages(client, folder="sentitems")
        assert result == []

    def test_list_with_top(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/mailFolders/inbox/messages").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            list_messages(client, top=5)
        request_url = str(route.calls[0].request.url)
        assert "top=5" in request_url


class TestGetMessage:
    def test_get_message(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/messages/msg-1").mock(
                return_value=httpx.Response(200, json=SAMPLE_MESSAGE_DETAIL)
            )
            result = get_message(client, "msg-1")
        assert result["subject"] == "Hello"
        assert result["body"]["content"] == "Hi there, how are you?"


class TestSendMessage:
    def test_send_basic(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/sendMail").mock(
                return_value=httpx.Response(202)
            )
            result = send_message(client, ["bob@example.com"], "Test", "Hello Bob")
        assert result == {}
        body = json.loads(route.calls[0].request.content)
        assert body["message"]["subject"] == "Test"
        assert body["message"]["toRecipients"][0]["emailAddress"]["address"] == "bob@example.com"
        assert body["saveToSentItems"] is True

    def test_send_with_cc(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/sendMail").mock(
                return_value=httpx.Response(202)
            )
            send_message(client, ["bob@example.com"], "Test", "Hi", cc=["carol@example.com"])
        body = json.loads(route.calls[0].request.content)
        assert body["message"]["ccRecipients"][0]["emailAddress"]["address"] == "carol@example.com"

    def test_send_multiple_recipients(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/sendMail").mock(
                return_value=httpx.Response(202)
            )
            send_message(client, ["a@example.com", "b@example.com"], "Test", "Hi")
        body = json.loads(route.calls[0].request.content)
        assert len(body["message"]["toRecipients"]) == 2


class TestReplyMessage:
    def test_reply(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.post("/me/messages/msg-1/reply").mock(
                return_value=httpx.Response(202)
            )
            result = reply_message(client, "msg-1", "Thanks!")
        assert result == {}
        body = json.loads(route.calls[0].request.content)
        assert body["comment"] == "Thanks!"


class TestDeleteMessage:
    def test_delete(self, client):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.delete("/me/messages/msg-1").mock(
                return_value=httpx.Response(204)
            )
            result = delete_message(client, "msg-1")
        assert result == {}
        assert route.called
