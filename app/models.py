# app/models.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


class CommandStatus(str, Enum):
    """Command execution status."""
    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"
    TRADOVATE_ERROR = "tradovate_error"
    AUTH_ERROR = "auth_error"
    PARSER_ERROR = "parser_error"


class CommandRequest(BaseModel):
    """Incoming command request."""
    command: str = Field(..., min_length=1, description="Natural language trading command")
    agent_id: str = Field(..., min_length=1, description="Agent identifier")


class ParsedCommand(BaseModel):
    """Parsed trading command structure."""
    action: str = Field(..., description="BUY, SELL, CANCEL, etc.")
    contract: Optional[str] = Field(None, description="Contract symbol (ES, NQ, etc.)")
    quantity: Optional[int] = Field(None, ge=0, description="Order quantity")
    price: Optional[float] = Field(None, gt=0, description="Order price (limit orders)")
    order_id: Optional[str] = Field(None, description="For CANCEL operations")


class CommandResponse(BaseModel):
    """Response to command execution."""
    status: CommandStatus
    message: str
    order_id: Optional[str] = None
    tradovate_response: Optional[dict] = None
    error_details: Optional[str] = None


class AuditLog(BaseModel):
    """Audit log entry."""
    id: Optional[int] = None
    agent_id: str
    command: str
    parsed_command: Optional[str] = None
    status: CommandStatus
    error_message: Optional[str] = None
    response: Optional[str] = None
    created_at: Optional[datetime] = None


class RateLimitInfo(BaseModel):
    """Rate limit status."""
    agent_id: str
    request_count: int
    limit: int
    requests_remaining: int
    reset_at: str
