# /// script
# dependencies = [
#   "pyyaml",
# ]
# ///

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "content" / "posts"

REQUIRED_LANGUAGE_FIELDS = ["canonical_path", "one_liner", "hook", "cta"]
REQUIRED_PLATFORM_FIELDS = {
    "twitter": ["post_text", "alt_text", "hashtags", "emoji"],
    "linkedin": ["post_text", "alt_text"],
    "reddit": ["title", "post_text"],
    "hn": ["title", "first_comment"],
}


@dataclass(frozen=True)
class PostBundle:
    bundle_dir: Path
    language_files: list[Path]
    frontmatter: dict


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if text.startswith("+++"):
        _, body = text.split("+++", 1)
        fm, _ = body.split("+++", 1)
        return tomllib.loads(fm)
    if text.startswith("---"):
        _, body = text.split("---", 1)
        fm, _ = body.split("---", 1)
        data = yaml.safe_load(fm)
        return data or {}
    return {}


def language_code(file_path: Path) -> str:
    name = file_path.name
    if name == "index.md":
        return "en"
    if name.startswith("index.") and name.endswith(".md"):
        return name.split(".")[1]
    raise ValueError(f"Unexpected language filename: {file_path}")


def iter_bundles() -> list[PostBundle]:
    bundles: list[PostBundle] = []
    for index_file in sorted(POSTS_DIR.rglob("index.md")):
        bundle_dir = index_file.parent
        lang_files = [index_file] + sorted(bundle_dir.glob("index.*.md"))
        fm = parse_frontmatter(index_file)
        bundles.append(PostBundle(bundle_dir=bundle_dir, language_files=lang_files, frontmatter=fm))
    return bundles


def bool_flag(data: dict, key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    return bool(value)


def normalized_share_languages(bundle: PostBundle) -> list[str]:
    share_cfg = bundle.frontmatter.get("share", {}) if isinstance(bundle.frontmatter.get("share"), dict) else {}
    explicit = share_cfg.get("languages")
    if isinstance(explicit, list) and explicit:
        return [str(item) for item in explicit]
    return [language_code(file_path) for file_path in bundle.language_files]


def validate_bundle(bundle: PostBundle) -> list[str]:
    errors: list[str] = []
    fm = bundle.frontmatter
    if bool_flag(fm, "draft", False):
        return errors

    share_cfg = fm.get("share", {}) if isinstance(fm.get("share"), dict) else {}
    if bool_flag(share_cfg, "disable", False):
        return errors

    share_path = bundle.bundle_dir / "share.toml"
    if not share_path.exists():
        return [f"{bundle.bundle_dir}: missing required share.toml"]

    data = tomllib.loads(share_path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        errors.append(f"{share_path}: version must be 1")

    languages = normalized_share_languages(bundle)
    lang_root = data.get("languages", {})
    if not isinstance(lang_root, dict):
        return [f"{share_path}: missing [languages] table"]

    for lang in languages:
        entry = lang_root.get(lang)
        if not isinstance(entry, dict):
            errors.append(f"{share_path}: missing [languages.{lang}] table")
            continue
        for field in REQUIRED_LANGUAGE_FIELDS:
            value = entry.get(field)
            if value in (None, ""):
                errors.append(f"{share_path}: [languages.{lang}] missing '{field}'")

    for platform, fields in REQUIRED_PLATFORM_FIELDS.items():
        platform_root = data.get(platform, {})
        if not isinstance(platform_root, dict):
            errors.append(f"{share_path}: missing [{platform}] table")
            continue

        for lang in languages:
            entry = platform_root.get(lang)
            if not isinstance(entry, dict):
                errors.append(f"{share_path}: missing [{platform}.{lang}] table")
                continue
            for field in fields:
                if entry.get(field) in (None, ""):
                    errors.append(f"{share_path}: [{platform}.{lang}] missing '{field}'")

    for lang in languages:
        twitter = data.get("twitter", {}).get(lang, {}) if isinstance(data.get("twitter"), dict) else {}
        if isinstance(twitter, dict):
            post_text = str(twitter.get("post_text", ""))
            thread = twitter.get("thread")
            if not thread and len(post_text) > 280:
                errors.append(f"{share_path}: [twitter.{lang}].post_text exceeds 280 chars without thread")
            if isinstance(thread, list):
                for idx, part in enumerate(thread, start=1):
                    if len(str(part)) > 280:
                        errors.append(f"{share_path}: [twitter.{lang}].thread part {idx} exceeds 280 chars")

    return errors


def main() -> int:
    bundles = iter_bundles()
    errors: list[str] = []
    for bundle in bundles:
        errors.extend(validate_bundle(bundle))

    if errors:
        print("Share pack validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Share pack validation passed for {len(bundles)} post bundles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
