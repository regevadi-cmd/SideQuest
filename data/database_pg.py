"""PostgreSQL database operations for production deployment."""
import os
import json
import logging
from datetime import datetime, date
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool, NullPool

from .models import (
    Job, Profile, Application, SavedLocation, ScheduleBlock, User,
    SearchSchedule, Notification, SavedSearchResult, NotificationPreferences
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabasePG:
    """PostgreSQL database manager for job search data."""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable required for PostgreSQL")

        # Handle Supabase/Heroku style URLs
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)

        # Add SSL mode for Supabase if not already specified
        if "sslmode" not in self.database_url:
            separator = "&" if "?" in self.database_url else "?"
            self.database_url = f"{self.database_url}{separator}sslmode=require"

        # Log connection attempt (hide password)
        safe_url = self.database_url
        if "@" in safe_url:
            # Hide password in logs
            parts = safe_url.split("@")
            prefix = parts[0].rsplit(":", 1)[0]  # Remove password
            safe_url = f"{prefix}:****@{parts[1]}"
        logger.info(f"Connecting to PostgreSQL: {safe_url}")

        try:
            # Use NullPool for serverless (Streamlit Cloud) - creates fresh connections
            self.engine = create_engine(
                self.database_url,
                poolclass=NullPool,  # Better for serverless
                connect_args={
                    "connect_timeout": 10,
                }
            )
            self._init_tables()
            logger.info("PostgreSQL connection successful")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {type(e).__name__}: {str(e)}")
            raise

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = self.engine.connect()
        trans = conn.begin()
        try:
            yield conn
            trans.commit()
        except Exception:
            trans.rollback()
            raise
        finally:
            conn.close()

    def _init_tables(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                );

                CREATE TABLE IF NOT EXISTS locations (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    radius_miles INTEGER DEFAULT 10,
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    name TEXT DEFAULT '',
                    major TEXT DEFAULT '',
                    skills TEXT DEFAULT '[]',
                    interests TEXT DEFAULT '[]',
                    min_hourly_rate REAL,
                    max_hours_per_week INTEGER,
                    preferred_job_types TEXT DEFAULT '[]',
                    preferred_job_sources TEXT DEFAULT '[]',
                    schedule_blocks TEXT DEFAULT '[]',
                    resume_text TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    salary_text TEXT,
                    salary_min REAL,
                    salary_max REAL,
                    salary_type TEXT,
                    job_type TEXT,
                    url TEXT NOT NULL,
                    posted_date TEXT,
                    scraped_at TEXT NOT NULL,
                    match_score REAL,
                    match_reasons TEXT DEFAULT '[]',
                    extracted_requirements TEXT DEFAULT '[]',
                    schedule_compatible INTEGER,
                    UNIQUE(source, source_id)
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER NOT NULL REFERENCES jobs(id),
                    status TEXT DEFAULT 'Saved',
                    applied_date TEXT,
                    notes TEXT DEFAULT '',
                    next_step TEXT,
                    next_step_date TEXT,
                    cover_letter TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
                CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
                CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

                CREATE TABLE IF NOT EXISTS search_schedules (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER DEFAULT 1,
                    enabled INTEGER DEFAULT 1,
                    frequency TEXT DEFAULT 'daily',
                    time_preference TEXT DEFAULT 'morning',
                    last_run TEXT,
                    next_run TEXT,
                    search_query TEXT DEFAULT '',
                    search_location_id INTEGER,
                    search_radius INTEGER DEFAULT 10,
                    search_sources TEXT DEFAULT '[]',
                    search_job_types TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT DEFAULT '',
                    related_job_ids TEXT DEFAULT '[]',
                    read INTEGER DEFAULT 0,
                    email_sent INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS saved_search_results (
                    id SERIAL PRIMARY KEY,
                    schedule_id INTEGER NOT NULL REFERENCES search_schedules(id),
                    run_at TEXT NOT NULL,
                    jobs_found INTEGER DEFAULT 0,
                    new_jobs INTEGER DEFAULT 0,
                    job_ids TEXT DEFAULT '[]',
                    error_message TEXT
                );

                CREATE TABLE IF NOT EXISTS notification_preferences (
                    id SERIAL PRIMARY KEY,
                    email_enabled INTEGER DEFAULT 0,
                    email_address TEXT,
                    email_verified INTEGER DEFAULT 0,
                    digest_frequency TEXT DEFAULT 'instant',
                    notify_new_jobs INTEGER DEFAULT 1,
                    notify_application_updates INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
                CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
            """))

    def _row_to_dict(self, row):
        """Convert SQLAlchemy row to dictionary."""
        if row is None:
            return None
        return dict(row._mapping)

    # Location operations
    def save_location(self, location: SavedLocation) -> SavedLocation:
        """Save or update a location."""
        with self._get_connection() as conn:
            if location.is_default:
                conn.execute(text("UPDATE locations SET is_default = 0"))

            if location.id:
                conn.execute(text("""
                    UPDATE locations SET name=:name, address=:address, latitude=:latitude,
                    longitude=:longitude, radius_miles=:radius_miles, is_default=:is_default
                    WHERE id=:id
                """), {
                    "name": location.name, "address": location.address,
                    "latitude": location.latitude, "longitude": location.longitude,
                    "radius_miles": location.radius_miles, "is_default": int(location.is_default),
                    "id": location.id
                })
            else:
                result = conn.execute(text("""
                    INSERT INTO locations (name, address, latitude, longitude, radius_miles, is_default, created_at)
                    VALUES (:name, :address, :latitude, :longitude, :radius_miles, :is_default, :created_at)
                    RETURNING id
                """), {
                    "name": location.name, "address": location.address,
                    "latitude": location.latitude, "longitude": location.longitude,
                    "radius_miles": location.radius_miles, "is_default": int(location.is_default),
                    "created_at": datetime.now().isoformat()
                })
                location.id = result.fetchone()[0]
        return location

    def get_locations(self) -> list[SavedLocation]:
        """Get all saved locations."""
        with self._get_connection() as conn:
            rows = conn.execute(text("SELECT * FROM locations ORDER BY is_default DESC, name")).fetchall()
            return [SavedLocation(
                id=row.id, name=row.name, address=row.address,
                latitude=row.latitude, longitude=row.longitude,
                radius_miles=row.radius_miles, is_default=bool(row.is_default),
                created_at=datetime.fromisoformat(row.created_at)
            ) for row in rows]

    def delete_location(self, location_id: int):
        """Delete a location."""
        with self._get_connection() as conn:
            conn.execute(text("DELETE FROM locations WHERE id = :id"), {"id": location_id})

    # Profile operations
    def get_profile(self) -> Optional[Profile]:
        """Get the user profile (single user app)."""
        with self._get_connection() as conn:
            row = conn.execute(text("SELECT * FROM profiles LIMIT 1")).fetchone()
            if not row:
                return None
            try:
                preferred_sources = json.loads(row.preferred_job_sources) if row.preferred_job_sources else []
            except (KeyError, TypeError):
                preferred_sources = []
            return Profile(
                id=row.id, name=row.name, major=row.major,
                skills=json.loads(row.skills), interests=json.loads(row.interests),
                min_hourly_rate=row.min_hourly_rate, max_hours_per_week=row.max_hours_per_week,
                preferred_job_types=json.loads(row.preferred_job_types),
                preferred_job_sources=preferred_sources,
                schedule_blocks=[ScheduleBlock(**b) for b in json.loads(row.schedule_blocks)],
                resume_text=row.resume_text,
                created_at=datetime.fromisoformat(row.created_at),
                updated_at=datetime.fromisoformat(row.updated_at)
            )

    def save_profile(self, profile: Profile) -> Profile:
        """Save or update the user profile."""
        now = datetime.now().isoformat()
        schedule_json = json.dumps([b.model_dump() for b in profile.schedule_blocks])

        with self._get_connection() as conn:
            if profile.id:
                conn.execute(text("""
                    UPDATE profiles SET name=:name, major=:major, skills=:skills, interests=:interests,
                    min_hourly_rate=:min_hourly_rate, max_hours_per_week=:max_hours_per_week,
                    preferred_job_types=:preferred_job_types, preferred_job_sources=:preferred_job_sources,
                    schedule_blocks=:schedule_blocks, resume_text=:resume_text, updated_at=:updated_at
                    WHERE id=:id
                """), {
                    "name": profile.name, "major": profile.major,
                    "skills": json.dumps(profile.skills), "interests": json.dumps(profile.interests),
                    "min_hourly_rate": profile.min_hourly_rate, "max_hours_per_week": profile.max_hours_per_week,
                    "preferred_job_types": json.dumps(profile.preferred_job_types),
                    "preferred_job_sources": json.dumps(profile.preferred_job_sources),
                    "schedule_blocks": schedule_json, "resume_text": profile.resume_text,
                    "updated_at": now, "id": profile.id
                })
            else:
                result = conn.execute(text("""
                    INSERT INTO profiles (name, major, skills, interests, min_hourly_rate,
                    max_hours_per_week, preferred_job_types, preferred_job_sources, schedule_blocks,
                    resume_text, created_at, updated_at)
                    VALUES (:name, :major, :skills, :interests, :min_hourly_rate, :max_hours_per_week,
                    :preferred_job_types, :preferred_job_sources, :schedule_blocks, :resume_text,
                    :created_at, :updated_at)
                    RETURNING id
                """), {
                    "name": profile.name, "major": profile.major,
                    "skills": json.dumps(profile.skills), "interests": json.dumps(profile.interests),
                    "min_hourly_rate": profile.min_hourly_rate, "max_hours_per_week": profile.max_hours_per_week,
                    "preferred_job_types": json.dumps(profile.preferred_job_types),
                    "preferred_job_sources": json.dumps(profile.preferred_job_sources),
                    "schedule_blocks": schedule_json, "resume_text": profile.resume_text,
                    "created_at": now, "updated_at": now
                })
                profile.id = result.fetchone()[0]
        return profile

    # Job operations
    def save_job(self, job: Job) -> Job:
        """Save or update a job listing."""
        with self._get_connection() as conn:
            posted = job.posted_date.isoformat() if job.posted_date else None
            existing = conn.execute(text(
                "SELECT id FROM jobs WHERE source = :source AND source_id = :source_id"
            ), {"source": job.source, "source_id": job.source_id}).fetchone()

            if existing:
                job.id = existing[0]
                conn.execute(text("""
                    UPDATE jobs SET title=:title, company=:company, location=:location,
                    description=:description, salary_text=:salary_text, salary_min=:salary_min,
                    salary_max=:salary_max, salary_type=:salary_type, job_type=:job_type,
                    url=:url, posted_date=:posted_date, scraped_at=:scraped_at,
                    match_score=:match_score, match_reasons=:match_reasons,
                    extracted_requirements=:extracted_requirements, schedule_compatible=:schedule_compatible
                    WHERE id=:id
                """), {
                    "title": job.title, "company": job.company, "location": job.location,
                    "description": job.description, "salary_text": job.salary_text,
                    "salary_min": job.salary_min, "salary_max": job.salary_max,
                    "salary_type": job.salary_type, "job_type": job.job_type,
                    "url": job.url, "posted_date": posted, "scraped_at": job.scraped_at.isoformat(),
                    "match_score": job.match_score, "match_reasons": json.dumps(job.match_reasons),
                    "extracted_requirements": json.dumps(job.extracted_requirements),
                    "schedule_compatible": int(job.schedule_compatible) if job.schedule_compatible is not None else None,
                    "id": job.id
                })
            else:
                result = conn.execute(text("""
                    INSERT INTO jobs (source, source_id, title, company, location, description,
                    salary_text, salary_min, salary_max, salary_type, job_type, url, posted_date,
                    scraped_at, match_score, match_reasons, extracted_requirements, schedule_compatible)
                    VALUES (:source, :source_id, :title, :company, :location, :description,
                    :salary_text, :salary_min, :salary_max, :salary_type, :job_type, :url, :posted_date,
                    :scraped_at, :match_score, :match_reasons, :extracted_requirements, :schedule_compatible)
                    RETURNING id
                """), {
                    "source": job.source, "source_id": job.source_id, "title": job.title,
                    "company": job.company, "location": job.location, "description": job.description,
                    "salary_text": job.salary_text, "salary_min": job.salary_min,
                    "salary_max": job.salary_max, "salary_type": job.salary_type,
                    "job_type": job.job_type, "url": job.url, "posted_date": posted,
                    "scraped_at": job.scraped_at.isoformat(), "match_score": job.match_score,
                    "match_reasons": json.dumps(job.match_reasons),
                    "extracted_requirements": json.dumps(job.extracted_requirements),
                    "schedule_compatible": int(job.schedule_compatible) if job.schedule_compatible is not None else None
                })
                job.id = result.fetchone()[0]
        return job

    def get_jobs(self, source: Optional[str] = None, limit: int = 100) -> list[Job]:
        """Get jobs, optionally filtered by source."""
        with self._get_connection() as conn:
            if source:
                rows = conn.execute(text(
                    "SELECT * FROM jobs WHERE source = :source ORDER BY scraped_at DESC LIMIT :limit"
                ), {"source": source, "limit": limit}).fetchall()
            else:
                rows = conn.execute(text(
                    "SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT :limit"
                ), {"limit": limit}).fetchall()
            return [self._row_to_job(row) for row in rows]

    def get_job(self, job_id: int) -> Optional[Job]:
        """Get a single job by ID."""
        with self._get_connection() as conn:
            row = conn.execute(text("SELECT * FROM jobs WHERE id = :id"), {"id": job_id}).fetchone()
            return self._row_to_job(row) if row else None

    def _row_to_job(self, row) -> Job:
        """Convert a database row to a Job model."""
        return Job(
            id=row.id, source=row.source, source_id=row.source_id,
            title=row.title, company=row.company, location=row.location,
            description=row.description, salary_text=row.salary_text,
            salary_min=row.salary_min, salary_max=row.salary_max,
            salary_type=row.salary_type, job_type=row.job_type, url=row.url,
            posted_date=date.fromisoformat(row.posted_date) if row.posted_date else None,
            scraped_at=datetime.fromisoformat(row.scraped_at),
            match_score=row.match_score,
            match_reasons=json.loads(row.match_reasons) if row.match_reasons else [],
            extracted_requirements=json.loads(row.extracted_requirements) if row.extracted_requirements else [],
            schedule_compatible=bool(row.schedule_compatible) if row.schedule_compatible is not None else None
        )

    # Application operations
    def save_application(self, app: Application) -> Application:
        """Save or update an application."""
        now = datetime.now().isoformat()
        applied = app.applied_date.isoformat() if app.applied_date else None
        next_date = app.next_step_date.isoformat() if app.next_step_date else None

        with self._get_connection() as conn:
            if app.id:
                conn.execute(text("""
                    UPDATE applications SET job_id=:job_id, status=:status, applied_date=:applied_date,
                    notes=:notes, next_step=:next_step, next_step_date=:next_step_date,
                    cover_letter=:cover_letter, updated_at=:updated_at WHERE id=:id
                """), {
                    "job_id": app.job_id, "status": app.status, "applied_date": applied,
                    "notes": app.notes, "next_step": app.next_step, "next_step_date": next_date,
                    "cover_letter": app.cover_letter, "updated_at": now, "id": app.id
                })
            else:
                result = conn.execute(text("""
                    INSERT INTO applications (job_id, status, applied_date, notes, next_step,
                    next_step_date, cover_letter, created_at, updated_at)
                    VALUES (:job_id, :status, :applied_date, :notes, :next_step, :next_step_date,
                    :cover_letter, :created_at, :updated_at)
                    RETURNING id
                """), {
                    "job_id": app.job_id, "status": app.status, "applied_date": applied,
                    "notes": app.notes, "next_step": app.next_step, "next_step_date": next_date,
                    "cover_letter": app.cover_letter, "created_at": now, "updated_at": now
                })
                app.id = result.fetchone()[0]
        return app

    def get_applications(self, status: Optional[str] = None) -> list[Application]:
        """Get applications with their associated jobs."""
        with self._get_connection() as conn:
            if status:
                rows = conn.execute(text("""
                    SELECT a.*, j.title as job_title, j.company as job_company
                    FROM applications a JOIN jobs j ON a.job_id = j.id
                    WHERE a.status = :status ORDER BY a.updated_at DESC
                """), {"status": status}).fetchall()
            else:
                rows = conn.execute(text("""
                    SELECT a.*, j.title as job_title, j.company as job_company
                    FROM applications a JOIN jobs j ON a.job_id = j.id
                    ORDER BY a.updated_at DESC
                """)).fetchall()

            apps = []
            for row in rows:
                app = Application(
                    id=row.id, job_id=row.job_id, status=row.status,
                    applied_date=date.fromisoformat(row.applied_date) if row.applied_date else None,
                    notes=row.notes, next_step=row.next_step,
                    next_step_date=date.fromisoformat(row.next_step_date) if row.next_step_date else None,
                    cover_letter=row.cover_letter,
                    created_at=datetime.fromisoformat(row.created_at),
                    updated_at=datetime.fromisoformat(row.updated_at)
                )
                app.job = Job(
                    id=row.job_id, source="", source_id="",
                    title=row.job_title, company=row.job_company,
                    location="", url=""
                )
                apps.append(app)
            return apps

    def get_application_for_job(self, job_id: int) -> Optional[Application]:
        """Check if an application exists for a job."""
        with self._get_connection() as conn:
            row = conn.execute(text(
                "SELECT * FROM applications WHERE job_id = :job_id"
            ), {"job_id": job_id}).fetchone()
            if not row:
                return None
            return Application(
                id=row.id, job_id=row.job_id, status=row.status,
                applied_date=date.fromisoformat(row.applied_date) if row.applied_date else None,
                notes=row.notes, next_step=row.next_step,
                next_step_date=date.fromisoformat(row.next_step_date) if row.next_step_date else None,
                cover_letter=row.cover_letter,
                created_at=datetime.fromisoformat(row.created_at),
                updated_at=datetime.fromisoformat(row.updated_at)
            )

    def delete_application(self, app_id: int):
        """Delete an application."""
        with self._get_connection() as conn:
            conn.execute(text("DELETE FROM applications WHERE id = :id"), {"id": app_id})

    def get_application_stats(self) -> dict:
        """Get application statistics."""
        with self._get_connection() as conn:
            rows = conn.execute(text(
                "SELECT status, COUNT(*) as count FROM applications GROUP BY status"
            )).fetchall()
            return {row.status: row.count for row in rows}

    # User authentication operations
    @staticmethod
    def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """Hash a password with salt."""
        import hashlib
        import secrets
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt

    @staticmethod
    def _verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash."""
        new_hash, _ = DatabasePG._hash_password(password, salt)
        return new_hash == password_hash

    def create_user(self, username: str, password: str, email: str = None) -> Optional[User]:
        """Create a new user account."""
        password_hash, salt = self._hash_password(password)
        stored_hash = f"{salt}:{password_hash}"

        with self._get_connection() as conn:
            try:
                result = conn.execute(text("""
                    INSERT INTO users (username, password_hash, email, created_at)
                    VALUES (:username, :password_hash, :email, :created_at)
                    RETURNING id
                """), {
                    "username": username, "password_hash": stored_hash,
                    "email": email, "created_at": datetime.now().isoformat()
                })
                return User(
                    id=result.fetchone()[0],
                    username=username,
                    password_hash=stored_hash,
                    email=email,
                    created_at=datetime.now()
                )
            except Exception:
                return None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user and return their info if successful."""
        with self._get_connection() as conn:
            row = conn.execute(text(
                "SELECT * FROM users WHERE username = :username"
            ), {"username": username}).fetchone()

            if not row:
                return None

            stored_hash = row.password_hash
            salt, password_hash = stored_hash.split(":")

            if self._verify_password(password, password_hash, salt):
                conn.execute(text(
                    "UPDATE users SET last_login = :last_login WHERE id = :id"
                ), {"last_login": datetime.now().isoformat(), "id": row.id})
                return User(
                    id=row.id,
                    username=row.username,
                    password_hash=stored_hash,
                    email=row.email,
                    created_at=datetime.fromisoformat(row.created_at),
                    last_login=datetime.now()
                )
            return None

    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        with self._get_connection() as conn:
            row = conn.execute(text(
                "SELECT * FROM users WHERE id = :id"
            ), {"id": user_id}).fetchone()

            if not row:
                return None

            return User(
                id=row.id,
                username=row.username,
                password_hash=row.password_hash,
                email=row.email,
                created_at=datetime.fromisoformat(row.created_at),
                last_login=datetime.fromisoformat(row.last_login) if row.last_login else None
            )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        with self._get_connection() as conn:
            row = conn.execute(text(
                "SELECT * FROM users WHERE username = :username"
            ), {"username": username}).fetchone()

            if not row:
                return None

            return User(
                id=row.id,
                username=row.username,
                password_hash=row.password_hash,
                email=row.email,
                created_at=datetime.fromisoformat(row.created_at),
                last_login=datetime.fromisoformat(row.last_login) if row.last_login else None
            )

    def user_exists(self) -> bool:
        """Check if any user exists in the database."""
        with self._get_connection() as conn:
            row = conn.execute(text("SELECT COUNT(*) as count FROM users")).fetchone()
            return row.count > 0

    # Settings operations
    def save_setting(self, key: str, value: str) -> None:
        """Save a setting (key-value pair)."""
        with self._get_connection() as conn:
            conn.execute(text("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (:key, :value, :updated_at)
                ON CONFLICT(key) DO UPDATE SET value = :value, updated_at = :updated_at
            """), {"key": key, "value": value, "updated_at": datetime.now().isoformat()})

    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value by key."""
        with self._get_connection() as conn:
            row = conn.execute(text("SELECT value FROM settings WHERE key = :key"), {"key": key}).fetchone()
            return row.value if row else None

    def get_all_settings(self) -> dict:
        """Get all settings as a dictionary."""
        with self._get_connection() as conn:
            rows = conn.execute(text("SELECT key, value FROM settings")).fetchall()
            return {row.key: row.value for row in rows}

    def delete_setting(self, key: str) -> None:
        """Delete a setting."""
        with self._get_connection() as conn:
            conn.execute(text("DELETE FROM settings WHERE key = :key"), {"key": key})

    def save_settings_dict(self, prefix: str, data: dict) -> None:
        """Save a dictionary of settings with a prefix."""
        for key, value in data.items():
            full_key = f"{prefix}.{key}"
            self.save_setting(full_key, json.dumps(value) if not isinstance(value, str) else value)

    def get_settings_dict(self, prefix: str) -> dict:
        """Get all settings with a given prefix as a dictionary."""
        with self._get_connection() as conn:
            rows = conn.execute(text(
                "SELECT key, value FROM settings WHERE key LIKE :prefix"
            ), {"prefix": f"{prefix}.%"}).fetchall()
            result = {}
            for row in rows:
                key = row.key.replace(f"{prefix}.", "", 1)
                value = row.value
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            return result

    # Search Schedule operations
    def save_search_schedule(self, schedule: SearchSchedule) -> SearchSchedule:
        """Save or update a search schedule."""
        now = datetime.now().isoformat()
        last_run = schedule.last_run.isoformat() if schedule.last_run else None
        next_run = schedule.next_run.isoformat() if schedule.next_run else None

        with self._get_connection() as conn:
            if schedule.id:
                conn.execute(text("""
                    UPDATE search_schedules SET user_id=:user_id, enabled=:enabled, frequency=:frequency,
                    time_preference=:time_preference, last_run=:last_run, next_run=:next_run,
                    search_query=:search_query, search_location_id=:search_location_id,
                    search_radius=:search_radius, search_sources=:search_sources,
                    search_job_types=:search_job_types, updated_at=:updated_at WHERE id=:id
                """), {
                    "user_id": schedule.user_id, "enabled": int(schedule.enabled),
                    "frequency": schedule.frequency, "time_preference": schedule.time_preference,
                    "last_run": last_run, "next_run": next_run, "search_query": schedule.search_query,
                    "search_location_id": schedule.search_location_id,
                    "search_radius": schedule.search_radius,
                    "search_sources": json.dumps(schedule.search_sources),
                    "search_job_types": json.dumps(schedule.search_job_types),
                    "updated_at": now, "id": schedule.id
                })
            else:
                result = conn.execute(text("""
                    INSERT INTO search_schedules (user_id, enabled, frequency, time_preference,
                    last_run, next_run, search_query, search_location_id, search_radius,
                    search_sources, search_job_types, created_at, updated_at)
                    VALUES (:user_id, :enabled, :frequency, :time_preference, :last_run, :next_run,
                    :search_query, :search_location_id, :search_radius, :search_sources,
                    :search_job_types, :created_at, :updated_at)
                    RETURNING id
                """), {
                    "user_id": schedule.user_id, "enabled": int(schedule.enabled),
                    "frequency": schedule.frequency, "time_preference": schedule.time_preference,
                    "last_run": last_run, "next_run": next_run, "search_query": schedule.search_query,
                    "search_location_id": schedule.search_location_id,
                    "search_radius": schedule.search_radius,
                    "search_sources": json.dumps(schedule.search_sources),
                    "search_job_types": json.dumps(schedule.search_job_types),
                    "created_at": now, "updated_at": now
                })
                schedule.id = result.fetchone()[0]
        return schedule

    def get_search_schedule(self) -> Optional[SearchSchedule]:
        """Get the search schedule (single user app)."""
        with self._get_connection() as conn:
            row = conn.execute(text("SELECT * FROM search_schedules LIMIT 1")).fetchone()
            if not row:
                return None
            return SearchSchedule(
                id=row.id, user_id=row.user_id, enabled=bool(row.enabled),
                frequency=row.frequency, time_preference=row.time_preference,
                last_run=datetime.fromisoformat(row.last_run) if row.last_run else None,
                next_run=datetime.fromisoformat(row.next_run) if row.next_run else None,
                search_query=row.search_query,
                search_location_id=row.search_location_id,
                search_radius=row.search_radius,
                search_sources=json.loads(row.search_sources) if row.search_sources else [],
                search_job_types=json.loads(row.search_job_types) if row.search_job_types else [],
                created_at=datetime.fromisoformat(row.created_at),
                updated_at=datetime.fromisoformat(row.updated_at)
            )

    def delete_search_schedule(self, schedule_id: int):
        """Delete a search schedule."""
        with self._get_connection() as conn:
            conn.execute(text("DELETE FROM search_schedules WHERE id = :id"), {"id": schedule_id})

    # Notification operations
    def save_notification(self, notification: Notification) -> Notification:
        """Save a new notification."""
        with self._get_connection() as conn:
            if notification.id:
                conn.execute(text("""
                    UPDATE notifications SET type=:type, title=:title, message=:message,
                    related_job_ids=:related_job_ids, read=:read, email_sent=:email_sent WHERE id=:id
                """), {
                    "type": notification.type, "title": notification.title,
                    "message": notification.message,
                    "related_job_ids": json.dumps(notification.related_job_ids),
                    "read": int(notification.read), "email_sent": int(notification.email_sent),
                    "id": notification.id
                })
            else:
                result = conn.execute(text("""
                    INSERT INTO notifications (type, title, message, related_job_ids, read, email_sent, created_at)
                    VALUES (:type, :title, :message, :related_job_ids, :read, :email_sent, :created_at)
                    RETURNING id
                """), {
                    "type": notification.type, "title": notification.title,
                    "message": notification.message,
                    "related_job_ids": json.dumps(notification.related_job_ids),
                    "read": int(notification.read), "email_sent": int(notification.email_sent),
                    "created_at": datetime.now().isoformat()
                })
                notification.id = result.fetchone()[0]
        return notification

    def get_notifications(self, unread_only: bool = False, limit: int = 50) -> list[Notification]:
        """Get notifications, optionally filtered to unread only."""
        with self._get_connection() as conn:
            if unread_only:
                rows = conn.execute(text(
                    "SELECT * FROM notifications WHERE read = 0 ORDER BY created_at DESC LIMIT :limit"
                ), {"limit": limit}).fetchall()
            else:
                rows = conn.execute(text(
                    "SELECT * FROM notifications ORDER BY created_at DESC LIMIT :limit"
                ), {"limit": limit}).fetchall()

            return [Notification(
                id=row.id, type=row.type, title=row.title, message=row.message,
                related_job_ids=json.loads(row.related_job_ids) if row.related_job_ids else [],
                read=bool(row.read), email_sent=bool(row.email_sent),
                created_at=datetime.fromisoformat(row.created_at)
            ) for row in rows]

    def get_unread_notification_count(self) -> int:
        """Get count of unread notifications."""
        with self._get_connection() as conn:
            row = conn.execute(text("SELECT COUNT(*) as count FROM notifications WHERE read = 0")).fetchone()
            return row.count

    def mark_notification_read(self, notification_id: int):
        """Mark a notification as read."""
        with self._get_connection() as conn:
            conn.execute(text("UPDATE notifications SET read = 1 WHERE id = :id"), {"id": notification_id})

    def mark_all_notifications_read(self):
        """Mark all notifications as read."""
        with self._get_connection() as conn:
            conn.execute(text("UPDATE notifications SET read = 1"))

    def delete_notification(self, notification_id: int):
        """Delete a notification."""
        with self._get_connection() as conn:
            conn.execute(text("DELETE FROM notifications WHERE id = :id"), {"id": notification_id})

    def clear_all_notifications(self):
        """Delete all notifications."""
        with self._get_connection() as conn:
            conn.execute(text("DELETE FROM notifications"))

    # Saved Search Result operations
    def save_search_result(self, result: SavedSearchResult) -> SavedSearchResult:
        """Save a search result record."""
        with self._get_connection() as conn:
            res = conn.execute(text("""
                INSERT INTO saved_search_results (schedule_id, run_at, jobs_found, new_jobs, job_ids, error_message)
                VALUES (:schedule_id, :run_at, :jobs_found, :new_jobs, :job_ids, :error_message)
                RETURNING id
            """), {
                "schedule_id": result.schedule_id, "run_at": result.run_at.isoformat(),
                "jobs_found": result.jobs_found, "new_jobs": result.new_jobs,
                "job_ids": json.dumps(result.job_ids), "error_message": result.error_message
            })
            result.id = res.fetchone()[0]
        return result

    def get_search_results(self, schedule_id: int = None, limit: int = 10) -> list[SavedSearchResult]:
        """Get search results, optionally filtered by schedule."""
        with self._get_connection() as conn:
            if schedule_id:
                rows = conn.execute(text(
                    "SELECT * FROM saved_search_results WHERE schedule_id = :schedule_id ORDER BY run_at DESC LIMIT :limit"
                ), {"schedule_id": schedule_id, "limit": limit}).fetchall()
            else:
                rows = conn.execute(text(
                    "SELECT * FROM saved_search_results ORDER BY run_at DESC LIMIT :limit"
                ), {"limit": limit}).fetchall()

            return [SavedSearchResult(
                id=row.id, schedule_id=row.schedule_id,
                run_at=datetime.fromisoformat(row.run_at),
                jobs_found=row.jobs_found, new_jobs=row.new_jobs,
                job_ids=json.loads(row.job_ids) if row.job_ids else [],
                error_message=row.error_message
            ) for row in rows]

    # Notification Preferences operations
    def save_notification_preferences(self, prefs: NotificationPreferences) -> NotificationPreferences:
        """Save notification preferences."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            if prefs.id:
                conn.execute(text("""
                    UPDATE notification_preferences SET email_enabled=:email_enabled,
                    email_address=:email_address, email_verified=:email_verified,
                    digest_frequency=:digest_frequency, notify_new_jobs=:notify_new_jobs,
                    notify_application_updates=:notify_application_updates, updated_at=:updated_at
                    WHERE id=:id
                """), {
                    "email_enabled": int(prefs.email_enabled), "email_address": prefs.email_address,
                    "email_verified": int(prefs.email_verified), "digest_frequency": prefs.digest_frequency,
                    "notify_new_jobs": int(prefs.notify_new_jobs),
                    "notify_application_updates": int(prefs.notify_application_updates),
                    "updated_at": now, "id": prefs.id
                })
            else:
                result = conn.execute(text("""
                    INSERT INTO notification_preferences (email_enabled, email_address, email_verified,
                    digest_frequency, notify_new_jobs, notify_application_updates, created_at, updated_at)
                    VALUES (:email_enabled, :email_address, :email_verified, :digest_frequency,
                    :notify_new_jobs, :notify_application_updates, :created_at, :updated_at)
                    RETURNING id
                """), {
                    "email_enabled": int(prefs.email_enabled), "email_address": prefs.email_address,
                    "email_verified": int(prefs.email_verified), "digest_frequency": prefs.digest_frequency,
                    "notify_new_jobs": int(prefs.notify_new_jobs),
                    "notify_application_updates": int(prefs.notify_application_updates),
                    "created_at": now, "updated_at": now
                })
                prefs.id = result.fetchone()[0]
        return prefs

    def get_notification_preferences(self) -> Optional[NotificationPreferences]:
        """Get notification preferences (single user app)."""
        with self._get_connection() as conn:
            row = conn.execute(text("SELECT * FROM notification_preferences LIMIT 1")).fetchone()
            if not row:
                return None
            return NotificationPreferences(
                id=row.id, email_enabled=bool(row.email_enabled),
                email_address=row.email_address, email_verified=bool(row.email_verified),
                digest_frequency=row.digest_frequency,
                notify_new_jobs=bool(row.notify_new_jobs),
                notify_application_updates=bool(row.notify_application_updates),
                created_at=datetime.fromisoformat(row.created_at),
                updated_at=datetime.fromisoformat(row.updated_at)
            )

    def get_location(self, location_id: int) -> Optional[SavedLocation]:
        """Get a single location by ID."""
        with self._get_connection() as conn:
            row = conn.execute(text("SELECT * FROM locations WHERE id = :id"), {"id": location_id}).fetchone()
            if not row:
                return None
            return SavedLocation(
                id=row.id, name=row.name, address=row.address,
                latitude=row.latitude, longitude=row.longitude,
                radius_miles=row.radius_miles, is_default=bool(row.is_default),
                created_at=datetime.fromisoformat(row.created_at)
            )
