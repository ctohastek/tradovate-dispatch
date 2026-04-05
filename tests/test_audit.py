import pytest
from app.logging.audit import AuditLogger
from app.models import CommandStatus
from app.database import Database


@pytest.mark.asyncio
async def test_audit_log_success():
    db = Database(":memory:")
    await db.init()

    logger = AuditLogger(db)

    await logger.log(
        agent_id="agent-1",
        command="BUY 10 ES",
        status=CommandStatus.SUCCESS,
        parsed_command="BUY ES 10",
        response='{"orderId": "ORD-123"}'
    )

    rows = await db.fetchall("SELECT * FROM audit_logs WHERE agent_id = 'agent-1'")
    assert len(rows) == 1

    await db.close()


@pytest.mark.asyncio
async def test_audit_log_error():
    db = Database(":memory:")
    await db.init()

    logger = AuditLogger(db)

    await logger.log(
        agent_id="agent-1",
        command="INVALID",
        status=CommandStatus.PARSER_ERROR,
        error_message="Failed to parse command"
    )

    rows = await db.fetchall(
        "SELECT status, error_message FROM audit_logs WHERE agent_id = 'agent-1'"
    )
    assert len(rows) == 1
    assert rows[0][0] == "parser_error"
    assert "parse" in rows[0][1].lower()

    await db.close()


@pytest.mark.asyncio
async def test_audit_query_by_agent():
    db = Database(":memory:")
    await db.init()
    logger = AuditLogger(db)

    for i in range(3):
        await logger.log(
            agent_id="agent-1",
            command=f"BUY {i+1} ES",
            status=CommandStatus.SUCCESS
        )

    logs = await logger.get_logs_by_agent("agent-1", limit=10)
    assert len(logs) == 3

    await db.close()


@pytest.mark.asyncio
async def test_audit_query_by_status():
    db = Database(":memory:")
    await db.init()
    logger = AuditLogger(db)

    await logger.log("agent-1", "BUY 10 ES", CommandStatus.SUCCESS)
    await logger.log("agent-1", "BAD", CommandStatus.PARSER_ERROR)
    await logger.log("agent-1", "CANCEL X", CommandStatus.VALIDATION_ERROR)

    errors = await logger.get_logs_by_status(CommandStatus.PARSER_ERROR)
    assert len(errors) == 1

    await db.close()
