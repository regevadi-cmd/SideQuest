"""Indeed job scraper."""
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import re

from .base import BaseScraper
from data.models import Job


class IndeedScraper(BaseScraper):
    """Scraper for Indeed job listings."""

    def __init__(self):
        super().__init__()
        self.source_name = "indeed"
        self.base_url = "https://www.indeed.com/jobs"

    def search(
        self,
        query: str,
        location: str,
        radius: int = 10,
        job_types: Optional[list[str]] = None,
        max_results: int = 50
    ) -> list[Job]:
        """Search Indeed for jobs."""
        jobs = []

        # Build job type filter
        jt_param = None
        if job_types:
            type_map = {
                "Full-time": "fulltime",
                "Part-time": "parttime",
                "Internship": "internship",
                "Contract": "contract",
                "Temporary": "temporary",
            }
            # Indeed only allows one job type at a time, prioritize
            for jt in job_types:
                if jt in type_map:
                    jt_param = type_map[jt]
                    break

        # Paginate through results
        start = 0
        page_size = 15  # Indeed shows ~15 per page

        while len(jobs) < max_results:
            params = {
                "q": query,
                "l": location,
                "radius": radius,
                "start": start,
                "sort": "date",  # Most recent first
            }

            if jt_param:
                params["jt"] = jt_param

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
                print(f"Indeed scraper error: {e}")
                break

        # Filter out masked/invalid jobs
        valid_jobs = self._filter_valid_jobs(jobs)
        return valid_jobs[:max_results]

    def _parse_results(self, html: str) -> list[Job]:
        """Parse job listings from Indeed HTML."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Indeed uses various class names, try common patterns
        job_cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|jobsearch-SerpJobCard|resultContent"))

        if not job_cards:
            # Try alternative selectors
            job_cards = soup.find_all("td", class_="resultContent")

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
        title_elem = card.find("h2", class_=re.compile(r"jobTitle")) or card.find("a", class_=re.compile(r"jobTitle"))
        if not title_elem:
            title_elem = card.find("span", {"id": re.compile(r"jobTitle")})

        if not title_elem:
            return None

        title = self._clean_text(title_elem.get_text())

        # URL
        link = card.find("a", href=True)
        if link:
            href = link.get("href", "")
            if href.startswith("/"):
                url = f"https://www.indeed.com{href}"
            else:
                url = href
        else:
            url = ""

        # Extract job ID from URL
        jk_match = re.search(r"jk=([a-f0-9]+)", url)
        source_id = jk_match.group(1) if jk_match else self._generate_source_id(title, url)

        # Company
        company_elem = card.find("span", {"data-testid": "company-name"}) or \
                      card.find("span", class_=re.compile(r"company"))
        company = self._clean_text(company_elem.get_text()) if company_elem else "Unknown"

        # Location
        location_elem = card.find("div", {"data-testid": "text-location"}) or \
                       card.find("div", class_=re.compile(r"location"))
        location = self._clean_text(location_elem.get_text()) if location_elem else ""

        # Salary
        salary_elem = card.find("div", {"data-testid": "attribute_snippet_testid"}) or \
                     card.find("span", class_=re.compile(r"salary|estimated"))
        salary_text = self._clean_text(salary_elem.get_text()) if salary_elem else None

        # Parse salary if present
        salary_min, salary_max, salary_type = self._parse_salary(salary_text)

        # Job type
        job_type = None
        metadata = card.find_all("div", class_=re.compile(r"metadata|attribute"))
        for meta in metadata:
            text = meta.get_text().lower()
            if "full-time" in text:
                job_type = "Full-time"
            elif "part-time" in text:
                job_type = "Part-time"
            elif "internship" in text:
                job_type = "Internship"
            elif "contract" in text:
                job_type = "Contract"

        # Description snippet
        desc_elem = card.find("div", class_=re.compile(r"job-snippet"))
        description = self._clean_text(desc_elem.get_text()) if desc_elem else ""

        # Posted date
        date_elem = card.find("span", class_=re.compile(r"date"))
        posted_date = self._parse_posted_date(date_elem.get_text() if date_elem else None)

        return Job(
            source=self.source_name,
            source_id=source_id,
            title=title,
            company=company,
            location=location,
            description=description,
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
        salary_type = "yearly"  # default
        if "hour" in salary_text or "/hr" in salary_text:
            salary_type = "hourly"
        elif "week" in salary_text:
            salary_type = "weekly"
        elif "month" in salary_text:
            salary_type = "monthly"

        # Extract numbers
        numbers = re.findall(r"[\d.]+", salary_text)
        numbers = [float(n) for n in numbers if float(n) > 0]

        if len(numbers) >= 2:
            return min(numbers), max(numbers), salary_type
        elif len(numbers) == 1:
            return numbers[0], numbers[0], salary_type

        return None, None, None

    def _parse_posted_date(self, date_text: Optional[str]) -> Optional:
        """Parse 'Posted X days ago' style dates."""
        if not date_text:
            return None

        date_text = date_text.lower()
        today = datetime.now().date()

        if "just posted" in date_text or "today" in date_text:
            return today

        days_match = re.search(r"(\d+)\s*day", date_text)
        if days_match:
            days = int(days_match.group(1))
            return today - timedelta(days=days)

        return None
