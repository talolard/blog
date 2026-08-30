"""Stable hashing helpers keep provenance comparisons unsurprising."""

from __future__ import annotations

import hashlib
from pathlib import Path


def bytes_sha256(content: bytes) -> str:
    """Return the lowercase SHA-256 digest for immutable output bytes."""

    return hashlib.sha256(content).hexdigest()


def file_sha256(path: Path) -> str:
    """Hash a file in bounded chunks so large reference images stay cheap."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(content: str) -> str:
    """Hash normalized UTF-8 text exactly as it enters a prompt."""

    return bytes_sha256(content.encode("utf-8"))
