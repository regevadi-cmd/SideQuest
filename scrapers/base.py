"""Base scraper class with common functionality."""
import time
import httpx
from abc import ABC, abstractmethod
from typing import Optional

from config import SCRAPE_DELAY_SECONDS, REQUEST_TIMEOUT, MAX_RETRIES
from data.models import Job


class BaseScraper(ABC):
    """Abstract base class for job scrapers."""

    def __init__(self):
        self.source_name = "base"
        self.delay = SCRAPE_DELAY_SECONDS
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        self._last_request_time = 0

        # Common headers to look like a browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()

    def _fetch(self, url: str, params: Optional[dict] = None) -> Optional[str]:
        """Fetch a URL with retries and rate limiting."""
        self._rate_limit()

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                    response = client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    return response.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    # Likely blocked, increase delay
                    self.delay *= 2
                    time.sleep(self.delay)
                elif e.response.status_code == 429:
                    # Rate limited, wait longer
                    time.sleep(self.delay * (attempt + 1) * 2)
                else:
                    raise
            except (httpx.TimeoutException, httpx.ConnectError):
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                else:
                    raise

        return None

    @abstractmethod
    def search(
        self,
        query: str,
        location: str,
        radius: int = 10,
        job_types: Optional[list[str]] = None,
        max_results: int = 50
    ) -> list[Job]:
        """
        Search for jobs.

        Args:
            query: Search keywords
            location: Location string
            radius: Search radius in miles
            job_types: Filter by job types
            max_results: Maximum number of results to return

        Returns:
            List of Job objects
        """
        pass

    def _clean_text(self, text: Optional[str]) -> str:
        """Clean up scraped text."""
        if not text:
            return ""
        # Remove extra whitespace
        return " ".join(text.split())

    def _generate_source_id(self, *parts) -> str:
        """Generate a unique source ID from parts."""
        import hashlib
        combined = "|".join(str(p) for p in parts if p)
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _is_valid_job(self, job: Job) -> bool:
        """Check if a job has valid (non-masked) content."""
        # Check for masked/invalid titles (asterisks, placeholder text)
        if not job.title or len(job.title) < 3:
            return False

        # Detect asterisk masking (e.g., "**************")
        asterisk_ratio = job.title.count('*') / len(job.title)
        if asterisk_ratio > 0.3:  # More than 30% asterisks
            return False

        # Check for common placeholder patterns
        invalid_patterns = [
            '****', '----', '....', 'xxxx',
            'confidential', 'hidden', 'private',
            'position title', 'job title', 'title here'
        ]
        title_lower = job.title.lower()
        if any(pattern in title_lower for pattern in invalid_patterns):
            return False

        # Check company name validity
        if job.company:
            company_asterisks = job.company.count('*') / max(len(job.company), 1)
            if company_asterisks > 0.3:
                return False

        return True

    def _filter_valid_jobs(self, jobs: list[Job]) -> list[Job]:
        """Filter out jobs with masked or invalid content."""
        return [job for job in jobs if self._is_valid_job(job)]
