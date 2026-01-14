"""WayUp job scraper - Jobs and internships for students and recent grads."""
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import re
import json

from .base import BaseScraper
from data.models import Job


class WayUpScraper(BaseScraper):
    """Scraper for WayUp - student and early career job platform."""

    def __init__(self):
        super().__init__()
        self.source_name = "wayup"
        self.base_url = "https://www.wayup.com/s/jobs-internships"
        self.delay = 2.5

    def search(
        self,
        query: str,
        location: str,
        radius: int = 10,
        job_types: Optional[list[str]] = None,
        max_results: int = 50
    ) -> list[Job]:
        """Search WayUp for student jobs and internships."""
        jobs = []

        # Build search parameters
        params = {
            "keywords": query or "student",
            "location": location,
        }

        # Add job type filter
        if job_types:
            if "Internship" in job_types:
                params["job_type"] = "internship"
            elif "Part-time" in job_types:
                params["job_type"] = "part-time"
            elif "Full-time" in job_types:
                params["job_type"] = "full-time"

        try:
            html = self._fetch(self.base_url, params)
            if html:
                jobs = self._parse_results(html)

                # Also try to parse JSON data if embedded
                json_jobs = self._parse_json_data(html)
                if json_jobs:
                    jobs.extend(json_jobs)

        except Exception as e:
            print(f"WayUp scraper error: {e}")

        # Filter by job type if specified
        if job_types and jobs:
            jobs = [j for j in jobs if not j.job_type or j.job_type in job_types]

        # Filter out masked/invalid jobs
        valid_jobs = self._filter_valid_jobs(jobs)
        return valid_jobs[:max_results]

    def _parse_results(self, html: str) -> list[Job]:
        """Parse job listings from WayUp HTML."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # WayUp uses various class patterns
        job_cards = soup.find_all("div", class_=re.compile(r"job-card|JobCard|listing"))

        if not job_cards:
            job_cards = soup.find_all("article", class_=re.compile(r"job|listing"))

        if not job_cards:
            # Try finding by link patterns
            job_links = soup.find_all("a", href=re.compile(r"/job/|/jobs/"))
            for link in job_links:
                parent = link.find_parent(["div", "article", "li"])
                if parent and parent not in job_cards:
                    job_cards.append(parent)

        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception:
                continue

        return jobs

    def _parse_json_data(self, html: str) -> list[Job]:
        """Parse JSON-LD or embedded JSON data."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Look for JSON-LD
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    job = self._parse_json_job(data)
                    if job:
                        jobs.append(job)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            job = self._parse_json_job(item)
                            if job:
                                jobs.append(job)
            except (json.JSONDecodeError, TypeError):
                continue

        # Look for embedded React/Next.js data
        scripts = soup.find_all("script", id=re.compile(r"__NEXT_DATA__|__NUXT__"))
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Navigate to job listings in the data structure
                jobs_data = self._find_jobs_in_json(data)
                for job_data in jobs_data:
                    job = self._parse_embedded_job(job_data)
                    if job:
                        jobs.append(job)
            except (json.JSONDecodeError, TypeError):
                continue

        return jobs

    def _find_jobs_in_json(self, data, depth=0) -> list:
        """Recursively find job listings in JSON data."""
        if depth > 5:  # Limit recursion
            return []

        jobs = []

        if isinstance(data, dict):
            # Check if this looks like a job
            if "title" in data and ("company" in data or "employer" in data):
                jobs.append(data)

            # Check common keys for job lists
            for key in ["jobs", "listings", "results", "items", "data"]:
                if key in data:
                    jobs.extend(self._find_jobs_in_json(data[key], depth + 1))

            # Recurse into pageProps, props, etc.
            for key in ["pageProps", "props", "state"]:
                if key in data:
                    jobs.extend(self._find_jobs_in_json(data[key], depth + 1))

        elif isinstance(data, list):
            for item in data:
                jobs.extend(self._find_jobs_in_json(item, depth + 1))

        return jobs

    def _parse_json_job(self, data: dict) -> Optional[Job]:
        """Parse a job from JSON-LD format."""
        title = data.get("title", "")
        if not title:
            return None

        company = ""
        hiring_org = data.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            company = hiring_org.get("name", "")

        location = ""
        job_loc = data.get("jobLocation", {})
        if isinstance(job_loc, dict):
            addr = job_loc.get("address", {})
            if isinstance(addr, dict):
                location = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}".strip(", ")

        url = data.get("url", "")
        description = data.get("description", "")
        if description:
            description = BeautifulSoup(description, "lxml").get_text()[:500]

        source_id = self._generate_source_id(title, company, url)

        return Job(
            source=self.source_name,
            source_id=source_id,
            title=title,
            company=company or "Unknown",
            location=location,
            description=self._clean_text(description),
            url=url
        )

    def _parse_embedded_job(self, data: dict) -> Optional[Job]:
        """Parse job from embedded JSON data."""
        title = data.get("title") or data.get("name") or ""
        if not title:
            return None

        company = data.get("company") or data.get("employer") or data.get("company_name") or "Unknown"
        if isinstance(company, dict):
            company = company.get("name", "Unknown")

        location = data.get("location") or data.get("city") or ""
        if isinstance(location, dict):
            location = f"{location.get('city', '')}, {location.get('state', '')}".strip(", ")

        url = data.get("url") or data.get("apply_url") or ""
        if url and not url.startswith("http"):
            url = f"https://www.wayup.com{url}"

        description = data.get("description") or data.get("summary") or ""

        job_type = None
        jt = data.get("job_type") or data.get("employment_type") or ""
        if isinstance(jt, str):
            jt_lower = jt.lower()
            if "intern" in jt_lower:
                job_type = "Internship"
            elif "part" in jt_lower:
                job_type = "Part-time"
            elif "full" in jt_lower:
                job_type = "Full-time"

        source_id = data.get("id") or self._generate_source_id(title, company, url)

        return Job(
            source=self.source_name,
            source_id=str(source_id),
            title=title,
            company=company if isinstance(company, str) else "Unknown",
            location=location,
            description=self._clean_text(description)[:500] if description else "",
            job_type=job_type,
            url=url
        )

    def _parse_job_card(self, card) -> Optional[Job]:
        """Parse a single job card from HTML."""
        # Title
        title_elem = card.find(["h2", "h3", "h4", "a"], class_=re.compile(r"title|name"))
        if not title_elem:
            title_elem = card.find("a", href=re.compile(r"/job"))

        if not title_elem:
            return None

        title = self._clean_text(title_elem.get_text())
        if not title or len(title) < 3:
            return None

        # URL
        link = title_elem if title_elem.name == "a" else card.find("a", href=True)
        url = ""
        if link and link.get("href"):
            href = link.get("href")
            if href.startswith("/"):
                url = f"https://www.wayup.com{href}"
            elif href.startswith("http"):
                url = href

        source_id = self._generate_source_id(title, url)

        # Company
        company_elem = card.find(["span", "div", "a"], class_=re.compile(r"company|employer"))
        company = self._clean_text(company_elem.get_text()) if company_elem else "Unknown"

        # Location
        location_elem = card.find(["span", "div"], class_=re.compile(r"location|city"))
        location = self._clean_text(location_elem.get_text()) if location_elem else ""

        # Job type
        job_type = None
        type_elem = card.find(["span", "div"], class_=re.compile(r"type|category"))
        if type_elem:
            text = type_elem.get_text().lower()
            if "intern" in text:
                job_type = "Internship"
            elif "part-time" in text or "part time" in text:
                job_type = "Part-time"
            elif "full-time" in text or "full time" in text:
                job_type = "Full-time"

        return Job(
            source=self.source_name,
            source_id=source_id,
            title=title,
            company=company,
            location=location,
            job_type=job_type,
            url=url
        )
