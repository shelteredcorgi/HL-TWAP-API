# API Reference

Complete API reference for the Hyperliquid TWAP API.

## Base URL

```
http://localhost:8000
```

## Authentication

All protected endpoints require an API key passed in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:8000/api/v1/trades
```

## Rate Limiting

Currently, no rate limiting is implemented. For production deployments, consider adding rate limiting middleware.

## Pagination

List endpoints support pagination using `limit` and `offset` query parameters:

- `limit`: Number of results per page (1-1000, default: 100)
- `offset`: Number of results to skip (default: 0)

Example:
```bash
# Get first 50 results
/api/v1/trades?limit=50&offset=0

# Get next 50 results
/api/v1/trades?limit=50&offset=50
```

## Date/Time Format

All dates and times use ISO 8601 format in UTC:

```
2024-01-01T12:00:00
```

## Endpoints

---

### `GET /`

Root endpoint with basic information.

#### Authentication
Not required

#### Response
```json
{
  "message": "Hyperliquid TWAP API",
  "docs": "/docs",
  "version": "0.1.0"
}
```

---

### `GET /health`

Health check endpoint for monitoring.

#### Authentication
Not required

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "database": "connected",
  "total_trades": 150000
}
```

#### Status Codes
- `200`: Service is healthy
- `503`: Service is unavailable

---

### `GET /api/v1/trades`

Retrieve trades with optional filtering and pagination.

#### Authentication
Required

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `wallet_addresses` | string | No | Comma-separated list of wallet addresses |
| `start_date` | datetime | No | Filter trades after this date (ISO 8601, UTC) |
| `end_date` | datetime | No | Filter trades before this date (ISO 8601, UTC) |
| `asset` | string | No | Filter by asset/coin (e.g., "BTC", "ETH") |
| `twap_id` | string | No | Filter by specific TWAP order ID |
| `limit` | integer | No | Results per page (1-1000, default: 100) |
| `offset` | integer | No | Offset for pagination (default: 0) |

#### Examples

Get all trades (paginated):
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trades?limit=100"
```

Get trades for specific wallet:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trades?wallet_addresses=0xabc123"
```

Get trades for multiple wallets:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trades?wallet_addresses=0xabc123,0xdef456"
```

Get trades in date range:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trades?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59"
```

Get BTC trades only:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trades?asset=BTC"
```

Complex query with multiple filters:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trades?wallet_addresses=0xabc123&asset=BTC&start_date=2024-01-01T00:00:00&limit=50"
```

#### Response

```json
[
  {
    "id": 1,
    "twap_id": "twap_12345",
    "wallet_address": "0xabc123",
    "timestamp": "2024-01-01T12:00:00",
    "asset": "BTC",
    "quantity": 1.5,
    "price": 45000.0,
    "side": "buy",
    "fee": 10.0,
    "exchange": "hyperliquid"
  },
  {
    "id": 2,
    "twap_id": "twap_12345",
    "wallet_address": "0xabc123",
    "timestamp": "2024-01-01T12:05:00",
    "asset": "BTC",
    "quantity": 1.0,
    "price": 45100.0,
    "side": "buy",
    "fee": 7.5,
    "exchange": "hyperliquid"
  }
]
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique trade ID |
| `twap_id` | string | TWAP order ID |
| `wallet_address` | string | Wallet address |
| `timestamp` | datetime | Trade execution time (UTC) |
| `asset` | string | Asset/coin symbol |
| `quantity` | float | Trade quantity |
| `price` | float | Execution price |
| `side` | string | Trade side ("buy" or "sell") |
| `fee` | float | Trading fee |
| `exchange` | string | Exchange name |

#### Status Codes
- `200`: Success
- `403`: Invalid API key
- `500`: Internal server error

---

### `GET /api/v1/twap/{twap_id}`

Get all trades for a specific TWAP order with aggregated statistics.

#### Authentication
Required

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `twap_id` | string | Yes | TWAP order ID |

#### Example

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/twap/twap_12345"
```

#### Response

```json
{
  "twap_id": "twap_12345",
  "total_trades": 10,
  "total_volume": 15.0,
  "avg_price": 45050.0,
  "trades": [
    {
      "id": 1,
      "twap_id": "twap_12345",
      "wallet_address": "0xabc123",
      "timestamp": "2024-01-01T12:00:00",
      "asset": "BTC",
      "quantity": 1.5,
      "price": 45000.0,
      "side": "buy",
      "fee": 10.0,
      "exchange": "hyperliquid"
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `twap_id` | string | TWAP order ID |
| `total_trades` | integer | Total number of trade executions |
| `total_volume` | float | Total volume traded |
| `avg_price` | float | Volume-weighted average price |
| `trades` | array | Array of trade objects (same schema as `/trades` endpoint) |

#### Status Codes
- `200`: Success
- `403`: Invalid API key
- `404`: TWAP order not found
- `500`: Internal server error

---

### `GET /api/v1/wallets/{wallet_address}/twaps`

Get all TWAP order IDs for a specific wallet.

#### Authentication
Required

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `wallet_address` | string | Yes | Wallet address |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | datetime | No | Filter TWAPs after this date |
| `end_date` | datetime | No | Filter TWAPs before this date |

#### Examples

Get all TWAP IDs for wallet:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/wallets/0xabc123/twaps"
```

