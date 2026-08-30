"""Mockable OpenAI boundary and retry classification."""

from __future__ import annotations

import base64
from contextlib import ExitStack
from pathlib import Path
from typing import Literal, Protocol

from openai import APIStatusError, AsyncOpenAI, BadRequestError, InternalServerError, RateLimitError

from .models import GeneratedImage


class ImageServiceError(RuntimeError):
    """A classified API failure with explicit retry intent."""

    def __init__(self, message: str, *, retryable: bool, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.retry_after = retry_after


class ImageClient(Protocol):
    """Minimum async image surface needed by the dependency graph."""

    async def create(self, *, prompt: str, size: str, references: tuple[Path, ...]) -> GeneratedImage:
        """Generate from text or edit from semantic image references."""

        ...


def _retry_after(error: APIStatusError) -> float | None:
    value = error.response.headers.get("retry-after")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


class OpenAIImageClient:
    """Use GPT Image directly while keeping credentials and SDK types contained."""

    def __init__(self, api_key: str, model: str, quality: Literal["high"] = "high", compression: int = 85) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._quality: Literal["high"] = quality
        self._compression = compression

    async def create(self, *, prompt: str, size: str, references: tuple[Path, ...]) -> GeneratedImage:
        """Return decoded WebP bytes and the server request ID for provenance."""

        try:
            if references:
                with ExitStack() as stack:
                    handles = [stack.enter_context(path.open("rb")) for path in references]
                    response = await self._client.images.with_raw_response.edit(
                        image=handles,
                        prompt=prompt,
                        model=self._model,
                        quality=self._quality,
                        size=size,
                        output_format="webp",
                        output_compression=self._compression,
                    )
            else:
                response = await self._client.images.with_raw_response.generate(
                    prompt=prompt,
                    model=self._model,
                    quality=self._quality,
                    size=size,
                    output_format="webp",
                    output_compression=self._compression,
                )
            parsed = response.parse()
            if not parsed.data:
                raise ImageServiceError("Image response had no data entries", retryable=False)
            encoded = parsed.data[0].b64_json
            if encoded is None:
                raise ImageServiceError("Image response had no base64 payload", retryable=False)
            return GeneratedImage(base64.b64decode(encoded, validate=True), response.request_id or "unknown")
        except (RateLimitError, InternalServerError) as error:
            raise ImageServiceError(str(error), retryable=True, retry_after=_retry_after(error)) from error
        except BadRequestError as error:
            raise ImageServiceError(str(error), retryable=False) from error
        except APIStatusError as error:
            retryable = error.status_code >= 500
            raise ImageServiceError(str(error), retryable=retryable, retry_after=_retry_after(error)) from error
