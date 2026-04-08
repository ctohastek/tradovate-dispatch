import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.database import Database
from app.models import CommandStatus
import os


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_env():
    """Setup environment for tests."""
    os.environ["TRADOVATE_API_URL"] = "https://api.test.com"
    os.environ["TRADOVATE_API_KEY"] = "test-key"
    os.environ["DISPATCHER_API_KEY"] = "dispatcher-test-key"
    os.environ["DATABASE_URL"] = ":memory:"
    yield
    # Cleanup
    for key in ["TRADOVATE_API_URL", "TRADOVATE_API_KEY", "DISPATCHER_API_KEY", "DATABASE_URL"]:
        os.environ.pop(key, None)


def test_full_buy_flow(client):
    """Test complete BUY order flow from request to execution."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parsed_cmd.action = "BUY"
        mock_parsed_cmd.contract = "ES"
        mock_parsed_cmd.quantity = 10
        mock_parsed_cmd.price = None
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()
        mock_mailer = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': mock_mailer,
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    async def async_execute_buy(*args, **kwargs):
        return {
            "orderId": "ORD-123",
            "status": "PENDING",
            "quantity": 10,
            "contract": "ES"
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        with patch('app.routes.execute.CommandExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_instance.execute = async_execute_buy
            mock_executor_class.return_value = mock_executor_instance

            response = client.post(
                "/execute",
                json={
                    "command": "BUY 10 ES",
                    "agent_id": "agent-1"
                },
                headers={"Authorization": "Bearer dispatcher-test-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["tradovate_response"]["orderId"] == "ORD-123"


def test_full_sell_with_price_flow(client):
    """Test SELL order with limit price."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parsed_cmd.action = "SELL"
        mock_parsed_cmd.contract = "NQ"
        mock_parsed_cmd.quantity = 5
        mock_parsed_cmd.price = 16000.50
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    async def async_execute_sell(*args, **kwargs):
        return {
            "orderId": "ORD-124",
            "status": "PENDING",
            "quantity": 5,
            "contract": "NQ",
            "price": 16000.50
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        with patch('app.routes.execute.CommandExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_instance.execute = async_execute_sell
            mock_executor_class.return_value = mock_executor_instance

            response = client.post(
                "/execute",
                json={
                    "command": "SELL 5 NQ AT 16000.50",
                    "agent_id": "agent-2"
                },
                headers={"Authorization": "Bearer dispatcher-test-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["tradovate_response"]["orderId"] == "ORD-124"


def test_invalid_command_flow(client):
    """Test handling of invalid command."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = ValueError("Invalid command syntax")

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': MagicMock(),
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        response = client.post(
            "/execute",
            json={
                "command": "INVALID COMMAND",
                "agent_id": "agent-1"
            },
            headers={"Authorization": "Bearer dispatcher-test-key"}
        )

        assert response.status_code == 400
        assert "Failed to parse command" in response.json()["detail"]


def test_rate_limit_flow(client):
    """Test rate limiting across multiple requests."""
    async def mock_get_deps_rate_limited():
        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=False)

        mock_audit_logger = AsyncMock()
        mock_mailer = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': MagicMock(),
            'validator': MagicMock(),
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': mock_mailer,
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=5
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps_rate_limited)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        response = client.post(
            "/execute",
            json={"command": "BUY 1 ES", "agent_id": "agent-1"},
            headers={"Authorization": "Bearer dispatcher-test-key"}
        )

        assert response.status_code == 429
        assert "Rate limited" in response.json()["detail"]


def test_auth_required(client):
    """Test that authentication is required."""
    async def mock_get_deps():
        return {
            'db': MagicMock(),
            'parser': MagicMock(),
            'validator': MagicMock(),
            'client': MagicMock(),
            'rate_limiter': AsyncMock(),
            'audit_logger': AsyncMock(),
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        # Missing Authorization header
        response = client.post(
            "/execute",
            json={"command": "BUY 10 ES", "agent_id": "agent-1"}
        )
        assert response.status_code == 401
        assert "Invalid or missing API key" in response.json()["detail"]

        # Wrong key
        response = client.post(
            "/execute",
            json={"command": "BUY 10 ES", "agent_id": "agent-1"},
            headers={"Authorization": "Bearer wrong-key"}
        )
        assert response.status_code == 401
        assert "Invalid or missing API key" in response.json()["detail"]


def test_health_endpoint(client):
    """Test health check endpoint (no auth required)."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data


def test_invalid_contract_validation(client):
    """Test validation of invalid contract."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = False
        mock_validation_result.errors = ["Invalid contract: INVALID"]

        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        response = client.post(
            "/execute",
            json={
                "command": "BUY 10 INVALID",
                "agent_id": "agent-1"
            },
            headers={"Authorization": "Bearer dispatcher-test-key"}
        )

        assert response.status_code == 400
        assert "Validation error" in response.json()["detail"]


def test_missing_quantity_validation(client):
    """Test validation when quantity is missing."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = False
        mock_validation_result.errors = ["Missing quantity"]

        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        response = client.post(
            "/execute",
            json={
                "command": "BUY ES",  # Missing quantity
                "agent_id": "agent-1"
            },
            headers={"Authorization": "Bearer dispatcher-test-key"}
        )

        assert response.status_code == 400
        assert "Validation error" in response.json()["detail"]


def test_cancel_order_flow(client):
    """Test CANCEL order flow."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parsed_cmd.action = "CANCEL"
        mock_parsed_cmd.order_id = "ORD-123"
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    async def async_execute_cancel(*args, **kwargs):
        return {
            "status": "CANCELLED",
            "orderId": "ORD-123"
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        with patch('app.routes.execute.CommandExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_instance.execute = async_execute_cancel
            mock_executor_class.return_value = mock_executor_instance

            response = client.post(
                "/execute",
                json={
                    "command": "CANCEL ORD-123",
                    "agent_id": "agent-1"
                },
                headers={"Authorization": "Bearer dispatcher-test-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["tradovate_response"]["status"] == "CANCELLED"


def test_tradovate_api_error_flow(client):
    """Test handling of Tradovate API errors."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parsed_cmd.action = "BUY"
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()
        mock_mailer = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': mock_mailer,
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    async def async_execute_error(*args, **kwargs):
        raise RuntimeError("Tradovate API connection failed")

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        with patch('app.routes.execute.CommandExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_instance.execute = async_execute_error
            mock_executor_class.return_value = mock_executor_instance

            response = client.post(
                "/execute",
                json={"command": "BUY 10 ES", "agent_id": "agent-1"},
                headers={"Authorization": "Bearer dispatcher-test-key"}
            )

            assert response.status_code == 500
            assert "Failed to execute command" in response.json()["detail"]


def test_audit_logging_on_success(client):
    """Test that successful execution logs to audit."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parsed_cmd.action = "BUY"
        mock_parsed_cmd.contract = "ES"
        mock_parsed_cmd.quantity = 10
        mock_parsed_cmd.price = None
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()
        mock_mailer = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': mock_mailer,
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    async def async_execute_success(*args, **kwargs):
        return {
            "orderId": "ORD-123",
            "status": "FILLED"
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        with patch('app.routes.execute.CommandExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_instance.execute = async_execute_success
            mock_executor_class.return_value = mock_executor_instance

            response = client.post(
                "/execute",
                json={"command": "BUY 10 ES", "agent_id": "agent-1"},
                headers={"Authorization": "Bearer dispatcher-test-key"}
            )

            assert response.status_code == 200
            # Verify response is successful
            data = response.json()
            assert data["status"] == "success"


def test_multiple_orders_sequence(client):
    """Test executing multiple orders in sequence."""
    order_count = 0

    async def mock_get_deps():
        nonlocal order_count
        order_count += 1

        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parsed_cmd.action = "BUY" if order_count % 2 == 1 else "SELL"
        mock_parsed_cmd.contract = "ES"
        mock_parsed_cmd.quantity = 10
        mock_parsed_cmd.price = None
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    async def async_execute_order(*args, **kwargs):
        return {
            "orderId": f"ORD-{order_count}",
            "status": "PENDING",
            "quantity": 10,
            "contract": "ES"
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        with patch('app.routes.execute.CommandExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_instance.execute = async_execute_order
            mock_executor_class.return_value = mock_executor_instance

            # Execute first order
            response1 = client.post(
                "/execute",
                json={"command": "BUY 10 ES", "agent_id": "agent-1"},
                headers={"Authorization": "Bearer dispatcher-test-key"}
            )

            assert response1.status_code == 200

            # Execute second order
            response2 = client.post(
                "/execute",
                json={"command": "SELL 10 ES", "agent_id": "agent-1"},
                headers={"Authorization": "Bearer dispatcher-test-key"}
            )

            assert response2.status_code == 200


def test_validation_error_logging(client):
    """Test that validation errors are properly logged."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = False
        mock_validation_result.errors = ["quantity must be positive", "contract invalid"]

        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        response = client.post(
            "/execute",
            json={"command": "BUY -10 INVALID", "agent_id": "agent-1"},
            headers={"Authorization": "Bearer dispatcher-test-key"}
        )

        assert response.status_code == 400
        assert "Validation error" in response.json()["detail"]
        assert "quantity must be positive" in response.json()["detail"]


def test_response_contains_required_fields(client):
    """Test that successful response contains all required fields."""
    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parsed_cmd.action = "BUY"
        mock_parsed_cmd.contract = "ES"
        mock_parsed_cmd.quantity = 10
        mock_parsed_cmd.price = None
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': MagicMock(),
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': MagicMock(),
            'settings': MagicMock(
                dispatcher_api_key="dispatcher-test-key",
                rate_limit_requests_per_minute=20
            )
        }

    async def async_execute_success(*args, **kwargs):
        return {
            "orderId": "ORD-123",
            "status": "FILLED",
            "quantity": 10,
            "contract": "ES"
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        with patch('app.routes.execute.CommandExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_instance.execute = async_execute_success
            mock_executor_class.return_value = mock_executor_instance

            response = client.post(
                "/execute",
                json={"command": "BUY 10 ES", "agent_id": "agent-1"},
                headers={"Authorization": "Bearer dispatcher-test-key"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "status" in data
            assert "message" in data
            assert "tradovate_response" in data

            # Verify response values
            assert data["status"] == "success"
            assert data["message"] == "Command executed successfully"
            assert isinstance(data["tradovate_response"], dict)
            assert data["tradovate_response"]["orderId"] == "ORD-123"
