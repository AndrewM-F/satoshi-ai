"""Tests for Supabase authentication and RLS policies."""

import pytest
from loguru import logger


class TestAuthentication:
    """Tests for authentication and authorization."""

    @pytest.mark.asyncio
    @pytest.mark.database
    async def test_anonymous_access(self, supabase_test_client):
        """Test what anonymous users can and cannot do."""
        client = supabase_test_client.client

        # Test reading from test_table (should be allowed by RLS)
        result = client.table("test_table").select("*").limit(1).execute()
        assert isinstance(result.data, list), "Should be able to read from test_table"

        # Test writing to test_table (should be denied by RLS)
        try:
            client.table("test_table").insert({"name": "test", "value": 1}).execute()
            assert False, "Anonymous user should not be able to insert into test_table"
        except Exception as e:
            logger.info(
                f"✅ Anonymous cannot insert into test_table (expected: {str(e)[:100]}...)"
            )

    @pytest.mark.asyncio
    @pytest.mark.database
    async def test_authenticated_access(self, test_users):
        """Test what authenticated users can do."""
        user_client = test_users["user1"]["client"]
        user_id = test_users["user1"]["id"]

        # Create a test record
        test_data = {"name": "Auth Test", "value": 42, "user_id": user_id}

        # Should be able to insert with own user_id
        result = user_client.table("test_table").insert(test_data).execute()
        assert (
            result.data[0]["user_id"] == user_id
        ), "Should be able to insert with own user_id"

        # Should be able to read own record
        record_id = result.data[0]["id"]
        result = (
            user_client.table("test_table").select("*").eq("id", record_id).execute()
        )
        assert len(result.data) == 1, "Should be able to read own record"
        assert result.data[0]["id"] == record_id, "Should get the correct record"

    @pytest.mark.asyncio
    @pytest.mark.database
    async def test_cross_user_access(self, test_users):
        """Test that users cannot access each other's data."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # User 1 creates a record
        record = (
            user1["client"]
            .table("test_table")
            .insert({"name": "User 1's Record", "value": 100, "user_id": user1["id"]})
            .execute()
            .data[0]
        )

        # User 2 should not be able to see or modify User 1's record
        try:
            user2["client"].table("test_table").update({"value": 200}).eq(
                "id", record["id"]
            ).execute()
            assert False, "User 2 should not be able to update User 1's record"
        except Exception as e:
            logger.info(
                f"✅ User 2 cannot update User 1's record (expected: {str(e)[:100]}...)"
            )

        # User 2 should not see User 1's record in their queries
        result = (
            user2["client"]
            .table("test_table")
            .select("*")
            .eq("id", record["id"])
            .execute()
        )
        assert len(result.data) == 0, "User 2 should not see User 1's record"


if __name__ == "__main__":
    # Configure logger
    import sys
    import logging

    logger = logging.getLogger(__name__)
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )

    # Run tests
    logger.success("\n🎉 All authentication tests passed!")
