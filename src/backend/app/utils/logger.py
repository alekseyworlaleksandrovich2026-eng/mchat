"""Loguru logger setup."""

import sys

from loguru import logger


def setup_logger() -> None:
    """Configure loguru logger with appropriate format and levels."""
    # Remove default handler
    logger.remove()

    # Add console handler with colorized output
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level="DEBUG",
        colorize=True,
    )

    # Add file handler for errors
    logger.add(
        "logs/error.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
    )

    # Add file handler for all logs
    logger.add(
        "logs/app.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        level="INFO",
        rotation="100 MB",
        retention="7 days",
    )

    logger.info("Logger initialized")
