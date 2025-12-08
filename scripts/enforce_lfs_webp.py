#!/usr/bin/env python3
"""Ensure staged WebP files are tracked via Git LFS.

Checks attributes for staged *.webp files and exits non-zero if any lack
`filter=lfs`. Intended for use via pre-commit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable


def staged_webps() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        check=False,
        capture_output=True,
        text=True,
    )
    paths = []
    for line in result.stdout.splitlines():
        p = Path(line)
        if p.suffix.lower() == ".webp" and p.exists():
            paths.append(p)
    return paths


def assert_lfs(paths: Iterable[Path]) -> int:
    failing: list[str] = []
    for p in paths:
        attr = subprocess.run(
            ["git", "check-attr", "filter", str(p)],
            check=False,
            capture_output=True,
            text=True,
        )
        if "lfs" not in attr.stdout:
            failing.append(str(p))
    if failing:
        print("These WebP files are not tracked by Git LFS:")
        for f in failing:
            print(f"  - {f}")
        print("Add an LFS rule in .gitattributes and re-stage.")
        return 1
    return 0


def main() -> int:
    return assert_lfs(staged_webps())


if __name__ == "__main__":
    raise SystemExit(main())
