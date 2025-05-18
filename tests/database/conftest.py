"""Pytest configuration and fixtures for database tests.

This module provides fixtures and utilities for testing database operations,
including Supabase client setup, test data management, and cleanup.
"""

import os
import pytest
import pytest_asyncio
from typing import Dict, Any, List, Optional

from supabase import create_client
from loguru import logger

# --- Test Client Class ---


class SupabaseTestClient:
    """Wrapper around Supabase client with test utilities.

    This class provides methods for common test operations like creating test users,
    managing test data, and cleaning up after tests. It automatically handles
    resource cleanup after tests complete.

    Attributes:
        url: Supabase project URL
        anon_key: Anonymous/public key for client operations
        service_key: Service role key for admin operations
        is_admin: Whether this client has admin privileges
        client: The main Supabase client
        service_client: Client with service role privileges
        admin_client: Alias for service_client
        created_users: List of test users created during tests
        test_data: List of test records created during tests
    """

    def __init__(
        self, url: str, anon_key: str, service_key: str, is_admin: bool = False
    ):
        """Initialize with Supabase URL and keys.

        Args:
            url: Supabase project URL (e.g., 'https://your-project.supabase.co')
            anon_key: Anonymous/public key for client operations
            service_key: Service role key for admin operations
            is_admin: Whether this client should use admin privileges
        """
        self.url = url
        self.anon_key = anon_key
        self.service_key = service_key
        self.is_admin = is_admin

        # Create clients with appropriate permissions
        self.client = create_client(url, service_key if is_admin else anon_key)
        self.service_client = create_client(url, service_key)
        self.admin_client = self.service_client  # Alias for backward compatibility

        # Track created resources for cleanup
        self.created_users: List[Dict[str, Any]] = []
        self.test_data: List[Dict[str, Any]] = []

        logger.info("Initialized SupabaseTestClient with admin access: {}", is_admin)

    async def create_record(self, table: str, data: dict) -> Optional[Dict[str, Any]]:
        """Create a record in the specified table asynchronously.

        Args:
            table: Name of the table to insert into
            data: Dictionary of data to insert

        Returns:
            The created record data, or None if creation failed

        Example:
            >>> record = await client.create_record("test_table", {"name": "Test"})
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.table(table).insert(data).execute()
            )
            if result.data:
                record_id = result.data[0].get("id")
                self.test_data.append((table, record_id))
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating record in {table}: {e}")
            return None

    async def create_test_user(
        self,
        email: str = None,
        password: str = None,
        email_suffix: str = "",
        **metadata,
    ) -> dict:
        """Create a test user asynchronously.

        Args:
            email: Email for the test user. If not provided, will be generated.
            password: Password for the test user. If not provided, will be generated.
            email_suffix: Optional suffix for generated email.
            **metadata: Additional user metadata.

        Returns:
            A dictionary containing the user's client, id, email, and password.
        """
        """Create a test user and return the user object.

        Args:
            email: Email for the test user. If not provided, will be generated.
            password: Password for the test user. If not provided, will be generated.
            email_suffix: Optional suffix for generated email.
            **metadata: Additional user metadata.

        Returns:
            A dictionary containing the user's client, id, email, and password.
        """
        if email is None:
            # Generate a unique email using current timestamp
            import time

            timestamp = int(time.time())
            email = f"testuser{email_suffix}_{timestamp}@example.com"
        if password is None:
            password = f"TestPassword{email_suffix}!".replace(
                " ", ""
            )  # Remove any spaces

        try:
            # Use the admin API to create the user with the service key
            user_metadata = {
                "name": f"Test User {email_suffix}" if email_suffix else "Test User"
            }
            user_metadata.update(metadata)

            # Create the user with the admin client
            auth_response = self.service_client.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": user_metadata,
                }
            )

            user = auth_response.user
            self.created_users.append(user.id)

            # Sign in to get a session
            auth_data = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            # Create a new client with the user's session
            user_client = create_client(self.url, self.anon_key)
            user_client.auth.set_session(
                auth_data.session.access_token, auth_data.session.refresh_token
            )

            return {
                "client": user_client,
                "id": user.id,
                "email": email,
                "password": password,
            }

        except Exception as e:
            logger.error(f"Error creating test user: {e}")
            raise

    async def setup_test_data(self):
        """Set up test data and RLS policies using raw SQL execution asynchronously."""
        try:
            # Use the service client to ensure we have admin privileges
            service_client = self.service_client

            # Define the SQL statements to execute
            sql_statements = [
                # Create the test table if it doesn't exist
                """
                CREATE TABLE IF NOT EXISTS public.test_table (
                    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    name TEXT NOT NULL,
                    value INTEGER,
                    user_id UUID REFERENCES auth.users(id) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """,
                # Enable RLS on the test table
                "ALTER TABLE public.test_table ENABLE ROW LEVEL SECURITY;",
                # Drop existing policies
                'DROP POLICY IF EXISTS "Users can view their own records" ON public.test_table;',
                'DROP POLICY IF EXISTS "Users can manage their own records" ON public.test_table;',
                'DROP POLICY IF EXISTS "Admins can do all operations" ON public.test_table;',
                # Create new policies
                """
                CREATE POLICY "Users can view their own records"
                ON public.test_table
                FOR SELECT
                USING (auth.uid() = user_id);
                """,
                """
                CREATE POLICY "Users can manage their own records"
                ON public.test_table
                FOR ALL
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id);
                """,
                """
                CREATE POLICY "Admins can do all operations"
                ON public.test_table
                FOR ALL
                USING (
                    EXISTS (
                        SELECT 1 FROM auth.users
                        WHERE id = auth.uid() 
                        AND (
                            (raw_user_meta_data->>'role' = 'admin') 
                            OR 
                            (raw_user_meta_data->>'is_super_admin')::boolean = true
                            OR
                            is_super_admin = true
                        )
                    )
                );
                """,
            ]

            # Execute each SQL statement asynchronously
            for sql in sql_statements:
                try:
                    # Execute SQL in a thread pool since supabase-py is not async
                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda s=sql: service_client.rpc(
                            "execute_sql", {"query": s}
                        ).execute(),
                    )

                    if hasattr(result, "error") and result.error:
                        logger.warning(f"SQL execution warning: {result.error}")

                except Exception as e:
                    # Ignore errors about policies not existing when dropping
                    if 'policy "' in str(e) and " does not exist" in str(e):
                        continue
                    logger.warning(f"SQL execution error (continuing): {e}")

            logger.info("Successfully set up test data and RLS policies")

        except Exception as e:
            logger.error(f"Error setting up test data: {e}")
            raise

    async def cleanup(self):
        """Clean up all test users and records asynchronously."""
        # Clean up test records from test_data
        for table, record_id in reversed(self.test_data):
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda t=table, r=record_id: self.client.table(t)
                    .delete()
                    .eq("id", r)
                    .execute(),
                )
                logger.debug(f"Cleaned up test record: {table}.{record_id}")
            except Exception as e:
                logger.warning(f"Failed to clean up {table} record {record_id}: {e}")

        # Clean up test users
        for user in self.created_users:
            try:
                if isinstance(user, dict) and "id" in user:
                    user_id = user["id"]
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda u=user_id: self.admin_client.auth.admin.delete_user(u),
                    )
                    logger.debug(f"Cleaned up test user: {user_id}")
            except Exception as e:
                logger.warning(f"Failed to delete test user {user}: {e}")

        self.created_users = []
        self.test_data = []


# --- Database Fixtures ---


@pytest_asyncio.fixture(scope="module")
async def supabase_test_client():
    """Fixture that provides a Supabase test client with automatic cleanup.

    This is the main fixture for database tests. It handles:
    - Async client initialization with environment variables
    - Automatic cleanup of test data after tests complete
    - Proper async resource management
    - Module-level scoping for better test performance

    Environment Variables:
        NEXT_PUBLIC_SUPABASE_URL: Your Supabase project URL
        NEXT_PUBLIC_SUPABASE_ANON_KEY: Your Supabase anonymous/public key
        SUPABASE_SERVICE_ROLE_KEY: Your Supabase service role key (for admin operations)
    """
    required_vars = {
        "url": os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
        "anon_key": os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"),
        "service_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    }

    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        pytest.skip(f"Missing required Supabase configuration: {', '.join(missing)}")

    # Create the test client
    client = SupabaseTestClient(**required_vars)

    # Set up test data
    try:
        await client.setup_test_data()
    except Exception as e:
        logger.error(f"Error setting up test data: {e}")
        raise

    yield client

    # Clean up after all tests are done
    try:
        await client.cleanup()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise


@pytest_asyncio.fixture(scope="module")
async def admin_client():
    """Create an admin client for Supabase with service role privileges.

    This client has full access to the database and bypasses RLS.
    Use this for test setup/teardown that requires elevated permissions.
    """
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    anon_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not all([url, anon_key, service_key]):
        pytest.skip("Missing Supabase configuration")

    # Create the client
    client = SupabaseTestClient(url, anon_key, service_key, is_admin=True)

    # Set up test data
    await client.setup_test_data()

    try:
        yield client
    finally:
        # Clean up after the test
        await client.cleanup()


@pytest_asyncio.fixture(scope="module")
async def anon_client():
    """Create an anonymous client for Supabase with minimal permissions.

    This client uses the anon key and is subject to RLS policies.
    Use this to test public-facing functionality.
    """
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    anon_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not all([url, anon_key, service_key]):
        pytest.skip("Missing Supabase configuration")

    # Create the client
    client = SupabaseTestClient(url, anon_key, service_key, is_admin=False)

    # Set up test data
    await client.setup_test_data()

    try:
        yield client
    finally:
        # Clean up after the test
        await client.cleanup()


# --- Test Data Fixtures ---


@pytest_asyncio.fixture
async def test_users(supabase_test_client):
    """Provide two test users with clients for testing access control.

    Returns:
        Dict[str, Dict]: Dictionary with two test users:
            - user1: First test user with client and credentials
            - user2: Second test user with client and credentials

    Each user has the following structure:
    {
        'client': Supabase client authenticated as this user,
        'id': User's UUID,
        'email': User's email,
        'password': User's password
    }
    """
    # Create two test users with different email suffixes
    user1 = await supabase_test_client.create_test_user(
        email_suffix="1", metadata={"role": "tester"}
    )
    user2 = await supabase_test_client.create_test_user(
        email_suffix="2", metadata={"role": "tester"}
    )

    yield {"user1": user1, "user2": user2}

    # Cleanup is handled by the supabase_test_client fixture


@pytest_asyncio.fixture
async def test_record(supabase_test_client, test_users):
    """Create a test record owned by user1 for testing data access.

    This fixture:
    1. Sets up the test data environment
    2. Creates a test record owned by user1
    3. Returns the created record data

    Returns:
        Dict: The created test record with the following structure:
        {
            'id': Record ID,
            'name': 'Test Record',
            'value': 42,
            'user_id': ID of user1
        }
    """
    # Ensure test data is set up (tables, RLS policies, etc.)
    await supabase_test_client.setup_test_data()

    # Get the first test user
    user1 = test_users["user1"]

    # Create a test record owned by user1
    record_data = {"name": "Test Record", "value": 42, "user_id": user1["id"]}

    # Use the service client to create the record to avoid RLS issues
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: (
            supabase_test_client.service_client.table("test_table")
            .insert(record_data)
            .execute()
        ),
    )

    if not result.data:
        pytest.fail("Failed to create test record")

    record = result.data[0]

    yield record

    # Clean up the test record
    try:
        supabase_test_client.service_client.table("test_table").delete().eq(
            "id", record["id"]
        ).execute()
    except Exception as e:
        logger.warning(f"Failed to clean up test record {record['id']}: {e}")
