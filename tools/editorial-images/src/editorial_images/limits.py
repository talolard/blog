"""Concurrency, rate limiting, and bounded retry policy."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from .models import GeneratedImage
from .service import ImageClient, ImageServiceError


class RequestLimiter:
    """Enforce both simultaneous-request and start-rate ceilings."""

    def __init__(self, requests_per_minute: int, maximum_concurrent: int = 4) -> None:
        if requests_per_minute < 1 or maximum_concurrent < 1:
            raise ValueError("Request limits must be positive")
        self._interval = 60.0 / requests_per_minute
        self._next_start = 0.0
        self._rate_lock = asyncio.Lock()
        self._concurrency = asyncio.Semaphore(maximum_concurrent)

    async def run(self, operation: Callable[[], Awaitable[GeneratedImage]]) -> GeneratedImage:
        """Start at the configured cadence and hold a slot only during the call."""

        async with self._concurrency:
            async with self._rate_lock:
                now = time.monotonic()
                delay = max(0.0, self._next_start - now)
                if delay:
                    await asyncio.sleep(delay)
                self._next_start = time.monotonic() + self._interval
            return await operation()


async def request_with_retry(
    client: ImageClient,
    limiter: RequestLimiter,
    *,
    prompt: str,
    size: str,
    references: tuple[Path, ...],
    attempts: int = 4,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    jitter: Callable[[], float] = random.random,
) -> tuple[GeneratedImage, int]:
    """Retry only classified transient failures, honoring explicit server delay."""

    for attempt in range(1, attempts + 1):
        try:
            result = await limiter.run(lambda: client.create(prompt=prompt, size=size, references=references))
            return result, attempt - 1
        except ImageServiceError as error:
            if not error.retryable or attempt == attempts:
                raise
            delay = error.retry_after if error.retry_after is not None else (2 ** (attempt - 1)) + jitter()
            await sleep(delay)
    raise AssertionError("Retry loop exhausted without returning or raising")
