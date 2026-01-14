"""LinkedIn job scraper."""
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import re
import urllib.parse

from .base import BaseScraper
from data.models import Job


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings (public job board, no login required)."""

    def __init__(self):
        super().__init__()
        self.source_name = "linkedin"
        self.base_url = "https://www.linkedin.com/jobs/search"
        # LinkedIn is stricter, use longer delays
        self.delay = 3.0

    def search(
        self,
        query: str,
        location: str,
        radius: int = 10,
        job_types: Optional[list[str]] = None,
        max_results: int = 50
    ) -> list[Job]:
        """Search LinkedIn for jobs."""
        jobs = []

        # Build job type filter (LinkedIn uses f_JT parameter)
        jt_codes = []
        if job_types:
            type_map = {
                "Full-time": "F",
                "Part-time": "P",
                "Internship": "I",
                "Contract": "C",
                "Temporary": "T",
            }
            for jt in job_types:
                if jt in type_map:
                    jt_codes.append(type_map[jt])

        # Convert radius to LinkedIn's distance parameter
        # LinkedIn uses: 0=exact, 5, 10, 25, 50, 100
        if radius <= 5:
            distance = 5
        elif radius <= 10:
            distance = 10
        elif radius <= 25:
            distance = 25
        elif radius <= 50:
            distance = 50
        else:
            distance = 100

        # Paginate through results
        start = 0
        page_size = 25  # LinkedIn shows 25 per page

        while len(jobs) < max_results:
            params = {
                "keywords": query,
                "location": location,
                "distance": distance,
                "start": start,
                "sortBy": "DD",  # Date descending
            }

            if jt_codes:
                params["f_JT"] = ",".join(jt_codes)

            # Add entry-level filter for student jobs
            params["f_E"] = "1,2"  # Entry level and Associate

            try:
                html = self._fetch(self.base_url, params)
                if not html:
                    break

                page_jobs = self._parse_results(html)
                if not page_jobs:
                    break

                jobs.extend(page_jobs)
                start += page_size

                # Stop if we've reached the last page
                if len(page_jobs) < page_size:
                    break

            except Exception as e:
                print(f"LinkedIn scraper error: {e}")
                break

        # Filter out masked/invalid jobs
        valid_jobs = self._filter_valid_jobs(jobs)
        return valid_jobs[:max_results]

    def _parse_results(self, html: str) -> list[Job]:
        """Parse job listings from LinkedIn HTML."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # LinkedIn job cards are in a list
        job_cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))

        if not job_cards:
            # Try alternative selector for the jobs list
            jobs_list = soup.find("ul", class_=re.compile(r"jobs-search__results-list"))
            if jobs_list:
                job_cards = jobs_list.find_all("li")

        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception:
                continue

        return jobs

    def _parse_job_card(self, card) -> Optional[Job]:
        """Parse a single job card."""
        # Title
        title_elem = card.find("h3", class_=re.compile(r"base-search-card__title|job-title")) or \
                    card.find("a", class_=re.compile(r"job-card-list__title"))

        if not title_elem:
            title_elem = card.find("span", class_=re.compile(r"sr-only"))

        if not title_elem:
            return None

        title = self._clean_text(title_elem.get_text())

        # URL
        link = card.find("a", class_=re.compile(r"base-card__full-link|job-card-container__link"))
        if not link:
            link = card.find("a", href=True)

        if link:
            url = link.get("href", "")
            if url.startswith("/"):
                url = f"https://www.linkedin.com{url}"
        else:
            url = ""

        # Extract job ID from URL
        job_id_match = re.search(r"jobs/view/(\d+)", url)
        if job_id_match:
            source_id = job_id_match.group(1)
        else:
            source_id = self._generate_source_id(title, url)

        # Company
        company_elem = card.find("h4", class_=re.compile(r"base-search-card__subtitle")) or \
                      card.find("a", class_=re.compile(r"job-card-container__company-name"))
        company = self._clean_text(company_elem.get_text()) if company_elem else "Unknown"

        # Location
        location_elem = card.find("span", class_=re.compile(r"job-search-card__location|job-card-container__metadata-item"))
        location = self._clean_text(location_elem.get_text()) if location_elem else ""

        # Posted date
        date_elem = card.find("time", class_=re.compile(r"job-search-card__listdate"))
        posted_date = None
        if date_elem:
            datetime_attr = date_elem.get("datetime")
            if datetime_attr:
                try:
                    posted_date = datetime.fromisoformat(datetime_attr.replace("Z", "+00:00")).date()
                except ValueError:
                    posted_date = self._parse_relative_date(date_elem.get_text())
            else:
                posted_date = self._parse_relative_date(date_elem.get_text())

        # Job type and salary (usually not in the card, would need to fetch detail page)
        job_type = None
        salary_text = None

        # Check for metadata items
        metadata = card.find_all("span", class_=re.compile(r"job-card-container__metadata-item"))
        for meta in metadata:
            text = meta.get_text().lower()
            if any(t in text for t in ["full-time", "part-time", "internship", "contract"]):
                if "full-time" in text:
                    job_type = "Full-time"
                elif "part-time" in text:
                    job_type = "Part-time"
                elif "internship" in text:
                    job_type = "Internship"
                elif "contract" in text:
                    job_type = "Contract"
            elif "$" in text or "hour" in text or "year" in text:
                salary_text = self._clean_text(meta.get_text())

        # Parse salary if present
        salary_min, salary_max, salary_type = self._parse_salary(salary_text)

        return Job(
            source=self.source_name,
            source_id=source_id,
            title=title,
            company=company,
            location=location,
            description="",  # Would need to fetch detail page for full description
            salary_text=salary_text,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_type=salary_type,
            job_type=job_type,
            url=url,
            posted_date=posted_date
        )

    def _parse_salary(self, salary_text: Optional[str]) -> tuple[Optional[float], Optional[float], Optional[str]]:
        """Parse salary string into min, max, and type."""
        if not salary_text:
            return None, None, None

        salary_text = salary_text.lower().replace(",", "").replace("$", "")

        # Determine salary type
        salary_type = "yearly"
        if "hour" in salary_text or "/hr" in salary_text:
            salary_type = "hourly"
        elif "week" in salary_text:
            salary_type = "weekly"
        elif "month" in salary_text:
            salary_type = "monthly"

        # Extract numbers
        numbers = re.findall(r"[\d.]+[km]?", salary_text)
        parsed_numbers = []
        for n in numbers:
            try:
                if n.endswith("k"):
                    parsed_numbers.append(float(n[:-1]) * 1000)
                elif n.endswith("m"):
                    parsed_numbers.append(float(n[:-1]) * 1000000)
                else:
                    val = float(n)
                    if val > 0:
                        parsed_numbers.append(val)
            except ValueError:
                continue

        if len(parsed_numbers) >= 2:
            return min(parsed_numbers), max(parsed_numbers), salary_type
        elif len(parsed_numbers) == 1:
            return parsed_numbers[0], parsed_numbers[0], salary_type

        return None, None, None

    def _parse_relative_date(self, date_text: Optional[str]) -> Optional:
        """Parse relative date strings like '2 days ago'."""
        if not date_text:
            return None

        date_text = date_text.lower().strip()
        today = datetime.now().date()

        if "just" in date_text or "now" in date_text or "today" in date_text:
            return today

        # Match patterns like "2 days ago", "1 week ago", etc.
        match = re.search(r"(\d+)\s*(day|week|month|hour|minute)s?\s*ago", date_text)
        if match:
            num = int(match.group(1))
            unit = match.group(2)

            if unit == "day":
                return today - timedelta(days=num)
            elif unit == "week":
                return today - timedelta(weeks=num)
            elif unit == "month":
                return today - timedelta(days=num * 30)
            elif unit in ("hour", "minute"):
                return today

        return None
