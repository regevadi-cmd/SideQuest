"""Schedule utilities for parsing and checking time conflicts."""
from datetime import time
from typing import Optional

from data.models import ScheduleBlock


DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def parse_time(time_str: str) -> Optional[time]:
    """Parse a time string (HH:MM) to a time object."""
    try:
        parts = time_str.strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return time(hour=hour, minute=minute)
    except (ValueError, IndexError):
        return None


def parse_schedule(schedule_text: str) -> list[ScheduleBlock]:
    """
    Parse a text schedule into ScheduleBlock objects.

    Format: One entry per line, e.g.:
        Mon 9:00-10:30 CS101
        Tue 14:00-15:30 Math202
        Wed 9:00-10:30 CS101
    """
    blocks = []
    for line in schedule_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        day = parts[0][:3].capitalize()
        if day not in DAYS_OF_WEEK:
            continue

        time_range = parts[1]
        if "-" not in time_range:
            continue

        start_str, end_str = time_range.split("-", 1)
        start = parse_time(start_str)
        end = parse_time(end_str)

        if not start or not end:
            continue

        label = " ".join(parts[2:]) if len(parts) > 2 else None

        blocks.append(ScheduleBlock(
            day=day,
            start_time=start_str,
            end_time=end_str,
            label=label
        ))

    return blocks


def check_schedule_conflict(
    blocks: list[ScheduleBlock],
    job_day: str,
    job_start: str,
    job_end: str
) -> bool:
    """
    Check if a job's hours conflict with the user's schedule.

    Args:
        blocks: User's unavailable time blocks
        job_day: Day of the job shift
        job_start: Start time of job (HH:MM)
        job_end: End time of job (HH:MM)

    Returns:
        True if there's a conflict (job overlaps with unavailable time)
    """
    job_start_time = parse_time(job_start)
    job_end_time = parse_time(job_end)

    if not job_start_time or not job_end_time:
        return False  # Can't determine, assume no conflict

    job_day = job_day[:3].capitalize()

    for block in blocks:
        if block.day != job_day:
            continue

        block_start = parse_time(block.start_time)
        block_end = parse_time(block.end_time)

        if not block_start or not block_end:
            continue

        # Check for overlap
        if job_start_time < block_end and job_end_time > block_start:
            return True

    return False


def get_available_hours(blocks: list[ScheduleBlock], day: str) -> list[tuple[str, str]]:
    """
    Get available time windows for a given day.
    Assumes availability from 6:00 to 23:00 minus blocked times.
    """
    day = day[:3].capitalize()
    day_blocks = sorted(
        [b for b in blocks if b.day == day],
        key=lambda b: parse_time(b.start_time) or time(0, 0)
    )

    available = []
    current_start = time(6, 0)
    end_of_day = time(23, 0)

    for block in day_blocks:
        block_start = parse_time(block.start_time)
        block_end = parse_time(block.end_time)

        if not block_start or not block_end:
            continue

        if current_start < block_start:
            available.append((
                current_start.strftime("%H:%M"),
                block_start.strftime("%H:%M")
            ))

        current_start = max(current_start, block_end)

    if current_start < end_of_day:
        available.append((
            current_start.strftime("%H:%M"),
            end_of_day.strftime("%H:%M")
        ))

    return available


def format_availability_summary(blocks: list[ScheduleBlock]) -> str:
    """Create a human-readable summary of availability."""
    if not blocks:
        return "Fully available"

    busy_days = set(b.day for b in blocks)
    free_days = [d for d in DAYS_OF_WEEK if d not in busy_days]

    summary_parts = []
    if free_days:
        summary_parts.append(f"Free: {', '.join(free_days)}")

    for day in DAYS_OF_WEEK:
        day_blocks = [b for b in blocks if b.day == day]
        if day_blocks:
            times = [f"{b.start_time}-{b.end_time}" for b in day_blocks]
            summary_parts.append(f"{day} busy: {', '.join(times)}")

    return "\n".join(summary_parts)
