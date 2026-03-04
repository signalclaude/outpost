"""Tests for outpost Graph API client."""

from unittest.mock import patch

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

    def test_put_success(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.put("/drives/d1/items/i1:/test.txt:/content").mock(
                return_value=httpx.Response(200, json={"id": "item-1", "name": "test.txt"})
            )
            client = GraphClient(token="fake")
            result = client.put(
                "/drives/d1/items/i1:/test.txt:/content",
                content=b"hello world",
            )
        assert result["name"] == "test.txt"
        assert route.called

    def test_put_error(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.put("/drives/d1/items/bad:/test.txt:/content").mock(
                return_value=httpx.Response(
                    404, json={"error": {"code": "NotFound", "message": "Not found"}}
                )
            )
            client = GraphClient(token="fake")
            with pytest.raises(GraphAPIError) as exc_info:
                client.put("/drives/d1/items/bad:/test.txt:/content", content=b"data")
            assert exc_info.value.status_code == 404

    def test_context_manager(self):
        with GraphClient(token="fake") as client:
            assert client._token == "fake"


class TestRetryOn429:
    def test_retry_succeeds(self):
        """429 on first try, 200 on retry."""
        with respx.mock(base_url=GRAPH_BASE) as router:
            route = router.get("/me").mock(
                side_effect=[
                    httpx.Response(429, headers={"Retry-After": "1"}),
                    httpx.Response(200, json={"displayName": "Test"}),
                ]
            )
            client = GraphClient(token="fake")
            with patch("outpost.api.client.time.sleep") as mock_sleep:
                result = client.get("/me")
            assert result["displayName"] == "Test"
            mock_sleep.assert_called_once_with(1)
            assert route.call_count == 2

    def test_retry_exhausted_raises(self):
        """429 on all retries raises GraphAPIError."""
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me").mock(
                return_value=httpx.Response(
                    429,
                    headers={"Retry-After": "1"},
                    json={"error": {"code": "TooManyRequests", "message": "Rate limited"}},
                )
            )
            client = GraphClient(token="fake", max_retries=2)
            with patch("outpost.api.client.time.sleep"):
                with pytest.raises(GraphAPIError) as exc_info:
                    client.get("/me")
            assert exc_info.value.status_code == 429

    def test_retry_uses_default_retry_after(self):
        """Missing Retry-After header uses default."""
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me").mock(
                side_effect=[
                    httpx.Response(429),
                    httpx.Response(200, json={"ok": True}),
                ]
            )
            client = GraphClient(token="fake")
            with patch("outpost.api.client.time.sleep") as mock_sleep:
                client.get("/me")
            from outpost.api.client import DEFAULT_RETRY_AFTER
            mock_sleep.assert_called_once_with(DEFAULT_RETRY_AFTER)


class TestGetAllPages:
    def test_single_page(self):
        with respx.mock(base_url=GRAPH_BASE) as router:
            router.get("/me/todo/lists").mock(
                return_value=httpx.Response(200, json={"value": [{"id": "1"}, {"id": "2"}]})
            )
            client = GraphClient(token="fake")
            result = client.get_all_pages("/me/todo/lists")
        assert len(result) == 2

    def test_multi_page(self):
        next_url = f"{GRAPH_BASE}/me/todo/lists?$skip=1"
        with respx.mock(base_url=GRAPH_BASE, assert_all_called=False) as router:
            router.get("/me/todo/lists").mock(
                side_effect=[
                    httpx.Response(200, json={
                        "value": [{"id": "1"}],
                        "@odata.nextLink": next_url,
                    }),
                    httpx.Response(200, json={"value": [{"id": "2"}]}),
                ]
            )
            client = GraphClient(token="fake")
            result = client.get_all_pages("/me/todo/lists")
        assert len(result) == 2

    def test_max_pages_limit(self):
        next_url = f"{GRAPH_BASE}/me/todo/lists?page=2"
        with respx.mock(base_url=GRAPH_BASE, assert_all_called=False) as router:
            router.get("/me/todo/lists").mock(
                side_effect=[
                    httpx.Response(200, json={
                        "value": [{"id": "1"}],
                        "@odata.nextLink": next_url,
                    }),
                    httpx.Response(200, json={
                        "value": [{"id": "2"}],
                        "@odata.nextLink": f"{GRAPH_BASE}/me/todo/lists?page=3",
                    }),
                ]
            )
            client = GraphClient(token="fake")
            result = client.get_all_pages("/me/todo/lists", max_pages=2)
        # Should stop after 2 pages even though there's a nextLink
        assert len(result) == 2
