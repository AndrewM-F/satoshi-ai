"""Tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.api_gateway.app.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    # For FastAPI 0.95.0 and Starlette 0.26.1, we need to use the FastAPI TestClient
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
