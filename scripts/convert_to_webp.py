#!/usr/bin/env python3
"""Convert staged raster images to WebP and stage the result.

- Converts .png/.jpg/.jpeg/.gif files to .webp alongside originals.
- Removes the source file after conversion.
- Re-stages the new WebP file so the commit picks it up.

Intended for use via pre-commit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from PIL import Image


ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".gif"}


def convert(path: Path) -> None:
    target = path.with_suffix(".webp")
    with Image.open(path) as im:
        save_kwargs = {"quality": 90}
        if getattr(im, "is_animated", False):
            save_kwargs.update(
                {
                    "save_all": True,
                    "duration": im.info.get("duration"),
                    "loop": im.info.get("loop", 0),
                }
            )
        im.save(target, "WEBP", **save_kwargs)
    path.unlink()
    subprocess.run(["git", "add", str(target)], check=False)


def main(files: Iterable[str]) -> int:
    for file in files:
        p = Path(file)
        if p.suffix.lower() in ALLOWED_EXTS and p.exists():
            convert(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(f) for f in __import__('sys').argv[1:]))
