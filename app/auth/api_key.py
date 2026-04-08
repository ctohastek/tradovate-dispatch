# app/auth/api_key.py
from typing import Optional
from app.config import Settings


def validate_api_key(api_key: Optional[str], settings: Settings) -> bool:
    """
    Validate incoming API key against configured dispatcher key.

    Args:
        api_key: API key from request header
        settings: Application settings

    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False

    return api_key == settings.dispatcher_api_key


def get_api_key_from_header(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract API key from Authorization header.
    Expected format: "Bearer <api_key>"

    Args:
        auth_header: Authorization header value

    Returns:
        API key or None if invalid format
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
