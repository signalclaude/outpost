"""Base Microsoft Graph API client for outpost."""

import logging
import time

import httpx

from outpost.config import GRAPH_BASE_URL

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
DEFAULT_RETRY_AFTER = 5


class GraphAPIError(Exception):
    """Error from the Microsoft Graph API."""

    def __init__(self, status_code: int, error_code: str, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(f"Graph API error {status_code}: [{error_code}] {message}")


class GraphClient:
    """Synchronous HTTP client for Microsoft Graph API with auth header injection."""

    def __init__(self, token: str, max_retries: int = MAX_RETRIES):
        self._token = token
        self._max_retries = max_retries
        self._client = httpx.Client(
            base_url=GRAPH_BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    def _request_with_retry(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Execute an HTTP request with automatic retry on 429 (rate limited)."""
        for attempt in range(self._max_retries + 1):
            response = getattr(self._client, method)(path, **kwargs)
            if response.status_code != 429 or attempt == self._max_retries:
                return response
            retry_after = int(response.headers.get("Retry-After", DEFAULT_RETRY_AFTER))
            logger.info(
                "Rate limited (429). Retrying after %ds (attempt %d/%d)",
                retry_after, attempt + 1, self._max_retries,
            )
            time.sleep(retry_after)
        return response  # unreachable but satisfies type checker

    def get(self, path: str, params: dict | None = None, headers: dict | None = None) -> dict:
        """Make a GET request to the Graph API."""
        response = self._request_with_retry("get", path, params=params, headers=headers)
        return self._handle_response(response)

    def post(self, path: str, json: dict | None = None) -> dict:
        """Make a POST request to the Graph API."""
        response = self._request_with_retry("post", path, json=json)
        return self._handle_response(response)

    def patch(self, path: str, json: dict | None = None) -> dict:
        """Make a PATCH request to the Graph API."""
        response = self._request_with_retry("patch", path, json=json)
        return self._handle_response(response)

    def put(self, path: str, content: bytes, content_type: str = "application/octet-stream") -> dict:
        """Make a PUT request with binary content (e.g. file upload)."""
        response = self._request_with_retry(
            "put", path, content=content,
            headers={"Content-Type": content_type},
        )
        return self._handle_response(response)

    def delete(self, path: str) -> dict:
        """Make a DELETE request to the Graph API."""
        response = self._request_with_retry("delete", path)
        return self._handle_response(response)

    def get_all_pages(
        self,
        path: str,
        params: dict | None = None,
        headers: dict | None = None,
        max_pages: int = 50,
    ) -> list[dict]:
        """GET with automatic @odata.nextLink pagination.

        Returns the combined 'value' arrays from all pages.
        """
        all_items: list[dict] = []
        result = self.get(path, params=params, headers=headers)
        all_items.extend(result.get("value", []))

        pages = 1
        while "@odata.nextLink" in result and pages < max_pages:
            next_url = result["@odata.nextLink"]
            response = self._request_with_retry("get", next_url)
            result = self._handle_response(response)
            all_items.extend(result.get("value", []))
            pages += 1

        return all_items

    def _handle_response(self, response: httpx.Response) -> dict:
        """Parse the response, raising GraphAPIError on failure."""
        if response.status_code >= 400:
            try:
                body = response.json()
                error = body.get("error", {})
                code = error.get("code", "unknown")
                message = error.get("message", response.text)
            except Exception:
                code = "unknown"
                message = response.text
            raise GraphAPIError(response.status_code, code, message)
        if response.status_code in (202, 204):
            return {}
        return response.json()

    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
