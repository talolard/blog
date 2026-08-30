"""Narrow, serialized Git operations for one-post commits."""

from __future__ import annotations

import fcntl
import subprocess
from contextlib import contextmanager
from collections.abc import Generator
from pathlib import Path

from .models import PostSource, ROLE_SPECS


def _git(root: Path, arguments: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=capture,
        text=True,
    )


def bundle_changes(post: PostSource) -> tuple[str, ...]:
    """List exactly the dirty paths beneath a post bundle."""

    relative = post.bundle.relative_to(post.root)
    result = _git(post.root, ["status", "--porcelain", "--", str(relative)], capture=True)
    return tuple(line for line in result.stdout.splitlines() if line)


def require_clean_bundle(post: PostSource) -> None:
    """Refuse generation when unrelated work already occupies the commit scope."""

    changes = bundle_changes(post)
    if changes:
        raise RuntimeError(f"Bundle has existing changes: {'; '.join(changes)}")


@contextmanager
def git_lock(root: Path) -> Generator[None]:
    """Serialize index and commit mutations across parallel post work."""

    lock_path = root / ".git" / "editorial-images.lock"
    with lock_path.open("w", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def commit_post(post: PostSource) -> str:
    """Stage only generated contract files and return the resulting commit hash."""

    relative = post.bundle.relative_to(post.root)
    explicit = [relative / "art.toml", *(relative / spec.filename for spec in ROLE_SPECS.values())]
    with git_lock(post.root):
        _git(post.root, ["add", "--", *(str(path) for path in explicit)])
        _git(post.root, ["commit", "-m", f"Add editorial art for {post.title}", "--", *(str(path) for path in explicit)])
        result = _git(post.root, ["rev-parse", "HEAD"], capture=True)
    return result.stdout.strip()