Get TWAP IDs in date range:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/wallets/0xabc123/twaps?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59"
```

#### Response

```json
["twap_12345", "twap_12346", "twap_12347"]
```

#### Status Codes
- `200`: Success
- `403`: Invalid API key
- `500`: Internal server error

---

### `GET /api/v1/status`

Get data ingestion status and metadata.

#### Authentication
Required

#### Example

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/status"
```

#### Response

```json
{
  "last_ingestion": "2024-01-01T02:00:00",
  "total_records": 150000,
  "status": "success",
  "last_error": null
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `last_ingestion` | datetime | Timestamp of last ingestion attempt |
| `total_records` | integer | Total number of trades in database |
| `status` | string | Status of last ingestion ("success", "partial", "failed", "no_data") |
| `last_error` | string | Error message from last failed ingestion (null if successful) |

#### Status Codes
- `200`: Success
- `403`: Invalid API key
- `500`: Internal server error

---

## Interactive Documentation

For interactive API documentation with try-it-out functionality, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Invalid parameters |
| 403 | Forbidden - Invalid or missing API key |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server-side error |
| 503 | Service Unavailable - Service is down |

## Code Examples

### Python

```python
import requests

API_BASE = "http://localhost:8000"
API_KEY = "your-api-key-here"

headers = {"X-API-Key": API_KEY}

# Get trades for wallet
response = requests.get(
    f"{API_BASE}/api/v1/trades",
    headers=headers,
    params={
        "wallet_addresses": "0xabc123",
        "start_date": "2024-01-01T00:00:00",
        "limit": 100
    }
)

trades = response.json()
print(f"Found {len(trades)} trades")

# Get TWAP order details
response = requests.get(
    f"{API_BASE}/api/v1/twap/twap_12345",
    headers=headers
)

twap_order = response.json()
print(f"TWAP {twap_order['twap_id']}: {twap_order['total_trades']} trades, avg price: {twap_order['avg_price']}")
```

### JavaScript/TypeScript

```javascript
const API_BASE = "http://localhost:8000";
const API_KEY = "your-api-key-here";

const headers = {
  "X-API-Key": API_KEY
};

// Get trades for wallet
async function getTrades(walletAddress) {
  const params = new URLSearchParams({
    wallet_addresses: walletAddress,
    limit: "100"
  });

  const response = await fetch(
    `${API_BASE}/api/v1/trades?${params}`,
    { headers }
  );

  const trades = await response.json();
  console.log(`Found ${trades.length} trades`);
  return trades;
}

// Get TWAP order details
async function getTwapOrder(twapId) {
  const response = await fetch(
    `${API_BASE}/api/v1/twap/${twapId}`,
    { headers }
  );

  const twapOrder = await response.json();
  console.log(`TWAP ${twapOrder.twap_id}: ${twapOrder.total_trades} trades`);
  return twapOrder;
}
```

### cURL

```bash
# Set variables
API_BASE="http://localhost:8000"
API_KEY="your-api-key-here"

# Get trades
curl -H "X-API-Key: $API_KEY" \
  "$API_BASE/api/v1/trades?wallet_addresses=0xabc123&limit=100"

# Get TWAP order
curl -H "X-API-Key: $API_KEY" \
  "$API_BASE/api/v1/twap/twap_12345"

# Get wallet's TWAP IDs
curl -H "X-API-Key: $API_KEY" \
  "$API_BASE/api/v1/wallets/0xabc123/twaps"
```

## Best Practices

### 1. Use Pagination

Always use pagination for large result sets:

```bash
# Good
curl -H "X-API-Key: $API_KEY" \
  "$API_BASE/api/v1/trades?limit=100&offset=0"

# Bad (could return too many results)
curl -H "X-API-Key: $API_KEY" \
  "$API_BASE/api/v1/trades?limit=1000"
```

### 2. Filter on the Server

Filter data server-side rather than fetching everything:

```bash
# Good
curl -H "X-API-Key: $API_KEY" \
  "$API_BASE/api/v1/trades?wallet_addresses=0xabc123&asset=BTC"

# Bad
curl -H "X-API-Key: $API_KEY" \
  "$API_BASE/api/v1/trades" | jq '.[] | select(.asset == "BTC")'
```

### 3. Use Date Ranges

Always specify date ranges for better performance:

```bash
# Good
curl -H "X-API-Key: $API_KEY" \
  "$API_BASE/api/v1/trades?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59"
```

### 4. Cache Results

Cache frequently accessed data to reduce API calls:

```python
import requests
from functools import lru_cache

@lru_cache(maxsize=100)
def get_twap_order(twap_id):
    response = requests.get(
        f"{API_BASE}/api/v1/twap/{twap_id}",
        headers={"X-API-Key": API_KEY}
    )
    return response.json()
```

### 5. Handle Errors

Always handle potential errors:

```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except requests.exceptions.ConnectionError:
    print("Connection error")
except requests.exceptions.Timeout:
    print("Request timeout")
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
```

## Versioning

The API uses URL versioning (e.g., `/api/v1/`). Future versions will be released under new URL paths (e.g., `/api/v2/`) to maintain backwards compatibility.

---

For more information, see the [README.md](README.md) or visit the interactive docs at http://localhost:8000/docs.
