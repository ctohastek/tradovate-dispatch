# app/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    # Tradovate API
    tradovate_live_url: Optional[str] = None
    tradovate_demo_url: Optional[str] = None
    tradovate_api_key: Optional[str] = None

    # Database
    database_url: str = "sqlite:///dispatcher.db"

    # Dispatcher security
    dispatcher_api_key: Optional[str] = None

    # Rate limiting
    rate_limit_requests_per_minute: int = 20

    # Alerts
    alert_email_enabled: bool = False
    alert_email_to: Optional[str] = None
    alert_email_from: Optional[str] = None
    alert_smtp_host: Optional[str] = None
    alert_smtp_port: int = 587
    alert_smtp_password: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/dispatcher.log"

    # Environment
    environment: str = "development"
    debug: bool = False


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
