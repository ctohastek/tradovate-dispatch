# app/tradovate/commands.py
from app.models import ParsedCommand
from app.tradovate.client import TradovateClient
from typing import Dict, Any


class CommandExecutor:
    """Map parsed commands to Tradovate API calls."""

    HELP_TEXT = """
    Supported Commands:

    BUY <qty> <contract> [AT <price>]
        Place a buy order
        Example: BUY 10 ES
        Example: BUY 5 NQ AT 16000.50

    SELL <qty> <contract> [AT <price>]
        Place a sell order
        Example: SELL 10 ES

    CANCEL <order_id>
        Cancel an existing order
        Example: CANCEL ORD-123

    STATUS [order_id]
        Get order status
        Example: STATUS ORD-123

    HELP
        Display this help message

    Supported Contracts: ES, NQ, YM, RTY, MES, MNQ, MYM, MRTY
    """

    def __init__(self, client: TradovateClient):
        self.client = client

    async def execute(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        Execute parsed command via Tradovate API.

        Args:
            command: Parsed trading command

        Returns:
            API response as dict

        Raises:
            Exception: If execution fails
        """
        action = command.action

        if action == "BUY":
            return await self.client.buy(
                symbol=command.contract,
                orderQty=command.quantity,
                price=command.price
            )

        elif action == "SELL":
            return await self.client.sell(
                symbol=command.contract,
                orderQty=command.quantity,
                price=command.price
            )

        elif action == "CANCEL":
            return await self.client.cancel(orderId=int(command.order_id))

        elif action == "STATUS":
            if command.order_id:
                return await self.client.get_order_status(orderId=int(command.order_id))
            else:
                return {"error": "Order ID required for STATUS"}

        elif action == "HELP":
            return {"help": self.HELP_TEXT}

        else:
            raise ValueError(f"Unknown action: {action}")
