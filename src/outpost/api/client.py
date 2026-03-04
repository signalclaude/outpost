"""Base Microsoft Graph API client for outpost."""

import httpx

from outpost.config import GRAPH_BASE_URL


class GraphAPIError(Exception):
    """Error from the Microsoft Graph API."""

    def __init__(self, status_code: int, error_code: str, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(f"Graph API error {status_code}: [{error_code}] {message}")


class GraphClient:
    """Synchronous HTTP client for Microsoft Graph API with auth header injection."""

    def __init__(self, token: str):
        self._token = token
        self._client = httpx.Client(
            base_url=GRAPH_BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    def get(self, path: str, params: dict | None = None, headers: dict | None = None) -> dict:
        """Make a GET request to the Graph API."""
        response = self._client.get(path, params=params, headers=headers)
        return self._handle_response(response)

    def post(self, path: str, json: dict | None = None) -> dict:
        """Make a POST request to the Graph API."""
        response = self._client.post(path, json=json)
        return self._handle_response(response)

    def patch(self, path: str, json: dict | None = None) -> dict:
        """Make a PATCH request to the Graph API."""
        response = self._client.patch(path, json=json)
        return self._handle_response(response)

    def delete(self, path: str) -> dict:
        """Make a DELETE request to the Graph API."""
        response = self._client.delete(path)
        return self._handle_response(response)

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
