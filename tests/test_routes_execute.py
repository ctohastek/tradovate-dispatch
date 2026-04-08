import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


def test_execute_missing_auth():
    """Test that request without auth header returns 401."""

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
                dispatcher_api_key="test-key",
                rate_limit_requests_per_minute=20
            )
        }

    # Use AsyncMock which returns a coroutine
    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/execute",
            json={"command": "BUY 10 ES", "agent_id": "agent-1"}
        )

        assert response.status_code == 401
        assert "Invalid or missing API key" in response.json()["detail"]


def test_execute_invalid_auth():
    """Test that request with invalid auth header returns 401."""

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
                dispatcher_api_key="test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/execute",
            json={"command": "BUY 10 ES", "agent_id": "agent-1"},
            headers={"Authorization": "Bearer wrong-key"}
        )

        assert response.status_code == 401
        assert "Invalid or missing API key" in response.json()["detail"]


def test_execute_missing_fields():
    """Test that missing required fields returns validation error."""

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
                dispatcher_api_key="test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/execute",
            json={"command": "BUY 10 ES"},  # Missing agent_id
            headers={"Authorization": "Bearer test-key"}
        )

        assert response.status_code == 422  # Pydantic validation error


def test_execute_rate_limited():
    """Test rate limiting enforcement."""

    async def mock_get_deps():
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
                dispatcher_api_key="test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/execute",
            json={"command": "BUY 10 ES", "agent_id": "agent-1"},
            headers={"Authorization": "Bearer test-key"}
        )

        assert response.status_code == 429
        assert "Rate limited" in response.json()["detail"]


def test_execute_parser_error():
    """Test handling of parser errors."""

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
                dispatcher_api_key="test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/execute",
            json={"command": "INVALID COMMAND", "agent_id": "agent-1"},
            headers={"Authorization": "Bearer test-key"}
        )

        assert response.status_code == 400
        assert "Failed to parse command" in response.json()["detail"]


def test_execute_validation_error():
    """Test handling of validation errors."""

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
                dispatcher_api_key="test-key",
                rate_limit_requests_per_minute=20
            )
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/execute",
            json={"command": "BUY -10 INVALID", "agent_id": "agent-1"},
            headers={"Authorization": "Bearer test-key"}
        )

        assert response.status_code == 400
        assert "Validation error" in response.json()["detail"]


def test_execute_tradovate_error():
    """Test handling of Tradovate API errors."""

    async def mock_get_deps():
        mock_parser = MagicMock()
        mock_parsed_cmd = MagicMock()
        mock_parser.parse.return_value = mock_parsed_cmd

        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True

        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_validation_result

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.is_allowed = AsyncMock(return_value=True)

        mock_audit_logger = AsyncMock()
        mock_mailer = AsyncMock()

        mock_client = MagicMock()

        return {
            'db': MagicMock(),
            'parser': mock_parser,
            'validator': mock_validator,
            'client': mock_client,
            'rate_limiter': mock_rate_limiter,
            'audit_logger': mock_audit_logger,
            'mailer': mock_mailer,
            'settings': MagicMock(
                dispatcher_api_key="test-key",
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

            from app.main import app
            client = TestClient(app)
            response = client.post(
                "/execute",
                json={"command": "BUY 10 ES", "agent_id": "agent-1"},
                headers={"Authorization": "Bearer test-key"}
            )

            assert response.status_code == 500
            assert "Failed to execute command" in response.json()["detail"]


def test_execute_success():
    """Test successful command execution."""

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
                dispatcher_api_key="test-key",
                rate_limit_requests_per_minute=20
            )
        }

    async def async_execute_success(*args, **kwargs):
        return {
            "order_id": "ORD-123",
            "status": "FILLED",
            "quantity": 10,
            "contract": "ES",
            "price": 5000.50
        }

    mock_dep_fn = AsyncMock(side_effect=mock_get_deps)

    with patch('app.routes.execute.get_dependencies', mock_dep_fn):
        with patch('app.routes.execute.CommandExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_instance.execute = async_execute_success
            mock_executor_class.return_value = mock_executor_instance

            from app.main import app
            client = TestClient(app)
            response = client.post(
                "/execute",
                json={"command": "BUY 10 ES", "agent_id": "agent-1"},
                headers={"Authorization": "Bearer test-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Command executed successfully"
            assert "tradovate_response" in data
            assert data["tradovate_response"]["order_id"] == "ORD-123"
