"""
Supabase client and database utilities for the Satoshi AI project.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from dotenv import load_dotenv
from loguru import logger
from postgrest import APIResponse
from supabase import Client, create_client

# Load environment variables from .env.local
env_path = Path(__file__).parent.parent.parent.parent / ".env.local"
load_dotenv(env_path)


class SupabaseClient:
    """A singleton wrapper around the Supabase client."""

    _instance: Optional["SupabaseClient"] = None
    _client: Optional[Client] = None

    def __new__(cls) -> "SupabaseClient":
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._client = cls._initialize_client()
        return cls._instance

    @classmethod
    def _initialize_client(cls) -> Client:
        """Initialize and return a Supabase client."""
        try:
            supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv(
                "NEXT_PUBLIC_SUPABASE_ANON_KEY"
            )

            if not supabase_url or not supabase_key:
                raise ValueError(
                    "Supabase URL and API key must be set in environment variables. "
                    f"URL: {'Set' if supabase_url else 'Not set'}, "
                    f"Key: {'Set' if supabase_key else 'Not set'}. "
                    f"Checked .env file at: {env_path}"
                )

            logger.info(f"Initializing Supabase client with URL: {supabase_url}")
            client = create_client(supabase_url, supabase_key)

            # Test the connection by making a simple request
            try:
                # This is a lightweight way to test the connection
                client.table("pg_tables").select("*").limit(1).execute()
            except Exception as e:
                logger.warning(f"Warning: Could not query pg_tables: {str(e)}")
                logger.info(
                    "This is normal if you don't have permissions to query system tables."
                )

            return client

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            logger.error(f"Supabase URL: {supabase_url}")
            logger.error(
                f"Supabase Key: {'*' * 8 + supabase_key[-4:] if supabase_key else 'Not set'}"
            )
            raise

    @property
    def client(self) -> Client:
        """Get the Supabase client instance."""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client

    def execute_query(self, query: str, params: Optional[Dict] = None) -> APIResponse:
        """Execute a raw SQL query."""
        if params is None:
            params = {}
        return cast(
            APIResponse,
            self.client.rpc(
                "execute_sql", {"query": query, "params": params}
            ).execute(),
        )

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a record into a table."""
        response = self.client.table(table).insert(data).execute()
        return response.data[0] if response.data else None

    def get_by_id(self, table: str, id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get a record by ID."""
        response = self.client.table(table).select("*").eq("id", id).execute()
        return response.data[0] if response.data else None

    def update(
        self, table: str, id: Union[str, int], data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a record."""
        response = self.client.table(table).update(data).eq("id", id).execute()
        return response.data[0] if response.data else None

    def delete(self, table: str, id: Union[str, int]) -> bool:
        """Delete a record.

        Returns:
            bool: True if the record was deleted, False otherwise
        """
        response = self.client.table(table).delete().eq("id", id).execute()
        return len(response.data) > 0 if response.data else False

    def query(self, table: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query a table with filters.

        Args:
            table: The name of the table to query
            query: A dictionary of query parameters
                - key_eq: value for equality check
                - key_neq: value for inequality check
                - key_gt: value for greater than
                - key_lt: value for less than
                - key_gte: value for greater than or equal
                - key_lte: value for less than or equal
                - key_ilike: value for case-insensitive pattern matching

        Returns:
            List[Dict[str, Any]]: A list of matching records
        """
        q = self.client.table(table).select("*")

        for key, value in query.items():
            if key.endswith("_eq"):
                field = key[:-4]  # Remove '_eq' suffix
                q = q.eq(field, value)
            elif key.endswith("_neq"):
                field = key[:-5]
                q = q.neq(field, value)
            elif key.endswith("_gt"):
                field = key[:-4]
                q = q.gt(field, value)
            elif key.endswith("_lt"):
                field = key[:-4]
                q = q.lt(field, value)
            elif key.endswith("_gte"):
                field = key[:-5]
                q = q.gte(field, value)
            elif key.endswith("_lte"):
                field = key[:-5]
                q = q.lte(field, value)
            elif key.endswith("_ilike"):
                field = key[:-7]
                q = q.ilike(field, f"%{value}%")
            else:
                q = q.eq(key, value)

        response = q.execute()
        return cast(List[Dict[str, Any]], response.data)


# Singleton instance
db = SupabaseClient()


def get_db() -> SupabaseClient:
    """Get the database client instance."""
    return db


# Example usage:
if __name__ == "__main__":
    try:
        # Example: Insert a record
        new_user = db.insert(
            "profiles",
            {"username": "testuser", "full_name": "Test User", "role": "viewer"},
        )
        print(f"Created user: {new_user}")

        # Example: Query records
        users = db.query("profiles", {"role_eq": "viewer"})
        print(f"Found {len(users)} viewers")

    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise
