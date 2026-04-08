import pytest
from unittest.mock import patch, AsyncMock, MagicMock

pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    """Configure pytest-asyncio to auto mode."""
    config.option.asyncio_mode = "auto"


@pytest.fixture
def mock_database():
    """Provide a mock database."""
    db = AsyncMock()
    db.init = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    settings = MagicMock()
    settings.database_url = "sqlite:///:memory:"
    settings.dispatcher_api_key = "test-key"
    settings.rate_limit_requests_per_minute = 20
    settings.alert_email_enabled = False
    return settings
