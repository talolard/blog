"""Command-line selection keeps paid generation explicit and resumable."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .content import load_all_posts, repository_root
from .gitops import commit_post, require_clean_bundle
from .manifest import is_stale, validate_bundle
from .models import PostSource
from .planner import DEFAULT_PLANNER_MODEL, OpenAIScenePlanner
from .prompting import PROMPT_VERSION, prompt_hash
from .review import build_review
from .runner import PostRun, generate_posts
from .service import OpenAIImageClient
from .scene import current_record, planner_input_hash

DEFAULT_MODEL = "gpt-image-2-2026-04-21"
LOGGER = logging.getLogger(__name__)
POC_KEYS = (
    "genai/vibe-coding-stablenormal-modal",
    "genai/engineering-agents-building-trust",
    "genai/learning-to-read-with-ai",
    "genai/triton-inference-server",
    "scripture-app",
)


class Arguments(argparse.Namespace):
    """Typed argparse result so option values never leak as dynamic values."""

    all_eligible: bool
    poc: bool
    stale: bool
    post: list[str]
    force: bool
    dry_run: bool
    model: str
    planner_model: str
    jobs: int
    requests_per_minute: int
    commit: bool
    validate: bool
    review: bool
    replan: bool


def parser() -> argparse.ArgumentParser:
    """Expose the accepted repeatable selection and execution controls."""

    result = argparse.ArgumentParser(prog="editorial-images")
    selection = result.add_mutually_exclusive_group()
    _ = selection.add_argument("--all-eligible", action="store_true")
    _ = selection.add_argument("--poc", action="store_true")
    _ = selection.add_argument("--stale", action="store_true")
    _ = result.add_argument("--post", action="append", default=[], metavar="PATH")
    _ = result.add_argument("--force", action="store_true")
    _ = result.add_argument("--dry-run", action="store_true")
    _ = result.add_argument("--model", default=DEFAULT_MODEL)
    _ = result.add_argument("--planner-model", default=DEFAULT_PLANNER_MODEL)
    _ = result.add_argument("--replan", action="store_true")
    _ = result.add_argument("--jobs", type=int, default=2)
    _ = result.add_argument("--requests-per-minute", type=int, default=5)
    _ = result.add_argument("--commit", action="store_true")
    _ = result.add_argument("--validate", action="store_true")
    _ = result.add_argument("--review", action="store_true")
    return result


def _key(value: str, root: Path) -> str:
    candidate = Path(value)
    if candidate.is_absolute():
        candidate = candidate.relative_to(root)
    text = candidate.as_posix().rstrip("/")
    for prefix in ("content/posts/", "posts/"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    if text.endswith("/index.md"):
        text = text[: -len("/index.md")]
    return text


def select_posts(arguments: Arguments, root: Path, all_posts: tuple[PostSource, ...]) -> tuple[PostSource, ...]:
    """Resolve exact bundle selections and reject typos instead of broad matching."""

    by_key = {post.catalog.key: post for post in all_posts}
    requested = tuple(arguments.post)
    if requested:
        keys = tuple(_key(value, root) for value in requested)
    elif arguments.poc:
        keys = POC_KEYS
    elif arguments.all_eligible or arguments.stale or arguments.validate or arguments.review:
        keys = tuple(by_key)
    else:
        raise ValueError("Choose --post, --poc, --all-eligible, --stale, --validate, or --review")
    unknown = tuple(key for key in keys if key not in by_key)
    if unknown:
        raise ValueError(f"Unknown post selection: {', '.join(unknown)}")
    return tuple(by_key[key] for key in keys)


def _print_dry_run(posts: tuple[PostSource, ...], model: str) -> None:
    print(f"dry-run: {len(posts)} posts, model={model}, prompt={PROMPT_VERSION}")
    for post in posts:
        scene_record = current_record(post)
        if scene_record is None:
            print(f"{post.catalog.key}\t{post.catalog.audit_mode}\tplan-needed\t{planner_input_hash(post)}")
        else:
            print(f"{post.catalog.key}\t{post.catalog.audit_mode}\tplan-current\t{prompt_hash(post, scene_record.scene)}")


def _validate(posts: tuple[PostSource, ...]) -> int:
    errors = tuple(error for post in posts for error in validate_bundle(post))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Validated {len(posts)} editorial manifests and {len(posts) * 3} WebP outputs.")
    return 0


async def _generate(arguments: Arguments, root: Path, posts: tuple[PostSource, ...]) -> tuple[PostRun, ...]:
    if arguments.replan and not arguments.force:
        raise ValueError("--replan requires --force because a new scene must regenerate all three images")
    for post in posts:
        require_clean_bundle(post)
    load_dotenv(root / ".env", override=False)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment or repository .env")
    LOGGER.info(
        "Selected %d post(s); image-model=%s, planner-model=%s, jobs=%d, requests/minute=%d, force=%s, replan=%s",
        len(posts),
        arguments.model,
        arguments.planner_model,
        arguments.jobs,
        arguments.requests_per_minute,
        arguments.force,
        arguments.replan,
    )
    planner = OpenAIScenePlanner(api_key, arguments.planner_model)
    client = OpenAIImageClient(api_key, arguments.model)
    return await generate_posts(
        posts,
        planner,
        client,
        model=arguments.model,
        planner_model=arguments.planner_model,
        jobs=arguments.jobs,
        requests_per_minute=arguments.requests_per_minute,
        force=arguments.force,
        replan=arguments.replan,
    )


def main() -> int:
    """Run read-only modes without credentials; generate only after explicit selection."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    arguments = parser().parse_args(namespace=Arguments())
    try:
        root = repository_root()
        all_posts = load_all_posts(root)
        posts = select_posts(arguments, root, all_posts)
        if arguments.validate:
            return _validate(posts)
        if arguments.review:
            location = build_review(root, posts)
            print(location)
            return 0
        if arguments.stale:
            stale = tuple(post for post in posts if is_stale(post))
            for post in stale:
                print(post.catalog.key)
            print(f"{len(stale)} stale of {len(posts)}", file=sys.stderr)
            return 0
        if arguments.dry_run:
            _print_dry_run(posts, arguments.model)
            return 0
        runs = asyncio.run(_generate(arguments, root, posts))
        commits: dict[str, str] = {}
        if arguments.commit:
            by_key = {post.catalog.key: post for post in posts}
            for run in runs:
                if run.status == "generated":
                    commits[run.key] = commit_post(by_key[run.key])
        build_review(root, posts, runs)
        failed = tuple(run for run in runs if run.status == "failed")
        for run in runs:
            suffix = f" commit={commits[run.key]}" if run.key in commits else ""
            print(f"{run.key}: {run.status}, retries={run.retries}, elapsed={run.elapsed_seconds:.1f}s{suffix}")
            if run.error:
                print(f"  {run.error}", file=sys.stderr)
        return 1 if failed else 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"editorial-images: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
