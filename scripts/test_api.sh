#!/bin/bash

# API Testing Script
# Test the Hyperliquid TWAP API endpoints

set -e

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${API_KEY:-dev-key-change-in-production}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Testing Hyperliquid TWAP API"
echo "================================"
echo "API Base URL: $API_BASE"
echo ""

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local auth=${4:-false}

    echo -e "${BLUE}Testing:${NC} $name"
    echo "URL: $url"

    if [ "$auth" = "true" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method -H "X-API-Key: $API_KEY" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$url")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ Status: $http_code${NC}"
        echo "Response: $(echo $body | jq -C '.' 2>/dev/null || echo $body)"
    elif [ "$http_code" -ge 400 ] && [ "$http_code" -lt 500 ]; then
        echo -e "${YELLOW}⚠ Status: $http_code${NC}"
        echo "Response: $(echo $body | jq -C '.' 2>/dev/null || echo $body)"
    else
        echo -e "${RED}✗ Status: $http_code${NC}"
        echo "Response: $(echo $body | jq -C '.' 2>/dev/null || echo $body)"
    fi
    echo ""
}

# Test 1: Root endpoint
test_endpoint "Root Endpoint" "$API_BASE/" "GET" "false"

# Test 2: Health check
test_endpoint "Health Check" "$API_BASE/health" "GET" "false"

# Test 3: Get trades without auth (should fail)
echo -e "${BLUE}Testing:${NC} Get Trades (No Auth - should fail with 403)"
response=$(curl -s -w "\n%{http_code}" "$API_BASE/api/v1/trades")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 403 ]; then
    echo -e "${GREEN}✓ Status: $http_code (correctly rejected)${NC}"
else
    echo -e "${RED}✗ Status: $http_code (expected 403)${NC}"
fi
echo "Response: $(echo $body | jq -C '.' 2>/dev/null || echo $body)"
echo ""

# Test 4: Get trades with auth
test_endpoint "Get Trades (With Auth)" "$API_BASE/api/v1/trades?limit=10" "GET" "true"

# Test 5: Get trades with filters
test_endpoint "Get Trades (Filtered by date)" \
    "$API_BASE/api/v1/trades?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59&limit=5" \
    "GET" "true"

# Test 6: Get TWAP order (will fail if no data)
echo -e "${BLUE}Testing:${NC} Get TWAP Order (may return 404 if no data)"
echo "URL: $API_BASE/api/v1/twap/twap_12345"
response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" "$API_BASE/api/v1/twap/twap_12345")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Status: $http_code (TWAP order found)${NC}"
elif [ "$http_code" -eq 404 ]; then
    echo -e "${YELLOW}⚠ Status: $http_code (TWAP order not found - expected if no data)${NC}"
else
    echo -e "${RED}✗ Status: $http_code${NC}"
fi
echo "Response: $(echo $body | jq -C '.' 2>/dev/null || echo $body)"
echo ""

# Test 7: Get wallet TWAPs
echo -e "${BLUE}Testing:${NC} Get Wallet TWAPs (may return empty if no data)"
echo "URL: $API_BASE/api/v1/wallets/0xabc123/twaps"
response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" "$API_BASE/api/v1/wallets/0xabc123/twaps")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Status: $http_code${NC}"
else
    echo -e "${RED}✗ Status: $http_code${NC}"
fi
echo "Response: $(echo $body | jq -C '.' 2>/dev/null || echo $body)"
echo ""

# Test 8: Get ingestion status
test_endpoint "Ingestion Status" "$API_BASE/api/v1/status" "GET" "true"

# Test 9: Interactive docs availability
echo -e "${BLUE}Testing:${NC} Interactive API Docs"
echo "URL: $API_BASE/docs"
response=$(curl -s -w "\n%{http_code}" "$API_BASE/docs")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Status: $http_code (Swagger docs available)${NC}"
    echo "Visit: $API_BASE/docs"
else
    echo -e "${RED}✗ Status: $http_code${NC}"
fi
echo ""

# Summary
echo "================================"
echo "Testing Complete!"
echo "================================"
echo ""
echo "API Documentation: $API_BASE/docs"
echo "Alternative Docs: $API_BASE/redoc"
echo ""
echo "To add test data, run the data ingestion manually:"
echo "  docker-compose exec api python -c \"from src.hl_twap_api.utils.scheduler import run_daily_ingestion; run_daily_ingestion()\""
echo ""
