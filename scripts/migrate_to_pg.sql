-- PostgreSQL Migration Script for SideQuest
-- Run this in your Supabase SQL editor or PostgreSQL client

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    created_at TEXT NOT NULL,
    last_login TEXT
);

-- Profiles table
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

-- Locations table
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

-- Jobs table
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

-- Applications table
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

-- Settings table (key-value store)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
