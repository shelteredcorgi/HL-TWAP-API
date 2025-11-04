"""Data processor for Hyperliquid trade data."""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import insert

from ..models.trade import Trade, TWAPMetadata

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and store trade data from Hyperliquid."""

    @staticmethod
    def parse_fill_data(raw_data: bytes) -> pd.DataFrame:
        """
        Parse Hyperliquid fill data into DataFrame.

        Hyperliquid fill format (from node_fills API):
        {
            "user": "0x...",
            "coin": "BTC",
            "px": "45000.0",
            "sz": "1.5",
            "side": "B" or "A",
            "time": 1704110400000,
            "startPosition": "0.0",
            "dir": "Open Long" or "Close Short", etc.,
            "closedPnl": "0.0",
            "hash": "0x...",
            "oid": 12345,
            "crossed": true,
            "fee": "10.0",
            "tid": 67890,
            "feeToken": "USDC"
        }

        Args:
            raw_data: Raw file content (JSON lines format)

        Returns:
            Parsed DataFrame
        """
        try:
            # Parse JSON lines format
            lines = raw_data.decode("utf-8").strip().split("\n")
            data = [json.loads(line) for line in lines if line.strip()]

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            logger.info(f"Parsed {len(df)} fill records")
            return df

        except Exception as e:
            logger.error(f"Error parsing fill data: {e}")
            raise

    @staticmethod
    def normalize_fill_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize Hyperliquid fill data to standard format.

        Args:
            df: Raw DataFrame with Hyperliquid fills

        Returns:
            Normalized DataFrame
        """
        if df.empty:
            return df

        # Map Hyperliquid columns to our schema
        column_mapping = {
            "user": "wallet_address",
            "coin": "asset",
            "px": "price",
            "sz": "quantity",
            "time": "timestamp",
            "oid": "twap_id",  # Use order ID as TWAP ID
        }

        df = df.rename(columns=column_mapping)

        # Convert timestamp from milliseconds to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)

        # Convert side (B=buy, A=sell)
        if "side" in df.columns:
            df["side"] = df["side"].map({"B": "buy", "A": "sell"}).fillna("unknown")

        # Ensure numeric types
        if "quantity" in df.columns:
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        if "price" in df.columns:
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
        if "fee" in df.columns:
            df["fee"] = pd.to_numeric(df["fee"], errors="coerce")
        else:
            df["fee"] = 0.0

        # Add exchange
        df["exchange"] = "hyperliquid"

        # Convert twap_id to string
        if "twap_id" in df.columns:
            df["twap_id"] = df["twap_id"].astype(str)

        # Drop rows with missing critical fields
        required_fields = ["wallet_address", "timestamp", "asset"]
        df = df.dropna(subset=[f for f in required_fields if f in df.columns])

        # Select only the columns we need
        final_columns = [
            "twap_id",
            "wallet_address",
            "timestamp",
            "asset",
            "quantity",
            "price",
            "side",
            "fee",
            "exchange",
        ]
        df = df[[col for col in final_columns if col in df.columns]]

        logger.info(f"Normalized to {len(df)} valid records")
        return df

    @staticmethod
    def group_by_twap(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Group trades by TWAP ID (order ID).

        Args:
            df: DataFrame with trade data

        Returns:
            Dictionary mapping TWAP IDs to DataFrames
        """
        if df.empty or "twap_id" not in df.columns:
            logger.warning("No twap_id column found or empty DataFrame")
            return {}

        grouped = {twap_id: group for twap_id, group in df.groupby("twap_id")}

        logger.info(f"Grouped data into {len(grouped)} TWAP orders")
        return grouped

    @staticmethod
    def bulk_insert_trades(df: pd.DataFrame, db: Session) -> int:
        """
        Bulk insert trades into database for better performance.

        Args:
            df: DataFrame with normalized trade data
            db: Database session

        Returns:
            Number of records inserted
        """
        if df.empty:
            return 0

        try:
            # Convert DataFrame to list of dicts
            records = df.to_dict("records")

            # Use SQLAlchemy bulk insert
            stmt = insert(Trade)
            db.execute(stmt, records)

            logger.info(f"Bulk inserted {len(records)} records")
            return len(records)

        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            raise

    @staticmethod
    def save_to_db(df: pd.DataFrame, db: Session, s3_key: str = None) -> int:
        """
        Save DataFrame to database using bulk insert.

        Args:
            df: DataFrame with normalized trade data
            db: Database session
            s3_key: S3 object key for metadata

        Returns:
            Number of records inserted
        """
        try:
            records_inserted = DataProcessor.bulk_insert_trades(df, db)

            # Add metadata record
            metadata = TWAPMetadata(
                last_ingestion_date=datetime.utcnow(),
                records_processed=records_inserted,
                s3_object_key=s3_key,
                status="success",
            )
            db.add(metadata)

            db.commit()
            logger.info(f"Inserted {records_inserted} records into database")
            return records_inserted

        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()

            # Log failed ingestion
            metadata = TWAPMetadata(
                last_ingestion_date=datetime.utcnow(),
                records_processed=0,
                s3_object_key=s3_key,
                status="failed",
                error_message=str(e),
            )
            db.add(metadata)
            db.commit()
            raise

    @staticmethod
    def process_and_store(
        file_list: List[Tuple[str, bytes]], db: Session
    ) -> int:
        """
        Process multiple data files and store in database.

        Args:
            file_list: List of tuples (file_key, content)
            db: Database session

        Returns:
            Total records processed
        """
        total_records = 0
        all_dataframes = []

        # Parse all files first
        for file_key, raw_data in file_list:
            try:
                df = DataProcessor.parse_fill_data(raw_data)
                if not df.empty:
                    all_dataframes.append(df)
            except Exception as e:
                logger.error(f"Error parsing file {file_key}: {e}")
                continue

        if not all_dataframes:
            logger.warning("No data to process")
            return 0

        # Concatenate all DataFrames
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        logger.info(f"Combined {len(combined_df)} records from {len(all_dataframes)} files")

        # Normalize data
        normalized_df = DataProcessor.normalize_fill_data(combined_df)

        # Remove duplicates based on key fields
        if not normalized_df.empty:
            normalized_df = normalized_df.drop_duplicates(
                subset=["wallet_address", "timestamp", "asset", "price", "quantity"],
                keep="first"
            )
            logger.info(f"After deduplication: {len(normalized_df)} records")

        # Bulk insert into database
        if not normalized_df.empty:
            total_records = DataProcessor.save_to_db(
                normalized_df,
                db,
                s3_key=f"batch_{len(file_list)}_files"
            )

        logger.info(f"Total records processed: {total_records}")
        return total_records
