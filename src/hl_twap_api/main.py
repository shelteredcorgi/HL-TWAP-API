"""Main entry point for the application."""

import logging
import uvicorn
from .api.app import app
from .utils.scheduler import start_scheduler
from .config import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Start the application with API server and scheduler."""
    logger.info("Starting Hyperliquid TWAP API...")

    # Start background scheduler
    start_scheduler()

    # Start API server
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level=config.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
