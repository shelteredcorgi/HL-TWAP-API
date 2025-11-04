"""Test API endpoints."""

import pytest
from datetime import datetime
from src.hl_twap_api.models.trade import Trade


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Hyperliquid TWAP API" in response.json()["message"]


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_get_trades_no_auth(client):
    """Test trades endpoint without authentication."""
    response = client.get("/api/v1/trades")
    assert response.status_code == 403


def test_get_trades_with_auth(client, test_db):
    """Test trades endpoint with authentication."""
    # Add test data
    trade = Trade(
        twap_id="twap_123",
        wallet_address="0xabc",
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        asset="BTC",
        quantity=1.5,
        price=45000.0,
        side="buy",
        fee=10.0,
    )
    test_db.add(trade)
    test_db.commit()

    response = client.get(
        "/api/v1/trades",
        headers={"X-API-Key": "dev-key-change-in-production"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["twap_id"] == "twap_123"


def test_get_trades_with_filters(client, test_db):
    """Test trades endpoint with filters."""
    # Add test data
    trades = [
        Trade(
            twap_id="twap_123",
            wallet_address="0xabc",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            asset="BTC",
            quantity=1.0,
            price=45000.0,
            side="buy",
        ),
        Trade(
            twap_id="twap_124",
            wallet_address="0xdef",
            timestamp=datetime(2024, 1, 2, 12, 0, 0),
            asset="ETH",
            quantity=10.0,
            price=3000.0,
            side="sell",
        ),
    ]
    for trade in trades:
        test_db.add(trade)
    test_db.commit()

    # Test wallet filter
    response = client.get(
        "/api/v1/trades?wallet_addresses=0xabc",
        headers={"X-API-Key": "dev-key-change-in-production"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["wallet_address"] == "0xabc"

    # Test asset filter
    response = client.get(
        "/api/v1/trades?asset=ETH",
        headers={"X-API-Key": "dev-key-change-in-production"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["asset"] == "ETH"


def test_get_twap_order(client, test_db):
    """Test TWAP order endpoint."""
    # Add test data
    trades = [
        Trade(
            twap_id="twap_123",
            wallet_address="0xabc",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            asset="BTC",
            quantity=1.0,
            price=45000.0,
            side="buy",
        ),
        Trade(
            twap_id="twap_123",
            wallet_address="0xabc",
            timestamp=datetime(2024, 1, 1, 12, 5, 0),
            asset="BTC",
            quantity=1.0,
            price=45100.0,
            side="buy",
        ),
    ]
    for trade in trades:
        test_db.add(trade)
    test_db.commit()

    response = client.get(
        "/api/v1/twap/twap_123",
        headers={"X-API-Key": "dev-key-change-in-production"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["twap_id"] == "twap_123"
    assert data["total_trades"] == 2
    assert data["total_volume"] == 2.0


def test_get_wallet_twaps(client, test_db):
    """Test wallet TWAPs endpoint."""
    # Add test data
    trades = [
        Trade(
            twap_id="twap_123",
            wallet_address="0xabc",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            asset="BTC",
            quantity=1.0,
            price=45000.0,
            side="buy",
        ),
        Trade(
            twap_id="twap_124",
            wallet_address="0xabc",
            timestamp=datetime(2024, 1, 2, 12, 0, 0),
            asset="ETH",
            quantity=10.0,
            price=3000.0,
            side="sell",
        ),
    ]
    for trade in trades:
        test_db.add(trade)
    test_db.commit()

    response = client.get(
        "/api/v1/wallets/0xabc/twaps",
        headers={"X-API-Key": "dev-key-change-in-production"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "twap_123" in data
    assert "twap_124" in data
