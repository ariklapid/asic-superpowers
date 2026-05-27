#!/usr/bin/env python3
"""Run deterministic ASIC Superpowers eval fixture checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evals/trigger-scenarios/scenarios.json"
FIXTURES = ROOT / "evals/fixtures"


def main() -> int:
    failures: list[str] = []
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    required_lanes = {"rtl", "dv", "physical-design"}
    lanes = {scenario.get("lane") for scenario in scenarios}
    missing_lanes = required_lanes.difference(lanes)
    for lane in sorted(missing_lanes):
        failures.append(f"missing trigger scenario lane: {lane}")

    for scenario in scenarios:
        sid = scenario.get("id", "<missing-id>")
        for field in ["prompt", "lane", "expected_skills", "must_collect", "must_not_claim"]:
            if not scenario.get(field):
                failures.append(f"{sid}: missing {field}")
        for skill in scenario.get("expected_skills", []):
            if not (ROOT / "skills" / skill / "SKILL.md").exists():
                failures.append(f"{sid}: expected skill does not exist: {skill}")
        for fixture in scenario.get("fixtures", []):
            if not (ROOT / fixture).exists():
                failures.append(f"{sid}: missing fixture {fixture}")

    required_fixtures = [
        "evals/fixtures/asic-ai-workflows/rtl/load_store_command_processor.sv",
        "evals/fixtures/asic-ai-workflows/dv/streaming_buffer.sv",
        "evals/fixtures/asic-ai-workflows/cdc/unsync_single_bit.sv",
        "evals/fixtures/third_party/sdc/efabless_caravel_caravan.sdc",
        "evals/fixtures/third_party/reports/openhw_cva6_spyglass_reference_summary.rpt",
        "evals/fixtures/third_party/reports/rtl_poweroptimization_c432_postsyn_power.rpt",
        "evals/fixtures/third_party/reports/pyrpl_post_place_timing_summary.rpt",
        "evals/fixtures/third_party/sv/opentitan_pins_if.sv",
        "evals/fixtures/generated/report_timing.rpt",
        "evals/fixtures/PROVENANCE.md",
    ]
    for fixture in required_fixtures:
        if not (ROOT / fixture).exists():
            failures.append(f"required fixture missing: {fixture}")

    provenance = (FIXTURES / "PROVENANCE.md").read_text(encoding="utf-8")
    for third_party in (FIXTURES / "third_party").rglob("*"):
        if third_party.is_file() and "licenses" not in third_party.parts:
            if third_party.name not in provenance:
                failures.append(f"fixture missing provenance entry: {third_party.relative_to(ROOT)}")

    if failures:
        print("ASIC eval fixture check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"ASIC eval fixture check passed: {len(scenarios)} trigger scenarios")
    for scenario in scenarios:
        print(f"- {scenario['id']}: {scenario['lane']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
