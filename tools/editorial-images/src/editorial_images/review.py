"""Generate an ignored, local-only before/after editorial review gallery."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .manifest import parse_manifest
from .models import PostSource, Role, ROLE_SPECS
from .runner import PostRun


def _fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = image.convert("RGB")
    copy.thumbnail(size)
    canvas = Image.new("RGB", size, "#f5f7f9")
    canvas.paste(copy, ((size[0] - copy.width) // 2, (size[1] - copy.height) // 2))
    return canvas


def contact_sheet(post: PostSource, destination: Path) -> None:
    """Place a prior semantic reference beside all three new variants."""

    prior = next((path for path in post.reference_paths if path.name.startswith("social")), post.reference_paths[0])
    files = [prior, *(post.bundle / ROLE_SPECS[role].filename for role in (Role.THUMBNAIL, Role.HERO_DESKTOP, Role.HERO_MOBILE))]
    labels = ["Prior reference", "Thumbnail 960×720", "Desktop hero 1920×640", "Mobile hero 960×720"]
    panel_size = (480, 260)
    sheet = Image.new("RGB", (panel_size[0] * 2, panel_size[1] * 2 + 64), "#ffffff")
    draw = ImageDraw.Draw(sheet)
    for index, (path, label) in enumerate(zip(files, labels, strict=True)):
        with Image.open(path) as image:
            panel = _fit(image, (panel_size[0], panel_size[1] - 32))
        x = (index % 2) * panel_size[0]
        y = (index // 2) * panel_size[1]
        sheet.paste(panel, (x, y + 24))
        draw.text((x + 8, y + 6), label, fill="#10151b", font=ImageFont.load_default())
    draw.text((8, panel_size[1] * 2 + 20), post.title, fill="#10151b", font=ImageFont.load_default())
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, format="WEBP", quality=85, method=6)


def build_review(root: Path, posts: tuple[PostSource, ...], runs: tuple[PostRun, ...] = ()) -> Path:
    """Create grouped indexes, contact sheets, placement previews, and run data."""

    destination = root / "artifacts" / "editorial-image-review"
    if destination.exists():
        shutil.rmtree(destination)
    sheets = destination / "sheets"
    previews = destination / "previews"
    destination.mkdir(parents=True, exist_ok=True)
    cards: list[str] = []
    for post in posts:
        if not (post.bundle / "art.toml").is_file():
            continue
        sheet_path = sheets / f"{post.catalog.key.replace('/', '--')}.webp"
        contact_sheet(post, sheet_path)
        preview_prefix = post.catalog.key.replace("/", "--")
        previews.mkdir(parents=True, exist_ok=True)
        preview_names: dict[Role, str] = {}
        for role, spec in ROLE_SPECS.items():
            name = f"{preview_prefix}--{spec.filename}"
            _ = shutil.copy2(post.bundle / spec.filename, previews / name)
            preview_names[role] = name
        manifest = parse_manifest(post.bundle / "art.toml")
        generated = html.escape(str(manifest.get("generated_at", "")))
        cards.append(
            f'<article data-mode="{html.escape(post.catalog.audit_mode)}">'
            f'<p>{html.escape(post.catalog.audit_mode)} · {html.escape(post.catalog.thread)}</p>'
            f'<h2>{html.escape(post.title)}</h2>'
            f'<img src="sheets/{sheet_path.name}" alt="Contact sheet for {html.escape(post.title)}">'
            f'<div class="placements"><img class="thumb" src="previews/{preview_names[Role.THUMBNAIL]}" alt="">'
            f'<img class="mobile" src="previews/{preview_names[Role.HERO_MOBILE]}" alt="">'
            f'<img class="desktop" src="previews/{preview_names[Role.HERO_DESKTOP]}" alt=""></div>'
            f'<small>{generated}</small></article>'
        )
    page = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Editorial image review</title><style>
body{margin:0;padding:30px;background:#f5f7f9;color:#10151b;font:16px sans-serif}main{max-width:1180px;margin:auto}article{padding:24px 0;border-top:1px solid #10151b}article>img{max-width:100%;height:auto;border:1px solid #8e9aa6}.placements{display:flex;gap:20px;align-items:flex-start;overflow:auto;margin-top:16px}.thumb{width:120px;height:90px;object-fit:cover}.mobile{width:362px;height:272px;object-fit:cover}.desktop{width:590px;height:197px;object-fit:cover}p,small{font:11px monospace;color:#64707d}h1{font-size:48px}h2{font-size:28px}</style></head><body><main><h1>Editorial image review</h1>""" + "".join(cards) + "</main></body></html>"
    (destination / "index.html").write_text(page, encoding="utf-8")
    report = [
        {
            "post": run.key,
            "status": run.status,
            "retries": run.retries,
            "elapsed_seconds": round(run.elapsed_seconds, 3),
            "error": run.error,
            "events": [
                {
                    "role": event.role.value,
                    "phase": event.phase,
                    "time": event.monotonic_seconds,
                    "request_id": event.request_id,
                }
                for event in run.events
            ],
        }
        for run in runs
    ]
    (destination / "run-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination
