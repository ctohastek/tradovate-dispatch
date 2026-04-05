import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from app.config import Settings
from app.models import CommandStatus


class AlertMailer:
    """Send email alerts for significant events."""

    def __init__(self, settings: Settings):
        self.enabled = settings.alert_email_enabled
        self.to_email = settings.alert_email_to
        self.from_email = settings.alert_email_from or "dispatcher@tradovate-dispatch"
        self.smtp_host = settings.alert_smtp_host or "localhost"
        self.smtp_port = settings.alert_smtp_port
        self.smtp_password = settings.alert_smtp_password

    async def send_alert(
        self,
        agent_id: str,
        command: str,
        status: CommandStatus,
        details: str
    ) -> bool:
        """Send alert email."""
        if not self.enabled:
            return True

        try:
            subject = f"[TRADOVATE DISPATCH] {status.value.upper()} - {agent_id}"
            body = self._format_alert_body(agent_id, command, status, details)

            self._send_email(subject, body)
            return True

        except Exception as e:
            print(f"Failed to send alert email: {str(e)}")
            return False

    def _format_alert_body(
        self,
        agent_id: str,
        command: str,
        status: CommandStatus,
        details: str
    ) -> str:
        """Format email body."""
        now = datetime.now(timezone.utc).isoformat()

        return f"""
Tradovate Dispatch Alert

Time: {now}
Agent: {agent_id}
Status: {status.value}
Command: {command}

Details:
{details}

---
Tradovate Dispatch System
"""

    def _send_email(self, subject: str, body: str):
        """Send email via SMTP."""
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if self.smtp_host and self.smtp_host != "localhost":
            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_password:
                        server.starttls()
                        server.login(self.from_email, self.smtp_password)
                    server.send_message(msg)
            except Exception as e:
                raise Exception(f"SMTP error: {str(e)}")
