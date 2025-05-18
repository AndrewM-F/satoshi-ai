"""Pytest configuration and fixtures for service layer tests.

This module contains fixtures and utilities for testing service layer components,
including service clients, mocks for external dependencies, and test data.
"""

from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any
import pytest

from loguru import logger

# --- Service Client Fixtures ---


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing services that make HTTP requests.

    Returns:
        A tuple of (mock_client, mock_response) where:
        - mock_client: The mocked HTTP client
        - mock_response: The response that will be returned by the client
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}

    mock_client = MagicMock()
    mock_client.request.return_value = mock_response
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response

    return mock_client, mock_response


@pytest.fixture
async def async_http_client():
    """Create an async HTTP client for testing async services.

    Returns:
        A tuple of (mock_client, mock_response) where:
        - mock_client: The mocked async HTTP client
        - mock_response: The async response that will be returned by the client
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}

    mock_client = AsyncMock()
    mock_client.request.return_value = mock_response
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response

    return mock_client, mock_response


# --- External Service Mocks ---


@pytest.fixture
def mock_google_services(monkeypatch):
    """Mock Google API clients and services.

    This fixture patches common Google API clients to prevent actual API calls
    during testing.
    """
    mocks = {
        "google.oauth2.credentials.Credentials": MagicMock(),
        "google_auth_oauthlib.flow.Flow": MagicMock(),
        "googleapiclient.discovery.build": MagicMock(),
    }

    for path, mock in mocks.items():
        monkeypatch.setattr(path, mock)

    return mocks


@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API client."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_completion = MagicMock()

    mock_chat.completions.create.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    mock_client.chat = mock_chat
    mock_client.completions = mock_completion

    monkeypatch.setattr("openai.OpenAI", lambda *args, **kwargs: mock_client)
    return mock_client


# --- Test Data Fixtures ---


@pytest.fixture
def sample_meeting_data() -> Dict[str, Any]:
    """Return sample meeting data for testing."""
    return {
        "id": "meet_123",
        "title": "Test Meeting",
        "description": "Test meeting description",
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T11:00:00Z",
        "timezone": "UTC",
        "meet_url": "https://meet.google.com/test-meeting",
        "status": "scheduled",
        "organizer_id": "user_123",
        "participants": ["user_456", "user_789"],
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Return sample user data for testing."""
    return {
        "id": "user_123",
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "metadata": {"role": "user"},
    }


# --- Database Mocks ---


@pytest.fixture
def mock_database_session():
    """Create a mock database session for testing."""
    session = AsyncMock()

    # Common session methods
    session.execute.return_value = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    # For testing queries
    query_mock = MagicMock()
    session.query.return_value = query_mock

    # For testing filter queries
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    filter_mock.all.return_value = []

    return session


# --- Service Initialization ---


@pytest.fixture
def init_service_fixture():
    """Fixture to help initialize service classes with mocks.

    Returns:
        A function that can be used to initialize a service with mocked dependencies.
    """

    def _init_service(service_class, **mock_deps):
        """Initialize a service with mocked dependencies.

        Args:
            service_class: The service class to instantiate
            **mock_deps: Keyword arguments with mock dependencies

        Returns:
            An instance of the service with mocked dependencies
        """
        return service_class(**mock_deps)

    return _init_service


# --- Async Test Support ---


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for async tests."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
