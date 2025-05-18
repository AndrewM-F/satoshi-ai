"""Integration tests for meeting workflows."""

import os
import pytest
import asyncio
import respx
from respx import MockResponse
from fastapi.testclient import TestClient
from backend.api_gateway.app.main import app


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def meet_service_base_url():
    # Use localhost:8001 in GitHub Actions, meet-service:8000 locally
    if os.getenv("GITHUB_ACTIONS") == "true":
        return "http://localhost:8001"
    else:
        return "http://meet-service:8000"


@pytest.fixture
def mock_meet_service(meet_service_base_url, meeting_data):
    with respx.mock(
        base_url=meet_service_base_url, assert_all_called=False
    ) as respx_mock:
        # Mock POST /meetings
        respx_mock.post("/meetings").mock(
            return_value=MockResponse(
                200, json=meeting_data, headers={"Content-Type": "application/json"}
            )
        )
        # Mock GET /meetings/{id}
        respx_mock.get(f"/meetings/{meeting_data['id']}").mock(
            return_value=MockResponse(
                200, json=meeting_data, headers={"Content-Type": "application/json"}
            )
        )
        yield respx_mock


class TestMeetingWorkflow:
    """Test suite for meeting-related workflows."""

    @pytest.fixture
    def client(self, meet_service_base_url):
        with TestClient(app) as test_client:
            if not hasattr(app.state, "SERVICES"):
                app.state.SERVICES = {}
            app.state.SERVICES["meet"] = meet_service_base_url
            yield test_client

    @pytest.fixture(autouse=True)
    def setup_mock_responses(self, mock_meet_service, meeting_data):
        """Set up mock responses for the meet service."""
        # Mock the POST /meetings endpoint
        mock_meet_service.post("/meetings").mock(
            return_value=MockResponse(
                200, json=meeting_data, headers={"Content-Type": "application/json"}
            )
        )

        # Mock the GET /meetings/{meeting_id} endpoint
        mock_meet_service.get(f"/meetings/{meeting_data['id']}").mock(
            return_value=MockResponse(
                200, json=meeting_data, headers={"Content-Type": "application/json"}
            )
        )

    @pytest.fixture
    def meeting_data(self):
        """Sample meeting data."""
        return {
            "id": "meet_integration_123",
            "title": "Integration Test Meeting",
            "description": "Test meeting created during integration testing",
            "start_time": "2025-06-01T10:00:00Z",
            "end_time": "2025-06-01T11:00:00Z",
        }

    @pytest.mark.asyncio
    async def test_create_and_retrieve_meeting(
        self, client, meeting_data, caplog, mock_meet_service
    ):
        """Test creating and retrieving a meeting through the API."""
        # Enable debug logging for the test
        caplog.set_level("DEBUG")

        # Create a meeting
        response = client.post("/api/meet/meetings", json=meeting_data)

        # Print the response for debugging
        print(f"Create response: {response.status_code} - {response.text}")

        # Check the response status code
        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        # Verify the response data
        response_data = response.json()
        assert isinstance(
            response_data, dict
        ), f"Expected dict, got {type(response_data)}"
        assert (
            response_data["id"] == meeting_data["id"]
        ), f"Expected id {meeting_data['id']}, got {response_data.get('id')}"

        # Verify the POST request was made with the correct parameters
        assert (
            len(mock_meet_service.calls) == 1
        ), "Expected one call to the meet service"

        # Get the request that was made
        post_request = mock_meet_service.calls[0].request
        assert post_request.url.path == "/meetings"
        assert post_request.method == "POST"

        # Clear the recorded calls for the next request
        mock_meet_service.calls.clear()

        # Retrieve the meeting
        response = client.get(f"/api/meet/meetings/{meeting_data['id']}")

        # Print the response for debugging
        print(f"Get response: {response.status_code} - {response.text}")

        # Check the response status code
        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        # Verify the response data
        response_data = response.json()
        assert isinstance(
            response_data, dict
        ), f"Expected dict, got {type(response_data)}"
        assert (
            response_data["id"] == meeting_data["id"]
        ), f"Expected id {meeting_data['id']}, got {response_data.get('id')}"

        # Verify the GET request was made with the correct parameters
        assert (
            len(mock_meet_service.calls) == 1
        ), f"Expected one call to GET /meetings/{meeting_data['id']}"

        # Get the request that was made
        get_request = mock_meet_service.calls[0].request
        assert get_request.url.path == f"/meetings/{meeting_data['id']}"
        assert get_request.method == "GET"

        # Print the response for debugging
        print(f"Get response: {response.status_code} - {response.text}")

        # Check the response status code
        assert (
            response.status_code == 200
        ), f"Expected status code 200, got {response.status_code}"

        # Verify the response data
        get_response_data = response.json()
        assert (
            get_response_data["id"] == meeting_data["id"]
        ), f"Expected id {meeting_data['id']} in GET response, got {get_response_data.get('id')}"

        # Check the response data
        assert (
            get_response_data["title"] == meeting_data["title"]
        ), f"Expected title {meeting_data['title']}, got {get_response_data.get('title')}"
        assert (
            get_response_data["description"] == meeting_data["description"]
        ), f"Expected description {meeting_data['description']}, got {get_response_data.get('description')}"
        assert (
            get_response_data["start_time"] == meeting_data["start_time"]
        ), f"Expected start_time {meeting_data['start_time']}, got {get_response_data.get('start_time')}"
        assert (
            get_response_data["end_time"] == meeting_data["end_time"]
        ), f"Expected end_time {meeting_data['end_time']}, got {get_response_data.get('end_time')}"
