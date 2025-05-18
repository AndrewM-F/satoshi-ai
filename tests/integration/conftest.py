"""Pytest configuration and fixtures for integration tests.

This module contains fixtures and utilities for testing the integration
between different components of the application.
"""

import pytest
from typing import AsyncGenerator, Dict, Any
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx

from backend.api_gateway.app.main import app
from loguru import logger

# --- Application Fixtures ---


@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_test_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


# --- Database Fixtures ---


@pytest.fixture(scope="module")
def test_database_url() -> str:
    """Get the test database URL from environment variables."""
    import os

    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL environment variable not set")
    return url


@pytest.fixture(scope="module")
async def test_db_connection(test_database_url: str):
    """Create a test database connection.

    This fixture sets up a connection to the test database and ensures
    it's properly closed after tests complete.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(test_database_url)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    yield async_session

    await engine.dispose()


# --- Authentication Fixtures ---


@pytest.fixture
def test_user() -> Dict[str, Any]:
    """Return test user data for authentication."""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
    }


@pytest.fixture
def authenticated_client(
    test_client: TestClient, test_user: Dict[str, Any]
) -> TestClient:
    """Return an authenticated test client."""
    test_client.headers.update(
        {
            "Authorization": f"Bearer {test_user['id']}",
            "Content-Type": "application/json",
        }
    )
    return test_client


# --- External Service Mocks ---


@pytest.fixture
def mock_external_services():
    """Mock external services used in integration tests."""
    with patch(
        "backend.services.meet.google_calendar.GoogleCalendar"
    ) as mock_calendar, patch(
        "backend.services.meet.google_meet.GoogleMeet"
    ) as mock_meet, patch(
        "backend.services.ai.openai_client.OpenAIClient"
    ) as mock_openai:

        # Setup mock calendar
        mock_calendar.return_value.create_event.return_value = {
            "id": "event_123",
            "meet_link": "https://meet.google.com/test-meeting",
            "start_time": "2025-01-01T10:00:00Z",
            "end_time": "2025-01-01T11:00:00Z",
        }

        # Setup mock meet
        mock_meet.return_value.create_meeting.return_value = {
            "id": "meet_123",
            "meet_url": "https://meet.google.com/test-meeting",
            "conference_data": {},
        }

        # Setup mock OpenAI
        mock_openai.return_value.generate_response.return_value = (
            "AI generated response"
        )

        yield {"calendar": mock_calendar, "meet": mock_meet, "openai": mock_openai}


# --- Test Data Management ---


@pytest.fixture
def load_test_data(test_data_dir: Path) -> callable:
    """Return a function to load test data from JSON files.

    Args:
        test_data_dir: Path to the test data directory

    Returns:
        A function that loads and returns test data from a JSON file
    """

    def _load_data(filename: str) -> Dict[str, Any]:
        """Load test data from a JSON file in the test_data directory."""
        filepath = test_data_dir / "integration" / filename
        if not filepath.exists():
            (test_data_dir / "integration").mkdir(exist_ok=True, parents=True)
            logger.warning(f"Test data file not found: {filepath}")
            return {}

        with open(filepath, "r") as f:
            return json.load(f)

    return _load_data


# --- Async Support ---


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# --- Test Configuration ---


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test (deselect with '-m not e2e')"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (deselect with '-m not slow')"
    )
    config.addinivalue_line(
        "markers", "external: mark test that requires external services"
    )
