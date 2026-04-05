from datetime import datetime, timezone
from typing import List, Optional
from app.database import Database
from app.models import CommandStatus, AuditLog


class AuditLogger:
    """Log all command executions to database for audit trail."""

    def __init__(self, db: Database):
        self.db = db

    async def log(
        self,
        agent_id: str,
        command: str,
        status: CommandStatus,
        parsed_command: Optional[str] = None,
        error_message: Optional[str] = None,
        response: Optional[str] = None
    ) -> int:
        """Log command execution."""
        now = datetime.now(timezone.utc).isoformat()

        cursor = await self.db.execute(
            """
            INSERT INTO audit_logs
            (agent_id, command, parsed_command, status, error_message, response, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (agent_id, command, parsed_command, status.value, error_message, response, now)
        )

        await self.db.commit()
        return cursor.lastrowid

    async def get_logs_by_agent(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get logs for specific agent."""
        rows = await self.db.fetchall(
            """
            SELECT id, agent_id, command, parsed_command, status, error_message,
                   response, created_at
            FROM audit_logs
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (agent_id, limit)
        )

        return [self._row_to_model(row) for row in rows]

    async def get_logs_by_status(
        self,
        status: CommandStatus,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get logs with specific status."""
        rows = await self.db.fetchall(
            """
            SELECT id, agent_id, command, parsed_command, status, error_message,
                   response, created_at
            FROM audit_logs
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (status.value, limit)
        )

        return [self._row_to_model(row) for row in rows]

    async def get_logs_by_date_range(
        self,
        start: datetime,
        end: datetime,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get logs within date range."""
        rows = await self.db.fetchall(
            """
            SELECT id, agent_id, command, parsed_command, status, error_message,
                   response, created_at
            FROM audit_logs
            WHERE created_at >= ? AND created_at <= ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (start.isoformat(), end.isoformat(), limit)
        )

        return [self._row_to_model(row) for row in rows]

    @staticmethod
    def _row_to_model(row: tuple) -> AuditLog:
        """Convert database row to AuditLog model."""
        return AuditLog(
            id=row[0],
            agent_id=row[1],
            command=row[2],
            parsed_command=row[3],
            status=CommandStatus(row[4]),
            error_message=row[5],
            response=row[6],
            created_at=datetime.fromisoformat(row[7]) if row[7] else None
        )
