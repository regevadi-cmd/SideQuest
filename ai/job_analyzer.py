"""AI-powered job description analysis."""
import json
from typing import Optional

from .providers import get_ai_provider


def analyze_job_description(job_description: str) -> dict:
    """
    Analyze a job description to extract key information.

    Args:
        job_description: The full job description text

    Returns:
        Dictionary with:
        - required_skills: List of required skills
        - nice_to_have: List of preferred but not required skills
        - responsibilities: Key job responsibilities
        - salary_estimate: Estimated salary if not provided
        - red_flags: Any potential concerns
        - summary: Brief summary of the role
    """
    provider = get_ai_provider()
    if not provider:
        return {
            "error": "AI provider not configured",
            "required_skills": [],
            "nice_to_have": [],
            "responsibilities": [],
        }

    system_prompt = """You are an expert job analyst helping students understand job postings.
Extract and organize information clearly. Be honest about what's required vs nice-to-have.
Respond in JSON format only."""

    prompt = f"""Analyze this job description and extract key information:

{job_description[:4000]}

Return a JSON object with:
{{
  "required_skills": ["skill1", "skill2", ...],
  "nice_to_have": ["skill1", "skill2", ...],
  "responsibilities": ["responsibility1", "responsibility2", ...],
  "salary_estimate": "Estimated range based on role/location, or null if stated",
  "experience_level": "entry/mid/senior/unclear",
  "red_flags": ["any concerns about the posting"],
  "summary": "2-3 sentence summary of the role"
}}

Be thorough but concise. Focus on what matters for a student applicant."""

    try:
        response = provider.generate(prompt, system=system_prompt, max_tokens=1000)
        # Parse JSON, handling potential markdown code blocks
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse AI response",
            "required_skills": [],
            "nice_to_have": [],
            "responsibilities": [],
        }
    except Exception as e:
        return {
            "error": str(e),
            "required_skills": [],
            "nice_to_have": [],
            "responsibilities": [],
        }


def compare_jobs(job1_desc: str, job2_desc: str) -> str:
    """
    Compare two job descriptions to help with decision making.

    Args:
        job1_desc: First job description
        job2_desc: Second job description

    Returns:
        Comparison analysis as text
    """
    provider = get_ai_provider()
    if not provider:
        return "Error: AI provider not configured"

    prompt = f"""Compare these two job opportunities for a student:

JOB 1:
{job1_desc[:2000]}

JOB 2:
{job2_desc[:2000]}

Compare them on:
1. Learning opportunities and skill development
2. Career growth potential
3. Work-life balance indicators
4. Compensation (if mentioned)
5. Company culture signals

Provide a balanced comparison that helps a student decide between them.
Don't declare a winner - highlight trade-offs."""

    try:
        return provider.generate(prompt, max_tokens=800)
    except Exception as e:
        return f"Error comparing jobs: {str(e)}"


def suggest_interview_questions(job_description: str) -> list[str]:
    """
    Generate questions to ask in an interview based on the job description.

    Args:
        job_description: The job description

    Returns:
        List of thoughtful questions to ask
    """
    provider = get_ai_provider()
    if not provider:
        return ["What does a typical day look like in this role?"]

    prompt = f"""Based on this job description, suggest 5-7 thoughtful questions
a student could ask during an interview:

{job_description[:2000]}

Questions should:
- Show genuine interest in the role
- Help the student evaluate if it's a good fit
- Not be easily answered by the job posting
- Be appropriate for a student/entry-level applicant

Return a JSON array of question strings."""

    try:
        response = provider.generate(prompt, max_tokens=400)
        questions = json.loads(response)
        return questions if isinstance(questions, list) else []
    except Exception:
        return [
            "What does a typical day look like in this role?",
            "What opportunities for growth and learning are available?",
            "How would you describe the team culture?",
        ]
