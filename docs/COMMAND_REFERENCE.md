# Command Reference

## Supported Commands

All commands are case-insensitive.

### BUY - Place Buy Order

```
BUY <quantity> <contract> [AT <price>]
```

**Examples:**
```
BUY 10 ES           # Market order for 10 E-mini S&P 500
BUY 5 NQ AT 16000   # Limit order for 5 E-mini Nasdaq at 16000
BUY 1 YM AT 38000   # 1 E-mini Russell 2000 at 38000
```

**Parameters:**
- `quantity` (required): 1-1000 contracts
- `contract` (required): Valid contract symbol
- `price` (optional): Limit price. If omitted, market order

**Valid Contracts:**
- `ES` - E-mini S&P 500
- `NQ` - E-mini Nasdaq 100
- `YM` - E-mini Russell 2000
- `RTY` - Russell 2000
- `MES` - Micro E-mini S&P 500
- `MNQ` - Micro E-mini Nasdaq
- `MYM` - Micro E-mini Russell 2000
- `MRTY` - Micro Russell 2000

### SELL - Place Sell Order

```
SELL <quantity> <contract> [AT <price>]
```

**Examples:**
```
SELL 10 ES              # Market sell
SELL 5 NQ AT 15950      # Limit sell
```

Same parameters and contracts as BUY.

### CANCEL - Cancel Order

```
CANCEL <order_id>
```

**Examples:**
```
CANCEL ORD-123456
CANCEL pending-order
```

**Parameters:**
- `order_id` (required): Order identifier from execution response

### STATUS - Check Order Status

```
STATUS [order_id]
```

**Examples:**
```
STATUS ORD-123456    # Get status of specific order
STATUS              # Get status of last order
```

**Parameters:**
- `order_id` (optional): Order identifier. If omitted, returns recent orders.

### HELP - Display Help

```
HELP
```

Shows command reference.

## Error Handling

All commands return standard HTTP responses:

- `200 OK` - Command executed successfully
- `400 Bad Request` - Parse or validation error
- `401 Unauthorized` - Invalid or missing API key
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Tradovate API error or server issue

## Validation Rules

- **Quantities**: Must be positive, max 1000
- **Prices**: Must be positive, max $1,000,000
- **Contracts**: Must be one of the valid symbols above
- **Order IDs**: Alphanumeric with hyphens, max 50 chars

## Rate Limiting

Default: 20 requests per minute per agent

When rate limited:
- Response: `429 Too Many Requests`
- Email alert sent (if configured)
- Audit log created

Reset: Automatic after 1 minute
