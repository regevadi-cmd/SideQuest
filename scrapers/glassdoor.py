"""Glassdoor job scraper."""
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import re
import json

from .base import BaseScraper
from data.models import Job


class GlassdoorScraper(BaseScraper):
    """Scraper for Glassdoor job listings."""

    def __init__(self):
        super().__init__()
        self.source_name = "glassdoor"
        self.base_url = "https://www.glassdoor.com/Job/jobs.htm"
        # Glassdoor has strong anti-scraping, use longer delays
        self.delay = 4.0

        # Update headers to look more like a real browser
        self.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        })

    def search(
        self,
        query: str,
        location: str,
        radius: int = 10,
        job_types: Optional[list[str]] = None,
        max_results: int = 50
    ) -> list[Job]:
        """Search Glassdoor for jobs."""
        jobs = []

        # Build the search URL
        # Glassdoor uses a different URL structure
        location_slug = self._slugify_location(location)

        # Job type codes for Glassdoor
        job_type_param = ""
        if job_types:
            type_codes = []
            type_map = {
                "Full-time": "fulltime",
                "Part-time": "parttime",
                "Internship": "internship",
                "Contract": "contract",
                "Temporary": "temporary",
            }
            for jt in job_types:
                if jt in type_map:
                    type_codes.append(type_map[jt])
            if type_codes:
                job_type_param = ",".join(type_codes)

        # Paginate through results
        page = 1
        page_size = 30  # Glassdoor shows ~30 per page

        while len(jobs) < max_results:
            params = {
                "sc.keyword": query,
                "locT": "C",  # City
                "locKeyword": location,
                "radius": radius,
                "fromAge": "7",  # Last 7 days
            }

            if job_type_param:
                params["jobType"] = job_type_param

            if page > 1:
                params["p"] = page

            try:
                html = self._fetch(self.base_url, params)
                if not html:
                    break

                page_jobs = self._parse_results(html)
                if not page_jobs:
                    # Try parsing JSON-LD data as fallback
                    page_jobs = self._parse_json_ld(html)

                if not page_jobs:
                    break

                jobs.extend(page_jobs)
                page += 1

                # Stop if we've reached the last page
                if len(page_jobs) < page_size:
                    break

            except Exception as e:
                print(f"Glassdoor scraper error: {e}")
                break

        # Filter out masked/invalid jobs
        valid_jobs = self._filter_valid_jobs(jobs)
        return valid_jobs[:max_results]

    def _slugify_location(self, location: str) -> str:
        """Convert location to URL-friendly slug."""
        # Remove special characters and convert to lowercase
        slug = re.sub(r"[^a-zA-Z0-9\s-]", "", location)
        slug = re.sub(r"\s+", "-", slug.strip())
        return slug.lower()

    def _parse_results(self, html: str) -> list[Job]:
        """Parse job listings from Glassdoor HTML."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Glassdoor job listings are typically in a list structure
        job_cards = soup.find_all("li", class_=re.compile(r"JobsList_jobListItem|react-job-listing"))

        if not job_cards:
            # Try alternative selectors
            job_cards = soup.find_all("div", {"data-test": "jobListing"})

        if not job_cards:
            # Try finding by data attributes
            job_cards = soup.find_all(attrs={"data-id": True, "data-normalize-job-title": True})

        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception:
                continue

        return jobs

    def _parse_json_ld(self, html: str) -> list[Job]:
        """Parse JSON-LD structured data from the page."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Look for JSON-LD script tags
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                data = json.loads(script.string)

                # Handle JobPosting schema
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    job = self._parse_json_ld_job(data)
                    if job:
                        jobs.append(job)

                # Handle array of job postings
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            job = self._parse_json_ld_job(item)
                            if job:
                                jobs.append(job)

                # Handle ItemList containing job postings
                elif isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        if isinstance(item, dict):
                            job_data = item.get("item", item)
                            if job_data.get("@type") == "JobPosting":
                                job = self._parse_json_ld_job(job_data)
                                if job:
                                    jobs.append(job)

            except (json.JSONDecodeError, TypeError):
                continue

        return jobs

    def _parse_json_ld_job(self, data: dict) -> Optional[Job]:
        """Parse a single job from JSON-LD data."""
        title = data.get("title", "")
        if not title:
            return None

        # Extract company
        company = ""
        hiring_org = data.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            company = hiring_org.get("name", "")
        elif isinstance(hiring_org, str):
            company = hiring_org

        # Extract location
        location = ""
        job_location = data.get("jobLocation", {})
        if isinstance(job_location, dict):
            address = job_location.get("address", {})
            if isinstance(address, dict):
                parts = [
                    address.get("addressLocality", ""),
                    address.get("addressRegion", ""),
                ]
                location = ", ".join(p for p in parts if p)
        elif isinstance(job_location, list) and job_location:
            first_loc = job_location[0]
            if isinstance(first_loc, dict):
                address = first_loc.get("address", {})
                if isinstance(address, dict):
                    parts = [
                        address.get("addressLocality", ""),
                        address.get("addressRegion", ""),
                    ]
                    location = ", ".join(p for p in parts if p)

        # Extract URL
        url = data.get("url", "")

        # Extract description
        description = data.get("description", "")
        # Clean HTML from description
        if description:
            description = BeautifulSoup(description, "lxml").get_text(separator=" ")
            description = self._clean_text(description)

        # Extract salary
        salary_text = None
        salary_min = None
        salary_max = None
        salary_type = None

        base_salary = data.get("baseSalary", {})
        if isinstance(base_salary, dict):
            value = base_salary.get("value", {})
            if isinstance(value, dict):
                salary_min = value.get("minValue")
                salary_max = value.get("maxValue")
                unit = base_salary.get("unitText", "YEAR")
                salary_type = "yearly" if "YEAR" in unit.upper() else "hourly"
                if salary_min and salary_max:
                    salary_text = f"${salary_min:,.0f} - ${salary_max:,.0f} per {salary_type.replace('ly', '')}"
                elif salary_min:
                    salary_text = f"${salary_min:,.0f} per {salary_type.replace('ly', '')}"

        # Extract employment type
        job_type = None
        employment_type = data.get("employmentType", "")
        if employment_type:
            if isinstance(employment_type, list):
                employment_type = employment_type[0] if employment_type else ""
            employment_type = employment_type.upper()
            if "FULL" in employment_type:
                job_type = "Full-time"
            elif "PART" in employment_type:
                job_type = "Part-time"
            elif "INTERN" in employment_type:
                job_type = "Internship"
            elif "CONTRACT" in employment_type:
                job_type = "Contract"

        # Extract posted date
        posted_date = None
        date_posted = data.get("datePosted", "")
        if date_posted:
            try:
                posted_date = datetime.fromisoformat(date_posted.replace("Z", "+00:00")).date()
            except ValueError:
                pass

        # Generate source ID
        source_id = data.get("identifier", {}).get("value", "")
        if not source_id:
            source_id = self._generate_source_id(title, company, url)

        return Job(
            source=self.source_name,
            source_id=str(source_id),
            title=title,
            company=company,
            location=location,
            description=description[:2000] if description else "",
            salary_text=salary_text,
            salary_min=float(salary_min) if salary_min else None,
            salary_max=float(salary_max) if salary_max else None,
            salary_type=salary_type,
            job_type=job_type,
            url=url,
            posted_date=posted_date
        )

    def _parse_job_card(self, card) -> Optional[Job]:
        """Parse a single job card from HTML."""
        # Title
        title_elem = card.find("a", class_=re.compile(r"jobTitle|JobCard_jobTitle")) or \
                    card.find("div", {"data-test": "job-title"})

        if not title_elem:
            title_elem = card.find(attrs={"data-normalize-job-title": True})
            if title_elem:
                title = title_elem.get("data-normalize-job-title", "")
            else:
                return None
        else:
            title = self._clean_text(title_elem.get_text())

        if not title:
            return None

        # URL
        link = card.find("a", href=True)
        if link:
            url = link.get("href", "")
            if url.startswith("/"):
                url = f"https://www.glassdoor.com{url}"
        else:
            url = ""

        # Extract job ID
        job_id = card.get("data-id") or card.get("data-job-id")
        if not job_id:
            job_id_match = re.search(r"jobListingId=(\d+)", url)
            job_id = job_id_match.group(1) if job_id_match else self._generate_source_id(title, url)

        # Company
        company_elem = card.find("div", {"data-test": "employer-short-name"}) or \
                      card.find("span", class_=re.compile(r"EmployerProfile_employerName|JobCard_companyName"))
        company = self._clean_text(company_elem.get_text()) if company_elem else "Unknown"

        # Location
        location_elem = card.find("div", {"data-test": "emp-location"}) or \
                       card.find("span", class_=re.compile(r"JobCard_location"))
        location = self._clean_text(location_elem.get_text()) if location_elem else ""

        # Salary
        salary_elem = card.find("div", {"data-test": "detailSalary"}) or \
                     card.find("span", class_=re.compile(r"JobCard_salaryEstimate"))
        salary_text = self._clean_text(salary_elem.get_text()) if salary_elem else None

        salary_min, salary_max, salary_type = self._parse_salary(salary_text)

        # Posted date
        date_elem = card.find("div", {"data-test": "job-age"}) or \
                   card.find("span", class_=re.compile(r"JobCard_listingAge"))
        posted_date = self._parse_relative_date(date_elem.get_text() if date_elem else None)

        return Job(
            source=self.source_name,
            source_id=str(job_id),
            title=title,
            company=company,
            location=location,
            description="",
            salary_text=salary_text,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_type=salary_type,
            job_type=None,
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
        if "hour" in salary_text or "/hr" in salary_text or "per hour" in salary_text:
            salary_type = "hourly"
        elif "week" in salary_text:
            salary_type = "weekly"
        elif "month" in salary_text:
            salary_type = "monthly"

        # Extract numbers (handle K notation)
        numbers = re.findall(r"[\d.]+k?", salary_text)
        parsed_numbers = []
        for n in numbers:
            try:
                if n.endswith("k"):
                    parsed_numbers.append(float(n[:-1]) * 1000)
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
        """Parse relative date strings."""
        if not date_text:
            return None

        date_text = date_text.lower().strip()
        today = datetime.now().date()

        if "just" in date_text or "now" in date_text or "today" in date_text:
            return today

        match = re.search(r"(\d+)\s*(d|day|h|hour|w|week|m|month)", date_text)
        if match:
            num = int(match.group(1))
            unit = match.group(2)[0]  # First letter

            if unit == "d":
                return today - timedelta(days=num)
            elif unit == "h":
                return today
            elif unit == "w":
                return today - timedelta(weeks=num)
            elif unit == "m":
                return today - timedelta(days=num * 30)

        return None
