"""The retry policy distinguishes transient service failures from terminal ones."""

from __future__ import annotations

from pathlib import Path

import pytest

from editorial_images.limits import RequestLimiter, request_with_retry
from editorial_images.models import GeneratedImage
from editorial_images.service import ImageServiceError


class SequenceClient:
    def __init__(self, failures: tuple[ImageServiceError, ...]) -> None:
        self.failures = list(failures)
        self.calls = 0

    async def create(self, *, prompt: str, size: str, references: tuple[Path, ...]) -> GeneratedImage:
        self.calls += 1
        if self.failures:
            raise self.failures.pop(0)
        return GeneratedImage(b"ok", "req-ok")


async def _no_sleep(delay: float) -> None:
    assert delay >= 0


async def test_retry_honors_retryable_classification() -> None:
    client = SequenceClient((ImageServiceError("rate", retryable=True, retry_after=0),))
    result, retries = await request_with_retry(
        client,
        RequestLimiter(60_000),
        prompt="p",
        size="960x720",
        references=(),
        sleep=_no_sleep,
        jitter=lambda: 0,
    )
    assert result.request_id == "req-ok"
    assert retries == 1
    assert client.calls == 2


async def test_terminal_failure_is_not_retried() -> None:
    client = SequenceClient((ImageServiceError("invalid", retryable=False),))
    with pytest.raises(ImageServiceError):
        await request_with_retry(
            client,
            RequestLimiter(60_000),
            prompt="p",
            size="960x720",
            references=(),
            sleep=_no_sleep,
        )
    assert client.calls == 1
