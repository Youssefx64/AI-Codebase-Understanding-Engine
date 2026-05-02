"""Centralized logging configuration using loguru."""

import sys
from typing import Any

from loguru import logger

from core.config import get_settings


def setup_logging() -> None:
    """Configure loguru logger for the application."""
    settings = get_settings()

    logger.remove()

    log_level = "DEBUG" if settings.debug else "INFO"
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(sys.stdout, format=log_format, level=log_level, colorize=True)

    if settings.environment == "production":
        logger.add(
            "logs/app.log",
            rotation="100 MB",
            retention="30 days",
            level="INFO",
            format="{time} | {level} | {name}:{function}:{line} | {message}",
        )

    logger.info(
        "Logging configured",
        environment=settings.environment,
        level=log_level,
    )


def get_logger(name: str) -> Any:
    """Get a named logger instance."""
    return logger.bind(module=name)
