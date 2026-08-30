"""A delayed fake proves the production dependency and overlap graph."""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

from PIL import Image

from editorial_images.content import load_all_posts, repository_root
from editorial_images.models import GeneratedImage, Role
from editorial_images.runner import generate_posts
from editorial_images.service import ImageServiceError


class DelayedFakeClient:
    def __init__(self, failing_title: str = "") -> None:
        self.active = 0
        self.maximum_active = 0
        self.starts: list[tuple[str, str, int]] = []
        self.completes: list[tuple[str, str]] = []
        self.failing_title = failing_title

    async def create(self, *, prompt: str, size: str, references: tuple[Path, ...]) -> GeneratedImage:
        title = next(line.removeprefix("Article title: ") for line in prompt.splitlines() if line.startswith("Article title: "))
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        self.starts.append((title, size, len(references)))
        try:
            await asyncio.sleep(0.02)
            if self.failing_title and self.failing_title in title:
                raise ImageServiceError("deliberate failure", retryable=False)
            width, height = (int(part) for part in size.split("x"))
            output = BytesIO()
            Image.new("RGB", (width, height), "#00a98f").save(output, format="WEBP", quality=85)
            self.completes.append((title, size))
            return GeneratedImage(output.getvalue(), f"fake-{len(self.completes)}")
        finally:
            self.active -= 1


async def test_posts_and_sibling_variants_overlap_with_desktop_first(tmp_path: Path) -> None:
    originals = load_all_posts(repository_root(Path(__file__)))[:2]
    posts = tuple(
        post.__class__(
            root=post.root,
            bundle=tmp_path / post.catalog.key.replace("/", "--"),
            catalog=post.catalog,
            english_path=post.english_path,
            title=post.title,
            normalized_article=post.normalized_article,
            localized=post.localized,
            reference_paths=post.reference_paths,
            reference_hashes=post.reference_hashes,
        )
        for post in originals
    )
    for post in posts:
        post.bundle.mkdir()
    client = DelayedFakeClient()
    runs = await generate_posts(posts, client, model="fake", jobs=2, requests_per_minute=60_000, force=True)
    assert all(run.status == "generated" for run in runs)
    assert 2 <= client.maximum_active <= 4
    desktop_starts = [start for start in client.starts if start[1] == "1920x640"]
    assert len(desktop_starts) == 2
    assert desktop_starts[0][0] != desktop_starts[1][0]
    for post in posts:
        events = runs[posts.index(post)].events
        desktop_complete = next(event.monotonic_seconds for event in events if event.role is Role.HERO_DESKTOP and event.phase == "complete")
        sibling_starts = [event.monotonic_seconds for event in events if event.role is not Role.HERO_DESKTOP and event.phase == "start"]
        assert sibling_starts and min(sibling_starts) >= desktop_complete
        assert (post.bundle / "art.toml").is_file()


async def test_failed_post_does_not_publish_or_block_other_post(tmp_path: Path) -> None:
    originals = load_all_posts(repository_root(Path(__file__)))[:2]
    posts = tuple(
        post.__class__(
            root=post.root,
            bundle=tmp_path / str(index),
            catalog=post.catalog,
            english_path=post.english_path,
            title=post.title,
            normalized_article=post.normalized_article,
            localized=post.localized,
            reference_paths=post.reference_paths,
            reference_hashes=post.reference_hashes,
        )
        for index, post in enumerate(originals)
    )
    for post in posts:
        post.bundle.mkdir()
    client = DelayedFakeClient(posts[0].title)
    runs = await generate_posts(posts, client, model="fake", jobs=2, requests_per_minute=60_000, force=True)
    assert runs[0].status == "failed"
    assert runs[1].status == "generated"
    assert not (posts[0].bundle / "art.toml").exists()
    assert (posts[1].bundle / "art.toml").exists()
