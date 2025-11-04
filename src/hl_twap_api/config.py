"""Configuration management for HL-TWAP-API."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hl_twap.db")

    # S3
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "hl-mainnet-node-data")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    S3_PREFIX = os.getenv("S3_PREFIX", "node_fills_by_block/")
    S3_REQUEST_PAYER = os.getenv("S3_REQUEST_PAYER", "requester")

    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_KEY = os.getenv("API_KEY", "dev-key-change-in-production")

    # Scheduler
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_HOUR = int(os.getenv("SCHEDULER_HOUR", "2"))
    SCHEDULER_MINUTE = int(os.getenv("SCHEDULER_MINUTE", "0"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
