# Setup Guide

## Prerequisites

- Python 3.8+
- pip or conda
- (Optional) SQLite3 CLI for debugging

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd tradovate-dispatch
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your actual Tradovate API credentials:

```bash
TRADOVATE_API_URL=https://api.tradovate.com
TRADOVATE_API_KEY=your-tradovate-key
DISPATCHER_API_KEY=your-dispatcher-key
```

### 5. Initialize Database

The database is automatically initialized on first run. Verify:

```bash
python -c "from app.database import Database; import asyncio; asyncio.run(Database().init())"
```

### 6. Run Tests

```bash
pytest tests/ -v
```

## Running the Server

### Development

```bash
python run.py
```

Server runs at `http://localhost:8000`

### Production

```bash
gunicorn -c gunicorn.conf.py run:app
```

## Verify Installation

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2026-04-05T12:34:56.789012",
  "version": "0.1.0"
}
```

## Configuration

See `.env.example` for all available configuration options:

- `RATE_LIMIT_REQUESTS_PER_MINUTE` - Default: 20
- `ALERT_EMAIL_ENABLED` - Default: false
- `LOG_LEVEL` - Default: INFO
- `ENVIRONMENT` - Default: development

## Troubleshooting

### "Connection refused" error

- Verify server is running: `curl http://localhost:8000/health`
- Check PORT environment variable

### "Invalid API key" error

- Verify `DISPATCHER_API_KEY` in .env matches Authorization header
- Ensure header format: `Authorization: Bearer <key>`

### Database locked error

- Only one process should access dispatcher.db at a time
- Use WAL mode for concurrent access (default in code)

## Next Steps

- Read [Command Reference](COMMAND_REFERENCE.md)
- Review [API documentation](API.md)
- Check [Deployment guide](DEPLOYMENT.md) for production setup
