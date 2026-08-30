"""Multimodal OpenAI boundary for turning article goals into one scene."""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from openai import AsyncOpenAI
from openai.types.responses import EasyInputMessageParam, ResponseInputContentParam

from .models import PostSource
from .scene import planning_prompt, ScenePlan

DEFAULT_PLANNER_MODEL = "gpt-5.4-mini-2026-03-17"


@dataclass(frozen=True)
class PlannedScene:
    """Typed planner output and its server-side response provenance."""

    scene: ScenePlan
    response_id: str


class ScenePlanner(Protocol):
    """Mockable boundary for the paid text-and-vision planning request."""

    async def create(self, post: PostSource) -> PlannedScene:
        """Create one canonical scene from the article and identity photos."""

        ...


def _data_url(path: Path) -> str:
    """Encode a small local identity reference without creating uploaded state."""

    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


class OpenAIScenePlanner:
    """Use structured Responses output so image prompts never depend on loose parsing."""

    def __init__(self, api_key: str, model: str = DEFAULT_PLANNER_MODEL) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def create(self, post: PostSource) -> PlannedScene:
        """Send both Tal photos with the complete planning brief and article."""

        content: list[ResponseInputContentParam] = [
            {"type": "input_text", "text": planning_prompt(post)},
            *(
                {"type": "input_image", "image_url": _data_url(path), "detail": "high"}
                for path in post.identity_paths
            ),
        ]
        message: EasyInputMessageParam = {"role": "user", "content": content}
        response = await self._client.responses.parse(
            model=self._model,
            input=[message],
            text_format=ScenePlan,
            reasoning={"effort": "low"},
            store=False,
        )
        scene = response.output_parsed
        if scene is None:
            raise RuntimeError("Scene planner returned no structured output")
        return PlannedScene(scene, response.id)
