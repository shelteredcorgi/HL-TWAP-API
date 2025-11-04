# Hyperliquid TWAP API

Open-source tool for fetching and serving historical Time-Weighted Average Price (TWAP) trade data from Hyperliquid. Built for tax compliance platforms and DeFi analytics.

## Project Overview

This project addresses the limitation of Hyperliquid's API, which only returns up to 2,000 TWAP trade records. By fetching data directly from Hyperliquid's S3 buckets and storing it in a relational database, this tool provides complete historical data access for tax compliance, efficient querying by wallet address and date range, daily automated updates, and a RESTful API for integration with tax platforms.

Bounty Project: Built for AwakenTax (6,000 USDC from @big_duca and @SolanaBoomerNFT)

## Features

- S3 Data Ingestion: Fetch historical TWAP data from Hyperliquid's public S3 buckets
- SQL Storage: PostgreSQL database with optimized indexes for fast queries
- Daily Updates: Automated scheduler fetches new data daily at 2 AM UTC
- REST API: Well-documented API with filtering and pagination
- Docker Support: Easy deployment with Docker Compose
- Tested: Comprehensive test suite included
- Grouped by TWAP ID: All trades aggregated by their TWAP order
- Open Source: MIT licensed for free use by any tax platform

## Tech Stack

- Language: Python 3.9+
- API Framework: FastAPI
- Database: PostgreSQL (SQLite for development)
- ORM: SQLAlchemy
- Data Processing: Pandas
- S3 Access: boto3
- Scheduling: APScheduler
- Testing: pytest
- Deployment: Docker and Docker Compose

## Requirements

- Python 3.9 or higher
- PostgreSQL 12+ (or SQLite for local development)
- Docker and Docker Compose (optional, for containerized deployment)

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/shelteredcorgi/HL-TWAP-API.git
cd HL-TWAP-API
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration (especially API_KEY)
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the API:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Local Development

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Set up environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
poetry run python -c "from src.hl_twap_api.models.database import init_db; init_db()"
```

5. Run the application:
```bash
poetry run python -m src.hl_twap_api.main
```

6. Run tests:
```bash
poetry run pytest
```

## API Documentation

### Authentication

All API endpoints (except `/` and `/health`) require an API key passed in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:8000/api/v1/trades
```

### Endpoints

#### GET /api/v1/trades

Get trades with optional filters.

Query Parameters:
- `wallet_addresses` (string): Comma-separated wallet addresses
- `start_date` (datetime): Start date (ISO format, UTC)
- `end_date` (datetime): End date (ISO format, UTC)
- `asset` (string): Filter by asset/coin (e.g., "BTC", "ETH")
- `twap_id` (string): Filter by specific TWAP order ID
- `limit` (integer): Results per page (1-1000, default: 100)
- `offset` (integer): Offset for pagination (default: 0)

Example:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trades?wallet_addresses=0xabc123&start_date=2024-01-01T00:00:00&limit=50"
```

Response:
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
  }
]
```

#### GET /api/v1/twap/{twap_id}

Get all trades for a specific TWAP order with aggregated statistics.

Example:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/twap/twap_12345"
```

Response:
```json
{
  "twap_id": "twap_12345",
  "total_trades": 10,
  "total_volume": 15.0,
  "avg_price": 45050.0,
  "trades": [...]
}
```

#### GET /api/v1/wallets/{wallet_address}/twaps

Get all TWAP IDs for a specific wallet.

Query Parameters:
- `start_date` (datetime): Filter TWAPs after this date
- `end_date` (datetime): Filter TWAPs before this date

Example:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/wallets/0xabc123/twaps"
```

Response:
```json
["twap_12345", "twap_12346", "twap_12347"]
```

#### GET /api/v1/status

Get data ingestion status.

Example:
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/status"
```

Response:
```json
{
  "last_ingestion": "2024-01-01T02:00:00",
  "total_records": 150000,
  "status": "success",
  "last_error": null
}
```

#### GET /health

Health check endpoint (no authentication required).

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "database": "connected",
  "total_trades": 150000
}
```

### Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation with try-it-out functionality, request/response examples, and schema definitions.

## Configuration

Configuration is managed through environment variables. See `.env.example` for all options:

### Database
- `DATABASE_URL`: PostgreSQL connection string (default: SQLite for development)

