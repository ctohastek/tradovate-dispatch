# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

All endpoints (except `/health`) require the **Dispatcher API Key** via Bearer token header.

The dispatcher uses this key to authenticate clients. Each dispatcher client receives a unique `DISPATCHER_API_KEY`.

Internally, the dispatcher authenticates with Tradovate using per-agent credentials configured in `.env` and `agents.yaml`.

### Dispatcher API Key (Client Authentication)

**Header Format:**
```
Authorization: Bearer <DISPATCHER_API_KEY>
```

**Example:**
```bash
curl -H "Authorization: Bearer 221d524aa69a29c14ecbd0f046565ff751bce829a1683d967f0dd40f50fc72f8" \
  http://localhost:8000/execute
```

### With Basic HTTP Auth (Behind Nginx Reverse Proxy)

When deployed behind nginx with `.htpasswd` authentication, provide basic auth credentials:

**Using `-u` flag:**
```bash
curl -u username:password \
  -H "Authorization: Bearer 221d524aa69a29c14ecbd0f046565ff751bce829a1683d967f0dd40f50fc72f8" \
  https://tradovate-dispatch.hastek.net/execute
```

**Example with actual credentials:**
```bash
curl -u dispatcher:mypassword \
  -H "Authorization: Bearer 221d524aa69a29c14ecbd0f046565ff751bce829a1683d967f0dd40f50fc72f8" \
  -H "Content-Type: application/json" \
  -d '{"command": "BUY 10 ES AT MARKET", "agent_id": "mini01"}' \
  https://tradovate-dispatch.hastek.net/execute
```

**Or encode basic auth header manually:**
```bash
curl -H "Authorization: Basic $(echo -n 'dispatcher:mypassword' | base64)" \
  -H "Authorization: Bearer 221d524aa69a29c14ecbd0f046565ff751bce829a1683d967f0dd40f50fc72f8" \
  https://tradovate-dispatch.hastek.net/execute
```

## Endpoints

### GET /health

Health check endpoint. No authentication required.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-04-05T12:00:00.000000",
  "version": "0.1.0"
}
```

**Status Codes:**
- `200` - Server is healthy

---

### POST /execute

Execute a trading command.

#### Example 1: Market Order (mini01 agent)

**Request:**
```json
{
  "command": "BUY 10 ES AT MARKET",
  "agent_id": "mini01"
}
```

**Curl Command:**
```bash
curl -X POST http://localhost:8000/execute \
  -H "Authorization: Bearer 221d524aa69a29c14ecbd0f046565ff751bce829a1683d967f0dd40f50fc72f8" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "BUY 10 ES AT MARKET",
    "agent_id": "mini01"
  }'
```

#### Example 2: Limit Order (mini02 agent)

**Request:**
```json
{
  "command": "SELL 5 NQ AT 16500",
  "agent_id": "mini02"
}
```

**Curl Command:**
```bash
curl -X POST http://localhost:8000/execute \
  -H "Authorization: Bearer 221d524aa69a29c14ecbd0f046565ff751bce829a1683d967f0dd40f50fc72f8" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "SELL 5 NQ AT 16500",
    "agent_id": "mini02"
  }'
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Command executed successfully",
  "tradovate_response": {
    "orderId": 12345678,
    "accountId": 33,
    "contractId": 560901,
    "action": "Buy",
    "ordStatus": "PendingNew",
    "orderQty": 10,
    "symbol": "ES"
  }
}
```

**Response (Parse Error):**
```json
{
  "detail": "Failed to parse command: ..."
}
```

**Status Codes:**
- `200` - Command executed
- `400` - Parse or validation error
- `401` - Invalid API key
- `429` - Rate limited
- `500` - Server error

## Error Codes

| Code | Meaning | Reason |
|------|---------|--------|
| `401` | Unauthorized | Missing or invalid API key |
| `400` | Bad Request | Parse or validation error |
| `429` | Rate Limited | Exceeded requests per minute |
| `500` | Server Error | Tradovate API failure or server issue |

## Rate Limiting

**Limit:** 20 requests per minute per agent

**Headers (future):**
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1617634860
```
