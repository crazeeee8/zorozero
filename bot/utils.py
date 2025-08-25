import asyncio
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple

import aiohttp
from aiohttp import ClientResponseError, ClientConnectorError, ClientPayloadError, ServerTimeoutError

# Timezone for display (IST)
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist_str() -> str:
    """Returns the current time in IST as a formatted string."""
    return datetime.now(timezone.utc).astimezone(IST).strftime('%Y-%m-%d %H:%M:%S')

def jitter(base: float, frac: float = 0.3) -> float:
    """Adds a small random variation to a number."""
    delta = base * frac
    return base + random.uniform(-delta, delta)

async def async_backoff(
    fn,
    *,
    retries: int = 5,
    base_delay: float = 1.5,
    max_delay: float = 20.0,
    exceptions: Tuple = (
        ClientConnectorError,
        ClientResponseError,
        ClientPayloadError,
        asyncio.TimeoutError,
        ServerTimeoutError,
    ),
    retry_on_status: Tuple[int, ...] = (429, 500, 502, 503, 504),
    label: str = "operation"
):
    """Generic async backoff wrapper for HTTP-like operations."""
    for attempt in range(1, retries + 1):
        try:
            return await fn()
        except ClientResponseError as cre:
            if cre.status in retry_on_status:
                delay = min(max_delay, jitter(base_delay * (2 ** (attempt - 1))))
                logging.warning(f"{label} HTTP {cre.status}, retry {attempt}/{retries} in {delay:.1f}s")
                await asyncio.sleep(delay)
                continue
            raise
        except exceptions as e:
            delay = min(max_delay, jitter(base_delay * (2 ** (attempt - 1))))
            logging.warning(f"{label} error {type(e).__name__}, retry {attempt}/{retries} in {delay:.1f}s: {e}")
            await asyncio.sleep(delay)
    # Final attempt (let exception bubble)
    return await fn()