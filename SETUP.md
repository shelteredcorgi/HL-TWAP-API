# Setup Guide

Detailed setup instructions for the Hyperliquid TWAP API.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
- **Poetry**: [Install Poetry](https://python-poetry.org/docs/#installation)
- **Docker & Docker Compose**: [Install Docker](https://docs.docker.com/get-docker/) (optional, for containerized deployment)
- **PostgreSQL 12+**: [Install PostgreSQL](https://www.postgresql.org/download/) (optional, SQLite works for development)

## Installation Methods

### Method 1: Docker Compose (Recommended for Production)

This method sets up both the API and PostgreSQL database in containers.

1. **Clone the repository**:
```bash
git clone https://github.com/shelteredcorgi/HL-TWAP-API.git
cd HL-TWAP-API
```

2. **Configure environment**:
```bash
cp .env.example .env
```

Edit `.env` and set your configuration:
```env
# IMPORTANT: Change the API key!
API_KEY=your-secure-api-key-here

# Database (already configured for docker-compose)
DATABASE_URL=postgresql://hl_twap_user:hl_twap_password@postgres:5432/hl_twap

# S3 Configuration (adjust if Hyperliquid's structure differs)
S3_BUCKET_NAME=hyperliquid-archive
S3_REGION=us-east-1
S3_PREFIX=twap_trades/

# Scheduler (adjust timezone if needed)
SCHEDULER_ENABLED=true
SCHEDULER_HOUR=2
SCHEDULER_MINUTE=0
```

3. **Start the services**:
```bash
docker-compose up -d
```

4. **Verify the setup**:
```bash
# Check logs
docker-compose logs -f api

# Test health endpoint
curl http://localhost:8000/health

# Test API with authentication
curl -H "X-API-Key: your-secure-api-key-here" \
  http://localhost:8000/api/v1/status
```

5. **Access the API**:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Method 2: Local Development with Poetry

This method is ideal for development and testing.

1. **Clone the repository**:
```bash
git clone https://github.com/shelteredcorgi/HL-TWAP-API.git
cd HL-TWAP-API
```

2. **Install Poetry** (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. **Install dependencies**:
```bash
poetry install
```

4. **Configure environment**:
```bash
cp .env.example .env
```

Edit `.env` for local development (using SQLite):
```env
# Use SQLite for local development
DATABASE_URL=sqlite:///./hl_twap.db

# API Configuration
API_KEY=dev-key-change-in-production
API_HOST=127.0.0.1
API_PORT=8000

# S3 Configuration
S3_BUCKET_NAME=hyperliquid-archive
S3_REGION=us-east-1
S3_PREFIX=twap_trades/

# Scheduler
SCHEDULER_ENABLED=false  # Disable for development
```

5. **Initialize the database**:
```bash
poetry run python -c "from src.hl_twap_api.models.database import init_db; init_db()"
```

6. **Run the application**:
```bash
poetry run python -m src.hl_twap_api.main
```

7. **Access the API**:
- **API**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs

### Method 3: Local Development with PostgreSQL

For a production-like setup locally.

1. **Install PostgreSQL**:
```bash
# macOS (using Homebrew)
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows: Download from https://www.postgresql.org/download/windows/
```

2. **Create database and user**:
```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE hl_twap;
CREATE USER hl_twap_user WITH PASSWORD 'hl_twap_password';
GRANT ALL PRIVILEGES ON DATABASE hl_twap TO hl_twap_user;
\q
```

3. **Follow steps 1-3 from Method 2**, then update `.env`:
```env
DATABASE_URL=postgresql://hl_twap_user:hl_twap_password@localhost:5432/hl_twap
```

4. **Continue with steps 5-7 from Method 2**.

## Configuration Details

### Environment Variables

#### Required
- `DATABASE_URL`: Database connection string
- `API_KEY`: API authentication key

#### S3 Configuration
- `S3_BUCKET_NAME`: Hyperliquid's S3 bucket (default: `hyperliquid-archive`)
- `S3_REGION`: AWS region (default: `us-east-1`)
- `S3_PREFIX`: Prefix for TWAP data files (default: `twap_trades/`)

**Note**: These defaults are assumptions. You'll need to verify the actual S3 structure from Hyperliquid's documentation.

#### Scheduler Configuration
- `SCHEDULER_ENABLED`: Enable/disable daily scheduler (`true`/`false`)
- `SCHEDULER_HOUR`: Hour to run (0-23, UTC)
- `SCHEDULER_MINUTE`: Minute to run (0-59)

#### API Configuration
- `API_HOST`: Host to bind (default: `0.0.0.0`)
- `API_PORT`: Port to bind (default: `8000`)
- `LOG_LEVEL`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

### Database Configuration

#### Using SQLite (Development)
```env
DATABASE_URL=sqlite:///./hl_twap.db
```

Pros: Zero setup, portable, good for testing
Cons: Not recommended for production, limited concurrency

#### Using PostgreSQL (Production)
```env
DATABASE_URL=postgresql://user:password@host:port/database
```

Pros: Production-ready, excellent performance, full SQL support
Cons: Requires separate installation/management

## Initial Data Ingestion

### Manual Trigger

For the first run, you may want to manually trigger data ingestion:

```bash
# Using Poetry
poetry run python -c "from src.hl_twap_api.utils.scheduler import run_daily_ingestion; run_daily_ingestion()"

# Inside Docker container
docker-compose exec api python -c "from src.hl_twap_api.utils.scheduler import run_daily_ingestion; run_daily_ingestion()"
```

### Monitor Progress

```bash
# View logs
docker-compose logs -f api

# Or for local development
tail -f logs/app.log
```

### Check Status

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/status
```

## Testing the Setup

### Run Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Run specific test file
poetry run pytest tests/test_api.py -v
```

### Manual API Testing

```bash
# Health check (no auth required)
curl http://localhost:8000/health

# Get trades (requires auth)
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trades?limit=10"

# Get specific TWAP order
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/twap/twap_12345"

# Get wallet's TWAP IDs
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/wallets/0xabc123/twaps"
```

## Troubleshooting

### Issue: Database connection errors

Solution: Verify your `DATABASE_URL` is correct and the database is running:
```bash
# For PostgreSQL
psql postgresql://hl_twap_user:hl_twap_password@localhost:5432/hl_twap

# For Docker
docker-compose exec postgres psql -U hl_twap_user -d hl_twap
```

### Issue: S3 access errors

Solution:
1. Verify the S3 bucket name and region in `.env`
2. Check if the bucket is publicly accessible
3. Review the S3 prefix structure
4. Check logs for specific error messages:
```bash
docker-compose logs api | grep "S3"
```

### Issue: Module not found errors

Solution: Ensure dependencies are installed:
```bash
poetry install
```

### Issue: Port already in use

Solution: Change the port in `.env` or stop the conflicting service:
```bash
# Check what's using port 8000
lsof -i :8000

# Or change the port
# Edit .env: API_PORT=8001
```

### Issue: Permission denied errors (Docker)

Solution: Ensure Docker has proper permissions:
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# macOS: Check Docker Desktop settings
```

### Issue: Scheduler not running

Solution:
1. Verify `SCHEDULER_ENABLED=true` in `.env`
2. Check logs for scheduler initialization:
```bash
docker-compose logs api | grep "Scheduler"
```
3. Verify timezone settings match your expectations (scheduler uses UTC)

## Security Considerations

### API Key

Change the default API key immediately:
```env
# Generate a strong random key
API_KEY=$(openssl rand -base64 32)
```

### Database Password

For PostgreSQL, use strong passwords:
```env
# In docker-compose.yml or .env
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### Network Security

- Production: Use HTTPS/TLS (configure a reverse proxy like nginx)
- Firewall: Restrict database ports to localhost only
- API Keys: Consider rotating keys periodically

## Production Deployment

### Using a Process Manager

For production deployments without Docker:

```bash
# Install gunicorn
poetry add gunicorn

# Run with gunicorn
poetry run gunicorn src.hl_twap_api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Using systemd (Linux)

Create `/etc/systemd/system/hl-twap-api.service`:
```ini
[Unit]
Description=Hyperliquid TWAP API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/HL-TWAP-API
Environment="PATH=/opt/HL-TWAP-API/.venv/bin"
ExecStart=/opt/HL-TWAP-API/.venv/bin/python -m src.hl_twap_api.main
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable hl-twap-api
sudo systemctl start hl-twap-api
```

### Using a Reverse Proxy

Example nginx configuration:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Maintenance

### Database Backups

```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U hl_twap_user hl_twap > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U hl_twap_user hl_twap < backup_20240101.sql
```

### Log Rotation

Configure log rotation to prevent disk space issues:
```bash
# /etc/logrotate.d/hl-twap-api
/opt/HL-TWAP-API/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
}
```

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Update dependencies
poetry install

# Restart services
docker-compose down
docker-compose up -d --build
```

## Next Steps

1. Read the [README.md](README.md) for API usage documentation
2. Test the API using the interactive docs at http://localhost:8000/docs
3. Verify S3 data structure matches the implementation
4. Customize data parsing logic if needed
5. Set up monitoring for production deployments

## Support

- Issues: [GitHub Issues](https://github.com/shelteredcorgi/HL-TWAP-API/issues)
- Discussions: [GitHub Discussions](https://github.com/shelteredcorgi/HL-TWAP-API/discussions)

---

If you encounter any issues not covered here, please open an issue on GitHub!
