"""Discover published bundles and normalize complete article sources."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import cast

from .hashing import file_sha256
from .models import CatalogEntry, LocalizedArticle, PostSource

CatalogValue = str | list[str]
CatalogTable = dict[str, CatalogValue]

_FRONT_MATTER = re.compile(r"\A(?P<mark>\+\+\+|---)\s*\n(?P<body>.*?)(?:\n(?P=mark)\s*\n)", re.DOTALL)
_TOML_TITLE = re.compile(r"(?m)^title\s*=\s*(['\"])(?P<title>.*?)\1\s*$")
_YAML_TITLE = re.compile(r"(?m)^title:\s*(['\"]?)(?P<title>.*?)\1\s*$")
_DRAFT_TRUE = re.compile(r"(?mi)^draft\s*(?:=|:)\s*true\s*$")
_IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\([^)]*\)")
_INLINE_LINK = re.compile(r"\[(?P<label>[^\]]+)\]\([^)]*\)")
_REFERENCE_LINK = re.compile(r"\[(?P<label>[^\]]+)\]\[[^\]]*\]")
_REFERENCE_DEFINITION = re.compile(r"(?m)^\s*\[[^\]]+\]:\s*\S+.*$")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def repository_root(start: Path | None = None) -> Path:
    """Find the Hugo root without depending on the caller's current directory."""

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "hugo.toml").is_file() and (candidate / "content" / "posts").is_dir():
            return candidate
    raise FileNotFoundError("Could not find Hugo repository root")


def split_front_matter(content: str) -> tuple[str, str]:
    """Separate either TOML or YAML front matter from the Markdown body."""

    match = _FRONT_MATTER.match(content)
    if match is None:
        return "", content
    return match.group("body"), content[match.end() :]


def front_matter_title(content: str) -> str:
    """Extract the title without coercing the rest of heterogeneous front matter."""

    front_matter, _ = split_front_matter(content)
    for pattern in (_TOML_TITLE, _YAML_TITLE):
        match = pattern.search(front_matter)
        if match is not None:
            return match.group("title").strip().strip("'\"")
    raise ValueError("Article front matter has no title")


def is_draft(content: str) -> bool:
    """Treat only an explicit true value as draft; published imports use false."""

    front_matter, _ = split_front_matter(content)
    return _DRAFT_TRUE.search(front_matter) is not None


def normalize_article(content: str) -> str:
    """Remove transport syntax while retaining all meaningful prose and code."""

    _, body = split_front_matter(content)
    body = _HTML_COMMENT.sub("", body)
    body = _IMAGE.sub(lambda match: f"[Image caption: {match.group('alt')}]", body)
    body = _INLINE_LINK.sub(lambda match: match.group("label"), body)
    body = _REFERENCE_LINK.sub(lambda match: match.group("label"), body)
    body = _REFERENCE_DEFINITION.sub("", body)
    lines = [line.rstrip() for line in body.splitlines()]
    return "\n".join(lines).strip() + "\n"


def load_catalog(root: Path) -> dict[str, CatalogEntry]:
    """Read the checked-in editorial audit as strictly shaped catalog entries."""

    raw = tomllib.loads((root / "data" / "editorial_posts.toml").read_text(encoding="utf-8"))
    posts = cast(dict[str, CatalogTable], raw["posts"])
    result: dict[str, CatalogEntry] = {}
    for key, values in posts.items():
        result[key] = CatalogEntry(
            key=key,
            thread=cast(str, values["thread"]),
            audit_mode=cast(str, values["audit_mode"]),
            concept=cast(str, values["concept"]),
            references=tuple(cast(list[str], values["references"])),
            localized_concepts=tuple(
                (language, cast(str, values[field]))
                for language, field in (("de", "alt_de"), ("he", "alt_he"))
                if field in values
            ),
        )
    return result


def _language_for(path: Path) -> str:
    parts = path.name.split(".")
    return parts[1] if len(parts) == 3 else "en"


def load_post(root: Path, entry: CatalogEntry) -> PostSource:
    """Resolve one catalog entry and reject missing or draft English sources."""

    bundle = root / "content" / "posts" / entry.key
    english_path = bundle / "index.md"
    english = english_path.read_text(encoding="utf-8")
    if is_draft(english):
        raise ValueError(f"Draft is not eligible: {english_path}")

    localized: list[LocalizedArticle] = []
    for path in sorted(bundle.glob("index*.md")):
        content = path.read_text(encoding="utf-8")
        if is_draft(content):
            continue
        localized.append(LocalizedArticle(_language_for(path), path, front_matter_title(content), file_sha256(path)))

    reference_paths = tuple(bundle / reference for reference in entry.references)
    missing = tuple(path for path in reference_paths if not path.is_file())
    if missing:
        listed = ", ".join(str(path.relative_to(root)) for path in missing)
        raise FileNotFoundError(f"Missing declared reference(s): {listed}")

    return PostSource(
        root=root,
        bundle=bundle,
        catalog=entry,
        english_path=english_path,
        title=front_matter_title(english),
        normalized_article=normalize_article(english),
        localized=tuple(localized),
        reference_paths=reference_paths,
        reference_hashes=tuple((path.name, file_sha256(path)) for path in reference_paths),
    )


def load_all_posts(root: Path) -> tuple[PostSource, ...]:
    """Load the exact thirty-entry published catalog in stable key order."""

    catalog = load_catalog(root)
    posts = tuple(load_post(root, catalog[key]) for key in sorted(catalog))
    if len(posts) != 30:
        raise ValueError(f"Expected 30 eligible bundles, found {len(posts)}")
    return posts
