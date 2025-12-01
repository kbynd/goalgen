"""
Retry utilities with exponential backoff
"""

import asyncio
import functools
from typing import Callable, TypeVar, Any
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


def async_retry(
    max_attempts: int = 3,
    backoff_strategy: str = "exponential",
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Async retry decorator with configurable backoff

    Args:
        max_attempts: Maximum retry attempts
        backoff_strategy: "exponential" or "linear"
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Tuple of exceptions to catch

    Usage:
        @async_retry(max_attempts=3, backoff_strategy="exponential")
        async def my_func():
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise

                    # Calculate delay
                    if backoff_strategy == "exponential":
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    else:  # linear
                        delay = min(base_delay * attempt, max_delay)

                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    await asyncio.sleep(delay)

        return wrapper
    return decorator
