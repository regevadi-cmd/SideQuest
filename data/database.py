"""SQLite database operations for the job search agent."""
import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from .models import Job, Profile, Application, SavedLocation, ScheduleBlock, User


class Database:
    """SQLite database manager for job search data."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_tables(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                );

                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    radius_miles INTEGER DEFAULT 10,
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'Saved',
                    applied_date TEXT,
                    notes TEXT DEFAULT '',
                    next_step TEXT,
                    next_step_date TEXT,
                    cover_letter TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
                CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
                CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Migration: Add preferred_job_sources column if it doesn't exist
            try:
                conn.execute("SELECT preferred_job_sources FROM profiles LIMIT 1")
            except Exception:
                conn.execute("ALTER TABLE profiles ADD COLUMN preferred_job_sources TEXT DEFAULT '[]'")

    # Location operations
    def save_location(self, location: SavedLocation) -> SavedLocation:
        """Save or update a location."""
        with self._get_connection() as conn:
            if location.is_default:
                conn.execute("UPDATE locations SET is_default = 0")

            if location.id:
                conn.execute("""
                    UPDATE locations SET name=?, address=?, latitude=?, longitude=?,
                    radius_miles=?, is_default=? WHERE id=?
                """, (location.name, location.address, location.latitude, location.longitude,
                      location.radius_miles, int(location.is_default), location.id))
            else:
                cursor = conn.execute("""
                    INSERT INTO locations (name, address, latitude, longitude, radius_miles, is_default, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (location.name, location.address, location.latitude, location.longitude,
                      location.radius_miles, int(location.is_default), datetime.now().isoformat()))
                location.id = cursor.lastrowid
        return location

    def get_locations(self) -> list[SavedLocation]:
        """Get all saved locations."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM locations ORDER BY is_default DESC, name").fetchall()
            return [SavedLocation(
                id=row["id"], name=row["name"], address=row["address"],
                latitude=row["latitude"], longitude=row["longitude"],
                radius_miles=row["radius_miles"], is_default=bool(row["is_default"]),
                created_at=datetime.fromisoformat(row["created_at"])
            ) for row in rows]

    def delete_location(self, location_id: int):
        """Delete a location."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))

    # Profile operations
    def get_profile(self) -> Optional[Profile]:
        """Get the user profile (single user app)."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM profiles LIMIT 1").fetchone()
            if not row:
                return None
            # Handle preferred_job_sources which may not exist in older databases
            try:
                preferred_sources = json.loads(row["preferred_job_sources"]) if row["preferred_job_sources"] else []
            except (KeyError, TypeError):
                preferred_sources = []
            return Profile(
                id=row["id"], name=row["name"], major=row["major"],
                skills=json.loads(row["skills"]), interests=json.loads(row["interests"]),
                min_hourly_rate=row["min_hourly_rate"], max_hours_per_week=row["max_hours_per_week"],
                preferred_job_types=json.loads(row["preferred_job_types"]),
                preferred_job_sources=preferred_sources,
                schedule_blocks=[ScheduleBlock(**b) for b in json.loads(row["schedule_blocks"])],
                resume_text=row["resume_text"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )

    def save_profile(self, profile: Profile) -> Profile:
        """Save or update the user profile."""
        now = datetime.now().isoformat()
        schedule_json = json.dumps([b.model_dump() for b in profile.schedule_blocks])

        with self._get_connection() as conn:
            if profile.id:
                conn.execute("""
                    UPDATE profiles SET name=?, major=?, skills=?, interests=?,
                    min_hourly_rate=?, max_hours_per_week=?, preferred_job_types=?,
                    preferred_job_sources=?, schedule_blocks=?, resume_text=?, updated_at=? WHERE id=?
                """, (profile.name, profile.major, json.dumps(profile.skills),
                      json.dumps(profile.interests), profile.min_hourly_rate,
                      profile.max_hours_per_week, json.dumps(profile.preferred_job_types),
                      json.dumps(profile.preferred_job_sources),
                      schedule_json, profile.resume_text, now, profile.id))
            else:
                cursor = conn.execute("""
                    INSERT INTO profiles (name, major, skills, interests, min_hourly_rate,
                    max_hours_per_week, preferred_job_types, preferred_job_sources, schedule_blocks, resume_text,
                    created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (profile.name, profile.major, json.dumps(profile.skills),
                      json.dumps(profile.interests), profile.min_hourly_rate,
                      profile.max_hours_per_week, json.dumps(profile.preferred_job_types),
                      json.dumps(profile.preferred_job_sources),
                      schedule_json, profile.resume_text, now, now))
                profile.id = cursor.lastrowid
        return profile

    # Job operations
    def save_job(self, job: Job) -> Job:
        """Save or update a job listing."""
        with self._get_connection() as conn:
            posted = job.posted_date.isoformat() if job.posted_date else None
            existing = conn.execute(
                "SELECT id FROM jobs WHERE source = ? AND source_id = ?",
                (job.source, job.source_id)
            ).fetchone()

            if existing:
                job.id = existing["id"]
                conn.execute("""
                    UPDATE jobs SET title=?, company=?, location=?, description=?,
                    salary_text=?, salary_min=?, salary_max=?, salary_type=?, job_type=?,
                    url=?, posted_date=?, scraped_at=?, match_score=?, match_reasons=?,
                    extracted_requirements=?, schedule_compatible=?
                    WHERE id=?
                """, (job.title, job.company, job.location, job.description,
                      job.salary_text, job.salary_min, job.salary_max, job.salary_type,
                      job.job_type, job.url, posted, job.scraped_at.isoformat(),
                      job.match_score, json.dumps(job.match_reasons),
                      json.dumps(job.extracted_requirements),
                      int(job.schedule_compatible) if job.schedule_compatible is not None else None,
                      job.id))
            else:
                cursor = conn.execute("""
                    INSERT INTO jobs (source, source_id, title, company, location, description,
                    salary_text, salary_min, salary_max, salary_type, job_type, url, posted_date,
                    scraped_at, match_score, match_reasons, extracted_requirements, schedule_compatible)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (job.source, job.source_id, job.title, job.company, job.location,
                      job.description, job.salary_text, job.salary_min, job.salary_max,
                      job.salary_type, job.job_type, job.url, posted, job.scraped_at.isoformat(),
                      job.match_score, json.dumps(job.match_reasons),
                      json.dumps(job.extracted_requirements),
                      int(job.schedule_compatible) if job.schedule_compatible is not None else None))
                job.id = cursor.lastrowid
        return job

    def get_jobs(self, source: Optional[str] = None, limit: int = 100) -> list[Job]:
        """Get jobs, optionally filtered by source."""
        with self._get_connection() as conn:
            if source:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE source = ? ORDER BY scraped_at DESC LIMIT ?",
                    (source, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [self._row_to_job(row) for row in rows]

    def get_job(self, job_id: int) -> Optional[Job]:
        """Get a single job by ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return self._row_to_job(row) if row else None

    def _row_to_job(self, row) -> Job:
        """Convert a database row to a Job model."""
        return Job(
            id=row["id"], source=row["source"], source_id=row["source_id"],
            title=row["title"], company=row["company"], location=row["location"],
            description=row["description"], salary_text=row["salary_text"],
            salary_min=row["salary_min"], salary_max=row["salary_max"],
            salary_type=row["salary_type"], job_type=row["job_type"], url=row["url"],
            posted_date=date.fromisoformat(row["posted_date"]) if row["posted_date"] else None,
            scraped_at=datetime.fromisoformat(row["scraped_at"]),
            match_score=row["match_score"],
            match_reasons=json.loads(row["match_reasons"]) if row["match_reasons"] else [],
            extracted_requirements=json.loads(row["extracted_requirements"]) if row["extracted_requirements"] else [],
            schedule_compatible=bool(row["schedule_compatible"]) if row["schedule_compatible"] is not None else None
        )

    # Application operations
    def save_application(self, app: Application) -> Application:
        """Save or update an application."""
        now = datetime.now().isoformat()
        applied = app.applied_date.isoformat() if app.applied_date else None
        next_date = app.next_step_date.isoformat() if app.next_step_date else None

        with self._get_connection() as conn:
            if app.id:
                conn.execute("""
                    UPDATE applications SET job_id=?, status=?, applied_date=?, notes=?,
                    next_step=?, next_step_date=?, cover_letter=?, updated_at=? WHERE id=?
                """, (app.job_id, app.status, applied, app.notes, app.next_step,
                      next_date, app.cover_letter, now, app.id))
            else:
                cursor = conn.execute("""
                    INSERT INTO applications (job_id, status, applied_date, notes, next_step,
                    next_step_date, cover_letter, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (app.job_id, app.status, applied, app.notes, app.next_step,
                      next_date, app.cover_letter, now, now))
                app.id = cursor.lastrowid
        return app

    def get_applications(self, status: Optional[str] = None) -> list[Application]:
        """Get applications with their associated jobs."""
        with self._get_connection() as conn:
            if status:
                rows = conn.execute("""
                    SELECT a.*, j.title as job_title, j.company as job_company
                    FROM applications a JOIN jobs j ON a.job_id = j.id
                    WHERE a.status = ? ORDER BY a.updated_at DESC
                """, (status,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT a.*, j.title as job_title, j.company as job_company
                    FROM applications a JOIN jobs j ON a.job_id = j.id
                    ORDER BY a.updated_at DESC
                """).fetchall()

            apps = []
            for row in rows:
                app = Application(
                    id=row["id"], job_id=row["job_id"], status=row["status"],
                    applied_date=date.fromisoformat(row["applied_date"]) if row["applied_date"] else None,
                    notes=row["notes"], next_step=row["next_step"],
                    next_step_date=date.fromisoformat(row["next_step_date"]) if row["next_step_date"] else None,
                    cover_letter=row["cover_letter"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
                # Add minimal job info for display
                app.job = Job(
                    id=row["job_id"], source="", source_id="",
                    title=row["job_title"], company=row["job_company"],
                    location="", url=""
                )
                apps.append(app)
            return apps

    def get_application_for_job(self, job_id: int) -> Optional[Application]:
        """Check if an application exists for a job."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM applications WHERE job_id = ?", (job_id,)
            ).fetchone()
            if not row:
                return None
            return Application(
                id=row["id"], job_id=row["job_id"], status=row["status"],
                applied_date=date.fromisoformat(row["applied_date"]) if row["applied_date"] else None,
                notes=row["notes"], next_step=row["next_step"],
                next_step_date=date.fromisoformat(row["next_step_date"]) if row["next_step_date"] else None,
                cover_letter=row["cover_letter"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )

    def delete_application(self, app_id: int):
        """Delete an application."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))

    def get_application_stats(self) -> dict:
        """Get application statistics."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT status, COUNT(*) as count FROM applications GROUP BY status
            """).fetchall()
            return {row["status"]: row["count"] for row in rows}

    # User authentication operations
    @staticmethod
    def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """Hash a password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt

    @staticmethod
    def _verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash."""
        new_hash, _ = Database._hash_password(password, salt)
        return new_hash == password_hash

    def create_user(self, username: str, password: str, email: str = None) -> Optional[User]:
        """Create a new user account."""
        password_hash, salt = self._hash_password(password)
        # Store salt with hash (salt:hash format)
        stored_hash = f"{salt}:{password_hash}"

        with self._get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO users (username, password_hash, email, created_at)
                    VALUES (?, ?, ?, ?)
                """, (username, stored_hash, email, datetime.now().isoformat()))
                return User(
                    id=cursor.lastrowid,
                    username=username,
                    password_hash=stored_hash,
                    email=email,
                    created_at=datetime.now()
                )
            except sqlite3.IntegrityError:
                # Username already exists
                return None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user and return their info if successful."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            if not row:
                return None

            stored_hash = row["password_hash"]
            salt, password_hash = stored_hash.split(":")

            if self._verify_password(password, password_hash, salt):
                # Update last login
                conn.execute(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.now().isoformat(), row["id"])
                )
                return User(
                    id=row["id"],
                    username=row["username"],
                    password_hash=stored_hash,
                    email=row["email"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_login=datetime.now()
                )
            return None

    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()

            if not row:
                return None

            return User(
                id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                email=row["email"],
                created_at=datetime.fromisoformat(row["created_at"]),
                last_login=datetime.fromisoformat(row["last_login"]) if row["last_login"] else None
            )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            if not row:
                return None

            return User(
                id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                email=row["email"],
                created_at=datetime.fromisoformat(row["created_at"]),
                last_login=datetime.fromisoformat(row["last_login"]) if row["last_login"] else None
            )

    def user_exists(self) -> bool:
        """Check if any user exists in the database."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
            return row["count"] > 0

    # Settings operations
    def save_setting(self, key: str, value: str) -> None:
        """Save a setting (key-value pair)."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
            """, (key, value, datetime.now().isoformat(), value, datetime.now().isoformat()))

    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value by key."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    def get_all_settings(self) -> dict:
        """Get all settings as a dictionary."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {row["key"]: row["value"] for row in rows}

    def delete_setting(self, key: str) -> None:
        """Delete a setting."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM settings WHERE key = ?", (key,))

    def save_settings_dict(self, prefix: str, data: dict) -> None:
        """Save a dictionary of settings with a prefix."""
        for key, value in data.items():
            full_key = f"{prefix}.{key}"
            self.save_setting(full_key, json.dumps(value) if not isinstance(value, str) else value)

    def get_settings_dict(self, prefix: str) -> dict:
        """Get all settings with a given prefix as a dictionary."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT key, value FROM settings WHERE key LIKE ?",
                (f"{prefix}.%",)
            ).fetchall()
            result = {}
            for row in rows:
                key = row["key"].replace(f"{prefix}.", "", 1)
                value = row["value"]
                # Try to parse as JSON
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            return result
