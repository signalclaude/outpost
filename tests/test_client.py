"""Tests for outpost Graph API client."""

import httpx
import pytest
import respx

from outpost.api.client import GraphClient, GraphAPIError


GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class TestGraphClient:
    def test_auth_header_injected(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me").mock(return_value=httpx.Response(200, json={"displayName": "Test"}))
            client = GraphClient(token="test-token-123")
            client.get("/me")
            assert route.called
            request = route.calls[0].request
            assert request.headers["authorization"] == "Bearer test-token-123"

    def test_get_success(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me").mock(return_value=httpx.Response(200, json={"displayName": "Test User"}))
            client = GraphClient(token="fake")
            result = client.get("/me")
            assert result["displayName"] == "Test User"

    def test_post_success(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.post("/me/todo/lists").mock(
                return_value=httpx.Response(201, json={"id": "list-1", "displayName": "My List"})
            )
            client = GraphClient(token="fake")
            result = client.post("/me/todo/lists", json={"displayName": "My List"})
            assert result["id"] == "list-1"

    def test_get_params(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/events").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            client = GraphClient(token="fake")
            client.get("/me/events", params={"$top": "10"})
            assert route.called

    def test_400_raises_graph_error(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me").mock(
                return_value=httpx.Response(
                    400,
                    json={"error": {"code": "BadRequest", "message": "Invalid request"}},
                )
            )
            client = GraphClient(token="fake")
            with pytest.raises(GraphAPIError) as exc_info:
                client.get("/me")
            assert exc_info.value.status_code == 400
            assert exc_info.value.error_code == "BadRequest"

    def test_401_raises_graph_error(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me").mock(
                return_value=httpx.Response(
                    401,
                    json={"error": {"code": "InvalidAuthenticationToken", "message": "Token expired"}},
                )
            )
            client = GraphClient(token="fake")
            with pytest.raises(GraphAPIError) as exc_info:
                client.get("/me")
            assert exc_info.value.status_code == 401

    def test_500_raises_graph_error(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )
            client = GraphClient(token="fake")
            with pytest.raises(GraphAPIError) as exc_info:
                client.get("/me")
            assert exc_info.value.status_code == 500

    def test_204_returns_empty_dict(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.post("/me/todo/lists/1/tasks/1").mock(
                return_value=httpx.Response(204)
            )
            client = GraphClient(token="fake")
            result = client.post("/me/todo/lists/1/tasks/1")
            assert result == {}

    def test_patch_success(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.patch("/me/todo/lists/1/tasks/1").mock(
                return_value=httpx.Response(200, json={"id": "1", "title": "Updated"})
            )
            client = GraphClient(token="fake")
            result = client.patch("/me/todo/lists/1/tasks/1", json={"title": "Updated"})
            assert result["title"] == "Updated"

    def test_patch_error(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.patch("/me/todo/lists/1/tasks/bad").mock(
                return_value=httpx.Response(
                    400, json={"error": {"code": "BadRequest", "message": "Invalid"}}
                )
            )
            client = GraphClient(token="fake")
            with pytest.raises(GraphAPIError) as exc_info:
                client.patch("/me/todo/lists/1/tasks/bad", json={})
            assert exc_info.value.status_code == 400

    def test_delete_success_204(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.delete("/me/todo/lists/1/tasks/1").mock(
                return_value=httpx.Response(204)
            )
            client = GraphClient(token="fake")
            result = client.delete("/me/todo/lists/1/tasks/1")
            assert result == {}

    def test_delete_error_404(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.delete("/me/todo/lists/1/tasks/bad").mock(
                return_value=httpx.Response(
                    404, json={"error": {"code": "NotFound", "message": "Not found"}}
                )
            )
            client = GraphClient(token="fake")
            with pytest.raises(GraphAPIError) as exc_info:
                client.delete("/me/todo/lists/1/tasks/bad")
            assert exc_info.value.status_code == 404

    def test_202_returns_empty_dict(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.post("/me/sendMail").mock(
                return_value=httpx.Response(202)
            )
            client = GraphClient(token="fake")
            result = client.post("/me/sendMail", json={})
            assert result == {}

    def test_get_with_extra_headers(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me/contacts").mock(
                return_value=httpx.Response(200, json={"value": []})
            )
            client = GraphClient(token="fake")
            client.get("/me/contacts", headers={"ConsistencyLevel": "eventual"})
            assert route.called
            request = route.calls[0].request
            assert request.headers["consistencylevel"] == "eventual"

    def test_context_manager(self):
        with GraphClient(token="fake") as client:
            assert client._token == "fake"
