import pytest
import sqlite3
from pathlib import Path
from app.database import Database


@pytest.fixture
async def test_db():
    """Create temporary test database."""
    db_path = ":memory:"
    db = Database(db_path)
    await db.init()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_database_init():
    """Database should initialize with required tables."""
    db = Database(":memory:")
    await db.init()

    # Verify tables exist
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in await cursor.fetchall()]

    assert "audit_logs" in tables
    assert "rate_limits" in tables

    await db.close()


@pytest.mark.asyncio
async def test_audit_log_insert(test_db):
    """Should insert audit log records."""
    await test_db.execute(
        "INSERT INTO audit_logs (agent_id, command, status, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("agent-1", "BUY 10 ES", "success")
    )
    await test_db.conn.commit()

    cursor = await test_db.execute("SELECT COUNT(*) FROM audit_logs")
    count = await cursor.fetchone()
    assert count[0] == 1


@pytest.mark.asyncio
async def test_rate_limit_insert(test_db):
    """Should insert rate limit records."""
    await test_db.execute(
        "INSERT INTO rate_limits (agent_id, request_count, reset_at) VALUES (?, ?, datetime('now', '+1 minute'))",
        ("agent-1", 1)
    )
    await test_db.conn.commit()

    cursor = await test_db.execute("SELECT agent_id FROM rate_limits WHERE agent_id = ?", ("agent-1",))
    row = await cursor.fetchone()
    assert row is not None
