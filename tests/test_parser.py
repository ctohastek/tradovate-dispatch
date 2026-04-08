# tests/test_parser.py
import pytest
from app.parser import CommandParser
from app.models import ParsedCommand


def test_parse_buy_command():
    """Should parse BUY command with quantity and contract."""
    parser = CommandParser()
    result = parser.parse("BUY 10 ES")

    assert result.action == "BUY"
    assert result.contract == "ES"
    assert result.quantity == 10


def test_parse_sell_command():
    """Should parse SELL command."""
    parser = CommandParser()
    result = parser.parse("SELL 5 NQ")

    assert result.action == "SELL"
    assert result.contract == "NQ"
    assert result.quantity == 5


def test_parse_buy_with_price():
    """Should parse BUY command with limit price."""
    parser = CommandParser()
    result = parser.parse("BUY 10 ES AT 4500.50")

    assert result.action == "BUY"
    assert result.quantity == 10
    assert result.price == 4500.50


def test_parse_cancel_command():
    """Should parse CANCEL command."""
    parser = CommandParser()
    result = parser.parse("CANCEL ORD-12345")

    assert result.action == "CANCEL"
    assert result.order_id == "ORD-12345"


def test_parse_status_command():
    """Should parse STATUS command."""
    parser = CommandParser()
    result = parser.parse("STATUS ORD-12345")

    assert result.action == "STATUS"
    assert result.order_id == "ORD-12345"


def test_parse_invalid_command():
    """Should raise exception on invalid command."""
    parser = CommandParser()

    with pytest.raises(Exception):
        parser.parse("INVALID COMMAND HERE")


def test_parse_case_insensitive():
    """Parser should be case-insensitive for keywords."""
    parser = CommandParser()
    result = parser.parse("buy 10 es")

    assert result.action == "BUY"
    assert result.contract == "ES"
