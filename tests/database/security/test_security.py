"""Tests for Row Level Security (RLS) policies."""

import pytest
from loguru import logger


class TestRowLevelSecurity:
    """Tests for Row Level Security (RLS) policies."""

    @pytest.mark.asyncio
    @pytest.mark.database
    async def test_record_ownership(self, admin_client, test_users):
        """Test that users can only access their own records."""
        logger.info("Starting test_record_ownership test")
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        if not user1 or not user2:
            logger.warning("Test users not properly set up, skipping test")
            pytest.skip("Test users not properly set up")

        # Ensure test data is set up
        logger.info("Setting up test data and RLS policies")
        await admin_client.setup_test_data()

        # Create a service role client for cleanup
        service_role_client = admin_client.service_client
        logger.info(
            f"Testing with user1 (id: {user1['id']}) and user2 (id: {user2['id']})"
        )

        # User 1 creates a record
        record_data = {"name": "User 1's Record", "value": 42, "user_id": user1["id"]}
        logger.info(f"Creating test record owned by user1: {record_data}")

        # Use the service client to create the record to avoid RLS issues
        logger.debug("Using service role client to create record (bypassing RLS)")
        record = service_role_client.table("test_table").insert(record_data).execute()

        if not record.data:
            logger.error("Failed to create test record")
            pytest.fail("Failed to create test record")

        record = record.data[0]
        logger.info(f"Created test record with ID: {record['id']}")

        try:
            # User 1 should be able to read their own record
            logger.info("Testing that user1 can read their own record")
            result = (
                user1["client"]
                .table("test_table")
                .select("*")
                .eq("id", record["id"])
                .execute()
            )
            assert len(result.data) == 1, "User 1 should see their own record"
            assert (
                result.data[0]["user_id"] == user1["id"]
            ), "Record should belong to user1"
            logger.info("✅ User1 can read their own record")

            # User 2 should not be able to read User 1's record
            logger.info("Testing that user2 cannot read user1's record")
            result = (
                user2["client"]
                .table("test_table")
                .select("*")
                .eq("id", record["id"])
                .execute()
            )
            assert len(result.data) == 0, "User 2 should not see User 1's record"
            logger.info("✅ User2 cannot read user1's record (RLS working)")

            # User 2 should not be able to update User 1's record
            logger.info("Testing that user2 cannot update user1's record")
            result = (
                user2["client"]
                .table("test_table")
                .update({"value": 100})
                .eq("id", record["id"])
                .execute()
            )
            assert not result.data, "Expected no rows updated due to RLS"
            logger.info("✅ User2 cannot update user1's record (RLS working)")

            # Verify the record was not updated by checking with user1's client
            result = (
                user1["client"]
                .table("test_table")
                .select("*")
                .eq("id", record["id"])
                .execute()
            )
            assert result.data[0]["value"] == 42, "Record should not have been updated"

            # User 2 should not be able to delete User 1's record
            logger.info("Testing that user2 cannot delete user1's record")
            result = (
                user2["client"]
                .table("test_table")
                .delete()
                .eq("id", record["id"])
                .execute()
            )
            assert not result.data, "Expected no rows deleted due to RLS"
            logger.info("✅ User2 cannot delete user1's record (RLS working)")

        finally:
            # Clean up the test record using service role client
            logger.info(f"Cleaning up test record {record['id']}")
            service_role_client.table("test_table").delete().eq(
                "id", record["id"]
            ).execute()
            logger.info("Test record_ownership completed successfully")

    @pytest.mark.asyncio
    @pytest.mark.database
    async def test_admin_access(self, admin_client, test_users):
        """Test that admins can access all records."""
        user1 = test_users["user1"]

        if not user1:
            pytest.skip("Test user not properly set up")

        # Ensure test data is set up
        await admin_client.setup_test_data()

        # Create a service role client for admin operations
        service_role_client = admin_client.service_client

        # User 1 creates a record
        record_data = {
            "name": "Admin Test Record",
            "value": 100,
            "user_id": user1["id"],
        }

        # Use the service client to create the record to ensure it's created
        record = service_role_client.table("test_table").insert(record_data).execute()

        if not record.data:
            pytest.fail("Failed to create test record")

        record = record.data[0]

        try:
            # Admin should be able to read the record
            result = (
                service_role_client.table("test_table")
                .select("*")
                .eq("id", record["id"])
                .execute()
            )
            assert len(result.data) == 1, "Admin should be able to read any record"
            assert (
                result.data[0]["user_id"] == user1["id"]
            ), "Record should belong to user1"

            # Admin should be able to update the record
            service_role_client.table("test_table").update({"value": 200}).eq(
                "id", record["id"]
            ).execute()

            # Verify the update
            result = (
                service_role_client.table("test_table")
                .select("*")
                .eq("id", record["id"])
                .execute()
            )
            assert (
                result.data[0]["value"] == 200
            ), "Admin should be able to update any record"

            # Admin should be able to delete the record
            service_role_client.table("test_table").delete().eq(
                "id", record["id"]
            ).execute()

            # Verify the record was deleted
            result = (
                service_role_client.table("test_table")
                .select("*")
                .eq("id", record["id"])
                .execute()
            )
            assert len(result.data) == 0, "Admin should be able to delete any record"

        except Exception as e:
            # Clean up if anything goes wrong
            service_role_client.table("test_table").delete().eq(
                "id", record["id"]
            ).execute()
            raise
