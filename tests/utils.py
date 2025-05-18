"""Test utilities and helpers."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_test_data(filename: str, model: Type[T]) -> T:
    """Load test data from a JSON file and validate it with a Pydantic model.

    Args:
        filename: Name of the JSON file in the test_data directory
        model: Pydantic model to validate the data against

    Returns:
        Validated model instance
    """
    filepath = Path(__file__).parent / "test_data" / filename
    with open(filepath, "r") as f:
        data = json.load(f)
    return model.parse_obj(data)


class AsyncContextManagerMock(MagicMock):
    """Mock for async context managers."""

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args, **kwargs):
        pass


def create_async_mock(**kwargs) -> MagicMock:
    """Create a mock that works with async/await."""
    mock = MagicMock(**kwargs)
    mock.__aenter__ = AsyncContextManagerMock(return_value=mock)
    mock.__aexit__ = AsyncContextManagerMock(return_value=None)
    return mock


def assert_dict_contains(actual: Dict[str, Any], expected: Dict[str, Any]) -> None:
    """Assert that the actual dict contains all items from expected dict."""
    for key, value in expected.items():
        assert key in actual, f"Key '{key}' not found in actual dict"
        assert actual[key] == value, f"Value for key '{key}' does not match"


@pytest.fixture
def mock_http_response(
    status_code: int = 200, json_data: Optional[dict] = None, text: Optional[str] = None
) -> MagicMock:
    """Create a mock HTTP response."""
    mock = MagicMock()
    mock.status_code = status_code

    if json_data is not None:
        mock.json.return_value = json_data
        mock.headers = {"content-type": "application/json"}

    if text is not None:
        mock.text = text
        mock.headers = {"content-type": "text/plain"}

    return mock
