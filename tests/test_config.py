# tests/test_config.py
import os
import pytest
from app.config import Settings


def test_settings_from_env():
    """Config should load from environment variables."""
    os.environ["TRADOVATE_API_URL"] = "https://api.tradovate.com"
    os.environ["TRADOVATE_API_KEY"] = "test-key-123"
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    os.environ["DISPATCHER_API_KEY"] = "dispatcher-key-456"
    os.environ["RATE_LIMIT_REQUESTS_PER_MINUTE"] = "30"
    os.environ["ALERT_EMAIL_ENABLED"] = "true"
    os.environ["ALERT_EMAIL_TO"] = "alerts@example.com"

    settings = Settings()
    assert settings.tradovate_api_url == "https://api.tradovate.com"
    assert settings.tradovate_api_key == "test-key-123"
    assert settings.database_url == "sqlite:///test.db"
    assert settings.dispatcher_api_key == "dispatcher-key-456"
    assert settings.rate_limit_requests_per_minute == 30
    assert settings.alert_email_enabled is True
    assert settings.alert_email_to == "alerts@example.com"


def test_settings_defaults():
    """Config should have sensible defaults."""
    # Clear env vars to test defaults
    for key in ["TRADOVATE_API_URL", "TRADOVATE_API_KEY", "DATABASE_URL",
                "DISPATCHER_API_KEY", "RATE_LIMIT_REQUESTS_PER_MINUTE",
                "ALERT_EMAIL_ENABLED", "ALERT_EMAIL_TO"]:
        os.environ.pop(key, None)

    settings = Settings()
    assert settings.database_url == "sqlite:///dispatcher.db"
    assert settings.rate_limit_requests_per_minute == 20
    assert settings.alert_email_enabled is False
