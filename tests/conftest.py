import pytest

pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    """Configure pytest-asyncio to auto mode."""
    config.option.asyncio_mode = "auto"
