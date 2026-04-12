from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
import yaml
import os
from app.models import CommandRequest, CommandResponse, CommandStatus
from app.auth.api_key import validate_api_key, get_api_key_from_header
from app.parser import CommandParser, CommandValidator
from app.tradovate import TradovateClient
from app.tradovate.commands import CommandExecutor
from app.rate_limit import RateLimiter
from app.alerts import AlertMailer
from app.logging import AuditLogger
from app.database import Database
from app.config import get_settings

router = APIRouter(tags=["execute"])

# Module-level dependency cache for single instantiation
_db = None
_parser = None
_validator = None
_rate_limiter = None
_audit_logger = None
_mailer = None
_settings = None
_agents_config = None


def _load_agents_config() -> Dict[str, Any]:
    """Load agents configuration from agents.yaml or agents.yaml.example."""
    global _agents_config

    if _agents_config is not None:
        return _agents_config

    config_path = "agents.yaml"
    if not os.path.exists(config_path):
        config_path = "agents.yaml.example"

    if not os.path.exists(config_path):
        _agents_config = {"agents": {}}
        return _agents_config

    with open(config_path, "r") as f:
        _agents_config = yaml.safe_load(f) or {"agents": {}}

    return _agents_config


async def get_dependencies(agent_id: Optional[str] = None):
    """Initialize and return all dependencies."""
    global _db, _parser, _validator, _rate_limiter, _audit_logger, _mailer, _settings

    if _settings is None:
        _settings = get_settings()

    if _db is None:
        _db = Database(_settings.database_url)
        await _db.init()

    if _parser is None:
        _parser = CommandParser()

    if _validator is None:
        _validator = CommandValidator()

    if _rate_limiter is None:
        _rate_limiter = RateLimiter(_db, _settings.rate_limit_requests_per_minute)

    if _audit_logger is None:
        _audit_logger = AuditLogger(_db)

    if _mailer is None:
        _mailer = AlertMailer(_settings)

    # Load agent config and create client with agent's environment
    agents_config = _load_agents_config()
    agent_env = "DEMO"  # default
    if agent_id and agent_id in agents_config.get("agents", {}):
        agent_env = agents_config["agents"][agent_id].get("environment", "DEMO")

    client = TradovateClient(_settings, environment=agent_env)

    return {
        'db': _db,
        'parser': _parser,
        'validator': _validator,
        'client': client,
        'rate_limiter': _rate_limiter,
        'audit_logger': _audit_logger,
        'mailer': _mailer,
        'settings': _settings
    }


@router.post("/execute", response_model=CommandResponse)
async def execute_command(
    request: CommandRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Execute a trading command through the full pipeline.

    Authenticates the request, parses and validates the command, executes it
    through the Tradovate API, and logs all activity for audit purposes.

    Args:
        request: CommandRequest with command and agent_id
        authorization: Bearer token for authentication

    Returns:
        CommandResponse with execution result and status

    Raises:
        HTTPException: For authentication, validation, rate limit, or execution errors
    """
    agent_id = request.agent_id
    command = request.command

    # Get dependencies with agent-specific configuration
    deps = await get_dependencies(agent_id=agent_id)
    settings = deps['settings']

    # Step 1: Authenticate
    api_key = get_api_key_from_header(authorization)
    if not validate_api_key(api_key, settings):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    # Step 2: Check rate limit
    if not await deps['rate_limiter'].is_allowed(agent_id):
        await deps['audit_logger'].log(
            agent_id=agent_id,
            command=command,
            status=CommandStatus.RATE_LIMITED,
            error_message=f"Rate limited: {settings.rate_limit_requests_per_minute} requests per minute"
        )

        try:
            await deps['mailer'].send_alert(
                agent_id=agent_id,
                command=command,
                status=CommandStatus.RATE_LIMITED,
                details=f"Agent exceeded {settings.rate_limit_requests_per_minute} requests per minute"
            )
        except Exception:
            pass  # Continue even if alert fails

        raise HTTPException(
            status_code=429,
            detail=f"Rate limited: max {settings.rate_limit_requests_per_minute} requests per minute"
        )

    # Step 3: Parse command
    try:
        parsed = deps['parser'].parse(command)
    except Exception as e:
        await deps['audit_logger'].log(
            agent_id=agent_id,
            command=command,
            status=CommandStatus.PARSER_ERROR,
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=f"Failed to parse command: {str(e)}")

    # Step 4: Validate command
    validation = deps['validator'].validate(parsed)
    if not validation.is_valid:
        error_msg = "; ".join(validation.errors)
        await deps['audit_logger'].log(
            agent_id=agent_id,
            command=command,
            parsed_command=str(parsed),
            status=CommandStatus.VALIDATION_ERROR,
            error_message=error_msg
        )
        raise HTTPException(status_code=400, detail=f"Validation error: {error_msg}")

    # Step 5: Execute command
    try:
        executor = CommandExecutor(deps['client'])
        result = await executor.execute(parsed)

        await deps['audit_logger'].log(
            agent_id=agent_id,
            command=command,
            parsed_command=str(parsed),
            status=CommandStatus.SUCCESS,
            response=str(result)
        )

        return CommandResponse(
            status=CommandStatus.SUCCESS,
            message="Command executed successfully",
            tradovate_response=result
        )

    except Exception as e:
        error_msg = str(e)
        await deps['audit_logger'].log(
            agent_id=agent_id,
            command=command,
            parsed_command=str(parsed),
            status=CommandStatus.TRADOVATE_ERROR,
            error_message=error_msg
        )

        try:
            await deps['mailer'].send_alert(
                agent_id=agent_id,
                command=command,
                status=CommandStatus.TRADOVATE_ERROR,
                details=error_msg
            )
        except Exception:
            pass  # Continue even if alert fails

        raise HTTPException(status_code=500, detail=f"Failed to execute command: {error_msg}")
