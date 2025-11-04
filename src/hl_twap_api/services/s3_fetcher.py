"""S3 data fetcher for Hyperliquid trade data."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import boto3
from botocore import UNSIGNED
from botocore.config import Config as BotoConfig
import gzip
import lz4.frame
import io

from ..config import config

logger = logging.getLogger(__name__)


class S3Fetcher:
    """Fetch trade data from Hyperliquid S3 buckets."""

    def __init__(self):
        """Initialize S3 client for Hyperliquid public buckets."""
        self.bucket_name = config.S3_BUCKET_NAME
        self.prefix = config.S3_PREFIX
        self.request_payer = config.S3_REQUEST_PAYER

        # Create S3 client with no signature (for public buckets with request-payer)
        self.s3_client = boto3.client(
            "s3",
            region_name=config.S3_REGION,
            config=BotoConfig(signature_version=UNSIGNED),
        )

    def list_objects(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[dict]:
        """
        List objects in S3 bucket within date range.

        Args:
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)

        Returns:
            List of S3 object metadata dicts
        """
        try:
            logger.info(f"Listing objects in bucket {self.bucket_name} with prefix {self.prefix}")

            objects = []
            paginator = self.s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=self.prefix,
                RequestPayer=self.request_payer
            ):
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    # Filter by date if provided
                    obj_date = obj["LastModified"].replace(tzinfo=None)

                    if start_date and obj_date < start_date:
                        continue
                    if end_date and obj_date > end_date:
                        continue

                    objects.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj_date,
                        }
                    )

            logger.info(f"Found {len(objects)} objects")
            return objects

        except Exception as e:
            logger.error(f"Error listing S3 objects: {e}")
            raise

    def fetch_object(self, key: str) -> bytes:
        """
        Fetch object content from S3.

        Args:
            key: S3 object key

        Returns:
            Object content as bytes (decompressed if needed)
        """
        try:
            logger.info(f"Fetching object: {key}")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key,
                RequestPayer=self.request_payer
            )
            content = response["Body"].read()

            # Handle compression based on file extension
            if key.endswith(".lz4"):
                content = lz4.frame.decompress(content)
            elif key.endswith(".gz"):
                content = gzip.decompress(content)

            return content

        except Exception as e:
            logger.error(f"Error fetching object {key}: {e}")
            raise

    def list_blocks_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[str]:
        """
        List block directories within date range.

        node_fills_by_block structure: node_fills_by_block/[block_number]/

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            List of block prefixes (directories)
        """
        try:
            objects = self.list_objects(start_date=start_date, end_date=end_date)

            # Extract unique block directories
            blocks = set()
            for obj in objects:
                # Extract block number from key path
                # Format: node_fills_by_block/[block_number]/...
                parts = obj["key"].split("/")
                if len(parts) >= 2:
                    blocks.add(f"{parts[0]}/{parts[1]}/")

            block_list = sorted(list(blocks))
            logger.info(f"Found {len(block_list)} unique blocks")
            return block_list

        except Exception as e:
            logger.error(f"Error listing blocks: {e}")
            raise

    def fetch_block_data(self, block_prefix: str) -> List[Tuple[str, bytes]]:
        """
        Fetch all files in a block directory.

        Args:
            block_prefix: Block directory prefix (e.g., 'node_fills_by_block/12345/')

        Returns:
            List of tuples (filename, content)
        """
        try:
            logger.info(f"Fetching data for block: {block_prefix}")

            # List all files in this block directory
            paginator = self.s3_client.get_paginator("list_objects_v2")
            files = []

            for page in paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=block_prefix,
                RequestPayer=self.request_payer
            ):
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]
                    # Skip directory markers
                    if not key.endswith("/"):
                        content = self.fetch_object(key)
                        files.append((key, content))

            logger.info(f"Fetched {len(files)} files from block {block_prefix}")
            return files

        except Exception as e:
            logger.error(f"Error fetching block data {block_prefix}: {e}")
            raise

    def fetch_new_data(
        self,
        last_fetch_date: Optional[datetime] = None,
        max_blocks: int = 100
    ) -> List[Tuple[str, bytes]]:
        """
        Fetch new data since last fetch date.

        Args:
            last_fetch_date: Last successful fetch date, or None for all data
            max_blocks: Maximum number of blocks to process in one batch

        Returns:
            List of tuples (file_key, content)
        """
        start_date = last_fetch_date or datetime(2023, 1, 1)

        # Get list of blocks
        block_prefixes = self.list_blocks_by_date_range(start_date=start_date)

        # Limit number of blocks to process
        if len(block_prefixes) > max_blocks:
            logger.warning(
                f"Found {len(block_prefixes)} blocks, limiting to {max_blocks} for this run"
            )
            block_prefixes = block_prefixes[:max_blocks]

        # Fetch data from each block
        all_files = []
        for block_prefix in block_prefixes:
            try:
                block_files = self.fetch_block_data(block_prefix)
                all_files.extend(block_files)
            except Exception as e:
                logger.warning(f"Failed to fetch block {block_prefix}: {e}")
                continue

        logger.info(f"Successfully fetched {len(all_files)} files from {len(block_prefixes)} blocks")
        return all_files
