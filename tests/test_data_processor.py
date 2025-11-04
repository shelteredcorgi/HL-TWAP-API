"""Test data processor."""

import pytest
import pandas as pd
from datetime import datetime
from src.hl_twap_api.services.data_processor import DataProcessor


def test_normalize_data():
    """Test data normalization."""
    # Create test DataFrame
    df = pd.DataFrame([
        {
            "twapId": "twap_123",
            "wallet": "0xabc",
            "time": 1704110400000,  # 2024-01-01 12:00:00 UTC in milliseconds
            "coin": "BTC",
            "qty": 1.5,
            "px": 45000.0,
            "side": "buy",
        }
    ])

    # Normalize
    normalized = DataProcessor.normalize_data(df)

    # Verify column names
    assert "twap_id" in normalized.columns
    assert "wallet_address" in normalized.columns
    assert "timestamp" in normalized.columns
    assert "asset" in normalized.columns
    assert "quantity" in normalized.columns
    assert "price" in normalized.columns

    # Verify data types
    assert normalized["twap_id"].iloc[0] == "twap_123"
    assert normalized["wallet_address"].iloc[0] == "0xabc"
    assert isinstance(normalized["timestamp"].iloc[0], pd.Timestamp)
    assert normalized["asset"].iloc[0] == "BTC"
    assert normalized["quantity"].iloc[0] == 1.5
    assert normalized["price"].iloc[0] == 45000.0


def test_group_by_twap():
    """Test grouping by TWAP ID."""
    df = pd.DataFrame([
        {
            "twap_id": "twap_123",
            "wallet_address": "0xabc",
            "timestamp": datetime(2024, 1, 1),
            "asset": "BTC",
            "quantity": 1.0,
            "price": 45000.0,
        },
        {
            "twap_id": "twap_123",
            "wallet_address": "0xabc",
            "timestamp": datetime(2024, 1, 1),
            "asset": "BTC",
            "quantity": 1.0,
            "price": 45100.0,
        },
        {
            "twap_id": "twap_124",
            "wallet_address": "0xdef",
            "timestamp": datetime(2024, 1, 2),
            "asset": "ETH",
            "quantity": 10.0,
            "price": 3000.0,
        },
    ])

    grouped = DataProcessor.group_by_twap(df)

    assert len(grouped) == 2
    assert "twap_123" in grouped
    assert "twap_124" in grouped
    assert len(grouped["twap_123"]) == 2
    assert len(grouped["twap_124"]) == 1


def test_save_to_db(test_db):
    """Test saving data to database."""
    df = pd.DataFrame([
        {
            "twap_id": "twap_123",
            "wallet_address": "0xabc",
            "timestamp": datetime(2024, 1, 1),
            "asset": "BTC",
            "quantity": 1.0,
            "price": 45000.0,
            "side": "buy",
            "fee": 10.0,
            "exchange": "hyperliquid",
        }
    ])

    records = DataProcessor.save_to_db(df, test_db, s3_key="test_key")

    assert records == 1

    # Verify data was saved
    from src.hl_twap_api.models.trade import Trade
    trade = test_db.query(Trade).first()
    assert trade is not None
    assert trade.twap_id == "twap_123"
    assert trade.wallet_address == "0xabc"
