"""Pydantic data models for the job search agent."""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """User account for authentication."""
    id: Optional[int] = None
    username: str = Field(..., description="Unique username")
    password_hash: str = Field(..., description="Hashed password")
    email: Optional[str] = Field(None, description="User email")
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None


class SavedLocation(BaseModel):
    """A saved search location (university, home, etc.)."""
    id: Optional[int] = None
    name: str = Field(..., description="Display name (e.g., 'UC Berkeley')")
    address: str = Field(..., description="Full address for geocoding")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_miles: int = Field(default=10, description="Default search radius")
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class ScheduleBlock(BaseModel):
    """A block of time when the user is NOT available (e.g., class)."""
    day: str = Field(..., description="Day of week: Mon, Tue, Wed, Thu, Fri, Sat, Sun")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    label: Optional[str] = Field(None, description="Optional label (e.g., 'CS101')")


class Profile(BaseModel):
    """User profile with preferences and availability."""
    id: Optional[int] = None
    name: str = Field(default="", description="User's name")
    major: str = Field(default="", description="Field of study")
    skills: list[str] = Field(default_factory=list, description="List of skills")
    interests: list[str] = Field(default_factory=list, description="Job interests")
    min_hourly_rate: Optional[float] = Field(None, description="Minimum acceptable hourly rate")
    max_hours_per_week: Optional[int] = Field(None, description="Max hours available to work")
    preferred_job_types: list[str] = Field(default_factory=list, description="Part-time, Full-time, etc.")
    preferred_job_sources: list[str] = Field(default_factory=list, description="Indeed, LinkedIn, etc.")
    schedule_blocks: list[ScheduleBlock] = Field(default_factory=list, description="Unavailable times")
    resume_text: Optional[str] = Field(None, description="Uploaded resume as text")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Job(BaseModel):
    """A job listing scraped from a source."""
    id: Optional[int] = None
    source: str = Field(..., description="Source site: indeed, linkedin, etc.")
    source_id: str = Field(..., description="Unique ID from the source")
    title: str
    company: str
    location: str
    description: str = ""
    salary_text: Optional[str] = Field(None, description="Raw salary string")
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_type: Optional[str] = Field(None, description="hourly, yearly, etc.")
    job_type: Optional[str] = Field(None, description="Full-time, Part-time, etc.")
    url: str = Field(..., description="Link to the job posting")
    posted_date: Optional[date] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    # AI-generated fields
    match_score: Optional[float] = Field(None, description="0-100 match score")
    match_reasons: list[str] = Field(default_factory=list)
    extracted_requirements: list[str] = Field(default_factory=list)
    schedule_compatible: Optional[bool] = None

    @property
    def unique_key(self) -> str:
        """Generate a unique key for deduplication."""
        return f"{self.source}:{self.source_id}"


class Application(BaseModel):
    """Tracks a job application."""
    id: Optional[int] = None
    job_id: int = Field(..., description="Foreign key to Job")
    status: str = Field(default="Saved", description="Current application status")
    applied_date: Optional[date] = None
    notes: str = ""
    next_step: Optional[str] = None
    next_step_date: Optional[date] = None
    cover_letter: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Joined field (not stored in DB)
    job: Optional[Job] = None
