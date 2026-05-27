#!/usr/bin/env python3
"""Check ASIC trigger metadata and bootstrap wiring."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []

    codex = json.loads(read(".codex-plugin/plugin.json"))
    if codex.get("name") != "asic-superpowers":
        failures.append(".codex-plugin/plugin.json name must be asic-superpowers")
    desc = codex.get("description", "").lower()
    for token in ["asic", "rtl", "dv", "physical design"]:
        if token not in desc:
            failures.append(f"codex description missing {token!r}")

    session_start = read("hooks/session-start")
    if "using-asic-superpowers" not in session_start:
        failures.append("session-start does not inject using-asic-superpowers")

    opencode = read(".opencode/plugins/asic-superpowers.js")
    if "using-asic-superpowers" not in opencode:
        failures.append("OpenCode plugin does not inject using-asic-superpowers")

    all_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            ROOT / "ASIC_SUPERPOWERS_PLAN.md",
            ROOT / "skills/using-asic-superpowers/SKILL.md",
            ROOT / "skills/hardware-evidence-first-development/SKILL.md",
        ]
    )
    stale_terms = [
        "rtl-verification-first-development",
        "rtl-coding-contract.md",
        "rtl-review-checklist.md",
        "RTL-aware Superpowers",
    ]
    for term in stale_terms:
        if term in all_text:
            failures.append(f"stale RTL-only term remains: {term}")

    required_refs = [
        "asic-engineering-contract.md",
        "rtl-design-lens.md",
        "dv-verification-lens.md",
        "physical-design-lens.md",
        "asic-review-checklist.md",
        "hardware-claim-discipline.md",
        "eda-toolchain-profile.md",
        "tool-evidence.md",
    ]
    for ref in required_refs:
        if not (ROOT / "skills/using-asic-superpowers/references" / ref).exists():
            failures.append(f"missing ASIC reference: {ref}")

    bootstrap = read("skills/using-asic-superpowers/SKILL.md").lower()
    evidence = read("skills/hardware-evidence-first-development/SKILL.md").lower()
    tool_profile = read("skills/using-asic-superpowers/references/eda-toolchain-profile.md").lower()
    for term in [
        "toolchain",
        "vendor-neutral",
        "do not assume",
        "domain routing",
        "generic superpowers",
        "mixed route",
        "local project overlays",
        "perforce",
        "mcp-backed source verification",
        "generated verilog",
    ]:
        if term not in bootstrap + evidence + tool_profile:
            failures.append(f"missing toolchain-awareness term: {term}")

    if failures:
        print("Trigger metadata check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Trigger metadata check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
