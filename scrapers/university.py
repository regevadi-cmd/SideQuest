"""University Job Board scraper - Generic scraper for university career center job boards."""
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import re
import json

from .base import BaseScraper
from data.models import Job


class UniversityJobBoardScraper(BaseScraper):
    """Generic scraper for university job boards.

    Supports various university job board formats including:
    - Static HTML job listings
    - RSS/Atom feeds
    - JSON-LD structured data
    - Common job board plugins (Simplicity, etc.)
    """

    def __init__(self, university_name: str = "University", job_board_url: str = ""):
        super().__init__()
        self.source_name = "university"
        self.university_name = university_name
        self.job_board_url = job_board_url
        self.delay = 2.0

    def search(
        self,
        query: str,
        location: str,
        radius: int = 10,
        job_types: Optional[list[str]] = None,
        max_results: int = 50
    ) -> list[Job]:
        """Search university job board for jobs."""
        if not self.job_board_url:
            return []

        jobs = []

        try:
            # Check if it's an RSS feed
            if self._is_rss_url(self.job_board_url):
                jobs = self._parse_rss_feed(self.job_board_url)
            else:
                # Fetch HTML page
                html = self._fetch(self.job_board_url)
                if html:
                    # Try multiple parsing strategies
                    jobs = self._parse_page(html, query)

        except Exception as e:
            print(f"University job board scraper error: {e}")

        # Filter by query if provided (but keep redirect/portal jobs)
        if query and jobs:
            query_lower = query.lower()
            jobs = [j for j in jobs if
                    "Access " in j.title or  # Keep redirect jobs
                    query_lower in j.title.lower() or
                    query_lower in (j.description or "").lower()]

        # Filter by job type if specified
        if job_types and jobs:
            jobs = [j for j in jobs if not j.job_type or j.job_type in job_types]

        # Filter out masked/invalid jobs, but keep redirect/portal jobs
        valid_jobs = []
        for job in jobs:
            # Keep portal redirect jobs (they link to external systems like Handshake)
            if "portal" in job.source_id or "Access " in job.title:
                valid_jobs.append(job)
            elif self._is_valid_job(job):
                valid_jobs.append(job)

        return valid_jobs[:max_results]

    def _is_rss_url(self, url: str) -> bool:
        """Check if URL is likely an RSS feed."""
        rss_indicators = ['.rss', '.xml', '/feed', '/rss', 'format=rss', 'format=atom']
        return any(ind in url.lower() for ind in rss_indicators)

    def _parse_page(self, html: str, query: str = "") -> list[Job]:
        """Parse jobs from HTML page using multiple strategies."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # FIRST: Check for external job systems (Handshake, etc.)
        # Do this early because these pages typically don't have direct job listings
        iframe_info = self._detect_iframe_system(soup)
        if iframe_info:
            system_name = iframe_info['system']
            requires_auth = iframe_info.get('requires_auth', True)

            if requires_auth:
                description = (
                    f"This university uses {system_name} for job postings, which requires university login. "
                    f"To search {system_name} jobs:\n"
                    f"1. Log into {iframe_info['url']} with your university credentials\n"
                    f"2. In Settings, enable authentication and paste your session cookie\n"
                    f"3. Or visit the link directly to browse jobs"
                )
            else:
                description = f"This university uses {system_name} for job postings. Click to access the job portal directly."

            # Return early with the redirect info - don't try other strategies
            return [Job(
                source=self.source_name,
                source_id=self._generate_source_id(self.university_name, "portal"),
                title=f"Access {self.university_name} jobs on {system_name}",
                company=self.university_name,
                location="",
                description=description,
                url=iframe_info['url'],
                job_type=None
            )]

        # Strategy 1: JSON-LD structured data
        json_ld_jobs = self._extract_json_ld(soup)
        if json_ld_jobs:
            jobs.extend(json_ld_jobs)

        # Strategy 2: Common job listing patterns
        html_jobs = self._extract_from_html(soup)
        if html_jobs:
            jobs.extend(html_jobs)

        # Strategy 3: Table-based listings (common in university sites)
        table_jobs = self._extract_from_tables(soup)
        if table_jobs:
            jobs.extend(table_jobs)

        # Deduplicate by title
        seen = set()
        unique_jobs = []
        for job in jobs:
            key = job.title.lower()
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs

    def _extract_json_ld(self, soup) -> list[Job]:
        """Extract jobs from JSON-LD structured data."""
        jobs = []
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)

                if isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        job = self._parse_json_ld_job(data)
                        if job:
                            jobs.append(job)
                    elif data.get("@type") == "ItemList":
                        for item in data.get("itemListElement", []):
                            if isinstance(item, dict):
                                job_data = item.get("item", item)
                                if job_data.get("@type") == "JobPosting":
                                    job = self._parse_json_ld_job(job_data)
                                    if job:
                                        jobs.append(job)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            job = self._parse_json_ld_job(item)
                            if job:
                                jobs.append(job)
            except (json.JSONDecodeError, TypeError):
                continue

        return jobs

    def _parse_json_ld_job(self, data: dict) -> Optional[Job]:
        """Parse a job from JSON-LD format."""
        title = data.get("title", "")
        if not title:
            return None

        company = self.university_name
        hiring_org = data.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            company = hiring_org.get("name", self.university_name)

        location = ""
        job_loc = data.get("jobLocation", {})
        if isinstance(job_loc, dict):
            addr = job_loc.get("address", {})
            if isinstance(addr, dict):
                location = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}".strip(", ")

        url = data.get("url", self.job_board_url)
        description = data.get("description", "")
        if description:
            description = BeautifulSoup(description, "lxml").get_text()[:500]

        job_type = self._extract_employment_type(data.get("employmentType"))

        return Job(
            source=self.source_name,
            source_id=self._generate_source_id(title, company),
            title=title,
            company=company,
            location=location,
            description=self._clean_text(description),
            job_type=job_type,
            url=url
        )

    def _extract_from_html(self, soup) -> list[Job]:
        """Extract jobs from common HTML patterns."""
        jobs = []

        # Common job listing patterns
        selectors = [
            ("div", r"job|posting|listing|position|opportunity"),
            ("article", r"job|posting|listing"),
            ("li", r"job|posting|listing|position"),
            ("tr", r"job|posting|listing"),
        ]

        for tag, pattern in selectors:
            elements = soup.find_all(tag, class_=re.compile(pattern, re.I))
            for elem in elements:
                job = self._parse_html_job(elem)
                if job:
                    jobs.append(job)
            if jobs:
                break  # Stop if we found jobs

        return jobs

    def _parse_html_job(self, elem) -> Optional[Job]:
        """Parse a job from an HTML element."""
        # Find title
        title_elem = elem.find(["h1", "h2", "h3", "h4", "a"], class_=re.compile(r"title|name|position", re.I))
        if not title_elem:
            title_elem = elem.find(["h1", "h2", "h3", "h4"])
        if not title_elem:
            title_elem = elem.find("a", href=True)

        if not title_elem:
            return None

        title = self._clean_text(title_elem.get_text())
        if not title or len(title) < 3:
            return None

        # Find URL
        link = title_elem if title_elem.name == "a" else elem.find("a", href=True)
        url = ""
        if link and link.get("href"):
            href = link.get("href")
            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                # Try to construct full URL
                from urllib.parse import urlparse
                parsed = urlparse(self.job_board_url)
                url = f"{parsed.scheme}://{parsed.netloc}{href}"

        # Find company/department
        company_elem = elem.find(["span", "div", "td"], class_=re.compile(r"company|employer|department|org", re.I))
        company = self._clean_text(company_elem.get_text()) if company_elem else self.university_name

        # Find location
        location_elem = elem.find(["span", "div", "td"], class_=re.compile(r"location|city|campus", re.I))
        location = self._clean_text(location_elem.get_text()) if location_elem else ""

        # Find description
        desc_elem = elem.find(["p", "div"], class_=re.compile(r"description|summary|details", re.I))
        description = self._clean_text(desc_elem.get_text())[:500] if desc_elem else ""

        # Find job type
        job_type = None
        type_elem = elem.find(["span", "div", "td"], class_=re.compile(r"type|category|employment", re.I))
        if type_elem:
            job_type = self._extract_job_type_from_text(type_elem.get_text())

        return Job(
            source=self.source_name,
            source_id=self._generate_source_id(title, company, url),
            title=title,
            company=company,
            location=location,
            description=description,
            job_type=job_type,
            url=url or self.job_board_url
        )

    def _extract_from_tables(self, soup) -> list[Job]:
        """Extract jobs from HTML tables (common in university sites)."""
        jobs = []

        tables = soup.find_all("table")
        for table in tables:
            # Check if this looks like a job listing table
            headers = table.find_all("th")
            header_text = " ".join(th.get_text().lower() for th in headers)

            if any(kw in header_text for kw in ["job", "position", "title", "employer", "company"]):
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        job = self._parse_table_row(cells)
                        if job:
                            jobs.append(job)

        return jobs

    def _parse_table_row(self, cells) -> Optional[Job]:
        """Parse a job from a table row."""
        if len(cells) < 2:
            return None

        # Usually: Title, Company, [Location], [Type], [Date]
        title = self._clean_text(cells[0].get_text())
        if not title or len(title) < 3:
            return None

        # Look for link in first cell
        link = cells[0].find("a", href=True)
        url = ""
        if link:
            href = link.get("href", "")
            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(self.job_board_url)
                url = f"{parsed.scheme}://{parsed.netloc}{href}"

        company = self._clean_text(cells[1].get_text()) if len(cells) > 1 else self.university_name
        location = self._clean_text(cells[2].get_text()) if len(cells) > 2 else ""

        job_type = None
        if len(cells) > 3:
            job_type = self._extract_job_type_from_text(cells[3].get_text())

        return Job(
            source=self.source_name,
            source_id=self._generate_source_id(title, company),
            title=title,
            company=company if company else self.university_name,
            location=location,
            job_type=job_type,
            url=url or self.job_board_url
        )

    def _detect_iframe_system(self, soup) -> Optional[dict]:
        """Detect if the page uses an iframe-based job system."""
        iframes = soup.find_all("iframe")
        for iframe in iframes:
            src = iframe.get("src", "")

            if "handshake" in src.lower():
                return {"system": "Handshake", "url": src}
            elif "simplicity" in src.lower():
                return {"system": "Simplicity", "url": src}
            elif "12twenty" in src.lower():
                return {"system": "12Twenty", "url": src}
            elif "symplicity" in src.lower():
                return {"system": "Symplicity", "url": src}

        # Also check for links to these systems (skip mailto and javascript links)
        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href", "")
            href_lower = href.lower()

            # Skip non-http links (mailto, javascript, etc.)
            if href_lower.startswith("mailto:") or href_lower.startswith("javascript:"):
                continue

            text = link.get_text().lower()

            if "joinhandshake.com" in href_lower:
                return {"system": "Handshake", "url": href}
            elif "handshake" in href_lower or "handshake" in text:
                # Only use if it's a valid URL
                if href.startswith("http"):
                    return {"system": "Handshake", "url": href}

        # Check page text for mentions of external systems
        page_text = soup.get_text().lower()
        if "handshake" in page_text or "hirebing" in page_text:
            # Try to construct Handshake URL from university name
            uni_slug = self.university_name.lower().replace(" ", "").replace("university", "")
            return {
                "system": "Handshake",
                "url": f"https://{uni_slug}.joinhandshake.com",
                "requires_auth": True
            }

        return None

    def _parse_rss_feed(self, url: str) -> list[Job]:
        """Parse jobs from an RSS/Atom feed."""
        jobs = []

        try:
            xml = self._fetch(url)
            if not xml:
                return jobs

            soup = BeautifulSoup(xml, "lxml-xml")

            # Try RSS format
            items = soup.find_all("item")
            if not items:
                # Try Atom format
                items = soup.find_all("entry")

            for item in items:
                job = self._parse_rss_item(item)
                if job:
                    jobs.append(job)

        except Exception as e:
            print(f"RSS parsing error: {e}")

        return jobs

    def _parse_rss_item(self, item) -> Optional[Job]:
        """Parse a job from an RSS/Atom item."""
        title_elem = item.find("title")
        if not title_elem:
            return None

        title = self._clean_text(title_elem.get_text())
        if not title:
            return None

        # URL
        link_elem = item.find("link")
        url = ""
        if link_elem:
            url = link_elem.get_text() or link_elem.get("href", "")

        # Description
        desc_elem = item.find("description") or item.find("summary") or item.find("content")
        description = ""
        if desc_elem:
            description = BeautifulSoup(desc_elem.get_text(), "lxml").get_text()[:500]

        # Date
        date_elem = item.find("pubDate") or item.find("published") or item.find("updated")
        posted_date = None
        if date_elem:
            try:
                from email.utils import parsedate_to_datetime
                posted_date = parsedate_to_datetime(date_elem.get_text()).date()
            except Exception:
                pass

        return Job(
            source=self.source_name,
            source_id=self._generate_source_id(title, url),
            title=title,
            company=self.university_name,
            location="",
            description=self._clean_text(description),
            url=url,
            posted_date=posted_date
        )

    def _extract_employment_type(self, emp_type) -> Optional[str]:
        """Extract job type from employment type field."""
        if not emp_type:
            return None

        if isinstance(emp_type, list):
            emp_type = emp_type[0] if emp_type else ""

        emp_lower = str(emp_type).lower()

        if "full" in emp_lower:
            return "Full-time"
        elif "part" in emp_lower:
            return "Part-time"
        elif "intern" in emp_lower:
            return "Internship"
        elif "work-study" in emp_lower or "workstudy" in emp_lower:
            return "Work-study"
        elif "on-campus" in emp_lower or "oncampus" in emp_lower:
            return "On-campus"
        elif "contract" in emp_lower:
            return "Contract"

        return None

    def _extract_job_type_from_text(self, text: str) -> Optional[str]:
        """Extract job type from text."""
        text_lower = text.lower()

        if "full-time" in text_lower or "full time" in text_lower:
            return "Full-time"
        elif "part-time" in text_lower or "part time" in text_lower:
            return "Part-time"
        elif "internship" in text_lower:
            return "Internship"
        elif "work-study" in text_lower or "work study" in text_lower:
            return "Work-study"
        elif "on-campus" in text_lower or "on campus" in text_lower:
            return "On-campus"

        return None
