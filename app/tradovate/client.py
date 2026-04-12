# app/tradovate/client.py
import httpx
from typing import Optional, Dict, Any
from app.config import Settings


class TradovateClient:
    """Async HTTP client for Tradovate API."""

    def __init__(self, settings: Settings, environment: str = "DEMO"):
        """
        Initialize Tradovate client.

        Args:
            settings: Application settings with API URLs
            environment: "LIVE" or "DEMO" to select endpoint
        """
        if environment.upper() == "LIVE":
            self.api_url = settings.tradovate_live_url
        else:
            self.api_url = settings.tradovate_demo_url

        self.api_key = settings.tradovate_api_key
        self.http_client = httpx.AsyncClient()
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Tradovate API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., "/orders/place")
            json: Request body as dict

        Returns:
            Response JSON

        Raises:
            Exception: If request fails
        """
        url = f"{self.api_url}{endpoint}"

        try:
            response = await self.http_client.request(
                method,
                url,
                json=json,
                headers=self._headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Tradovate API error: {str(e)}")

    async def buy(
        self,
        contract: str,
        quantity: int,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place BUY order.

        Args:
            contract: Contract symbol (ES, NQ, etc.)
            quantity: Number of contracts
            price: Limit price (optional, None = market order)

        Returns:
            Order response from Tradovate
        """
        payload = {
            "contract": contract,
            "quantity": quantity,
            "side": "BUY"
        }

        if price is not None:
            payload["price"] = price
            payload["orderType"] = "LIMIT"
        else:
            payload["orderType"] = "MARKET"

        return await self._request("POST", "/orders/place", json=payload)

    async def sell(
        self,
        contract: str,
        quantity: int,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place SELL order.

        Args:
            contract: Contract symbol
            quantity: Number of contracts
            price: Limit price (optional)

        Returns:
            Order response from Tradovate
        """
        payload = {
            "contract": contract,
            "quantity": quantity,
            "side": "SELL"
        }

        if price is not None:
            payload["price"] = price
            payload["orderType"] = "LIMIT"
        else:
            payload["orderType"] = "MARKET"

        return await self._request("POST", "/orders/place", json=payload)

    async def cancel(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel existing order.

        Args:
            order_id: Tradovate order ID

        Returns:
            Cancellation response
        """
        payload = {"orderId": order_id}
        return await self._request("POST", "/orders/cancel", json=payload)

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get order status.

        Args:
            order_id: Tradovate order ID

        Returns:
            Order details
        """
        return await self._request("GET", f"/orders/{order_id}")

    async def close(self):
        """Close HTTP client connection."""
        await self.http_client.aclose()
