"""Job scrapers package."""
from .base import BaseScraper
from .indeed import IndeedScraper
from .linkedin import LinkedInScraper
from .glassdoor import GlassdoorScraper
from .collegerecruiter import CollegeRecruiterScraper
from .wayup import WayUpScraper
from .university import UniversityJobBoardScraper

__all__ = [
    "BaseScraper",
    "IndeedScraper",
    "LinkedInScraper",
    "GlassdoorScraper",
    "CollegeRecruiterScraper",
    "WayUpScraper",
    "UniversityJobBoardScraper",
]
