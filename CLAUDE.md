# Tradovate Dispatch Development Guide

## Project Overview

FastAPI-based command dispatcher for Tradovate trading API. Parses natural language commands, validates them, applies rate limiting, logs activity, and forwards to Tradovate.

## Key Files & Modules

- `app/main.py` - FastAPI app entry point
- `app/config.py` - Environment configuration (Pydantic Settings)
- `app/database.py` - Async SQLite wrapper with audit and rate_limit tables
- `app/models.py` - Pydantic data models for requests/responses
- `app/parser/` - Command parsing with Lark grammar (grammar.lark, parser.py)
- `app/parser/validator.py` - Semantic validation (quantities, prices, contracts)
- `app/auth/api_key.py` - API key validation
- `app/tradovate/client.py` - Async HTTP client for Tradovate API
- `app/tradovate/commands.py` - CommandExecutor: maps ParsedCommand to API calls
- `app/rate_limit/limiter.py` - Per-agent sliding window rate limiting
- `app/alerts/mailer.py` - Email notifications for events
- `app/logging/audit.py` - Audit trail logging with query methods
- `app/routes/health.py` - GET /health endpoint
- `app/routes/execute.py` - POST /execute endpoint (core API)

## Development Workflow

1. **Tests First** - TDD approach
2. **Run Tests** - `pytest tests/ -v`
3. **Commit Frequently** - Small, focused commits
4. **Update Docs** - Keep documentation current

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_parser.py -v

# With coverage
pytest tests/ --cov=app
```

## Environment Variables

See `.env.example` for all options. Required:

- `TRADOVATE_API_URL`
- `TRADOVATE_API_KEY`
- `DISPATCHER_API_KEY`

## Dependencies

See `requirements.txt`. Key:

- FastAPI - Web framework
- Lark - Parser library
- aiosqlite - Async SQLite
- httpx - Async HTTP client
- Pydantic - Data validation

## Code Style

- Follow PEP 8
- Type hints for all functions
- Docstrings for modules and public functions
- Test coverage > 80%

## Architecture

Request flow for POST /execute:
1. Authentication (API key validation)
2. Rate Limiting (per-agent sliding window)
3. Parsing (Lark grammar → ParsedCommand)
4. Validation (semantic checks on quantities, prices, contracts)
5. Execution (Tradovate API call)
6. Logging (audit trail to database)
7. Alerts (email on errors/rate limits)

## Known Limitations

- SQLite for development; PostgreSQL recommended for production
- Email alerts require SMTP configuration
- Lark grammar could be extended for more command types

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Multi-threading for Tradovate client
- [ ] Agent configuration file (YAML) support
- [ ] GraphQL API option
- [ ] Admin dashboard
- [ ] Advanced audit log querying endpoints
