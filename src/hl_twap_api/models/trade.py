"""SQLAlchemy models for TWAP trades."""

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Trade(Base):
    """Individual trade execution within a TWAP order."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    twap_id = Column(String, nullable=False, index=True)
    wallet_address = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    asset = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    side = Column(String, nullable=False)  # 'buy' or 'sell'
    fee = Column(Float, default=0.0)
    exchange = Column(String, default="hyperliquid")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_wallet_timestamp", "wallet_address", "timestamp"),
        Index("idx_twap_timestamp", "twap_id", "timestamp"),
    )

    def __repr__(self):
        return f"<Trade(twap_id={self.twap_id}, wallet={self.wallet_address}, asset={self.asset}, qty={self.quantity})>"


class TWAPMetadata(Base):
    """Metadata for tracking data ingestion status."""

    __tablename__ = "twap_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_ingestion_date = Column(DateTime, nullable=False)
    records_processed = Column(Integer, default=0)
    s3_object_key = Column(String, nullable=True)
    status = Column(String, default="success")  # success, partial, failed
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TWAPMetadata(date={self.last_ingestion_date}, status={self.status})>"
