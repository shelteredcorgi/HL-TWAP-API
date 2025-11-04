"""Scheduler for daily data ingestion."""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import config
from ..models.database import get_db
from ..models.trade import TWAPMetadata
from ..services.s3_fetcher import S3Fetcher
from ..services.data_processor import DataProcessor

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_daily_ingestion():
    """
    Run daily data ingestion from S3.

    This job:
    1. Fetches the last successful ingestion date from metadata
    2. Retrieves new data from S3 since that date
    3. Processes and stores the data in the database
    4. Logs the results
    """
    logger.info("Starting daily data ingestion...")

    try:
        with get_db() as db:
            # Get last successful ingestion date
            last_metadata = (
                db.query(TWAPMetadata)
                .filter(TWAPMetadata.status == "success")
                .order_by(TWAPMetadata.last_ingestion_date.desc())
                .first()
            )

            last_fetch_date = last_metadata.last_ingestion_date if last_metadata else None

            if last_fetch_date:
                logger.info(f"Last successful ingestion: {last_fetch_date}")
            else:
                logger.info("No previous ingestion found, fetching all available data")

            # Fetch new data from S3
            s3_fetcher = S3Fetcher()
            raw_data_list = s3_fetcher.fetch_new_data(last_fetch_date)

            if not raw_data_list:
                logger.info("No new data to process")
                return

            # Process and store data
            total_records = DataProcessor.process_and_store(raw_data_list, db)

            logger.info(f"Daily ingestion completed successfully. Processed {total_records} records.")

    except Exception as e:
        logger.error(f"Daily ingestion failed: {e}", exc_info=True)
        raise


def start_scheduler():
    """
    Start the background scheduler for daily data ingestion.

    The scheduler runs at the configured time (default: 2:00 AM UTC).
    """
    if not config.SCHEDULER_ENABLED:
        logger.info("Scheduler is disabled")
        return

    # Schedule daily job
    trigger = CronTrigger(
        hour=config.SCHEDULER_HOUR,
        minute=config.SCHEDULER_MINUTE,
        timezone="UTC",
    )

    scheduler.add_job(
        run_daily_ingestion,
        trigger=trigger,
        id="daily_ingestion",
        name="Daily TWAP Data Ingestion",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started. Daily ingestion scheduled at {config.SCHEDULER_HOUR:02d}:{config.SCHEDULER_MINUTE:02d} UTC"
    )


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
