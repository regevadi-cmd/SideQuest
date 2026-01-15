"""Rate limiting utilities to prevent abuse."""
import time
import streamlit as st
from typing import Optional
from collections import defaultdict


class RateLimiter:
    """Rate limiter using sliding window algorithm.

    Tracks requests per user within a time window and blocks
    requests that exceed the limit.
    """

    def __init__(self, max_requests: int = 10, time_window: int = 3600):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default 1 hour)
        """
        self.max_requests = max_requests
        self.time_window = time_window

    def _get_requests_key(self, action: str) -> str:
        """Get session state key for tracking requests."""
        return f"rate_limit_{action}_requests"

    def is_allowed(self, action: str = "search") -> bool:
        """Check if action is allowed under rate limit.

        Args:
            action: Type of action (e.g., 'search', 'ai_call')

        Returns:
            True if action is allowed, False if rate limited
        """
        key = self._get_requests_key(action)
        now = time.time()

        # Get existing requests from session state
        if key not in st.session_state:
            st.session_state[key] = []

        # Filter to only requests within time window
        requests = [t for t in st.session_state[key] if now - t < self.time_window]

        # Check if under limit
        if len(requests) >= self.max_requests:
            return False

        # Record this request
        requests.append(now)
        st.session_state[key] = requests
        return True

    def get_remaining(self, action: str = "search") -> int:
        """Get remaining requests allowed.

        Args:
            action: Type of action

        Returns:
            Number of requests remaining
        """
        key = self._get_requests_key(action)
        now = time.time()

        if key not in st.session_state:
            return self.max_requests

        requests = [t for t in st.session_state[key] if now - t < self.time_window]
        return max(0, self.max_requests - len(requests))

    def get_reset_time(self, action: str = "search") -> Optional[int]:
        """Get seconds until rate limit resets.

        Args:
            action: Type of action

        Returns:
            Seconds until oldest request expires, or None if not rate limited
        """
        key = self._get_requests_key(action)
        now = time.time()

        if key not in st.session_state or not st.session_state[key]:
            return None

        requests = [t for t in st.session_state[key] if now - t < self.time_window]
        if len(requests) < self.max_requests:
            return None

        # Time until oldest request expires
        oldest = min(requests)
        return int(self.time_window - (now - oldest))

    def reset(self, action: str = "search"):
        """Reset rate limit for an action.

        Args:
            action: Type of action to reset
        """
        key = self._get_requests_key(action)
        st.session_state[key] = []


# Default rate limiters for different actions
search_limiter = RateLimiter(max_requests=10, time_window=3600)  # 10 per hour
ai_limiter = RateLimiter(max_requests=20, time_window=3600)  # 20 per hour


def check_search_rate_limit() -> tuple[bool, str]:
    """Check if search is allowed under rate limit.

    Returns:
        Tuple of (is_allowed, message)
    """
    if search_limiter.is_allowed("search"):
        remaining = search_limiter.get_remaining("search")
        return True, f"{remaining} searches remaining this hour"

    reset_time = search_limiter.get_reset_time("search")
    if reset_time:
        minutes = reset_time // 60
        return False, f"Rate limit exceeded. Try again in {minutes} minutes."
    return False, "Rate limit exceeded. Please try again later."


def check_ai_rate_limit() -> tuple[bool, str]:
    """Check if AI operation is allowed under rate limit.

    Returns:
        Tuple of (is_allowed, message)
    """
    if ai_limiter.is_allowed("ai"):
        remaining = ai_limiter.get_remaining("ai")
        return True, f"{remaining} AI operations remaining this hour"

    reset_time = ai_limiter.get_reset_time("ai")
    if reset_time:
        minutes = reset_time // 60
        return False, f"AI rate limit exceeded. Try again in {minutes} minutes."
    return False, "AI rate limit exceeded. Please try again later."
