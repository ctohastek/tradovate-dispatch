# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

All endpoints (except `/health`) require API key authentication via Bearer token header.

When deployed behind nginx with basic HTTP authentication, include basic auth credentials.

### Bearer Token (API Key)

**Header Format:**
```
Authorization: Bearer <api_key>
```

**Example:**
```bash
curl -H "Authorization: Bearer dispatcher-key-123" \
  http://localhost:8000/execute
```

### With Basic HTTP Auth (Behind Nginx Reverse Proxy)

When deployed behind nginx with `.htpasswd` authentication, provide basic auth credentials:

**Using `-u` flag:**
```bash
curl -u username:password \
  -H "Authorization: Bearer dispatcher-key-123" \
  https://tradovate-dispatch.hastek.net/execute
```

**Example with actual credentials:**
```bash
curl -u dispatcher:mypassword \
  -H "Authorization: Bearer dispatcher-key-123" \
  -H "Content-Type: application/json" \
  -d '{"command": "BUY 10 ES AT 4500", "agent_id": "agent-1"}' \
  https://tradovate-dispatch.hastek.net/execute
```

**Or encode basic auth header manually:**
```bash
curl -H "Authorization: Basic $(echo -n 'dispatcher:mypassword' | base64)" \
  -H "Authorization: Bearer dispatcher-key-123" \
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

#### Example 1: Market Order

**Request:**
```json
{
  "command": "BUY 10 ES AT 4500",
  "agent_id": "agent-1"
}
```

**Curl Command:**
```bash
curl -X POST http://localhost:8000/execute \
  -H "Authorization: Bearer dispatcher-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "BUY 10 ES AT 4500",
    "agent_id": "agent-1"
  }'
```

#### Example 2: Set Stop Loss

**Request:**
```json
{
  "command": "SET STOP LOSS AT 4450 FOR ES",
  "agent_id": "agent-1"
}
```

**Curl Command:**
```bash
curl -X POST http://localhost:8000/execute \
  -H "Authorization: Bearer dispatcher-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "SET STOP LOSS AT 4450 FOR ES",
    "agent_id": "agent-1"
  }'
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Command executed successfully",
  "order_id": "ORD-123456",
  "tradovate_response": {
    "orderId": "ORD-123456",
    "status": "PENDING",
    "quantity": 10,
    "contract": "ES",
    "price": 4500
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
