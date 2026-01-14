"""AI-powered resume and cover letter assistance."""
from typing import Optional

from .providers import get_ai_provider


def generate_cover_letter(
    job_title: str,
    company: str,
    job_description: str,
    resume: str,
    tone: str = "professional",
    length: str = "medium"
) -> str:
    """
    Generate a tailored cover letter for a specific job.

    Args:
        job_title: Title of the job
        company: Company name
        job_description: Full job description
        resume: User's resume text
        tone: Writing tone (professional, enthusiastic, confident, humble)
        length: Length (short ~150 words, medium ~250 words, long ~400 words)

    Returns:
        Generated cover letter text
    """
    provider = get_ai_provider()
    if not provider:
        return "Error: AI provider not configured. Please set up an AI provider in Settings."

    length_words = {"short": 150, "medium": 250, "long": 400}.get(length, 250)

    system_prompt = f"""You are an expert career counselor helping a student write a cover letter.
Write in a {tone} tone. The letter should be approximately {length_words} words.
Focus on connecting the student's experience to the job requirements.
Be specific and avoid generic phrases. Use concrete examples from their resume.
Format as a proper business letter without the address header."""

    prompt = f"""Write a cover letter for this job application:

JOB TITLE: {job_title}
COMPANY: {company}

JOB DESCRIPTION:
{job_description[:2000]}

APPLICANT'S RESUME:
{resume[:3000]}

Write a compelling cover letter that:
1. Shows enthusiasm for this specific role and company
2. Highlights relevant skills and experiences from the resume
3. Connects the applicant's background to the job requirements
4. Ends with a clear call to action"""

    try:
        return provider.generate(prompt, system=system_prompt, max_tokens=1000)
    except Exception as e:
        return f"Error generating cover letter: {str(e)}"


def analyze_resume(resume: str, target_job: Optional[str] = None) -> str:
    """
    Analyze a resume and provide improvement suggestions.

    Args:
        resume: The resume text to analyze
        target_job: Optional target job description for tailored advice

    Returns:
        Analysis and suggestions as text
    """
    provider = get_ai_provider()
    if not provider:
        return "Error: AI provider not configured. Please set up an AI provider in Settings."

    system_prompt = """You are an expert career counselor and resume reviewer.
Provide constructive, actionable feedback to help students improve their resumes.
Be encouraging but honest. Focus on concrete improvements they can make."""

    prompt = f"""Analyze this resume and provide improvement suggestions:

RESUME:
{resume[:4000]}
"""

    if target_job:
        prompt += f"""
TARGET JOB DESCRIPTION:
{target_job[:2000]}

Provide specific suggestions for tailoring this resume to this job.
"""
    else:
        prompt += """
Provide general suggestions for improving this resume for student/entry-level job applications.
"""

    prompt += """
Structure your response as:

## Strengths
- What's working well

## Areas for Improvement
- Specific suggestions with examples

## Quick Wins
- Easy changes that would have immediate impact

## For Entry-Level Positions
- Advice specific to students/new grads"""

    try:
        return provider.generate(prompt, system=system_prompt, max_tokens=1500)
    except Exception as e:
        return f"Error analyzing resume: {str(e)}"


def tailor_resume_bullet(
    original_bullet: str,
    job_requirement: str
) -> str:
    """
    Rewrite a resume bullet point to better match a job requirement.

    Args:
        original_bullet: The original bullet point from the resume
        job_requirement: The requirement to tailor toward

    Returns:
        Rewritten bullet point
    """
    provider = get_ai_provider()
    if not provider:
        return original_bullet

    prompt = f"""Rewrite this resume bullet point to better demonstrate the required skill/experience.

ORIGINAL: {original_bullet}

TARGET REQUIREMENT: {job_requirement}

Rewrite to:
- Use action verbs
- Include metrics if possible
- Clearly show relevance to the requirement
- Keep it concise (1-2 sentences)

Return ONLY the rewritten bullet point, nothing else."""

    try:
        return provider.generate(prompt, max_tokens=100)
    except Exception:
        return original_bullet
