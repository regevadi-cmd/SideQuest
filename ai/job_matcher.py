"""AI-powered job matching functionality."""
from typing import Optional
import json

from .providers import get_ai_provider
from data.models import Job, Profile


MATCH_SYSTEM_PROMPT = """You are a job matching assistant helping a student find relevant job opportunities.
Analyze the job posting against the student's profile and provide:
1. A match score from 0-100
2. Key reasons why this job is a good/bad match
3. Any extracted requirements from the job description

Be honest and practical - consider the student's skills, interests, and career goals.
Respond in JSON format only."""


def score_job_match(job: Job, profile: Profile) -> tuple[float, list[str]]:
    """
    Score how well a job matches the user's profile.

    Args:
        job: The job to score
        profile: User's profile with skills, interests, etc.

    Returns:
        Tuple of (score 0-100, list of reasons)
    """
    provider = get_ai_provider()
    if not provider:
        return 0.0, ["AI not configured"]

    prompt = f"""Analyze this job match:

JOB:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Type: {job.job_type or 'Not specified'}
- Salary: {job.salary_text or 'Not specified'}
- Description: {job.description[:1000]}

STUDENT PROFILE:
- Major: {profile.major}
- Skills: {', '.join(profile.skills)}
- Interests: {', '.join(profile.interests)}
- Preferred job types: {', '.join(profile.preferred_job_types)}
- Min hourly rate: ${profile.min_hourly_rate or 'Not specified'}
- Max hours/week: {profile.max_hours_per_week or 'Not specified'}

Return JSON with:
{{"score": <0-100>, "reasons": ["reason1", "reason2", ...], "requirements": ["req1", "req2", ...]}}"""

    try:
        response = provider.generate(prompt, system=MATCH_SYSTEM_PROMPT, max_tokens=500)
        # Parse JSON from response
        data = json.loads(response)
        return float(data.get("score", 0)), data.get("reasons", [])
    except Exception as e:
        return 0.0, [f"Matching failed: {str(e)}"]


def batch_score_jobs(jobs: list[Job], profile: Profile) -> list[Job]:
    """
    Score multiple jobs and update their match scores.

    Args:
        jobs: List of jobs to score
        profile: User's profile

    Returns:
        Jobs with updated match_score and match_reasons
    """
    for job in jobs:
        score, reasons = score_job_match(job, profile)
        job.match_score = score
        job.match_reasons = reasons

    # Sort by match score
    return sorted(jobs, key=lambda j: j.match_score or 0, reverse=True)


def extract_job_requirements(job: Job) -> list[str]:
    """Extract key requirements from a job description."""
    provider = get_ai_provider()
    if not provider:
        return []

    prompt = f"""Extract the key requirements from this job posting:

Title: {job.title}
Company: {job.company}
Description: {job.description}

Return a JSON array of strings, each being a distinct requirement.
Focus on skills, experience, education, and qualifications.
Example: ["Python programming", "2+ years experience", "Bachelor's degree"]
Return ONLY the JSON array, nothing else."""

    try:
        response = provider.generate(prompt, max_tokens=300)
        requirements = json.loads(response)
        return requirements if isinstance(requirements, list) else []
    except Exception:
        return []
