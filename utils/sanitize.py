"""HTML sanitization and URL validation utilities for XSS protection."""
import html
import re
from urllib.parse import urlparse
from typing import Optional


def safe_html(text: Optional[str]) -> str:
    """Escape HTML special characters to prevent XSS attacks.

    Args:
        text: User-provided text that may contain HTML

    Returns:
        HTML-escaped string safe for rendering
    """
    if text is None:
        return ""
    return html.escape(str(text))


def is_safe_url(url: Optional[str]) -> bool:
    """Validate URL is HTTP/HTTPS only to prevent javascript: and data: attacks.

    Args:
        url: URL to validate

    Returns:
        True if URL uses http or https scheme
    """
    if not url:
        return False
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme.lower() in ['http', 'https'] and bool(parsed.netloc)
    except Exception:
        return False


def safe_url(url: Optional[str], default: str = "#") -> str:
    """Return URL if safe, otherwise return default.

    Args:
        url: URL to validate
        default: Default URL to return if validation fails

    Returns:
        Original URL if safe, otherwise default
    """
    if is_safe_url(url):
        return url
    return default


def sanitize_text(text: Optional[str], max_length: int = 10000) -> str:
    """Sanitize user text input by removing control characters and limiting length.

    Args:
        text: User-provided text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if text is None:
        return ""
    # Remove control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(text))
    # Limit length
    return sanitized[:max_length]


def safe_html_attr(value: Optional[str]) -> str:
    """Escape a value for use in HTML attributes.

    Escapes quotes and other special characters.

    Args:
        value: Value to escape

    Returns:
        Escaped value safe for HTML attributes
    """
    if value is None:
        return ""
    # Escape HTML entities and quotes
    escaped = html.escape(str(value), quote=True)
    return escaped


def strip_html_tags(text: Optional[str]) -> str:
    """Remove all HTML tags from text.

    Args:
        text: Text that may contain HTML tags

    Returns:
        Text with all HTML tags removed
    """
    if text is None:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', str(text))
    return clean