### S3 Configuration
- `S3_BUCKET_NAME`: Hyperliquid S3 bucket name (default: `hyperliquid-archive`)
- `S3_REGION`: AWS region (default: `us-east-1`)
- `S3_PREFIX`: S3 key prefix for TWAP data (default: `twap_trades/`)

### API Configuration
- `API_HOST`: API host (default: `0.0.0.0`)
- `API_PORT`: API port (default: `8000`)
- `API_KEY`: API key for authentication (change in production)

### Scheduler Configuration
- `SCHEDULER_ENABLED`: Enable daily scheduler (default: `true`)
- `SCHEDULER_HOUR`: Hour to run daily ingestion (default: `2`, 2 AM UTC)
- `SCHEDULER_MINUTE`: Minute to run daily ingestion (default: `0`)

### Logging
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Database Schema

### trades Table

Stores individual trade executions within TWAP orders.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| twap_id | String | TWAP order ID (indexed) |
| wallet_address | String | Wallet address (indexed) |
| timestamp | DateTime | Trade timestamp (indexed) |
| asset | String | Asset/coin symbol |
| quantity | Float | Trade quantity |
| price | Float | Execution price |
| side | String | 'buy' or 'sell' |
| fee | Float | Trading fee |
| exchange | String | Exchange name |

Indexes:
- `idx_wallet_timestamp`: Composite index on (wallet_address, timestamp)
- `idx_twap_timestamp`: Composite index on (twap_id, timestamp)

### twap_metadata Table

Tracks data ingestion status.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| last_ingestion_date | DateTime | Last ingestion timestamp |
| records_processed | Integer | Number of records processed |
| s3_object_key | String | S3 object key |
| status | String | 'success', 'partial', or 'failed' |
| error_message | String | Error details (if any) |
| created_at | DateTime | Record creation time |

## Data Pipeline

### Daily Ingestion Flow

1. Scheduler triggers at configured time (default: 2 AM UTC)
2. Query database for last successful ingestion date
3. List S3 objects to find new files since last ingestion
4. Download files from S3 (handles gzip compression)
5. Parse and normalize data, converting to DataFrame with standardized columns
6. Group trades by TWAP order ID
7. Insert trades and metadata into database
8. Log results with success or failure details

### Manual Ingestion

Trigger manual data ingestion:

```python
from src.hl_twap_api.utils.scheduler import run_daily_ingestion

run_daily_ingestion()
```

## Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_api.py

# Run with verbose output
poetry run pytest -v
```

## Docker Deployment

### Production Deployment

1. Update environment variables:
```bash
# Edit docker-compose.yml or create a .env file
export API_KEY=your-secure-api-key-here
```

2. Build and start:
```bash
docker-compose up -d --build
```

3. Check logs:
```bash
docker-compose logs -f api
```

4. Stop services:
```bash
docker-compose down
```

### Backup Database

```bash
docker-compose exec postgres pg_dump -U hl_twap_user hl_twap > backup.sql
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U hl_twap_user hl_twap < backup.sql
```

## Contributing

This is an open-source project. Contributions are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- AwakenTax (@big_duca) for sponsoring this bounty project (5,000 USDC)
- @SolanaBoomerNFT for additional bounty support (1,000 USDC)
- Hyperliquid for providing public S3 data access
- The open-source community for the tools used in this project

## Support

- Issues: [GitHub Issues](https://github.com/shelteredcorgi/HL-TWAP-API/issues)
- Discussions: [GitHub Discussions](https://github.com/shelteredcorgi/HL-TWAP-API/discussions)
- Documentation: [API Docs](http://localhost:8000/docs)

## Important Notes

### S3 Data Structure

This implementation assumes Hyperliquid's S3 bucket structure. You may need to adjust the S3 bucket name and prefix in `.env`, the data parsing logic in `data_processor.py` based on actual data format, and column mappings if S3 data uses different field names.

### First-Time Setup

On first run, the tool will attempt to fetch all historical data from S3. Depending on the data volume, this could take significant time. Consider setting a reasonable `start_date` for initial ingestion, monitoring disk space for database storage, and adjusting the scheduler to run during off-peak hours.

### API Rate Limiting

Currently, basic API key authentication is implemented. For production use, consider adding rate limiting (e.g., using `slowapi`), multiple API keys for different users, and token-based authentication (JWT).

---

Total Bounty: 6,000 USDC | License: MIT | Status: Open Source
