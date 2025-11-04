"""FastAPI application."""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.database import get_db_session, init_db
from ..models.trade import Trade, TWAPMetadata
from ..config import config
from .schemas import (
    TradeResponse,
    TWAPGroupResponse,
    HealthResponse,
    IngestionStatusResponse,
)

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hyperliquid TWAP API",
    description="Open-source API for accessing historical TWAP trade data from Hyperliquid",
    version="0.1.0",
)


# API Key dependency
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header."""
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "Hyperliquid TWAP API",
        "docs": "/docs",
        "version": "0.1.0",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db_session)):
    """Health check endpoint."""
    try:
        total_trades = db.query(func.count(Trade.id)).scalar()
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            database="connected",
            total_trades=total_trades,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/api/v1/trades", response_model=List[TradeResponse], tags=["Trades"])
async def get_trades(
    wallet_addresses: Optional[str] = Query(None, description="Comma-separated wallet addresses"),
    start_date: Optional[datetime] = Query(None, description="Start date (UTC)"),
    end_date: Optional[datetime] = Query(None, description="End date (UTC)"),
    asset: Optional[str] = Query(None, description="Asset filter"),
    twap_id: Optional[str] = Query(None, description="TWAP ID filter"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """
    Get trades with optional filters.

    - **wallet_addresses**: Filter by wallet addresses (comma-separated)
    - **start_date**: Filter trades after this date (ISO format)
    - **end_date**: Filter trades before this date (ISO format)
    - **asset**: Filter by specific asset/coin
    - **twap_id**: Filter by specific TWAP order ID
    - **limit**: Maximum number of results (1-1000)
    - **offset**: Offset for pagination
    """
    try:
        query = db.query(Trade)

        # Apply filters
        if wallet_addresses:
            wallet_list = [w.strip() for w in wallet_addresses.split(",")]
            query = query.filter(Trade.wallet_address.in_(wallet_list))

        if start_date:
            query = query.filter(Trade.timestamp >= start_date)

        if end_date:
            query = query.filter(Trade.timestamp <= end_date)

        if asset:
            query = query.filter(Trade.asset == asset)

        if twap_id:
            query = query.filter(Trade.twap_id == twap_id)

        # Order by timestamp descending
        query = query.order_by(Trade.timestamp.desc())

        # Pagination
        total_count = query.count()
        trades = query.offset(offset).limit(limit).all()

        logger.info(
            f"Retrieved {len(trades)} trades (total: {total_count}) with filters: "
            f"wallets={wallet_addresses}, start={start_date}, end={end_date}, asset={asset}"
        )

        return trades

    except Exception as e:
        logger.error(f"Error retrieving trades: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/twap/{twap_id}", response_model=TWAPGroupResponse, tags=["TWAP"])
async def get_twap_order(
    twap_id: str,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """
    Get all trades for a specific TWAP order, grouped and aggregated.

    - **twap_id**: The TWAP order ID to retrieve
    """
    try:
        trades = db.query(Trade).filter(Trade.twap_id == twap_id).all()

        if not trades:
            raise HTTPException(status_code=404, detail=f"TWAP order {twap_id} not found")

        total_volume = sum(trade.quantity for trade in trades)
        avg_price = sum(trade.price * trade.quantity for trade in trades) / total_volume if total_volume > 0 else 0

        return TWAPGroupResponse(
            twap_id=twap_id,
            total_trades=len(trades),
            total_volume=total_volume,
            avg_price=avg_price,
            trades=trades,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving TWAP order {twap_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/wallets/{wallet_address}/twaps", response_model=List[str], tags=["Wallets"])
async def get_wallet_twaps(
    wallet_address: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """
    Get all TWAP IDs for a specific wallet.

    - **wallet_address**: Wallet address to query
    - **start_date**: Filter TWAP orders after this date
    - **end_date**: Filter TWAP orders before this date
    """
    try:
        query = db.query(Trade.twap_id).filter(Trade.wallet_address == wallet_address)

        if start_date:
            query = query.filter(Trade.timestamp >= start_date)

        if end_date:
            query = query.filter(Trade.timestamp <= end_date)

        twap_ids = query.distinct().all()
        return [twap_id[0] for twap_id in twap_ids]

    except Exception as e:
        logger.error(f"Error retrieving TWAP IDs for wallet {wallet_address}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/status", response_model=IngestionStatusResponse, tags=["Status"])
async def get_ingestion_status(
    db: Session = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get data ingestion status."""
    try:
        latest_metadata = (
            db.query(TWAPMetadata)
            .order_by(TWAPMetadata.created_at.desc())
            .first()
        )

        if not latest_metadata:
            return IngestionStatusResponse(
                last_ingestion=None,
                total_records=0,
                status="no_data",
                last_error=None,
            )

        total_records = db.query(func.count(Trade.id)).scalar()

        return IngestionStatusResponse(
            last_ingestion=latest_metadata.last_ingestion_date,
            total_records=total_records,
            status=latest_metadata.status,
            last_error=latest_metadata.error_message,
        )

    except Exception as e:
        logger.error(f"Error retrieving ingestion status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
