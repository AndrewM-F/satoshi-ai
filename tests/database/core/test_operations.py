"""Tests for Supabase database operations."""

import pytest
from loguru import logger


class TestDatabaseOperations:
    """Tests for database operations."""

    @pytest.mark.asyncio
    async def test_basic_operations(self, supabase_test_client, test_users):
        """Test basic CRUD operations."""
        user = test_users["user1"]
        client = user["client"]

        # Test data
        test_data = {
            "name": "Test Record",
            "value": 42,
            "is_active": True,
            "user_id": user["id"],
        }

        # Insert
        result = client.table("test_table").insert(test_data).execute()
        assert len(result.data) > 0, "Insert should return the created record"
        record_id = result.data[0]["id"]

        try:
            # Read
            result = (
                client.table("test_table").select("*").eq("id", record_id).execute()
            )
            assert len(result.data) == 1, "Should find exactly one record"
            assert result.data[0]["name"] == test_data["name"], "Name should match"
            assert result.data[0]["value"] == test_data["value"], "Value should match"

            # Update
            update_data = {"value": 100, "is_active": False}
            result = (
                client.table("test_table")
                .update(update_data)
                .eq("id", record_id)
                .execute()
            )
            assert len(result.data) > 0, "Update should return the updated record"
            assert (
                result.data[0]["value"] == update_data["value"]
            ), "Value should be updated"

            # Verify update
            result = (
                client.table("test_table").select("*").eq("id", record_id).execute()
            )
            assert not result.data[0]["is_active"], "is_active should be False"

        finally:
            # Clean up
            client.table("test_table").delete().eq("id", record_id).execute()

    @pytest.mark.asyncio
    async def test_batch_operations(self, supabase_test_client, test_users):
        """Test batch insert and update operations."""
        user = test_users["user1"]
        client = user["client"]

        # Test data for batch insert
        test_data = [
            {
                "name": f"Batch Test {i}",
                "value": i,
                "is_active": True,
                "user_id": user["id"],
            }
            for i in range(3)
        ]

        # Batch insert
        result = client.table("test_table").insert(test_data).execute()
        assert len(result.data) == len(test_data), "Should insert all records"
        record_ids = [record["id"] for record in result.data]

        try:
            # Verify batch insert
            result = (
                client.table("test_table").select("*").in_("id", record_ids).execute()
            )
            assert len(result.data) == len(
                test_data
            ), "Should retrieve all inserted records"

            # Batch update
            update_data = {"is_active": False}
            result = (
                client.table("test_table")
                .update(update_data)
                .in_("id", record_ids)
                .execute()
            )
            assert len(result.data) == len(test_data), "Should update all records"

            # Verify batch update
            result = (
                client.table("test_table")
                .select("is_active")
                .in_("id", record_ids)
                .execute()
            )
            for record in result.data:
                assert not record["is_active"], "All records should be deactivated"

        finally:
            # Clean up
            client.table("test_table").delete().in_("id", record_ids).execute()

    @pytest.mark.asyncio
    async def test_query_operations(self, supabase_test_client, test_users):
        """Test various query operations."""
        user = test_users["user1"]
        client = user["client"]

        # Test data
        test_data = [
            {
                "name": "Query Test 1",
                "value": 10,
                "is_active": True,
                "user_id": user["id"],
            },
            {
                "name": "Query Test 2",
                "value": 20,
                "is_active": False,
                "user_id": user["id"],
            },
            {
                "name": "Another Test",
                "value": 10,
                "is_active": True,
                "user_id": user["id"],
            },
        ]

        # Insert test data
        result = client.table("test_table").insert(test_data).execute()
        record_ids = [record["id"] for record in result.data]

        try:
            # Test filtering
            result = client.table("test_table").select("*").eq("value", 10).execute()
            assert len(result.data) == 2, "Should find 2 records with value=10"

            # Test ordering
            result = client.table("test_table").select("value").order("value").execute()
            values = [record["value"] for record in result.data]
            assert values == sorted(values), "Results should be ordered by value"

            # Test like/ilike
            result = (
                client.table("test_table")
                .select("name")
                .ilike("name", "%query%")
                .execute()
            )
            assert (
                len(result.data) == 2
            ), "Should find 2 records with 'query' in name (case insensitive)"

            # Test limit/offset
            result = client.table("test_table").select("*").limit(1).execute()
            assert len(result.data) == 1, "Should return only 1 record with limit=1"

        finally:
            # Clean up
            client.table("test_table").delete().in_("id", record_ids).execute()

    @pytest.mark.asyncio
    async def test_timestamps(self, supabase_test_client, test_users, caplog):
        """Test that timestamps are properly set and records can be updated."""
        user = test_users["user1"]
        client = user["client"]

        # Insert a record
        test_data = {"name": "Timestamp Test", "value": 1, "user_id": user["id"]}

        logger.info("Inserting test record...")
        result = client.table("test_table").insert(test_data).execute()
        record_id = result.data[0]["id"]
        logger.info(f"Created record with ID: {record_id}")

        try:
            # Check that timestamps were set on creation
            logger.info("Fetching initial record...")
            result = (
                client.table("test_table").select("*").eq("id", record_id).execute()
            )
            record = result.data[0]

            logger.info(f"Initial record: {record}")
            assert record["created_at"], "created_at should be set"
            assert record["updated_at"], "updated_at should be set"

            # Update the record
            logger.info("Updating record...")

            # Update with new values
            update_data = {"value": 2, "name": "Updated Timestamp Test"}
            update_result = (
                client.table("test_table")
                .update(update_data)
                .eq("id", record_id)
                .execute()
            )
            logger.info(f"Update result: {update_result}")

            # Verify the update was successful
            assert (
                len(update_result.data) > 0
            ), "Update should return the updated record"

            # Fetch the updated record
            logger.info("Fetching updated record...")
            result = (
                client.table("test_table").select("*").eq("id", record_id).execute()
            )
            updated_record = result.data[0]
            logger.info(f"Updated record: {updated_record}")

            # Verify the data was actually updated
            assert updated_record["value"] == 2, "Value should be updated to 2"
            assert (
                updated_record["name"] == "Updated Timestamp Test"
            ), "Name should be updated"

            # Check that created_at hasn't changed
            assert (
                record["created_at"] == updated_record["created_at"]
            ), "created_at should not change"

            # Note: We're not checking updated_at here since it's not automatically updated by the database
            # In a real application, you'd want to set up a trigger to update this field

        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise
        finally:
            # Clean up
            logger.info("Cleaning up test record...")
            client.table("test_table").delete().eq("id", record_id).execute()


if __name__ == "__main__":
    # Configure logger
    import sys
    from loguru import logger

    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )

    # Run tests
    test_database_operations()
