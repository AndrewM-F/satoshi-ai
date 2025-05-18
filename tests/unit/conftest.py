"""Pytest configuration and fixtures for unit tests.

This module contains fixtures and utilities for unit testing individual
components in isolation.
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock

from loguru import logger

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


# --- Mock Fixtures ---


@pytest.fixture
def mock_async_context_manager():
    """Create a mock async context manager."""
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_async_iterator():
    """Create a mock async iterator."""

    class MockAsyncIterator:
        def __init__(self, seq):
            self.iter = iter(seq)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self.iter)
            except StopIteration:
                raise StopAsyncIteration

    return MockAsyncIterator


@pytest.fixture
def mock_coroutine():
    """Create a mock coroutine."""

    async def _mock_coroutine(*args, **kwargs):
        return None

    return _mock_coroutine


# --- Test Doubles ---


class MockAsyncSession:
    """A mock async SQLAlchemy session for testing."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False

    async def execute(self, *args, **kwargs):
        return AsyncMock()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def close(self):
        self.closed = True


@pytest.fixture
def mock_async_db_session():
    """Create a mock async database session."""
    return MockAsyncSession()


# --- Patch Fixtures ---


@pytest.fixture
def patch_datetime_now():
    """Patch datetime.now() for consistent testing."""
    import datetime
    from unittest.mock import patch

    mock_now = datetime.datetime(2025, 1, 1, 12, 0, 0)

    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        yield mock_now


# --- Configuration ---


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (default for this directory)"
    )
    config.addinivalue_line(
        "markers", "fast: mark test as fast (select with '-m fast')"
    )


def pytest_collection_modifyitems(items):
    """Automatically add unit marker to all tests in this directory."""
    for item in items:
        if "unit" not in item.keywords:
            item.add_marker(pytest.mark.unit)
