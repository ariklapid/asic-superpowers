#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from upstream_superpowers_policy import (  # noqa: E402
    Ownership,
    classify_change,
    classify_path,
)


class UpstreamSuperpowersPolicyTests(unittest.TestCase):
    def test_generic_upstream_paths_default_to_candidate(self) -> None:
        self.assertEqual(
            classify_path("skills/systematic-debugging/SKILL.md"),
            Ownership.CANDIDATE_GENERIC,
        )
        self.assertEqual(
            classify_path("new-generic-file.md"),
            Ownership.CANDIDATE_GENERIC,
        )

    def test_asic_owned_paths_are_explicit(self) -> None:
        for path in (
            "ASIC_SUPERPOWERS_PLAN.md",
            "PLAN_AUDIT.md",
            "skills/using-asic-superpowers/SKILL.md",
            "skills/hardware-evidence-first-development/SKILL.md",
            "skills/syncing-upstream-superpowers/SKILL.md",
            "evals/trigger-scenarios/scenarios.json",
            "scripts/check_skill_contracts.py",
            "scripts/run_asic_evals.py",
            "scripts/validate.sh",
            "tests/upstream-release-monitor/test_workflow_contract.py",
        ):
            with self.subTest(path=path):
                self.assertEqual(classify_path(path), Ownership.ASIC_OWNED)

    def test_mixed_manual_paths_are_explicit(self) -> None:
        for path in (
            ".upstream-superpowers.json",
            ".gitignore",
            ".version-bump.json",
            ".github/workflows/validate.yml",
            ".codex-plugin/plugin.json",
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            "README.md",
            "RELEASE-NOTES.md",
            "assets/app-icon.png",
            "hooks/session-start",
            "package.json",
            "scripts/bump-version.sh",
            "scripts/prepare_upstream_superpowers_sync.py",
            "scripts/run-python.sh",
            "scripts/sync-to-codex-plugin.sh",
            "scripts/monitor_upstream_superpowers_releases.py",
            "scripts/upstream_superpowers_policy.py",
            "tests/codex-plugin-sync/test-sync-to-codex-plugin.sh",
            "tests/opencode/test-plugin-loading.sh",
        ):
            with self.subTest(path=path):
                self.assertEqual(classify_path(path), Ownership.MIXED_MANUAL)

    def test_paths_are_normalized_before_matching(self) -> None:
        self.assertEqual(
            classify_path("/skills/using-asic-superpowers/SKILL.md/"),
            Ownership.ASIC_OWNED,
        )

    def test_rename_uses_the_most_conservative_label(self) -> None:
        self.assertEqual(
            classify_change(("skills/systematic-debugging/SKILL.md", "README.md")),
            Ownership.MIXED_MANUAL,
        )
        self.assertEqual(
            classify_change(("README.md", "skills/using-asic-superpowers/SKILL.md")),
            Ownership.ASIC_OWNED,
        )


if __name__ == "__main__":
    unittest.main()
