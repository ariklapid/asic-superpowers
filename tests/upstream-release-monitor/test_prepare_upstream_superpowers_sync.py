#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_upstream_superpowers_sync import (  # noqa: E402
    Change,
    build_summary,
    partition_changes,
)
from upstream_superpowers_policy import Ownership  # noqa: E402


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    ).stdout.strip()


class PrepareUpstreamSyncCompatibilityTests(unittest.TestCase):
    def test_partition_keeps_two_patch_contract(self) -> None:
        changes = [
            Change("M", ("skills/systematic-debugging/SKILL.md",)),
            Change("M", ("skills/using-asic-superpowers/SKILL.md",)),
            Change("M", ("README.md",)),
        ]
        candidate, protected = partition_changes(changes)
        self.assertEqual(
            [change.ownership for change in candidate],
            [Ownership.CANDIDATE_GENERIC],
        )
        self.assertEqual(
            [change.ownership for change in protected],
            [Ownership.ASIC_OWNED, Ownership.MIXED_MANUAL],
        )

    def test_summary_retains_existing_patch_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            git(root, "init")
            git(root, "config", "user.email", "test@example.com")
            git(root, "config", "user.name", "Test")
            (root / ".codex-plugin").mkdir()
            (root / ".codex-plugin/plugin.json").write_text('{"version":"1.0.0"}\n')
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            base = git(root, "rev-parse", "HEAD")
            (root / "generic.txt").write_text("changed\n")
            git(root, "add", ".")
            git(root, "commit", "-m", "latest")
            latest = git(root, "rev-parse", "HEAD")
            report_dir = root / "triage" / "report"
            report_dir.mkdir(parents=True)

            summary = build_summary(
                root=root,
                report_dir=report_dir,
                upstream_url="https://github.com/obra/superpowers.git",
                remote="superpowers-upstream",
                branch="main",
                base=base,
                latest=latest,
                changes=[Change("A", ("generic.txt",))],
                protected_changes=[],
                candidate_changes=[Change("A", ("generic.txt",))],
            )

        self.assertIn("candidate-generic.patch", summary)
        self.assertIn("protected-manual.patch", summary)
        self.assertNotIn("asic-owned.patch", summary)
        self.assertIn("## Required Agent Flow", summary)
        self.assertNotIn("Required Codex Flow", summary)


if __name__ == "__main__":
    unittest.main()
