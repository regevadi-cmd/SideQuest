"""Auto-search engine for automated job searches."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from data.models import SearchSchedule, SavedSearchResult, Notification, Job

logger = logging.getLogger(__name__)


class AutoSearchEngine:
    """Engine for running automated job searches based on user schedule."""

    def __init__(self, db):
        """Initialize the auto-search engine.

        Args:
            db: Database instance (SQLite or PostgreSQL)
        """
        self.db = db

    def should_run(self, schedule: SearchSchedule) -> bool:
        """Check if auto-search should run based on schedule.

        Args:
            schedule: The search schedule configuration

        Returns:
            True if search should run now
        """
        if not schedule or not schedule.enabled:
            return False

        # If never run, should run
        if not schedule.next_run:
            return True

        # Check if it's time to run
        return datetime.now() >= schedule.next_run

    def calculate_next_run(self, schedule: SearchSchedule) -> datetime:
        """Calculate the next run time based on frequency and time preference.

        Args:
            schedule: The search schedule configuration

        Returns:
            Next run datetime
        """
        now = datetime.now()

        # Determine base time based on preference
        hour_map = {
            "morning": 8,
            "afternoon": 14,
            "evening": 20
        }
        target_hour = hour_map.get(schedule.time_preference, 8)

        # Calculate next run based on frequency
        if schedule.frequency == "daily":
            # Next day at preferred time
            next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif schedule.frequency == "weekly":
            # Next week at preferred time (same weekday)
            next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
            next_run += timedelta(days=7)
        else:
            # Default to next day
            next_run = now + timedelta(days=1)

        return next_run

    def run_search(self, schedule: SearchSchedule) -> SavedSearchResult:
        """Execute an automated job search.

        Args:
            schedule: The search schedule with configuration

        Returns:
            SavedSearchResult with search outcome
        """
        logger.info(f"Running auto-search for schedule {schedule.id}")

        result = SavedSearchResult(
            schedule_id=schedule.id,
            run_at=datetime.now(),
            jobs_found=0,
            new_jobs=0,
            job_ids=[]
        )

        try:
            # Get location for search
            location = None
            if schedule.search_location_id:
                location = self.db.get_location(schedule.search_location_id)

            if not location:
                # Try to get default location
                locations = self.db.get_locations()
                location = next((l for l in locations if l.is_default), None)
                if not location and locations:
                    location = locations[0]

            if not location:
                result.error_message = "No search location configured"
                return result

            # Import scrapers
            from scrapers.indeed import IndeedScraper
            from scrapers.linkedin import LinkedInScraper
            from scrapers.glassdoor import GlassdoorScraper
            from scrapers.collegerecruiter import CollegeRecruiterScraper
            from scrapers.wayup import WayUpScraper

            # Map source names to scrapers
            scraper_map = {
                "Indeed": IndeedScraper,
                "LinkedIn": LinkedInScraper,
                "Glassdoor": GlassdoorScraper,
                "College Recruiter": CollegeRecruiterScraper,
                "WayUp": WayUpScraper
            }

            all_jobs = []
            sources = schedule.search_sources or ["Indeed", "LinkedIn"]

            for source in sources:
                scraper_class = scraper_map.get(source)
                if not scraper_class:
                    continue

                try:
                    scraper = scraper_class()
                    jobs = scraper.search(
                        query=schedule.search_query or "student jobs",
                        location=location.address,
                        radius=schedule.search_radius or 10,
                        job_types=schedule.search_job_types if schedule.search_job_types else None,
                        max_results=30
                    )
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"Error searching {source}: {e}")

            # Deduplicate jobs
            seen = set()
            unique_jobs = []
            for job in all_jobs:
                key = (job.title.lower(), job.company.lower())
                if key not in seen:
                    seen.add(key)
                    unique_jobs.append(job)

            result.jobs_found = len(unique_jobs)

            # Save jobs and track new ones
            new_job_ids = []
            for job in unique_jobs:
                # Check if job already exists
                existing_jobs = self.db.get_jobs(limit=1000)
                is_new = not any(
                    j.source == job.source and j.source_id == job.source_id
                    for j in existing_jobs
                )

                saved_job = self.db.save_job(job)

                if is_new:
                    new_job_ids.append(saved_job.id)

            result.new_jobs = len(new_job_ids)
            result.job_ids = new_job_ids

            logger.info(f"Auto-search complete: {result.jobs_found} found, {result.new_jobs} new")

        except Exception as e:
            logger.error(f"Auto-search failed: {e}")
            result.error_message = str(e)

        return result

    def create_notification(self, result: SavedSearchResult) -> Optional[Notification]:
        """Create a notification for search results.

        Args:
            result: The search result to notify about

        Returns:
            Created notification, or None if no notification needed
        """
        if result.error_message:
            return self.db.save_notification(Notification(
                type="system",
                title="Auto-Search Failed",
                message=f"Your scheduled job search failed: {result.error_message}",
                related_job_ids=[]
            ))

        if result.new_jobs == 0:
            # No new jobs, no notification needed
            return None

        # Create notification for new jobs
        notification = Notification(
            type="new_jobs",
            title=f"{result.new_jobs} New Jobs Found!",
            message=f"Your scheduled search found {result.new_jobs} new job{'s' if result.new_jobs > 1 else ''} matching your criteria.",
            related_job_ids=result.job_ids
        )

        return self.db.save_notification(notification)

    def run_if_due(self) -> Optional[SavedSearchResult]:
        """Check if auto-search is due and run it if so.

        This is the main entry point to call on app load.

        Returns:
            SavedSearchResult if search was run, None otherwise
        """
        schedule = self.db.get_search_schedule()

        if not self.should_run(schedule):
            return None

        # Run the search
        result = self.run_search(schedule)

        # Save the result
        self.db.save_search_result(result)

        # Create notification
        self.create_notification(result)

        # Update schedule times
        schedule.last_run = datetime.now()
        schedule.next_run = self.calculate_next_run(schedule)
        self.db.save_search_schedule(schedule)

        return result


def trigger_auto_search(db) -> Optional[SavedSearchResult]:
    """Convenience function to trigger auto-search check.

    Call this on app startup to check and run scheduled searches.

    Args:
        db: Database instance

    Returns:
        Search result if search was run, None otherwise
    """
    engine = AutoSearchEngine(db)
    return engine.run_if_due()
