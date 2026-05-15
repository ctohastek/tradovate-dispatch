# Setup Guide

## Prerequisites

- Python 3.9+
- pip or conda
- Tradovate account with API Access subscription
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
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Tradovate API Keys

For each agent (mini01, mini02, mini03):
1. Log into Tradovate
2. Navigate to **Settings → API Access**
3. Click **Generate API Key**
4. Give it a nickname (e.g., "mini01")
5. **Protect with password** - set a unique password (this will be used for authentication)
6. Save the credentials shown:
   - API Secret (`sec`)
   - Client ID (`cid`)

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your Tradovate credentials:

```bash
# Shared authentication (same for all agents)
TRADOVATE_ACCOUNT_NAME=mini01              # First agent name
TRADOVATE_ACCOUNT_PASS=your-api-password   # Password from API key generation
TRADOVATE_DEVICE_ID=uuid-from-tradovate    # Device ID from Tradovate

# Per-agent API credentials (from API key generation)
TRADOVATE_API_KEY_MINI01=your-api-secret-mini01
TRADOVATE_API_KEY_MINI02=your-api-secret-mini02
TRADOVATE_API_KEY_MINI03=your-api-secret-mini03

TRADOVATE_CLIENT_ID_MINI01=your-client-id-mini01
TRADOVATE_CLIENT_ID_MINI02=your-client-id-mini02
TRADOVATE_CLIENT_ID_MINI03=your-client-id-mini03

# Dispatcher API key (for this service's clients)
DISPATCHER_API_KEY=221d524aa69a29c14ecbd0f046565ff751bce829a1683d967f0dd40f50fc72f8
```
(NOTE: sample DISPATCHER_API_KEY, but variables with *_MINI* are referenced in code base so will need to be updated everywhere to match your config)
### 6. Configure Agents

```bash
cp agents.yaml.example agents.yaml
```

Edit `agents.yaml` to set each agent's environment (demo/live) and appId:

```yaml
agents:
  mini01:
    name: "mini01"
    api_key: "mini01-api-key-here"
    appId: "mini01"              # Must match Tradovate API key nickname
    environment: "demo"          # demo or live
    rate_limit_override: 20
    max_contracts_allowed: 6
    enabled: true

  mini02:
    name: "mini02"
    api_key: "mini02-api-key-here"
    appId: "mini02"              # Must match Tradovate API key nickname
    environment: "demo"
    rate_limit_override: 20
    max_contracts_allowed: 6
    enabled: true
```

### 7. Initialize Database

The database is automatically initialized on first run:

```bash
python -c "from app.database import Database; import asyncio; asyncio.run(Database().init())"
```

### 8. Run Tests

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

## Tradovate API Authentication Flow

1. **Get Access Token** - Call `/auth/accesstokenrequest` with:
   - `name`: TRADOVATE_ACCOUNT_NAME (e.g., mini01)
   - `password`: TRADOVATE_ACCOUNT_PASS (password set during API key generation)
   - `cid`: TRADOVATE_CLIENT_ID_<AGENT> (from API key generation)
   - `sec`: TRADOVATE_API_KEY_<AGENT> (from API key generation)
   - `deviceId`: TRADOVATE_DEVICE_ID (device identifier)
   - `appId`: Agent appId (from agents.yaml)

2. **Use Access Token** - All subsequent API calls include:
   - `Authorization: Bearer <accessToken>`
   - Account and order details in request body

## Configuration

See `.env.example` for all available options:

- `RATE_LIMIT_REQUESTS_PER_MINUTE` - Per-agent request limit (default: 10)
- `ALERT_EMAIL_ENABLED` - Enable email alerts (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)

## Troubleshooting

### "Incorrect username or password" error

- Verify `TRADOVATE_ACCOUNT_NAME` matches your API key account
- Verify `TRADOVATE_ACCOUNT_PASS` is the password set during API key generation (NOT your account password)
- Ensure these match exactly as shown in `.env`

### "Rate limit exceeded" error

- You've hit the 5 requests/hour limit for `/auth/accesstokenrequest`
- Wait the time specified in the response before retrying
- This is a Tradovate API limit, not a dispatcher limit

### "Invalid API key" error (Dispatcher)

- Verify `DISPATCHER_API_KEY` in Authorization header matches .env
- Ensure header format: `Authorization: Bearer <DISPATCHER_API_KEY>`

### Database locked error

- Only one process should access dispatcher.db at a time
- Use WAL mode for concurrent access (enabled by default)

## Next Steps

- Read [Command Reference](COMMAND_REFERENCE.md)
- Review [API documentation](API.md)
- Check [Deployment guide](DEPLOYMENT.md) for production setup
