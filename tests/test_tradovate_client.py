# tests/test_tradovate_client.py
import pytest
from unittest.mock import AsyncMock, patch
from app.tradovate.client import TradovateClient
from app.config import Settings


@pytest.mark.asyncio
async def test_tradovate_client_init_demo():
    """Should initialize Tradovate client with DEMO environment."""
    settings = Settings()
    settings.tradovate_demo_url = "https://demo.tradovateapi.com/"
    settings.tradovate_api_key = "test-key"

    client = TradovateClient(settings, environment="DEMO")
    assert client.api_url == "https://demo.tradovateapi.com/"
    assert client.api_key == "test-key"


@pytest.mark.asyncio
async def test_tradovate_client_init_live():
    """Should initialize Tradovate client with LIVE environment."""
    settings = Settings()
    settings.tradovate_live_url = "https://live.tradovateapi.com/"
    settings.tradovate_api_key = "test-key"

    client = TradovateClient(settings, environment="LIVE")
    assert client.api_url == "https://live.tradovateapi.com/"
    assert client.api_key == "test-key"


@pytest.mark.asyncio
async def test_tradovate_client_buy_order():
    """Should execute BUY order via API."""
    settings = Settings()
    settings.tradovate_demo_url = "https://demo.tradovateapi.com/"
    settings.tradovate_api_key = "test-key"

    client = TradovateClient(settings, environment="DEMO")

    # Mock the HTTP request
    with patch.object(client.http_client, 'request', new_callable=AsyncMock) as mock_request:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        # json() is not async in httpx, but mock needs to handle the call
        mock_response.json = lambda: {"orderId": "ORD-123", "status": "PENDING"}
        # raise_for_status() should be a regular method, not async
        mock_response.raise_for_status = lambda: None
        mock_request.return_value = mock_response

        result = await client.buy(symbol="ES", orderQty=10, price=None)

        assert result["orderId"] == "ORD-123"
        assert result["status"] == "PENDING"


@pytest.mark.asyncio
async def test_tradovate_client_close():
    """Should close HTTP client on shutdown."""
    settings = Settings()
    settings.tradovate_demo_url = "https://demo.tradovateapi.com/"
    settings.tradovate_api_key = "test-key"

    client = TradovateClient(settings, environment="DEMO")

    with patch.object(client.http_client, 'aclose', new_callable=AsyncMock) as mock_close:
        await client.close()
        mock_close.assert_called_once()
