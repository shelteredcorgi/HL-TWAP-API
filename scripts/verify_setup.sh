#!/bin/bash

# Verification script for Hyperliquid TWAP API setup
# Run this after installation to verify everything works

set -e

echo "🔍 Verifying Hyperliquid TWAP API Setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_passed() {
    echo -e "${GREEN}✓${NC} $1"
}

check_failed() {
    echo -e "${RED}✗${NC} $1"
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
    check_passed "Python $PYTHON_VERSION installed"
else
    check_failed "Python 3.9+ required (found $PYTHON_VERSION)"
    exit 1
fi

# Check Poetry
echo "Checking Poetry..."
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version 2>&1 | awk '{print $3}')
    check_passed "Poetry $POETRY_VERSION installed"
else
    check_warning "Poetry not found (optional, can use pip)"
fi

# Check Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    check_passed "Docker $DOCKER_VERSION installed"

    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | tr -d ',')
        check_passed "Docker Compose $COMPOSE_VERSION installed"
    else
        check_warning "Docker Compose not found (optional)"
    fi
else
    check_warning "Docker not found (optional)"
fi

# Check .env file
echo "Checking configuration..."
if [ -f ".env" ]; then
    check_passed ".env file exists"

    # Check if API_KEY is set and not default
    API_KEY=$(grep "^API_KEY=" .env | cut -d= -f2)
    if [ -n "$API_KEY" ] && [ "$API_KEY" != "dev-key-change-in-production" ]; then
        check_passed "API_KEY is configured"
    else
        check_warning "API_KEY not set or using default (change for production!)"
    fi
else
    check_failed ".env file not found (copy from .env.example)"
fi

# Check project structure
echo "Checking project structure..."
REQUIRED_DIRS=("src/hl_twap_api" "tests" "src/hl_twap_api/api" "src/hl_twap_api/models" "src/hl_twap_api/services" "src/hl_twap_api/utils")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_passed "Directory $dir exists"
    else
        check_failed "Directory $dir missing"
    fi
done

# Check key files
echo "Checking key files..."
REQUIRED_FILES=("README.md" "pyproject.toml" "Dockerfile" "docker-compose.yml" "src/hl_twap_api/main.py" "src/hl_twap_api/api/app.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_passed "File $file exists"
    else
        check_failed "File $file missing"
    fi
done

# Try to import the package
echo "Checking Python package..."
if python3 -c "import sys; sys.path.insert(0, 'src'); import hl_twap_api" 2>/dev/null; then
    check_passed "Python package can be imported"
else
    check_warning "Python package import failed (install dependencies first)"
fi

# Check if dependencies are installed
echo "Checking dependencies..."
if poetry run python -c "import fastapi; import sqlalchemy; import pandas; import boto3" 2>/dev/null; then
    check_passed "All required dependencies installed"
elif python3 -c "import fastapi; import sqlalchemy; import pandas; import boto3" 2>/dev/null; then
    check_passed "All required dependencies installed"
else
    check_warning "Dependencies not installed (run: poetry install)"
fi

# Final summary
echo ""
echo "================================"
echo "Verification Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. If dependencies not installed: poetry install"
echo "2. Configure .env file (especially API_KEY)"
echo "3. Start with Docker: docker-compose up -d"
echo "   OR run locally: poetry run python -m src.hl_twap_api.main"
echo "4. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "For detailed setup instructions, see SETUP.md"
echo ""
