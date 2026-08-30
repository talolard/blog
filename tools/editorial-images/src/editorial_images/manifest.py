"""Render, parse, compare, and validate the co-located art contract."""

from __future__ import annotations

import os
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from PIL import Image

from .hashing import file_sha256
from .models import OutputRecord, PostSource, ROLE_SPECS
from .prompting import PROMPT_VERSION, prompt_hash

Scalar = str | int | bool
ManifestTable = dict[str, Scalar | dict[str, Scalar]]


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def localized_alt(post: PostSource) -> dict[str, str]:
    """Build deterministic localized alt text from each translated title and concept."""

    return {
        article.language: f"Editorial illustration for {article.title}: {post.catalog.concept}"
        for article in post.localized
    }


def render_manifest(
    post: PostSource,
    outputs: tuple[OutputRecord, ...],
    *,
    model: str,
    source_revision: str,
    generated_at: datetime | None = None,
) -> str:
    """Serialize only the known schema so manifests remain stable and reviewable."""

    timestamp = (generated_at or datetime.now(UTC)).isoformat().replace("+00:00", "Z")
    lines = [
        "schema_version = 1",
        'status = "complete"',
        "eligible = true",
        'eligibility_reason = "published English bundle declared in editorial catalog"',
        f"generation_mode = {_quote(post.catalog.audit_mode)}",
        f"thread = {_quote(post.catalog.thread)}",
        f"visual_concept = {_quote(post.catalog.concept)}",
        f"prompt_version = {_quote(PROMPT_VERSION)}",
        f"prompt_hash = {_quote(prompt_hash(post))}",
        f"model = {_quote(model)}",
        f"source_git_revision = {_quote(source_revision)}",
        f"generated_at = {_quote(timestamp)}",
        "",
        "[placement]",
        'mobile_breakpoint = "760px"',
        'selection = "picture source at 760px and below"',
        "",
        "[inputs.articles]",
    ]
    lines.extend(f"{_quote(article.language)} = {_quote(article.sha256)}" for article in post.localized)
    lines.extend(["", "[inputs.references]"])
    lines.extend(f"{_quote(name)} = {_quote(digest)}" for name, digest in post.reference_hashes)
    lines.extend(["", "[alt]"])
    lines.extend(f"{_quote(language)} = {_quote(alt)}" for language, alt in localized_alt(post).items())
    for output in outputs:
        lines.extend(
            [
                "",
                f"[outputs.{output.role.value}]",
                f"path = {_quote(output.path)}",
                f"sha256 = {_quote(output.sha256)}",
                f"width = {output.width}",
                f"height = {output.height}",
                f"compression = {output.compression}",
                f"request_id = {_quote(output.request_id)}",
                f"placement = {_quote(ROLE_SPECS[output.role].placement)}",
            ]
        )
    return "\n".join(lines) + "\n"


def parse_manifest(path: Path) -> ManifestTable:
    """Parse a manifest for read-only selection and staleness checks."""

    return cast(ManifestTable, tomllib.loads(path.read_text(encoding="utf-8")))


def is_stale(post: PostSource) -> bool:
    """Compare every deterministic input without initiating paid work."""

    path = post.bundle / "art.toml"
    if not path.is_file():
        return True
    manifest = parse_manifest(path)
    if manifest.get("status") != "complete" or manifest.get("prompt_hash") != prompt_hash(post):
        return True
    inputs = cast(dict[str, dict[str, str]], manifest.get("inputs", {}))
    articles = inputs.get("articles", {})
    references = inputs.get("references", {})
    if articles != {article.language: article.sha256 for article in post.localized}:
        return True
    if references != dict(post.reference_hashes):
        return True
    outputs = cast(dict[str, dict[str, Scalar]], manifest.get("outputs", {}))
    for role, spec in ROLE_SPECS.items():
        record = outputs.get(role.value)
        if record is None:
            return True
        output_path = post.bundle / cast(str, record["path"])
        if not output_path.is_file() or file_sha256(output_path) != record["sha256"]:
            return True
        if record["width"] != spec.width or record["height"] != spec.height:
            return True
    return False


def validate_bundle(post: PostSource) -> tuple[str, ...]:
    """Return all contract violations for one bundle instead of failing fast."""

    errors: list[str] = []
    manifest_path = post.bundle / "art.toml"
    if not manifest_path.is_file():
        return (f"{post.catalog.key}: missing art.toml",)
    try:
        manifest = parse_manifest(manifest_path)
    except (OSError, tomllib.TOMLDecodeError) as error:
        return (f"{post.catalog.key}: invalid art.toml: {error}",)
    if manifest.get("status") != "complete":
        errors.append(f"{post.catalog.key}: manifest status is not complete")
    alt = cast(dict[str, str], manifest.get("alt", {}))
    for article in post.localized:
        if not alt.get(article.language, "").strip():
            errors.append(f"{post.catalog.key}: missing {article.language} alt text")
    outputs = cast(dict[str, dict[str, Scalar]], manifest.get("outputs", {}))
    for role, spec in ROLE_SPECS.items():
        record = outputs.get(role.value)
        if record is None:
            errors.append(f"{post.catalog.key}: missing {role.value} record")
            continue
        output_path = post.bundle / cast(str, record.get("path", ""))
        if not output_path.is_file():
            errors.append(f"{post.catalog.key}: missing {output_path.name}")
            continue
        try:
            with Image.open(output_path) as image:
                image.load()
                if image.format != "WEBP":
                    errors.append(f"{post.catalog.key}: {output_path.name} is not WebP")
                if image.size != (spec.width, spec.height):
                    errors.append(f"{post.catalog.key}: {output_path.name} is {image.size}, expected {(spec.width, spec.height)}")
        except OSError as error:
            errors.append(f"{post.catalog.key}: cannot decode {output_path.name}: {error}")
        if record.get("sha256") != file_sha256(output_path):
            errors.append(f"{post.catalog.key}: hash mismatch for {output_path.name}")
    return tuple(errors)


def publish_staged(staging: Path, bundle: Path) -> None:
    """Expose a complete staged set only after all files and manifest exist."""

    required = [spec.filename for spec in ROLE_SPECS.values()] + ["art.toml"]
    missing = [name for name in required if not (staging / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Incomplete staging set: {', '.join(missing)}")
    for name in required:
        os.replace(staging / name, bundle / name)
