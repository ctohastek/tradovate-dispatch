# tests/test_validator.py
import pytest
from app.parser.validator import CommandValidator
from app.models import ParsedCommand


def test_validate_buy_command():
    """Should validate correct BUY command."""
    validator = CommandValidator()
    cmd = ParsedCommand(action="BUY", contract="ES", quantity=10)

    result = validator.validate(cmd)
    assert result.is_valid is True
    assert result.errors == []


def test_validate_buy_missing_quantity():
    """Should reject BUY without quantity."""
    validator = CommandValidator()
    cmd = ParsedCommand(action="BUY", contract="ES", quantity=None)

    result = validator.validate(cmd)
    assert result.is_valid is False
    assert "quantity" in str(result.errors).lower()


def test_validate_buy_invalid_quantity():
    """Should reject BUY with zero or negative quantity."""
    validator = CommandValidator()
    cmd = ParsedCommand(action="BUY", contract="ES", quantity=0)

    result = validator.validate(cmd)
    assert result.is_valid is False


def test_validate_buy_invalid_price():
    """Should reject BUY with invalid price."""
    validator = CommandValidator()
    # Price > MAX_PRICE should fail validation
    cmd = ParsedCommand(action="BUY", contract="ES", quantity=10, price=2_000_000)

    result = validator.validate(cmd)
    assert result.is_valid is False


def test_validate_cancel_missing_order_id():
    """Should reject CANCEL without order_id."""
    validator = CommandValidator()
    cmd = ParsedCommand(action="CANCEL", contract="ES")

    result = validator.validate(cmd)
    assert result.is_valid is False
    assert "order" in str(result.errors).lower()


def test_validate_unknown_contract():
    """Should reject unknown contract symbol."""
    validator = CommandValidator()
    cmd = ParsedCommand(action="BUY", contract="INVALID", quantity=10)

    result = validator.validate(cmd)
    assert result.is_valid is False
    assert "contract" in str(result.errors).lower()


def test_validate_sell_command():
    """Should validate correct SELL command."""
    validator = CommandValidator()
    cmd = ParsedCommand(action="SELL", contract="NQ", quantity=5)

    result = validator.validate(cmd)
    assert result.is_valid is True
