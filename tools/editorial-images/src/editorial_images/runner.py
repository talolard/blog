"""Execute the desktop-first graph across independent post jobs."""

from __future__ import annotations

import asyncio
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .hashing import bytes_sha256
from .limits import RequestLimiter, request_with_retry
from .manifest import is_stale, publish_staged, render_manifest
from .models import GenerationEvent, OutputRecord, PostSource, Role, ROLE_SPECS
from .prompting import assemble_prompt
from .service import ImageClient


@dataclass(frozen=True)
class PostRun:
    """Complete result for one post, including recoverable failure detail."""

    key: str
    status: str
    retries: int
    elapsed_seconds: float
    events: tuple[GenerationEvent, ...]
    error: str = ""


def source_revision(root: Path) -> str:
    """Record the exact Git revision without including uncommitted content."""

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _validate_bytes(content: bytes, role: Role) -> None:
    spec = ROLE_SPECS[role]
    with tempfile.NamedTemporaryFile(suffix=".webp") as handle:
        handle.write(content)
        handle.flush()
        with Image.open(handle.name) as image:
            image.load()
            if image.format != "WEBP" or image.size != (spec.width, spec.height):
                raise ValueError(f"Invalid {role.value}: format={image.format}, size={image.size}")


async def _one_image(
    post: PostSource,
    role: Role,
    references: tuple[Path, ...],
    client: ImageClient,
    limiter: RequestLimiter,
    events: list[GenerationEvent],
) -> tuple[OutputRecord, bytes, int]:
    events.append(GenerationEvent(post.catalog.key, role, "start", time.monotonic()))
    spec = ROLE_SPECS[role]
    generated, retries = await request_with_retry(
        client,
        limiter,
        prompt=assemble_prompt(post, role),
        size=spec.size,
        references=references,
    )
    _validate_bytes(generated.content, role)
    events.append(GenerationEvent(post.catalog.key, role, "complete", time.monotonic(), generated.request_id))
    record = OutputRecord(role, spec.filename, bytes_sha256(generated.content), spec.width, spec.height, 85, generated.request_id)
    return record, generated.content, retries


async def generate_post(
    post: PostSource,
    client: ImageClient,
    limiter: RequestLimiter,
    *,
    model: str,
    force: bool,
) -> PostRun:
    """Stage desktop then concurrent recompositions, publishing only on success."""

    started = time.monotonic()
    if not force and not is_stale(post):
        return PostRun(post.catalog.key, "current", 0, 0.0, ())
    events: list[GenerationEvent] = []
    retries = 0
    try:
        with tempfile.TemporaryDirectory(prefix=".editorial-", dir=post.bundle) as temporary:
            staging = Path(temporary)
            desktop_record, desktop_bytes, desktop_retries = await _one_image(
                post,
                Role.HERO_DESKTOP,
                post.reference_paths,
                client,
                limiter,
                events,
            )
            retries += desktop_retries
            desktop_path = staging / ROLE_SPECS[Role.HERO_DESKTOP].filename
            desktop_path.write_bytes(desktop_bytes)

            thumbnail_task = asyncio.create_task(
                _one_image(post, Role.THUMBNAIL, (desktop_path,), client, limiter, events)
            )
            mobile_task = asyncio.create_task(
                _one_image(post, Role.HERO_MOBILE, (desktop_path,), client, limiter, events)
            )
            thumbnail_result, mobile_result = await asyncio.gather(thumbnail_task, mobile_task)
            thumbnail_record, thumbnail_bytes, thumbnail_retries = thumbnail_result
            mobile_record, mobile_bytes, mobile_retries = mobile_result
            retries += thumbnail_retries + mobile_retries
            (staging / ROLE_SPECS[Role.THUMBNAIL].filename).write_bytes(thumbnail_bytes)
            (staging / ROLE_SPECS[Role.HERO_MOBILE].filename).write_bytes(mobile_bytes)
            records = (thumbnail_record, desktop_record, mobile_record)
            manifest = render_manifest(post, records, model=model, source_revision=source_revision(post.root))
            (staging / "art.toml").write_text(manifest, encoding="utf-8")
            publish_staged(staging, post.bundle)
        return PostRun(post.catalog.key, "generated", retries, time.monotonic() - started, tuple(events))
    except Exception as error:
        return PostRun(post.catalog.key, "failed", retries, time.monotonic() - started, tuple(events), str(error))


async def generate_posts(
    posts: tuple[PostSource, ...],
    client: ImageClient,
    *,
    model: str,
    jobs: int,
    requests_per_minute: int,
    force: bool = False,
) -> tuple[PostRun, ...]:
    """Overlap independent posts while one failure leaves the rest running."""

    if jobs < 1:
        raise ValueError("jobs must be positive")
    limiter = RequestLimiter(requests_per_minute, maximum_concurrent=4)
    post_slots = asyncio.Semaphore(jobs)

    async def run(post: PostSource) -> PostRun:
        async with post_slots:
            return await generate_post(post, client, limiter, model=model, force=force)

    return tuple(await asyncio.gather(*(run(post) for post in posts)))
