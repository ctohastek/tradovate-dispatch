import pytest
from unittest.mock import patch, AsyncMock
from app.alerts.mailer import AlertMailer
from app.config import Settings
from app.models import CommandStatus


@pytest.mark.asyncio
async def test_mailer_init():
    settings = Settings()
    settings.alert_email_enabled = True
    settings.alert_email_to = "alerts@example.com"
    settings.alert_smtp_host = "smtp.example.com"

    mailer = AlertMailer(settings)
    assert mailer.enabled is True
    assert mailer.to_email == "alerts@example.com"


@pytest.mark.asyncio
async def test_mailer_disabled():
    settings = Settings()
    settings.alert_email_enabled = False

    mailer = AlertMailer(settings)

    result = await mailer.send_alert(
        agent_id="agent-1",
        command="BUY 10 ES",
        status=CommandStatus.SUCCESS,
        details="Order placed"
    )

    assert result is True


@pytest.mark.asyncio
async def test_send_alert():
    settings = Settings()
    settings.alert_email_enabled = True
    settings.alert_email_to = "alerts@example.com"
    settings.alert_email_from = "dispatcher@example.com"
    settings.alert_smtp_host = "smtp.example.com"
    settings.alert_smtp_port = 587

    mailer = AlertMailer(settings)

    result = await mailer.send_alert(
        agent_id="agent-1",
        command="BUY 10 ES",
        status=CommandStatus.VALIDATION_ERROR,
        details="Invalid quantity"
    )

    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_alert_on_rate_limit():
    settings = Settings()
    settings.alert_email_enabled = True

    mailer = AlertMailer(settings)

    result = await mailer.send_alert(
        agent_id="aggressive-agent",
        command="BUY 100 ES",
        status=CommandStatus.RATE_LIMITED,
        details="Exceeded 20 requests per minute"
    )

    assert isinstance(result, bool)
