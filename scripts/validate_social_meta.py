# /// script
# dependencies = [
#   "pillow",
# ]
# ///

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
HUGO_CONFIG = ROOT / "hugo.toml"

MIN_WIDTH = 1200
MIN_HEIGHT = 630
MIN_RATIO = 1.86
MAX_RATIO = 1.96
WARN_BYTES = 4 * 1024 * 1024
MAX_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class PageInfo:
    html_path: Path
    canonical: str
    content_file: str
    og_type: str
    tags: dict[str, str]


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs if v is not None}
        if tag == "meta":
            if "property" in attr_map and "content" in attr_map:
                self.tags[attr_map["property"]] = attr_map["content"]
            if "name" in attr_map and "content" in attr_map:
                self.tags[attr_map["name"]] = attr_map["content"]
        if tag == "link" and attr_map.get("rel") == "canonical" and "href" in attr_map:
            self.tags["canonical"] = attr_map["href"]


def load_base_url() -> str:
    config = tomllib.loads(HUGO_CONFIG.read_text(encoding="utf-8"))
    base = str(config.get("baseURL", "")).rstrip("/")
    if not base:
        raise SystemExit("hugo.toml missing baseURL")
    return base


def parse_page(html_path: Path) -> PageInfo:
    parser = HeadParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    tags = parser.tags
    return PageInfo(
        html_path=html_path,
        canonical=tags.get("canonical", ""),
        content_file=tags.get("x-content-file", ""),
        og_type=tags.get("og:type", ""),
        tags=tags,
    )


def iter_pages() -> list[PageInfo]:
    pages: list[PageInfo] = []
    for html_path in sorted(PUBLIC_DIR.rglob("index.html")):
        pages.append(parse_page(html_path))
    return pages


def url_to_local_image(url: str, base_url: str) -> Path | None:
    if url.startswith(base_url + "/"):
        relative = url[len(base_url) :]
        return PUBLIC_DIR / relative.lstrip("/")
    if url.startswith("/"):
        return PUBLIC_DIR / url.lstrip("/")
    return None


def validate_dimensions(page: PageInfo, image_url: str, base_url: str) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []
    local_path = url_to_local_image(image_url, base_url)
    if local_path is None:
        errors.append(
            f"{page.canonical or page.html_path}: og:image is remote ({image_url}); use local image for strict validation"
        )
        return errors
    if not local_path.exists():
        errors.append(
            f"{page.canonical or page.html_path}: og:image resolved to missing local file {local_path}"
        )
        return errors

    size = local_path.stat().st_size
    if size > MAX_BYTES:
        errors.append(
            f"{page.canonical or page.html_path}: image {local_path} is {size} bytes (> {MAX_BYTES})"
        )
    elif size > WARN_BYTES:
        warnings.append(
            f"WARN {page.canonical or page.html_path}: image {local_path} is {size} bytes (> {WARN_BYTES})"
        )

    with Image.open(local_path) as image:
        width, height = image.size

    ratio = width / height
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        errors.append(
            f"{page.canonical or page.html_path}: image {local_path} is {width}x{height}; expected at least {MIN_WIDTH}x{MIN_HEIGHT}"
        )
    if ratio < MIN_RATIO or ratio > MAX_RATIO:
        errors.append(
            f"{page.canonical or page.html_path}: image {local_path} ratio={ratio:.3f}; expected between {MIN_RATIO} and {MAX_RATIO}"
        )

    if warnings:
        print("\n".join(warnings))
    return errors


def validate_page(page: PageInfo, base_url: str) -> list[str]:
    errors: list[str] = []
    canonical = page.canonical
    if not canonical:
        return errors
    if "localhost:1313" in canonical:
        return errors
    if not canonical.startswith(base_url):
        return errors
    if page.html_path == PUBLIC_DIR / "index.html":
        return errors
    if "noindex" in page.tags.get("robots", "") and not page.tags.get("og:type"):
        return errors

    required_global = ["og:title", "og:description", "og:url", "og:type", "og:image", "twitter:card"]
    for key in required_global:
        if not page.tags.get(key):
            errors.append(f"{page.canonical or page.html_path}: missing required tag {key}")

    robots = page.tags.get("robots", "")
    if "noindex" not in robots:
        required_robots = ["max-image-preview:large", "max-snippet:-1", "max-video-preview:-1"]
        for token in required_robots:
            if token not in robots:
                errors.append(f"{page.canonical or page.html_path}: robots missing '{token}'")

    if page.og_type == "article":
        article_keys = [
            "twitter:image",
            "twitter:image:alt",
            "article:published_time",
            "article:modified_time",
            "x-social-image-source",
            "x-social-image-path",
        ]
        for key in article_keys:
            if not page.tags.get(key):
                errors.append(f"{page.canonical or page.html_path}: missing article tag {key}")

        image_url = page.tags.get("og:image", "")
        if image_url:
            errors.extend(validate_dimensions(page, image_url, base_url))

        source = page.tags.get("x-social-image-source", "")
        path = page.tags.get("x-social-image-path", "")
        if not source:
            source = "unknown"
        if not path:
            path = "unknown"
        if source in {"site_default", "unknown"}:
            errors.append(
                f"{page.canonical or page.html_path}: article resolved to fallback image source '{source}' (path={path}); set a per-post social image"
            )
        if errors:
            print(
                "\n".join(
                    [
                        f"Context for {page.canonical}:",
                        f"  content_file={page.content_file or 'unknown'}",
                        f"  social_source={source}",
                        f"  social_path={path}",
                    ]
                )
            )

    return errors


def validate_duplicate_article_images(pages: list[PageInfo], base_url: str) -> list[str]:
    errors: list[str] = []
    hashes: dict[str, list[tuple[str, str]]] = {}
    for page in pages:
        if page.og_type != "article":
            continue
        image_url = page.tags.get("og:image", "")
        local_path = url_to_local_image(image_url, base_url) if image_url else None
        if local_path is None or not local_path.exists():
            continue
        image_hash = hashlib.sha256(local_path.read_bytes()).hexdigest()
        canonical = page.canonical or str(page.html_path)
        parsed_path = urlparse(canonical).path.strip("/")
        parts = parsed_path.split("/")
        slug_key = "/".join(parts[1:]) if len(parts) > 1 else parsed_path
        hashes.setdefault(image_hash, []).append((canonical, slug_key))

    for _, entries in hashes.items():
        unique_slugs = {slug for _, slug in entries}
        if len(unique_slugs) > 1:
            joined = ", ".join(url for url, _ in entries)
            errors.append(
                f"Multiple different posts share the same social image file bytes: {joined}"
            )
    return errors


def main() -> int:
    base_url = load_base_url()
    errors: list[str] = []
    pages = iter_pages()
    if not pages:
        raise SystemExit("No generated pages found in public/; run `make build` first")

    for page in pages:
        errors.extend(validate_page(page, base_url))
    errors.extend(validate_duplicate_article_images(pages, base_url))

    if errors:
        print("Social metadata validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Social metadata validation passed for {len(pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
