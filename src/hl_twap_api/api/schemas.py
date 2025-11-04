"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TradeResponse(BaseModel):
    """Response schema for individual trade."""

    id: int
    twap_id: str
    wallet_address: str
    timestamp: datetime
    asset: str
    quantity: float
    price: float
    side: str
    fee: float
    exchange: str

    class Config:
        from_attributes = True


class TWAPGroupResponse(BaseModel):
    """Response schema for grouped TWAP trades."""

    twap_id: str
    total_trades: int
    total_volume: float
    avg_price: float
    trades: List[TradeResponse]


class TradeQueryParams(BaseModel):
    """Query parameters for trade endpoint."""

    wallet_addresses: Optional[List[str]] = Field(None, description="List of wallet addresses")
    start_date: Optional[datetime] = Field(None, description="Start date (UTC)")
    end_date: Optional[datetime] = Field(None, description="End date (UTC)")
    asset: Optional[str] = Field(None, description="Asset/coin filter")
    twap_id: Optional[str] = Field(None, description="Specific TWAP ID")
    limit: int = Field(100, ge=1, le=1000, description="Max results per page")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    database: str
    total_trades: int


class IngestionStatusResponse(BaseModel):
    """Ingestion status response."""

    last_ingestion: Optional[datetime]
    total_records: int
    status: str
    last_error: Optional[str]
