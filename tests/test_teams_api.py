"""Tests for outpost Teams API operations."""

from unittest.mock import patch, MagicMock

import httpx
import pytest
import respx

from outpost.api.teams import (
    list_teams,
    list_channels,
    list_messages,
    send_message,
    get_channel_files_folder,
    list_files,
    download_file,
    upload_file,
)
from outpost.api.client import GraphClient


GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class TestListTeams:
    def test_returns_teams(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/joinedTeams").mock(
                return_value=httpx.Response(200, json={
                    "value": [
                        {"id": "team-1", "displayName": "Engineering"},
                        {"id": "team-2", "displayName": "Marketing"},
                    ]
                })
            )
            client = GraphClient(token="fake")
            teams = list_teams(client)
        assert len(teams) == 2
        assert teams[0]["displayName"] == "Engineering"

    def test_empty_teams(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/joinedTeams").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            client = GraphClient(token="fake")
            teams = list_teams(client)
        assert teams == []


class TestListChannels:
    def test_returns_channels(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/teams/team-1/channels").mock(
                return_value=httpx.Response(200, json={
                    "value": [
                        {"id": "ch-1", "displayName": "General", "membershipType": "standard"},
                        {"id": "ch-2", "displayName": "Random", "membershipType": "standard"},
                    ]
                })
            )
            client = GraphClient(token="fake")
            channels = list_channels(client, "team-1")
        assert len(channels) == 2
        assert channels[0]["displayName"] == "General"


class TestListMessages:
    def test_returns_messages(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/teams/team-1/channels/ch-1/messages").mock(
                return_value=httpx.Response(200, json={
                    "value": [
                        {
                            "id": "msg-1",
                            "body": {"content": "Hello world"},
                            "from": {"user": {"displayName": "Alice"}},
                            "createdDateTime": "2026-03-01T10:00:00Z",
                        },
                    ]
                })
            )
            client = GraphClient(token="fake")
            messages = list_messages(client, "team-1", "ch-1", top=10)
        assert len(messages) == 1
        assert route.called

    def test_default_top(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/teams/team-1/channels/ch-1/messages").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            client = GraphClient(token="fake")
            list_messages(client, "team-1", "ch-1")
        assert route.called


class TestSendMessage:
    def test_sends_message(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.post("/teams/team-1/channels/ch-1/messages").mock(
                return_value=httpx.Response(201, json={
                    "id": "msg-new",
                    "body": {"content": "Hi team!"},
                })
            )
            client = GraphClient(token="fake")
            result = send_message(client, "team-1", "ch-1", "Hi team!")
        assert result["id"] == "msg-new"


class TestGetChannelFilesFolder:
    def test_returns_folder(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/teams/team-1/channels/ch-1/filesFolder").mock(
                return_value=httpx.Response(200, json={
                    "id": "folder-1",
                    "name": "General",
                    "parentReference": {"driveId": "drive-1"},
                })
            )
            client = GraphClient(token="fake")
            folder = get_channel_files_folder(client, "team-1", "ch-1")
        assert folder["id"] == "folder-1"
        assert folder["parentReference"]["driveId"] == "drive-1"


class TestListFiles:
    def test_returns_files(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/drives/drive-1/items/folder-1/children").mock(
                return_value=httpx.Response(200, json={
                    "value": [
                        {"id": "file-1", "name": "doc.pdf", "size": 1024},
                        {"id": "folder-2", "name": "subfolder", "folder": {"childCount": 3}},
                    ]
                })
            )
            client = GraphClient(token="fake")
            files = list_files(client, "drive-1", "folder-1")
        assert len(files) == 2
        assert files[0]["name"] == "doc.pdf"


class TestDownloadFile:
    def test_downloads_file(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/drives/drive-1/items/file-1").mock(
                return_value=httpx.Response(200, json={
                    "id": "file-1",
                    "name": "report.pdf",
                    "@microsoft.graph.downloadUrl": "https://cdn.example.com/report.pdf",
                })
            )
            # Mock the actual file download (outside Graph API)
            with respx.mock() as dl_router:
                dl_router.get("https://cdn.example.com/report.pdf").mock(
                    return_value=httpx.Response(200, content=b"PDF content here")
                )
                client = GraphClient(token="fake")
                filename, content = download_file(client, "drive-1", "file-1")
        assert filename == "report.pdf"
        assert content == b"PDF content here"

    def test_missing_download_url(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/drives/drive-1/items/file-1").mock(
                return_value=httpx.Response(200, json={
                    "id": "file-1",
                    "name": "report.pdf",
                })
            )
            client = GraphClient(token="fake")
            with pytest.raises(ValueError, match="No download URL"):
                download_file(client, "drive-1", "file-1")


class TestUploadFile:
    def test_uploads_file(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.put("/drives/drive-1/items/folder-1:/test.txt:/content").mock(
                return_value=httpx.Response(200, json={
                    "id": "new-item",
                    "name": "test.txt",
                    "size": 11,
                })
            )
            client = GraphClient(token="fake")
            result = upload_file(client, "drive-1", "folder-1", "test.txt", b"hello world")
        assert result["name"] == "test.txt"
        assert route.called
