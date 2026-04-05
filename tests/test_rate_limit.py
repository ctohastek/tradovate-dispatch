import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from app.rate_limit.limiter import RateLimiter
from app.database import Database


@pytest.mark.asyncio
async def test_rate_limit_init():
    db = Database(":memory:")
    await db.init()

    limiter = RateLimiter(db, requests_per_minute=30)
    assert limiter.requests_per_minute == 30

    await db.close()


@pytest.mark.asyncio
async def test_allow_first_request():
    db = Database(":memory:")
    await db.init()
    limiter = RateLimiter(db, requests_per_minute=30)

    allowed = await limiter.is_allowed("agent-1")
    assert allowed is True

    await db.close()


@pytest.mark.asyncio
async def test_allow_within_limit():
    db = Database(":memory:")
    await db.init()
    limiter = RateLimiter(db, requests_per_minute=30)

    for i in range(15):
        allowed = await limiter.is_allowed("agent-1")
        assert allowed is True

    await db.close()


@pytest.mark.asyncio
async def test_reject_over_limit():
    db = Database(":memory:")
    await db.init()
    limiter = RateLimiter(db, requests_per_minute=5)

    for i in range(5):
        allowed = await limiter.is_allowed("agent-1")
        assert allowed is True

    allowed = await limiter.is_allowed("agent-1")
    assert allowed is False

    await db.close()


@pytest.mark.asyncio
async def test_rate_limit_different_agents():
    db = Database(":memory:")
    await db.init()
    limiter = RateLimiter(db, requests_per_minute=3)

    for i in range(3):
        assert await limiter.is_allowed("agent-1") is True

    assert await limiter.is_allowed("agent-2") is True

    await db.close()
