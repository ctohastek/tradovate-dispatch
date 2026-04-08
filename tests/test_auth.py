# tests/test_auth.py
import pytest
from app.auth.api_key import validate_api_key
from app.config import Settings


def test_validate_api_key_valid():
    """Should accept valid API key."""
    valid_key = "valid-dispatcher-key-123"
    settings = Settings()
    settings.dispatcher_api_key = valid_key

    result = validate_api_key(valid_key, settings)
    assert result is True


def test_validate_api_key_invalid():
    """Should reject invalid API key."""
    invalid_key = "wrong-key"
    settings = Settings()
    settings.dispatcher_api_key = "valid-key"

    result = validate_api_key(invalid_key, settings)
    assert result is False


def test_validate_api_key_empty():
    """Should reject empty API key."""
    settings = Settings()
    settings.dispatcher_api_key = "valid-key"

    result = validate_api_key("", settings)
    assert result is False


def test_validate_api_key_none():
    """Should reject None API key."""
    settings = Settings()
    settings.dispatcher_api_key = "valid-key"

    result = validate_api_key(None, settings)
    assert result is False
