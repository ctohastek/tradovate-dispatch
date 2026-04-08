import aiosqlite
from typing import Any, List


class Database:
    """AsyncIO wrapper for SQLite database."""

    def __init__(self, db_path: str = "dispatcher.db"):
        self.db_path = db_path
        self.conn = None

    async def init(self):
        """Initialize database and create tables."""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA journal_mode = WAL")
        await self._create_tables()
        await self.conn.commit()

    async def _create_tables(self):
        """Create required database tables."""
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                command TEXT NOT NULL,
                parsed_command TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                response TEXT
            )
        """)

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL UNIQUE,
                request_count INTEGER DEFAULT 0,
                reset_at TEXT NOT NULL
            )
        """)

        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_agent_time
            ON audit_logs(agent_id, created_at DESC)
        """)

        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_status
            ON audit_logs(status)
        """)

    async def execute(self, query: str, params: tuple = None):
        """Execute a query and return cursor."""
        if params:
            return await self.conn.execute(query, params)
        return await self.conn.execute(query)

    async def fetchone(self, query: str, params: tuple = None):
        """Execute query and fetch one row."""
        cursor = await self.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = None):
        """Execute query and fetch all rows."""
        cursor = await self.execute(query, params)
        return await cursor.fetchall()

    async def commit(self):
        """Commit transaction."""
        await self.conn.commit()

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
