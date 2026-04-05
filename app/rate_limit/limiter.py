from datetime import datetime, timedelta
from app.database import Database


class RateLimiter:
    """Per-agent request rate limiting."""

    def __init__(self, db: Database, requests_per_minute: int = 20):
        self.db = db
        self.requests_per_minute = requests_per_minute

    async def is_allowed(self, agent_id: str) -> bool:
        """Check if agent is allowed to make a request."""
        now = datetime.utcnow()

        entry = await self.db.fetchone(
            "SELECT request_count, reset_at FROM rate_limits WHERE agent_id = ?",
            (agent_id,)
        )

        if entry is None:
            reset_at = now + timedelta(minutes=1)
            await self.db.execute(
                "INSERT INTO rate_limits (agent_id, request_count, reset_at) VALUES (?, ?, ?)",
                (agent_id, 1, reset_at.isoformat())
            )
            await self.db.commit()
            return True

        request_count, reset_at_str = entry
        reset_at = datetime.fromisoformat(reset_at_str)

        if now >= reset_at:
            new_reset = now + timedelta(minutes=1)
            await self.db.execute(
                "UPDATE rate_limits SET request_count = 1, reset_at = ? WHERE agent_id = ?",
                (new_reset.isoformat(), agent_id)
            )
            await self.db.commit()
            return True

        if request_count < self.requests_per_minute:
            await self.db.execute(
                "UPDATE rate_limits SET request_count = request_count + 1 WHERE agent_id = ?",
                (agent_id,)
            )
            await self.db.commit()
            return True

        return False

    async def get_remaining(self, agent_id: str) -> int:
        """Get remaining requests for agent in current window."""
        entry = await self.db.fetchone(
            "SELECT request_count, reset_at FROM rate_limits WHERE agent_id = ?",
            (agent_id,)
        )

        if entry is None:
            return self.requests_per_minute

        request_count, reset_at_str = entry
        reset_at = datetime.fromisoformat(reset_at_str)

        if datetime.utcnow() >= reset_at:
            return self.requests_per_minute

        return max(0, self.requests_per_minute - request_count)
