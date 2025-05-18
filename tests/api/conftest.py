"""Shared test fixtures and configurations for API tests.

This module contains fixtures that are specific to API testing, including:
- Test clients (sync and async)
- Authentication helpers
- Common request payloads
- Mock services for API dependencies
"""

import pytest
import json
from typing import Dict, Any, AsyncGenerator
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from loguru import logger

# Import the FastAPI app
from backend.api_gateway.app.main import app

# --- Test Clients ---


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Create a test client for the FastAPI application.

    This client is session-scoped to avoid creating a new client for each test.
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client for testing.

    This is useful for testing async endpoints directly.
    """
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


# --- Authentication Fixtures ---


@pytest.fixture
def test_user() -> Dict[str, Any]:
    """Return a test user's data."""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
    }


@pytest.fixture
def authenticated_client(client: TestClient, test_user: Dict[str, Any]) -> TestClient:
    """Return an authenticated test client.

    This fixture depends on the client fixture and adds authentication headers.
    """
    client.headers.update(
        {
            "Authorization": f"Bearer {test_user['id']}",
            "Content-Type": "application/json",
        }
    )
    return client


# --- Test Data Loaders ---


@pytest.fixture
def load_api_test_data(test_data_dir: Path) -> callable:
    """Return a function to load test data for API tests.

    Args:
        test_data_dir: Path to the test data directory (from the root conftest)

    Returns:
        A function that loads and returns test data from a JSON file
    """

    def _load_data(filename: str) -> Dict[str, Any]:
        """Load test data from a JSON file in the test_data directory."""
        filepath = test_data_dir / "api" / filename
        if not filepath.exists():
            (test_data_dir / "api").mkdir(exist_ok=True, parents=True)
            logger.warning(f"Test data file not found: {filepath}")
            return {}

        with open(filepath, "r") as f:
            return json.load(f)

    return _load_data


# --- Mock Services ---


@pytest.fixture
def mock_external_service(monkeypatch):
    """Mock an external service used by the API.

    Example usage:
        def test_something(mock_external_service):
            mock_external_service.return_value = {"status": "success"}
            # Test code that calls the external service
    """

    def _mock_service(*args, **kwargs):
        return {"status": "mocked"}

    monkeypatch.setattr("some.module.external_service_call", _mock_service)
    return _mock_service
