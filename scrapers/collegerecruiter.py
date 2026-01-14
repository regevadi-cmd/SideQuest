"""College Recruiter job scraper - Entry-level jobs for students and recent grads."""
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import re
import json

from .base import BaseScraper
from data.models import Job


class CollegeRecruiterScraper(BaseScraper):
    """Scraper for College Recruiter - focuses on entry-level and student jobs."""

    def __init__(self):
        super().__init__()
        self.source_name = "collegerecruiter"
        self.base_url = "https://www.collegerecruiter.com/job-search"
        self.delay = 2.5

    def search(
        self,
        query: str,
        location: str,
        radius: int = 10,
        job_types: Optional[list[str]] = None,
        max_results: int = 50
    ) -> list[Job]:
        """Search College Recruiter for entry-level jobs."""
        jobs = []

        # Build search parameters
        params = {
            "keyword": query or "student",
            "location": location or "US",
        }

        # Paginate through results
        page = 1
        page_size = 25

        while len(jobs) < max_results:
            try:
                if page > 1:
                    params["page"] = page

                html = self._fetch(self.base_url, params)

                if not html:
                    break

                page_jobs = self._parse_results(html)
                if not page_jobs:
                    break

                # Filter by job type if specified
                if job_types:
                    page_jobs = [j for j in page_jobs if not j.job_type or j.job_type in job_types]

                jobs.extend(page_jobs)
                page += 1

                if len(page_jobs) < page_size:
                    break

            except Exception as e:
                print(f"College Recruiter scraper error: {e}")
                break

        # Filter out masked/invalid jobs
        valid_jobs = self._filter_valid_jobs(jobs)
        return valid_jobs[:max_results]

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s-]", "", text)
        text = re.sub(r"\s+", "-", text)
        return text

    def _parse_results(self, html: str) -> list[Job]:
        """Parse job listings from College Recruiter HTML."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # College Recruiter uses Next.js - try to extract JSON data first
        json_jobs = self._extract_nextjs_data(soup)
        if json_jobs:
            return json_jobs

        # Also try JSON-LD structured data
        json_ld_jobs = self._extract_json_ld(soup)
        if json_ld_jobs:
            jobs.extend(json_ld_jobs)

        # Fall back to HTML parsing
        job_cards = soup.find_all("div", class_=re.compile(r"job-listing|job-card|listing-item"))

        if not job_cards:
            job_cards = soup.find_all("article", class_=re.compile(r"job"))

        if not job_cards:
            job_cards = soup.find_all("li", class_=re.compile(r"job"))

        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception:
                continue

        return jobs

    def _extract_nextjs_data(self, soup) -> list[Job]:
        """Extract job data from Next.js __NEXT_DATA__ script."""
        jobs = []

        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return jobs

        try:
            data = json.loads(script.string)
            # Navigate through Next.js data structure to find jobs
            props = data.get("props", {})
            page_props = props.get("pageProps", {})

            # Look for job listings in various locations
            for key in ["jobs", "listings", "results", "data", "initialJobs"]:
                if key in page_props:
                    job_list = page_props[key]
                    if isinstance(job_list, list):
                        for job_data in job_list:
                            job = self._parse_json_job(job_data)
                            if job:
                                jobs.append(job)

            # Also check nested structures
            if "searchResults" in page_props:
                results = page_props["searchResults"]
                if isinstance(results, dict) and "jobs" in results:
                    for job_data in results["jobs"]:
                        job = self._parse_json_job(job_data)
                        if job:
                            jobs.append(job)

        except (json.JSONDecodeError, TypeError, KeyError):
            pass

        return jobs

    def _extract_json_ld(self, soup) -> list[Job]:
        """Extract jobs from JSON-LD structured data."""
        jobs = []

        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)

                # Handle JobPosting type
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    job = self._parse_json_ld_job(data)
                    if job:
                        jobs.append(job)

                # Handle ItemList containing jobs
                elif isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        if isinstance(item, dict):
                            job_data = item.get("item", item)
                            if job_data.get("@type") == "JobPosting":
                                job = self._parse_json_ld_job(job_data)
                                if job:
                                    jobs.append(job)

                # Handle array of jobs
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            job = self._parse_json_ld_job(item)
                            if job:
                                jobs.append(job)

            except (json.JSONDecodeError, TypeError):
                continue

        return jobs

    def _parse_json_job(self, data: dict) -> Optional[Job]:
        """Parse job from JSON data structure."""
        title = data.get("title") or data.get("jobTitle") or data.get("name") or ""
        if not title:
            return None

        company = data.get("company") or data.get("employer") or data.get("companyName") or "Unknown"
        if isinstance(company, dict):
            company = company.get("name", "Unknown")

        location = data.get("location") or data.get("city") or ""
        if isinstance(location, dict):
            city = location.get("city", "")
            state = location.get("state", location.get("region", ""))
            location = f"{city}, {state}".strip(", ")

        url = data.get("url") or data.get("applyUrl") or data.get("jobUrl") or ""
        if url and not url.startswith("http"):
            url = f"https://www.collegerecruiter.com{url}"

        description = data.get("description") or data.get("summary") or ""
        if description and len(description) > 500:
            description = description[:500] + "..."

        job_type = None
        emp_type = data.get("employmentType") or data.get("jobType") or ""
        if isinstance(emp_type, str):
            emp_lower = emp_type.lower()
            if "full" in emp_lower:
                job_type = "Full-time"
            elif "part" in emp_lower:
                job_type = "Part-time"
            elif "intern" in emp_lower:
                job_type = "Internship"
            elif "contract" in emp_lower:
                job_type = "Contract"

        source_id = str(data.get("id") or data.get("jobId") or self._generate_source_id(title, company, url))

        return Job(
            source=self.source_name,
            source_id=source_id,
            title=title,
            company=company if isinstance(company, str) else "Unknown",
            location=location,
            description=self._clean_text(description),
            job_type=job_type,
            url=url
        )

    def _parse_json_ld_job(self, data: dict) -> Optional[Job]:
        """Parse job from JSON-LD JobPosting format."""
        title = data.get("title", "")
        if not title:
            return None

        company = ""
        hiring_org = data.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            company = hiring_org.get("name", "Unknown")
        elif isinstance(hiring_org, str):
            company = hiring_org

        location = ""
        job_loc = data.get("jobLocation", {})
        if isinstance(job_loc, dict):
            addr = job_loc.get("address", {})
            if isinstance(addr, dict):
                city = addr.get("addressLocality", "")
                state = addr.get("addressRegion", "")
                location = f"{city}, {state}".strip(", ")
        elif isinstance(job_loc, list) and job_loc:
            first = job_loc[0]
            if isinstance(first, dict):
                addr = first.get("address", {})
                if isinstance(addr, dict):
                    location = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}".strip(", ")

        url = data.get("url", "")
        description = data.get("description", "")
        if description:
            description = BeautifulSoup(description, "lxml").get_text()[:500]

        job_type = None
        emp_type = data.get("employmentType", "")
        if emp_type:
            if isinstance(emp_type, list):
                emp_type = emp_type[0]
            emp_lower = emp_type.lower() if isinstance(emp_type, str) else ""
            if "full" in emp_lower:
                job_type = "Full-time"
            elif "part" in emp_lower:
                job_type = "Part-time"
            elif "intern" in emp_lower:
                job_type = "Internship"

        source_id = self._generate_source_id(title, company, url)

        return Job(
            source=self.source_name,
            source_id=source_id,
            title=title,
            company=company or "Unknown",
            location=location,
            description=self._clean_text(description),
            job_type=job_type,
            url=url
        )

    def _parse_job_card(self, card) -> Optional[Job]:
        """Parse a single job card."""
        # Title
        title_elem = card.find(["h2", "h3", "h4", "a"], class_=re.compile(r"title|job-title"))
        if not title_elem:
            title_elem = card.find("a", href=re.compile(r"/job/"))

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
                url = f"https://www.collegerecruiter.com{href}"
            elif href.startswith("http"):
                url = href

        # Generate source ID
        job_id_match = re.search(r"/job/(\d+)", url)
        source_id = job_id_match.group(1) if job_id_match else self._generate_source_id(title, url)

        # Company
        company_elem = card.find(["span", "div", "a"], class_=re.compile(r"company|employer"))
        company = self._clean_text(company_elem.get_text()) if company_elem else "Unknown"

        # Location
        location_elem = card.find(["span", "div"], class_=re.compile(r"location|city"))
        location = self._clean_text(location_elem.get_text()) if location_elem else ""

        # Job type
        job_type = self._extract_job_type(card)

        # Description
        desc_elem = card.find(["p", "div"], class_=re.compile(r"description|summary|snippet"))
        description = self._clean_text(desc_elem.get_text()) if desc_elem else ""

        # Posted date
        date_elem = card.find(["span", "time", "div"], class_=re.compile(r"date|posted|time"))
        posted_date = self._parse_posted_date(date_elem.get_text() if date_elem else None)

        return Job(
            source=self.source_name,
            source_id=source_id,
            title=title,
            company=company,
            location=location,
            description=description,
            job_type=job_type,
            url=url,
            posted_date=posted_date
        )

    def _extract_job_type(self, card) -> Optional[str]:
        """Extract job type from card."""
        type_elem = card.find(["span", "div"], class_=re.compile(r"type|category|employment"))
        if type_elem:
            text = type_elem.get_text().lower()
            if "full-time" in text or "full time" in text:
                return "Full-time"
            elif "part-time" in text or "part time" in text:
                return "Part-time"
            elif "internship" in text:
                return "Internship"
            elif "contract" in text:
                return "Contract"

        # Check card text for job type keywords
        card_text = card.get_text().lower()
        if "internship" in card_text:
            return "Internship"
        elif "part-time" in card_text or "part time" in card_text:
            return "Part-time"

        return None

    def _parse_posted_date(self, date_text: Optional[str]) -> Optional:
        """Parse date text into a date object."""
        if not date_text:
            return None

        date_text = date_text.lower().strip()
        today = datetime.now().date()

        if "today" in date_text or "just" in date_text or "now" in date_text:
            return today

        if "yesterday" in date_text:
            return today - timedelta(days=1)

        # Match "X days/weeks/hours ago"
        match = re.search(r"(\d+)\s*(day|week|hour|minute|month)s?\s*ago", date_text)
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
