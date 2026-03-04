"""Shared test fixtures for outpost."""

import pytest
import respx
import httpx

from outpost.api.client import GraphClient


GRAPH_BASE = "https://graph.microsoft.com/v1.0"


@pytest.fixture
def mock_graph():
    """respx mock router scoped to Graph API base URL."""
    with respx.mock(base_url=GRAPH_BASE) as router:
        yield router


@pytest.fixture
def graph_client():
    """GraphClient with a fake token for testing."""
    return GraphClient(token="fake-test-token")
