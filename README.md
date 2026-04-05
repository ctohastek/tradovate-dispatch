# Tradovate Dispatch

A FastAPI-based command dispatcher for the Tradovate trading platform. Parses natural language trading commands, validates them, enforces rate limits, and forwards them to Tradovate's API.

## Features

- **Natural Language Commands** - Write trading commands in plain English (e.g., "BUY 10 ES AT 4500")
- **Command Validation** - Semantic validation of quantities, prices, contracts
- **Rate Limiting** - Per-agent request throttling with sliding window
- **Audit Logging** - Complete audit trail of all commands and execution results
- **Email Alerts** - Notifications for errors and significant events
- **API Key Authentication** - Secure access control
- **Production Ready** - Async SQLite, Gunicorn support, comprehensive logging

## Quick Start

1. **Clone & Install**
   ```bash
   git clone <repo>
   cd tradovate-dispatch
   pip install -r requirements.txt
   ```

2. **Configure**
   ```bash
   cp .env.example .env
   # Edit .env with your Tradovate credentials
   ```

3. **Run**
   ```bash
   python run.py
   ```

   Server runs at http://localhost:8000

4. **Test the API**
   ```bash
   curl -X POST http://localhost:8000/execute \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"command": "BUY 10 ES", "agent_id": "agent-1"}'
   ```

## Documentation

- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Command Reference](docs/COMMAND_REFERENCE.md) - Supported trading commands
- [API Documentation](docs/API.md) - HTTP API endpoints and responses
- [Deployment](docs/DEPLOYMENT.md) - Production deployment checklist

## Architecture

```
Request → Auth → Parser → Validator → Tradovate Client → Response
                    ↓         ↓            ↓
                Rate Limit  Audit Log   Alert/Email
```

## License

MIT
