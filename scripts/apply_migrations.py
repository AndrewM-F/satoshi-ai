"""
Supabase migration script for applying SQL migrations.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Custom exception for migration errors."""

    pass


class SupabaseMigrator:
    """Handles database migrations for Supabase."""

    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize the migrator with Supabase credentials."""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.migrations_table = "schema_migrations"
        self.migrations_dir = (
            Path(__file__).parent.parent / "infra" / "supabase" / "migrations"
        )
        self._ensure_migrations_table()

    def _ensure_migrations_table(self) -> None:
        """Create the migrations table if it doesn't exist."""
        try:
            # First check if table exists
            try:
                self.supabase.table(self.migrations_table).select("*").limit(
                    1
                ).execute()
                return  # Table exists
            except Exception:
                # Table doesn't exist, create it
                pass

            # Create the table using a raw query (this requires pg_catalog access)
            # For Supabase, we'll use the SQL editor to run this once
            logger.warning(
                """
            ===================================================================
            Please run this SQL in your Supabase SQL Editor to enable migrations:
            
            CREATE TABLE IF NOT EXISTS public.schema_migrations (
                version BIGINT PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            GRANT ALL PRIVILEGES ON public.schema_migrations TO postgres;
            ===================================================================
            """
            )
            raise MigrationError(
                "Migrations table does not exist. Please create it first using the SQL above."
            )

        except Exception as e:
            raise MigrationError(f"Failed to ensure migrations table: {e}")

    def get_applied_migrations(self) -> List[int]:
        """Get a list of applied migration versions."""
        try:
            result = (
                self.supabase.table(self.migrations_table)
                .select("version")
                .order("version")
                .execute()
            )
            return [migration["version"] for migration in result.data]
        except Exception as e:
            raise MigrationError(f"Failed to get applied migrations: {e}")

    def get_pending_migrations(self) -> List[Path]:
        """Get a list of pending migration files."""
        try:
            applied = set(self.get_applied_migrations())
            migrations = []

            for file in sorted(self.migrations_dir.glob("*.sql")):
                version = int(file.stem.split("_")[0])
                if version not in applied:
                    migrations.append((version, file))

            # Sort by version
            return [m[1] for m in sorted(migrations, key=lambda x: x[0])]
        except Exception as e:
            raise MigrationError(f"Failed to get pending migrations: {e}")

    def apply_migration(self, migration_file: Path) -> None:
        """Apply a single migration."""
        version = int(migration_file.stem.split("_")[0])
        name = migration_file.stem.split("_", 1)[1]

        try:
            # Read the migration SQL
            with open(migration_file, "r") as f:
                sql = f.read()

            logger.info(f"\n{'='*80}")
            logger.info(f"Applying migration: {migration_file.name}")
            logger.info(f"{'-'*80}")

            # For Supabase, we need to run this in the SQL Editor
            # So we'll just log the SQL that needs to be run
            logger.warning(
                f"""
            ===================================================================
            Please run this SQL in your Supabase SQL Editor:
            
            -- Migration: {migration_file.name}
            {sql}
            
            -- Record the migration
            INSERT INTO public.schema_migrations (version, name)
            VALUES ({version}, '{name}')
            ON CONFLICT (version) DO NOTHING;
            ===================================================================
            """
            )

            # For the script to continue, we'll just record the migration
            # without actually running the SQL (since we can't run arbitrary SQL)
            try:
                self.supabase.table(self.migrations_table).insert(
                    {"version": version, "name": name}
                ).execute()
            except Exception as e:
                logger.warning(
                    f"Could not record migration (this is normal if you haven't created the table yet): {e}"
                )

            input("Press Enter after you've run the SQL above...")
            logger.info(f"Successfully applied migration: {migration_file.name}")

        except Exception as e:
            raise MigrationError(
                f"Failed to apply migration {migration_file.name}: {e}"
            )

    def apply_all_migrations(self) -> None:
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("No pending migrations to apply.")
            return

        logger.info(f"Found {len(pending)} pending migrations.")

        for migration_file in pending:
            self.apply_migration(migration_file)


def main():
    """Main function to run migrations."""
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env.local"
    load_dotenv(env_path)

    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("Missing Supabase URL or API key in environment variables.")
        return

    try:
        migrator = SupabaseMigrator(supabase_url, supabase_key)
        migrator.apply_all_migrations()
        logger.info("All migrations applied successfully!")
    except MigrationError as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
