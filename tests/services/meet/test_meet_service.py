"""Tests for the Meet Service using the new testing patterns."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Import the service or app to test
from backend.services.meet.meet_service import app, meetings_db

# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.services,
]


class TestMeetServiceNew:
    """Test suite for the Meet Service using new patterns."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the Meet Service."""
        with TestClient(app) as test_client:
            yield test_client

    @pytest.fixture
    def sample_meeting_data(self) -> dict:
        """Return sample meeting data for testing."""
        return {
            "id": "meet_123",
            "title": "Test Meeting",
            "participants": ["user1@example.com"],
            "start_time": "2025-06-01T10:00:00Z",
            "end_time": "2025-06-01T11:00:00Z",
            "transcript": None,
            "summary": None,
        }

    def test_create_meeting_success(
        self, client: TestClient, sample_meeting_data: dict
    ):
        """Test creating a meeting successfully."""
        # Clear any existing test data
        meetings_db.clear()

        # Act
        response = client.post("/meetings/", json=sample_meeting_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == sample_meeting_data["id"]
        assert response.json()["title"] == sample_meeting_data["title"]

        # Verify the meeting was stored
        assert sample_meeting_data["id"] in meetings_db

    def test_get_meeting_not_found(self, client: TestClient):
        """Test getting a non-existent meeting returns 404."""
        # Arrange
        meeting_id = "non_existent_id"

        # Ensure the meeting doesn't exist
        if meeting_id in meetings_db:
            del meetings_db[meeting_id]

        # Act
        response = client.get(f"/meetings/{meeting_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Meeting not found" in response.json()["detail"]

    @pytest.mark.integration
    def test_meeting_workflow(self, client: TestClient, sample_meeting_data: dict):
        """Test the complete meeting workflow (integration test)."""
        # Clear any existing test data
        meetings_db.clear()

        # Create a meeting
        response = client.post("/meetings/", json=sample_meeting_data)
        assert response.status_code == status.HTTP_200_OK
        meeting_id = response.json()["id"]

        # Get the meeting
        response = client.get(f"/meetings/{meeting_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == meeting_id

        # Clean up
        if meeting_id in meetings_db:
            del meetings_db[meeting_id]
