#!/usr/bin/env python3
"""Validate local SKILL.md contracts without external dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        raise ValueError("missing YAML frontmatter")
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta, match.group(2)


def main() -> int:
    failures: list[str] = []
    names: dict[str, Path] = {}
    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        try:
            meta, body = parse_frontmatter(skill_md)
        except ValueError as exc:
            failures.append(f"{skill_md.relative_to(ROOT)}: {exc}")
            continue

        name = meta.get("name", "")
        description = meta.get("description", "")
        if not name:
            failures.append(f"{skill_md.relative_to(ROOT)}: missing name")
        elif name != skill_md.parent.name:
            failures.append(
                f"{skill_md.relative_to(ROOT)}: name {name!r} does not match folder {skill_md.parent.name!r}"
            )
        elif name in names:
            failures.append(
                f"{skill_md.relative_to(ROOT)}: duplicate skill name also in {names[name].relative_to(ROOT)}"
            )
        else:
            names[name] = skill_md

        if not description:
            failures.append(f"{skill_md.relative_to(ROOT)}: missing description")
        if re.search(r"\[(TODO|TBD|PLACEHOLDER)[^\]]*\]", body, re.I):
            failures.append(f"{skill_md.relative_to(ROOT)}: placeholder text remains")

    required = {
        "using-asic-superpowers",
        "hardware-evidence-first-development",
        "brainstorming",
        "writing-plans",
        "systematic-debugging",
        "verification-before-completion",
        "requesting-code-review",
    }
    missing = required.difference(names)
    for name in sorted(missing):
        failures.append(f"missing required skill: {name}")

    if failures:
        print("Skill contract check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Skill contract check passed: {len(names)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
