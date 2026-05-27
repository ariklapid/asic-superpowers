#!/usr/bin/env python3
"""Validate relative markdown links in ASIC-owned docs and skill references."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = [
    ROOT / "ASIC_SUPERPOWERS_PLAN.md",
    ROOT / "PLAN_AUDIT.md",
    ROOT / "README.md",
    ROOT / "docs" / "ASIC_PLUGIN_VALIDATION_PLAN.md",
    ROOT / "evals",
    ROOT / "skills" / "using-asic-superpowers",
    ROOT / "skills" / "hardware-evidence-first-development",
]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def iter_markdown() -> list[Path]:
    paths: list[Path] = []
    for root in SEARCH_ROOTS:
        if root.is_file() and root.suffix == ".md":
            paths.append(root)
        elif root.is_dir():
            paths.extend(root.rglob("*.md"))
    return sorted(set(paths))


def is_external(target: str) -> bool:
    parsed = urlparse(target)
    return bool(parsed.scheme or target.startswith("#") or target.startswith("mailto:"))


def main() -> int:
    failures: list[str] = []
    for md in iter_markdown():
        text = md.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw = match.group(1).strip()
            if is_external(raw):
                continue
            target = unquote(raw.split("#", 1)[0])
            if not target:
                continue
            resolved = (md.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                failures.append(f"{md.relative_to(ROOT)}: link escapes repo: {raw}")
                continue
            if not resolved.exists():
                failures.append(f"{md.relative_to(ROOT)}: missing link target: {raw}")

    if failures:
        print("Markdown link check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Markdown link check passed: {len(iter_markdown())} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
