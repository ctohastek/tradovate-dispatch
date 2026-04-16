# app/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra='ignore')

    # Tradovate API
    tradovate_api_key: Optional[str] = None
    tradovate_live_url: Optional[str] = None
    tradovate_demo_url: Optional[str] = None
    tradovate_device_id: Optional[str] = None
    tradovate_account_name: Optional[str] = None
    tradovate_account_pass: Optional[str] = None

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

    def get_agent_tradovate_config(self, agent_name: str) -> dict:
        """Get Tradovate credentials and environment for a specific agent.

        Retrieves per-agent configuration from environment variables:
        - TRADOVATE_API_KEY_<agent_name>
        - TRADOVATE_CLIENT_ID_<agent_name>
        - AGENT_ENVIRONMENT_<agent_name>

        Args:
            agent_name: The name of the agent (e.g., 'mini01')

        Returns:
            Dictionary with keys: api_key, client_id, environment
        """
        api_key_var = f"TRADOVATE_API_KEY_{agent_name}".upper()
        client_id_var = f"TRADOVATE_CLIENT_ID_{agent_name}".upper()
        env_var = f"AGENT_ENVIRONMENT_{agent_name}".upper()

        return {
            "api_key": os.getenv(api_key_var),
            "client_id": os.getenv(client_id_var),
            "environment": os.getenv(env_var, "demo").lower(),
        }


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
