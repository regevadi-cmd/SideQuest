"""Simple caching for job search results."""
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from config import DATA_DIR
from data.models import Job


CACHE_DIR = DATA_DIR / "cache"
CACHE_EXPIRY_HOURS = 6


def _get_cache_key(query: str, location: str, radius: int, job_types: Optional[list[str]]) -> str:
    """Generate a cache key from search parameters."""
    parts = [query.lower(), location.lower(), str(radius), ",".join(sorted(job_types or []))]
    combined = "|".join(parts)
    return hashlib.md5(combined.encode()).hexdigest()


def get_cached_results(
    query: str,
    location: str,
    radius: int,
    job_types: Optional[list[str]] = None
) -> Optional[list[Job]]:
    """
    Get cached search results if available and not expired.

    Returns:
        List of Job objects if cache hit, None if cache miss or expired
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_key = _get_cache_key(query, location, radius, job_types)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r") as f:
            data = json.load(f)

        # Check expiry
        cached_at = datetime.fromisoformat(data["cached_at"])
        if datetime.now() - cached_at > timedelta(hours=CACHE_EXPIRY_HOURS):
            cache_file.unlink()
            return None

        # Reconstruct Job objects
        jobs = [Job(**job_data) for job_data in data["jobs"]]
        return jobs

    except (json.JSONDecodeError, KeyError, ValueError):
        # Invalid cache, delete it
        cache_file.unlink()
        return None


def cache_results(
    query: str,
    location: str,
    radius: int,
    job_types: Optional[list[str]],
    jobs: list[Job]
):
    """Cache search results for later retrieval."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_key = _get_cache_key(query, location, radius, job_types)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    data = {
        "cached_at": datetime.now().isoformat(),
        "query": query,
        "location": location,
        "radius": radius,
        "job_types": job_types,
        "jobs": [job.model_dump(mode="json") for job in jobs]
    }

    with open(cache_file, "w") as f:
        json.dump(data, f, default=str)


def clear_cache():
    """Clear all cached results."""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()


def get_cache_stats() -> dict:
    """Get statistics about the cache."""
    if not CACHE_DIR.exists():
        return {"files": 0, "total_jobs": 0}

    files = list(CACHE_DIR.glob("*.json"))
    total_jobs = 0

    for f in files:
        try:
            with open(f, "r") as fh:
                data = json.load(fh)
                total_jobs += len(data.get("jobs", []))
        except Exception:
            pass

    return {
        "files": len(files),
        "total_jobs": total_jobs
    }
