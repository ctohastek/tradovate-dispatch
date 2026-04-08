# tests/test_models.py
import pytest
from pydantic import ValidationError
from app.models import (
    CommandRequest, CommandResponse, AuditLog,
    CommandStatus, ParsedCommand
)


def test_command_request_valid():
    """Should validate valid command request."""
    req = CommandRequest(
        command="BUY 10 ES",
        agent_id="agent-1"
    )
    assert req.command == "BUY 10 ES"
    assert req.agent_id == "agent-1"


def test_command_request_missing_fields():
    """Should reject command request with missing fields."""
    with pytest.raises(ValidationError):
        CommandRequest(command="BUY 10 ES")  # Missing agent_id


def test_command_response_success():
    """Should create success response."""
    resp = CommandResponse(
        status=CommandStatus.SUCCESS,
        message="Order placed",
        order_id="ORD-123"
    )
    assert resp.status == CommandStatus.SUCCESS
    assert resp.order_id == "ORD-123"


def test_parsed_command():
    """Should validate parsed command structure."""
    cmd = ParsedCommand(
        action="BUY",
        contract="ES",
        quantity=10,
        price=None
    )
    assert cmd.action == "BUY"
    assert cmd.quantity == 10


def test_audit_log():
    """Should validate audit log."""
    log = AuditLog(
        agent_id="agent-1",
        command="BUY 10 ES",
        status=CommandStatus.SUCCESS,
        parsed_command="BUY ES 10"
    )
    assert log.agent_id == "agent-1"
    assert log.status == CommandStatus.SUCCESS
