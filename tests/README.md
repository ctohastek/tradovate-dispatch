# Test Suite

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_parser.py -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
```

## Test Organization

- `test_config.py` - Configuration module (2 tests)
- `test_database.py` - Database initialization and operations (3 tests)
- `test_models.py` - Pydantic models validation (5 tests)
- `test_auth.py` - API key authentication (4 tests)
- `test_parser.py` - Command parsing with Lark (7 tests)
- `test_validator.py` - Semantic validation (7 tests)
- `test_tradovate_client.py` - Tradovate HTTP client (3 tests)
- `test_tradovate_commands.py` - Command execution mapping (5 tests)
- `test_rate_limit.py` - Rate limiting logic (5 tests)
- `test_alerts.py` - Email alert system (4 tests)
- `test_audit.py` - Audit logging (4 tests)
- `test_routes_health.py` - Health check endpoint (2 tests)
- `test_routes_execute.py` - Execute endpoint (2 tests)
- `test_integration.py` - Full end-to-end flows (14 tests)

**Total: 67 tests across 14 test files**

## Test Coverage

Target: >80% code coverage

Run coverage report:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Mocking Strategy

Tests use unittest.mock for:
- Database connections (in-memory SQLite)
- Tradovate API calls (AsyncMock)
- Email/SMTP
- HTTP clients

This allows isolated unit testing without external dependencies.

## Async Tests

Uses `pytest-asyncio` for async test support:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result == expected
```

## Adding New Tests

1. Create file: `tests/test_<module>.py`
2. Add failing test first (TDD)
3. Implement function/class
4. Add test assertions
5. Run tests to verify: `pytest tests/test_<module>.py -v`
6. Commit: `git add tests/test_<module>.py app/...; git commit -m "..."`
