# app/parser/parser.py
import re
from lark import Lark, Transformer, v_args
from app.models import ParsedCommand
from pathlib import Path


class CommandTransformer(Transformer):
    """Transform Lark parse tree into ParsedCommand."""

    def NUMBER(self, token):
        value = str(token)
        return float(value) if '.' in value else int(value)

    def CONTRACT(self, token):
        return str(token).upper()

    def quantity(self, items):
        return items[0]

    def contract(self, items):
        return items[0]

    def price(self, items):
        # items contains AT token and the NUMBER
        # Filter out tokens and return the number
        for item in items:
            if isinstance(item, (int, float)):
                return item
        return items[-1] if items else None

    def order_id(self, items):
        # items[0] is a Token with the order_id value
        value = str(items[0])
        return value.upper()

    def buy(self, items):
        data = {"action": "BUY"}
        for item in items:
            if isinstance(item, int):
                data["quantity"] = item
            elif isinstance(item, str):
                data["contract"] = item
            elif isinstance(item, float):
                data["price"] = item
        return data

    def sell(self, items):
        data = {"action": "SELL"}
        for item in items:
            if isinstance(item, int):
                data["quantity"] = item
            elif isinstance(item, str):
                data["contract"] = item
            elif isinstance(item, float):
                data["price"] = item
        return data

    def cancel(self, items):
        # items contains the CANCEL token and the order_id
        order_id = None
        for item in items:
            if isinstance(item, str):
                order_id = item
        return {"action": "CANCEL", "order_id": order_id}

    def status(self, items):
        # items contains the STATUS token and optionally the order_id
        data = {"action": "STATUS"}
        for item in items:
            if isinstance(item, str):
                data["order_id"] = item
        return data

    def help(self, items):
        return {"action": "HELP"}

    def command(self, items):
        return items[0]


class CommandParser:
    """Parse natural language trading commands using Lark grammar."""

    def __init__(self):
        grammar_path = Path(__file__).parent / "grammar.lark"
        with open(grammar_path) as f:
            grammar = f.read()

        self.parser = Lark(
            grammar,
            parser='lalr',
            transformer=CommandTransformer(),
            propagate_positions=False
        )

    def parse(self, command: str) -> ParsedCommand:
        """
        Parse natural language command into ParsedCommand.

        Args:
            command: Raw command string (e.g., "BUY 10 ES AT 4500")

        Returns:
            ParsedCommand with structured data

        Raises:
            Exception: If command is invalid
        """
        try:
            tree = self.parser.parse(command.strip())
            return ParsedCommand(**tree)
        except Exception as e:
            raise ValueError(f"Failed to parse command '{command}': {str(e)}")
