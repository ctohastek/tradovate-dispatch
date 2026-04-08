# tests/test_tradovate_commands.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.tradovate.commands import CommandExecutor
from app.models import ParsedCommand


@pytest.mark.asyncio
async def test_execute_buy_command():
    """Should map ParsedCommand BUY to Tradovate API call."""
    mock_client = AsyncMock()
    mock_client.buy = AsyncMock(return_value={"orderId": "ORD-1", "status": "PENDING"})

    executor = CommandExecutor(mock_client)
    cmd = ParsedCommand(action="BUY", contract="ES", quantity=10)

    result = await executor.execute(cmd)

    assert result["orderId"] == "ORD-1"
    mock_client.buy.assert_called_once_with(contract="ES", quantity=10, price=None)


@pytest.mark.asyncio
async def test_execute_sell_with_price():
    """Should map SELL command with limit price."""
    mock_client = AsyncMock()
    mock_client.sell = AsyncMock(return_value={"orderId": "ORD-2"})

    executor = CommandExecutor(mock_client)
    cmd = ParsedCommand(action="SELL", contract="NQ", quantity=5, price=16000.5)

    result = await executor.execute(cmd)

    mock_client.sell.assert_called_once_with(
        contract="NQ", quantity=5, price=16000.5
    )


@pytest.mark.asyncio
async def test_execute_cancel_command():
    """Should map CANCEL command."""
    mock_client = AsyncMock()
    mock_client.cancel = AsyncMock(return_value={"status": "CANCELLED"})

    executor = CommandExecutor(mock_client)
    cmd = ParsedCommand(action="CANCEL", contract="ES", order_id="ORD-123")

    result = await executor.execute(cmd)

    mock_client.cancel.assert_called_once_with("ORD-123")


@pytest.mark.asyncio
async def test_execute_status_command():
    """Should map STATUS command."""
    mock_client = AsyncMock()
    mock_client.get_order_status = AsyncMock(
        return_value={"orderId": "ORD-123", "status": "FILLED"}
    )

    executor = CommandExecutor(mock_client)
    cmd = ParsedCommand(action="STATUS", contract="ES", order_id="ORD-123")

    result = await executor.execute(cmd)

    mock_client.get_order_status.assert_called_once_with("ORD-123")


@pytest.mark.asyncio
async def test_execute_help_command():
    """Should return help text for HELP command."""
    mock_client = AsyncMock()
    executor = CommandExecutor(mock_client)
    cmd = ParsedCommand(action="HELP", contract="ES")

    result = await executor.execute(cmd)

    assert isinstance(result, dict)
    assert "help" in result or "commands" in result
