"""Deterministic source, manifest, and staleness behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image

from editorial_images.content import load_all_posts, normalize_article, repository_root
from editorial_images.hashing import bytes_sha256
from editorial_images.manifest import is_stale, parse_manifest, publish_staged, render_manifest
from editorial_images.models import OutputRecord, Role, ROLE_SPECS
from editorial_images.prompting import assemble_prompt


def _webp(size: tuple[int, int], color: str) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format="WEBP", quality=85)
    return output.getvalue()


def test_normalization_removes_urls_but_preserves_prose_code_and_caption() -> None:
    source = """+++\ntitle = 'Example'\ndraft = false\n+++\n# Heading\nA [useful link](https://example.com) and ![meaningful plot](plot.png).\n```python\nprint('kept')\n```\n[ref]: https://example.com\n"""
    normalized = normalize_article(source)
    assert "https://" not in normalized
    assert "useful link" in normalized
    assert "[Image caption: meaningful plot]" in normalized
    assert "print('kept')" in normalized


def test_catalog_has_exactly_thirty_published_posts_and_prompt_is_complete() -> None:
    posts = load_all_posts(repository_root(Path(__file__)))
    assert len(posts) == 30
    post = next(item for item in posts if item.catalog.key == "genai/vibe-coding-stablenormal-modal")
    prompt = assemble_prompt(post, Role.HERO_DESKTOP)
    assert post.normalized_article in prompt
    assert post.catalog.concept in prompt
    assert "1920x640" in prompt


def test_manifest_parsing_hash_staleness_and_atomic_publish(tmp_path: Path) -> None:
    source = next(item for item in load_all_posts(repository_root(Path(__file__))) if item.catalog.key == "scripture-app")
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    staged = tmp_path / "staged"
    staged.mkdir()
    records: list[OutputRecord] = []
    for role, spec in ROLE_SPECS.items():
        content = _webp((spec.width, spec.height), "#1647ff")
        (staged / spec.filename).write_bytes(content)
        records.append(OutputRecord(role, spec.filename, bytes_sha256(content), spec.width, spec.height, 85, f"req-{role.value}"))
    manifest = render_manifest(source, tuple(records), model="test-model", source_revision="abc", generated_at=datetime(2026, 1, 1, tzinfo=UTC))
    (staged / "art.toml").write_text(manifest, encoding="utf-8")
    publish_staged(staged, bundle)
    parsed = parse_manifest(bundle / "art.toml")
    assert parsed["status"] == "complete"
    assert not staged.exists() or not any(staged.iterdir())

    redirected = source.__class__(
        root=source.root,
        bundle=bundle,
        catalog=source.catalog,
        english_path=source.english_path,
        title=source.title,
        normalized_article=source.normalized_article,
        localized=source.localized,
        reference_paths=source.reference_paths,
        reference_hashes=source.reference_hashes,
    )
    assert not is_stale(redirected)
    (bundle / "thumbnail.webp").write_bytes(b"changed")
    assert is_stale(redirected)
