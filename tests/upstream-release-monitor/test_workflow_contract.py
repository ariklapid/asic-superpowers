#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/upstream-superpowers-release-monitor.yml"


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_has_schedule_dispatch_permissions_and_pinned_checkout(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("cron: '17 6 * * 1'", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("contents: read", text)
        self.assertIn("issues: write", text)
        self.assertIn(
            "actions/checkout@9f698171ed81b15d1823a05fc7211befd50c8ae0", text
        )
        self.assertIn("persist-credentials: false", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn('--tracking-floor "$TRACKING_FLOOR"', text)
        self.assertIn("--dry-run", text)

    def test_workflow_does_not_grant_unneeded_permissions(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for forbidden in (
            "actions: write",
            "checks: write",
            "contents: write",
            "pull-requests: write",
        ):
            with self.subTest(permission=forbidden):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
