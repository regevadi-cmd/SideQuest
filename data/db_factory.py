"""Database factory for automatic SQLite/PostgreSQL switching."""
import os

# Check if DATABASE_URL is set (indicates production/PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production: Use PostgreSQL
    from .database_pg import DatabasePG as Database
else:
    # Development: Use SQLite
    from .database import Database
