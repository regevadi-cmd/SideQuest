"""Configuration settings for the Student Job Search Agent."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
DATABASE_URL = os.getenv("DATABASE_URL")

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "jobs.db"

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Scraping settings
SCRAPE_DELAY_SECONDS = 2.0  # Delay between requests to avoid rate limiting
REQUEST_TIMEOUT = 30  # Seconds
MAX_RETRIES = 3

# Default search settings
DEFAULT_RADIUS_MILES = 10
MAX_RESULTS_PER_SOURCE = 50

# AI settings
DEFAULT_AI_PROVIDER = "claude"  # Options: claude, openai, ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_ENABLED = not IS_PRODUCTION  # Ollama not available in cloud deployment

# Job types for filtering
JOB_TYPES = [
    "Full-time",
    "Part-time",
    "Internship",
    "Contract",
    "Temporary",
    "Work-study",
    "On-campus",
]

# Application statuses
APPLICATION_STATUSES = [
    "Saved",
    "Applied",
    "Phone Screen",
    "Interview",
    "Offer",
    "Accepted",
    "Rejected",
    "Withdrawn",
]
