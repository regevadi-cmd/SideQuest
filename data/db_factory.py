"""Database factory for automatic SQLite/PostgreSQL switching."""
import os

# Check if DATABASE_URL is set (indicates production/PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production: Use PostgreSQL
    from .database_pg import DatabasePG as _DatabasePG

    # Wrapper class that ignores the db_path argument (used for SQLite)
    class Database(_DatabasePG):
        def __init__(self, db_path=None):
            # Ignore db_path, use DATABASE_URL from environment
            super().__init__()
else:
    # Development: Use SQLite
    from .database import Database
