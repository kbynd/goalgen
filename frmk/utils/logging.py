"""
Structured logging utilities
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get configured logger

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """

    logger = logging.getLogger(name)

    if not logger.handlers:
        # Configure handler
        handler = logging.StreamHandler(sys.stdout)

        # JSON formatter for Azure Application Insights
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Set level
    log_level = level or "INFO"
    logger.setLevel(getattr(logging, log_level.upper()))

    return logger
