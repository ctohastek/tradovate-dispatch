# app/tradovate/client.py
import httpx
from typing import Optional, Dict, Any
from app.config import Settings


class TradovateClient:
    """Async HTTP client for Tradovate API per Tradovate REST API spec."""

    # Valid orderType values per Tradovate spec
    VALID_ORDER_TYPES = {
        "Limit", "MIT", "Market", "QTS", "Stop",
        "StopLimit", "TrailingStop", "TrailingStopLimit"
    }

    def __init__(self, settings: Settings, environment: str = "DEMO", agent_name: Optional[str] = None, app_id: Optional[str] = None):
        """
        Initialize Tradovate client.

        Args:
            settings: Application settings with API URLs and credentials
            environment: "LIVE" or "DEMO" to select endpoint
            agent_name: Agent name to get per-agent credentials (e.g., 'mini01')
            app_id: Tradovate API appId (nickname of API key from agents.yaml)
        """
        self.settings = settings
        self.agent_name = agent_name
        self.app_id = app_id
        self.environment = environment.upper()

        if self.environment == "LIVE":
            self.api_url = settings.tradovate_live_url
        else:
            self.api_url = settings.tradovate_demo_url

        # Get agent-specific Tradovate credentials
        if agent_name:
            agent_config = settings.get_agent_tradovate_config(agent_name)
            self.api_key = agent_config.get("api_key")  # sec (API secret)
            self.client_id = agent_config.get("client_id")  # cid
        else:
            self.api_key = settings.tradovate_api_key
            self.client_id = None

        # Shared credentials for auth
        self.account_name = settings.tradovate_account_name
        self.account_pass = settings.tradovate_account_pass
        self.device_id = settings.tradovate_device_id

        self.http_client = httpx.AsyncClient()
        self._access_token: Optional[str] = None
        self._headers: Dict[str, str] = {
            "Content-Type": "application/json"
        }

        # Account info (fetched via initialize())
        self.account_id: Optional[int] = None
        self.account_spec: Optional[str] = None

    async def initialize(self) -> None:
        """Authenticate and fetch account info. Must be called before placing orders."""
        try:
            # Step 1: Get access token via auth flow
            self._access_token = await self._get_access_token()
            self._headers["Authorization"] = f"Bearer {self._access_token}"

            # Step 2: Fetch account list
            accounts = await self._request("GET", "/account/list")
            if not accounts:
                raise Exception("No accounts found for authenticated user")

            # Step 3: Use first account
            account = accounts[0]
            self.account_id = account.get("id")
            self.account_spec = account.get("name")
            if not self.account_id or not self.account_spec:
                raise Exception("Account missing id or name")
        except Exception as e:
            raise Exception(f"Failed to initialize: {str(e)}")

    async def _get_access_token(self) -> str:
        """Request access token using account + agent API credentials."""
        if not all([self.account_name, self.account_pass, self.api_key, self.client_id, self.device_id]):
            raise Exception("Missing required auth credentials: account_name, account_pass, api_key, client_id, device_id")

        payload = {
            "name": self.account_name,  # Account name (e.g., mini01)
            "password": self.account_pass,  # Password set during API key creation
            "cid": self.client_id,
            "sec": self.api_key,
            "deviceId": self.device_id,
            "appId": self.app_id or "TradovateDispatcher",
            "appVersion": "1.0"
        }

        base_url = self.api_url.rstrip('/')
        url = f"{base_url}/auth/accesstokenrequest"

        try:
            response = await self.http_client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            # Check for rate limit response
            if "p-ticket" in result or "p-time" in result:
                raise Exception(
                    f"Rate limited: wait {result.get('p-time', '?')} seconds. "
                    f"p-ticket: {result.get('p-ticket', 'N/A')}"
                )

            if "errorText" in result and result["errorText"]:
                raise Exception(f"Auth error: {result['errorText']}")

            if "accessToken" not in result:
                raise Exception("No accessToken in response")

            return result["accessToken"]
        except httpx.HTTPError as e:
            raise Exception(f"Auth request failed: {str(e)}")

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
            endpoint: API endpoint path (e.g., "/order/placeorder")
            json: Request body as dict

        Returns:
            Response JSON

        Raises:
            Exception: If request fails
        """
        base_url = self.api_url.rstrip('/')
        url = f"{base_url}{endpoint}"

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

    def _validate_order_type(self, order_type: str) -> None:
        """Validate orderType against Tradovate spec."""
        if order_type not in self.VALID_ORDER_TYPES:
            raise ValueError(
                f"Invalid orderType '{order_type}'. Must be one of: {', '.join(sorted(self.VALID_ORDER_TYPES))}"
            )

    async def buy(
        self,
        symbol: str,
        orderQty: int,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place BUY order per Tradovate PlaceOrder spec.

        Args:
            symbol: Contract symbol (ES, NQ, etc.)
            orderQty: Number of contracts
            price: Limit price (optional, None = market order)

        Returns:
            Order response from Tradovate
        """
        orderType = "Limit" if price is not None else "Market"
        self._validate_order_type(orderType)

        payload = {
            "accountSpec": self.account_spec,
            "accountId": self.account_id,
            "action": "Buy",
            "symbol": symbol,
            "orderQty": orderQty,
            "orderType": orderType,
            "isAutomated": True
        }

        if price is not None:
            payload["price"] = price

        return await self._request("POST", "/order/placeorder", json=payload)

    async def sell(
        self,
        symbol: str,
        orderQty: int,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place SELL order per Tradovate PlaceOrder spec.

        Args:
            symbol: Contract symbol
            orderQty: Number of contracts
            price: Limit price (optional, None = market order)

        Returns:
            Order response from Tradovate
        """
        orderType = "Limit" if price is not None else "Market"
        self._validate_order_type(orderType)

        payload = {
            "accountSpec": self.account_spec,
            "accountId": self.account_id,
            "action": "Sell",
            "symbol": symbol,
            "orderQty": orderQty,
            "orderType": orderType,
            "isAutomated": True
        }

        if price is not None:
            payload["price"] = price

        return await self._request("POST", "/order/placeorder", json=payload)

    async def place_oco(
        self,
        symbol: str,
        orderQty: int,
        action: str,
        orderType: str,
        other: Dict[str, Any],
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place One-Cancels-Other (OCO) order per Tradovate PlaceOCO spec.

        OCO orders link 2 orders together such that if one fills, the other is cancelled.

        Args:
            symbol: Contract symbol
            orderQty: Quantity for primary order
            action: "Buy" or "Sell"
            orderType: Order type (Limit, Stop, etc.)
            other: Secondary order specification dict
            price: Price for primary order (if applicable)

        Returns:
            Order response with orderId and ocoId
        """
        self._validate_order_type(orderType)

        payload = {
            "accountSpec": self.account_spec,
            "accountId": self.account_id,
            "action": action,
            "symbol": symbol,
            "orderQty": orderQty,
            "orderType": orderType,
            "other": other,
            "isAutomated": True
        }

        if price is not None:
            payload["price"] = price

        return await self._request("POST", "/order/placeoco", json=payload)

    async def place_oso(
        self,
        symbol: str,
        orderQty: int,
        action: str,
        orderType: str,
        bracket1: Dict[str, Any],
        price: Optional[float] = None,
        bracket2: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Place One-Sends-Other (OSO) bracket order per Tradovate PlaceOSO spec.

        OSO orders (bracket orders) link 3 orders: primary order with 2 bracket orders.

        Args:
            symbol: Contract symbol
            orderQty: Quantity for primary order
            action: "Buy" or "Sell"
            orderType: Order type
            bracket1: First bracket order (e.g., take profit)
            price: Price for primary order (if applicable)
            bracket2: Optional second bracket order (e.g., stop loss)

        Returns:
            Order response with orderId and osoId
        """
        self._validate_order_type(orderType)

        payload = {
            "accountSpec": self.account_spec,
            "accountId": self.account_id,
            "action": action,
            "symbol": symbol,
            "orderQty": orderQty,
            "orderType": orderType,
            "bracket1": bracket1,
            "isAutomated": True
        }

        if price is not None:
            payload["price"] = price

        if bracket2 is not None:
            payload["bracket2"] = bracket2

        return await self._request("POST", "/order/placeoso", json=payload)

    async def modify_order(
        self,
        orderId: int,
        orderQty: int,
        orderType: str,
        price: Optional[float] = None,
        stopPrice: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Modify existing order per Tradovate ModifyOrder spec.

        Args:
            orderId: Tradovate order ID
            orderQty: New order quantity
            orderType: New order type
            price: New limit price (if applicable)
            stopPrice: New stop price (if applicable)

        Returns:
            Modified order response
        """
        self._validate_order_type(orderType)

        payload = {
            "accountSpec": self.account_spec,
            "accountId": self.account_id,
            "orderId": orderId,
            "orderQty": orderQty,
            "orderType": orderType,
            "isAutomated": True
        }

        if price is not None:
            payload["price"] = price

        if stopPrice is not None:
            payload["stopPrice"] = stopPrice

        return await self._request("POST", "/order/modifyorder", json=payload)

    async def cancel(self, orderId: int) -> Dict[str, Any]:
        """
        Cancel existing order per Tradovate CancelOrder spec.

        Args:
            orderId: Tradovate order ID

        Returns:
            Cancellation response
        """
        payload = {
            "accountSpec": self.account_spec,
            "accountId": self.account_id,
            "orderId": orderId
        }
        return await self._request("POST", "/order/cancelorder", json=payload)

    async def get_order_status(self, orderId: int) -> Dict[str, Any]:
        """
        Get order status.

        Args:
            orderId: Tradovate order ID

        Returns:
            Order details
        """
        return await self._request("GET", f"/order/{orderId}")

    async def close(self):
        """Close HTTP client connection."""
        await self.http_client.aclose()
