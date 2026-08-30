"""A delayed fake proves the production dependency and overlap graph."""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

from PIL import Image

from editorial_images.content import load_all_posts, repository_root
from editorial_images.models import GeneratedImage, PostSource, Role
from editorial_images.planner import PlannedScene
from editorial_images.runner import generate_posts
from editorial_images.scene import new_record, render_record, SCENE_FILENAME, ScenePlan
from editorial_images.service import ImageServiceError


def _scene(title: str) -> ScenePlan:
    return ScenePlan(
        metaphor=f"A physical metaphor for {title}",
        setting="A cool-gray miniature workshop",
        humor_register="deadpan",
        tal_role="Tal operates the central mechanism",
        frozen_incident="One harmless component springs loose",
        physical_materials=("brushed metal", "cobalt resin"),
        semantic_anchors=("article-specific machinery",),
        avoid=("text", "logos"),
        image_instruction="Tal operates a tactile miniature metaphor during a harmless absurd mechanical incident.",
    )


class DelayedFakePlanner:
    """Prove that structured scene planning completes before image work begins."""

    def __init__(self) -> None:
        self.completed: set[str] = set()

    async def create(self, post: PostSource) -> PlannedScene:
        title = post.title
        await asyncio.sleep(0.005)
        self.completed.add(title)
        return PlannedScene(_scene(title), f"plan-{len(self.completed)}")


class NeverPlanner:
    """Fail immediately if a forced image rerun incorrectly replaces a current plan."""

    async def create(self, post: PostSource) -> PlannedScene:
        raise AssertionError(f"Planner should not be called for {post.catalog.key}")


class DelayedFakeClient:
    def __init__(self, planner: DelayedFakePlanner, failing_title: str = "") -> None:
        self.active = 0
        self.maximum_active = 0
        self.starts: list[tuple[str, str, int]] = []
        self.completes: list[tuple[str, str]] = []
        self.planner = planner
        self.failing_title = failing_title

    async def create(self, *, prompt: str, size: str, references: tuple[Path, ...]) -> GeneratedImage:
        title = next(line.removeprefix("Article title: ") for line in prompt.splitlines() if line.startswith("Article title: "))
        assert title in self.planner.completed
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
            identity_paths=post.identity_paths,
            identity_hashes=post.identity_hashes,
            reference_paths=post.reference_paths,
            reference_hashes=post.reference_hashes,
        )
        for post in originals
    )
    for post in posts:
        post.bundle.mkdir()
    planner = DelayedFakePlanner()
    client = DelayedFakeClient(planner)
    runs = await generate_posts(
        posts,
        planner,
        client,
        model="fake",
        planner_model="fake-planner",
        jobs=2,
        requests_per_minute=60_000,
        force=True,
    )
    assert all(run.status == "generated" for run in runs)
    assert 2 <= client.maximum_active <= 4
    desktop_starts = [start for start in client.starts if start[1] == "1920x640"]
    assert len(desktop_starts) == 2
    assert desktop_starts[0][0] != desktop_starts[1][0]
    assert all(start[2] >= 2 for start in desktop_starts)
    sibling_starts = [start for start in client.starts if start[1] != "1920x640"]
    assert sibling_starts and all(start[2] == 3 for start in sibling_starts)
    for post in posts:
        events = runs[posts.index(post)].events
        desktop_complete = next(event.monotonic_seconds for event in events if event.role is Role.HERO_DESKTOP and event.phase == "complete")
        sibling_starts = [event.monotonic_seconds for event in events if event.role is not Role.HERO_DESKTOP and event.phase == "start"]
        assert sibling_starts and min(sibling_starts) >= desktop_complete
        assert (post.bundle / "art.toml").is_file()
        assert (post.bundle / SCENE_FILENAME).is_file()


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
            identity_paths=post.identity_paths,
            identity_hashes=post.identity_hashes,
            reference_paths=post.reference_paths,
            reference_hashes=post.reference_hashes,
        )
        for index, post in enumerate(originals)
    )
    for post in posts:
        post.bundle.mkdir()
    planner = DelayedFakePlanner()
    client = DelayedFakeClient(planner, posts[0].title)
    runs = await generate_posts(
        posts,
        planner,
        client,
        model="fake",
        planner_model="fake-planner",
        jobs=2,
        requests_per_minute=60_000,
        force=True,
    )
    assert runs[0].status == "failed"
    assert runs[1].status == "generated"
    assert not (posts[0].bundle / "art.toml").exists()
    assert (posts[1].bundle / "art.toml").exists()


async def test_force_reuses_current_scene_plan(tmp_path: Path) -> None:
    original = load_all_posts(repository_root(Path(__file__)))[0]
    post = original.__class__(
        root=original.root,
        bundle=tmp_path / "post",
        catalog=original.catalog,
        english_path=original.english_path,
        title=original.title,
        normalized_article=original.normalized_article,
        localized=original.localized,
        identity_paths=original.identity_paths,
        identity_hashes=original.identity_hashes,
        reference_paths=original.reference_paths,
        reference_hashes=original.reference_hashes,
    )
    post.bundle.mkdir()
    record = new_record(post, _scene(post.title), model="planner", response_id="existing-plan")
    (post.bundle / SCENE_FILENAME).write_text(render_record(record), encoding="utf-8")
    observer = DelayedFakePlanner()
    client = DelayedFakeClient(observer)
    observer.completed.add(post.title)

    runs = await generate_posts(
        (post,),
        NeverPlanner(),
        client,
        model="fake",
        planner_model="fake-planner",
        jobs=1,
        requests_per_minute=60_000,
        force=True,
    )

    assert runs[0].status == "generated"
    assert (post.bundle / SCENE_FILENAME).read_text(encoding="utf-8") == render_record(record)
