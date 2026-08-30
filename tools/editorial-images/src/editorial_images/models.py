"""Small immutable types shared across selection, generation, and validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Role(StrEnum):
    """The three independent compositions required by every published post."""

    THUMBNAIL = "thumbnail"
    HERO_DESKTOP = "hero_desktop"
    HERO_MOBILE = "hero_mobile"


@dataclass(frozen=True)
class RoleSpec:
    """Generation and placement contract for one editorial composition."""

    role: Role
    filename: str
    width: int
    height: int
    placement: str

    @property
    def size(self) -> str:
        return f"{self.width}x{self.height}"


ROLE_SPECS: dict[Role, RoleSpec] = {
    Role.THUMBNAIL: RoleSpec(Role.THUMBNAIL, "thumbnail.webp", 960, 720, "280x210 featured; 120x90 archive"),
    Role.HERO_DESKTOP: RoleSpec(Role.HERO_DESKTOP, "hero-desktop.webp", 1920, 640, "approximately 1180x393"),
    Role.HERO_MOBILE: RoleSpec(Role.HERO_MOBILE, "hero-mobile.webp", 960, 720, "approximately 362x272"),
}


@dataclass(frozen=True)
class CatalogEntry:
    """Human-reviewed intent and references for one bundle."""

    key: str
    thread: str
    audit_mode: str
    concept: str
    references: tuple[str, ...]
    localized_concepts: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class LocalizedArticle:
    """A localized source file whose title and content hash affect staleness."""

    language: str
    path: Path
    title: str
    sha256: str


@dataclass(frozen=True)
class PostSource:
    """All deterministic inputs for one eligible published bundle."""

    root: Path
    bundle: Path
    catalog: CatalogEntry
    english_path: Path
    title: str
    normalized_article: str
    localized: tuple[LocalizedArticle, ...]
    reference_paths: tuple[Path, ...]
    reference_hashes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class GeneratedImage:
    """Decoded image bytes and request provenance returned by a client."""

    content: bytes
    request_id: str


@dataclass(frozen=True)
class OutputRecord:
    """Validated output metadata written into `art.toml`."""

    role: Role
    path: str
    sha256: str
    width: int
    height: int
    compression: int
    request_id: str


@dataclass(frozen=True)
class GenerationEvent:
    """One trace point used for real and fake concurrency evidence."""

    post: str
    role: Role
    phase: str
    monotonic_seconds: float
    request_id: str = ""
