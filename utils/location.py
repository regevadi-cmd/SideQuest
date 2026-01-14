"""Location utilities for geocoding and distance calculations."""
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


# Initialize geocoder with a user agent
_geocoder = Nominatim(user_agent="student-job-search-agent")


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert an address to latitude/longitude coordinates.

    Args:
        address: Full address string (e.g., "UC Berkeley, Berkeley, CA")

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    try:
        location = _geocoder.geocode(address, timeout=10)
        if location:
            return (location.latitude, location.longitude)
        return None
    except (GeocoderTimedOut, GeocoderServiceError):
        return None


def calculate_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two points in miles.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in miles
    """
    return geodesic((lat1, lon1), (lat2, lon2)).miles


def format_distance(miles: float) -> str:
    """Format distance for display."""
    if miles < 0.1:
        return "< 0.1 mi"
    elif miles < 1:
        return f"{miles:.1f} mi"
    else:
        return f"{miles:.0f} mi"


def get_location_string(city: str, state: str = "", country: str = "USA") -> str:
    """Build a location string for geocoding."""
    parts = [city]
    if state:
        parts.append(state)
    if country:
        parts.append(country)
    return ", ".join(parts)
