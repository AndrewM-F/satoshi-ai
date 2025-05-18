"""Global pytest configuration and shared fixtures for all tests.

This file contains configurations and fixtures that are used across multiple test modules.
Module-specific fixtures should be placed in their respective conftest.py files.
"""

import os
import sys
import pytest
import asyncio
import logging
from pathlib import Path

from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env.local
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Remove default logger and add custom format
logger.remove()
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

# Set log level for other loggers
logging.basicConfig(level=logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Test data directory (used across multiple test modules)
TEST_DATA_DIR = Path(__file__).parent / "test_data"

# --- Global Fixtures ---


@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test module.

    This is required for any async tests. This implementation ensures that:
    1. A new event loop is created for each test module
    2. The event loop is properly closed after all tests in the module complete
    3. The event loop is set as the current event loop for the thread
    """
    # Create a new event loop
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()

    # Set the event loop as the current event loop for this thread
    asyncio.set_event_loop(loop)

    try:
        yield loop
    finally:
        # Cancel all running tasks
        pending = asyncio.all_tasks(loop=loop)
        for task in pending:
            task.cancel()

        # Run the loop until all tasks are done or cancelled
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

        # Shutdown async generators
        loop.run_until_complete(loop.shutdown_asyncgens())

        # Close the loop
        if loop.is_running():
            loop.stop()
        loop.close()
        asyncio.set_event_loop(None)


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the path to the test data directory.

    Creates the directory if it doesn't exist.
    """
    TEST_DATA_DIR.mkdir(exist_ok=True, parents=True)
    return TEST_DATA_DIR


# --- Markers ---


def pytest_configure(config):
    """Configure pytest with custom markers.

    This function is automatically called by pytest during test collection.
    """
    markers = [
        "unit: mark test as a unit test (deselect with '-m not unit')",
        "integration: mark test as integration test (deselect with '-m not integration')",
        "e2e: mark test as an end-to-end test (deselect with '-m not e2e')",
        "slow: mark test as slow (deselect with '-m not slow')",
        "flaky: mark test as flaky (may fail occasionally)",
        "database: test that interacts with the database",
        "api: test that makes API calls",
        "auth: test related to authentication/authorization",
    ]

    for marker in markers:
        config.addinivalue_line("markers", marker)
