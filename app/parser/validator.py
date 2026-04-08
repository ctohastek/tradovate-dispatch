# app/parser/validator.py
from typing import List
from dataclasses import dataclass
from app.models import ParsedCommand


@dataclass
class ValidationResult:
    """Result of command validation."""
    is_valid: bool
    errors: List[str]


class CommandValidator:
    """Validate parsed trading commands for semantic correctness."""

    # Valid contracts (subset - expand as needed)
    VALID_CONTRACTS = {"ES", "NQ", "YM", "RTY", "MES", "MNQ", "MYM", "MRTY"}

    # Valid actions
    VALID_ACTIONS = {"BUY", "SELL", "CANCEL", "STATUS", "HELP"}

    # Max values for safety
    MAX_QUANTITY = 1000
    MAX_PRICE = 1_000_000

    def validate(self, command: ParsedCommand) -> ValidationResult:
        """
        Validate parsed command for semantic correctness.

        Args:
            command: Parsed command to validate

        Returns:
            ValidationResult with is_valid and list of errors
        """
        errors = []

        # Validate action
        if command.action not in self.VALID_ACTIONS:
            errors.append(f"Unknown action: {command.action}")

        # Action-specific validation
        if command.action in ["BUY", "SELL"]:
            errors.extend(self._validate_order(command))
        elif command.action == "CANCEL":
            errors.extend(self._validate_cancel(command))
        elif command.action == "STATUS":
            errors.extend(self._validate_status(command))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def _validate_order(self, command: ParsedCommand) -> List[str]:
        """Validate BUY/SELL order command."""
        errors = []

        # Quantity is required
        if command.quantity is None:
            errors.append("Quantity is required for BUY/SELL")
        elif command.quantity <= 0:
            errors.append(f"Quantity must be positive, got {command.quantity}")
        elif command.quantity > self.MAX_QUANTITY:
            errors.append(f"Quantity exceeds maximum of {self.MAX_QUANTITY}")

        # Contract is required and must be valid
        if not command.contract:
            errors.append("Contract is required")
        elif command.contract not in self.VALID_CONTRACTS:
            errors.append(
                f"Unknown contract '{command.contract}'. "
                f"Valid: {', '.join(sorted(self.VALID_CONTRACTS))}"
            )

        # Price validation (optional, but if provided must be positive)
        if command.price is not None:
            if command.price <= 0:
                errors.append(f"Price must be positive, got {command.price}")
            elif command.price > self.MAX_PRICE:
                errors.append(f"Price exceeds maximum of {self.MAX_PRICE}")

        return errors

    def _validate_cancel(self, command: ParsedCommand) -> List[str]:
        """Validate CANCEL command."""
        errors = []

        if not command.order_id:
            errors.append("Order ID is required for CANCEL")

        return errors

    def _validate_status(self, command: ParsedCommand) -> List[str]:
        """Validate STATUS command."""
        # Order ID is optional for STATUS
        return []
