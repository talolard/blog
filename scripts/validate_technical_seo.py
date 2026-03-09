# /// script
# dependencies = []
# ///

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
HUGO_CONFIG = ROOT / "hugo.toml"

SUSPICIOUS_KEYS = {
    "name",
    "headline",
    "description",
    "url",
    "mainEntityOfPage",
}


@dataclass(frozen=True)
class PageMeta:
    path: Path
    meta_by_name: dict[str, str]
    json_ld_blocks: list[str]


class HeadInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta_by_name: dict[str, str] = {}
        self._in_json_ld = False
        self._json_buffer: list[str] = []
        self.json_ld_blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs if v is not None}
        if tag == "meta" and "name" in attr_map and "content" in attr_map:
            self.meta_by_name[attr_map["name"]] = attr_map["content"]
        if tag == "script" and attr_map.get("type") == "application/ld+json":
            self._in_json_ld = True
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_json_ld:
            self._in_json_ld = False
            block = "".join(self._json_buffer).strip()
            if block:
                self.json_ld_blocks.append(block)


def load_base_url() -> str:
    config = tomllib.loads(HUGO_CONFIG.read_text(encoding="utf-8"))
    base = str(config.get("baseURL", "")).rstrip("/")
    if not base:
        raise SystemExit("hugo.toml missing baseURL")
    return base


def parse_page(path: Path) -> PageMeta:
    parser = HeadInspector()
    parser.feed(path.read_text(encoding="utf-8"))
    return PageMeta(path=path, meta_by_name=parser.meta_by_name, json_ld_blocks=parser.json_ld_blocks)


def iter_html_pages() -> list[Path]:
    return sorted(PUBLIC_DIR.rglob("index.html")) + sorted(PUBLIC_DIR.rglob("404.html"))


def has_suspicious_quote_wrapping(key: str, value: object) -> bool:
    if key not in SUSPICIOUS_KEYS:
        return False
    if not isinstance(value, str):
        return False
    trimmed = value.strip()
    return len(trimmed) >= 2 and trimmed.startswith('"') and trimmed.endswith('"')


def walk_json(node: object, errors: list[str], context: str) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if has_suspicious_quote_wrapping(key, value):
                errors.append(f"{context}: JSON-LD field '{key}' looks double-quoted ({value})")
            walk_json(value, errors, context)
    elif isinstance(node, list):
        for item in node:
            walk_json(item, errors, context)


def validate_json_ld(page: PageMeta) -> list[str]:
    errors: list[str] = []
    for idx, block in enumerate(page.json_ld_blocks, start=1):
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"{page.path}: invalid JSON-LD block #{idx}: {exc}")
            continue
        walk_json(parsed, errors, f"{page.path} block #{idx}")
    return errors


def validate_robots_file(base_url: str) -> list[str]:
    errors: list[str] = []
    robots_path = PUBLIC_DIR / "robots.txt"
    if not robots_path.exists():
        return ["public/robots.txt is missing"]

    content = robots_path.read_text(encoding="utf-8")
    expected = f"Sitemap: {base_url}/sitemap.xml"
    if expected not in content:
        errors.append(f"public/robots.txt missing expected sitemap line: '{expected}'")
    if "ronaldsvilcins.com" in content:
        errors.append("public/robots.txt contains stale sitemap host 'ronaldsvilcins.com'")
    return errors


def validate_404_noindex() -> list[str]:
    errors: list[str] = []
    for path in [PUBLIC_DIR / "404.html", PUBLIC_DIR / "en/404.html", PUBLIC_DIR / "de/404.html", PUBLIC_DIR / "he/404.html"]:
        if not path.exists():
            errors.append(f"{path} is missing")
            continue
        page = parse_page(path)
        robots = page.meta_by_name.get("robots", "")
        if "noindex" not in robots:
            errors.append(f"{path}: expected robots noindex, got '{robots or 'missing'}'")
    return errors


def main() -> int:
    base_url = load_base_url()
    errors: list[str] = []

    errors.extend(validate_robots_file(base_url))
    errors.extend(validate_404_noindex())

    for path in iter_html_pages():
        page = parse_page(path)
        errors.extend(validate_json_ld(page))

    if errors:
        print("Technical SEO validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Technical SEO validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
