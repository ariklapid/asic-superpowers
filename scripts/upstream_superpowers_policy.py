#!/usr/bin/env python3
"""Ownership policy for changes originating in obra/superpowers."""

from __future__ import annotations

import fnmatch
from enum import Enum
from typing import Iterable


class Ownership(str, Enum):
    CANDIDATE_GENERIC = "candidate-generic"
    MIXED_MANUAL = "mixed-manual"
    ASIC_OWNED = "asic-owned"


ASIC_OWNED_PATTERNS = (
    "ASIC_SUPERPOWERS_PLAN.md",
    "PLAN_AUDIT.md",
    "docs/ASIC_PLUGIN_VALIDATION_PLAN.md",
    "docs/superpowers/plans/*upstream-release-monitor*",
    "docs/superpowers/specs/*upstream-release-monitor*",
    "evals/**",
    "scripts/check_skill_contracts.py",
    "scripts/check_trigger_metadata.py",
    "scripts/run_asic_evals.py",
    "scripts/validate.sh",
    "skills/hardware-evidence-first-development/**",
    "skills/syncing-upstream-superpowers/**",
    "skills/using-asic-superpowers/**",
    "tests/upstream-release-monitor/**",
)

MIXED_MANUAL_PATTERNS = (
    ".upstream-superpowers.json",
    ".gitignore",
    ".version-bump.json",
    ".claude-plugin/**",
    ".codex-plugin/**",
    ".cursor-plugin/**",
    ".github/**",
    ".opencode/**",
    "AGENTS.md",
    "assets/**",
    "CLAUDE.md",
    "CODE_OF_CONDUCT.md",
    "GEMINI.md",
    "LICENSE",
    "README.md",
    "RELEASE-NOTES.md",
    "docs/README.opencode.md",
    "gemini-extension.json",
    "hooks/**",
    "package.json",
    "scripts/bump-version.sh",
    "scripts/monitor_upstream_superpowers_releases.py",
    "scripts/prepare_upstream_superpowers_sync.py",
    "scripts/run-python.sh",
    "scripts/sync-to-codex-plugin.sh",
    "scripts/upstream_superpowers_policy.py",
    "tests/codex-plugin-sync/**",
    "tests/opencode/**",
)

_PRIORITY = {
    Ownership.CANDIDATE_GENERIC: 0,
    Ownership.MIXED_MANUAL: 1,
    Ownership.ASIC_OWNED: 2,
}


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def classify_path(path: str) -> Ownership:
    normalized = path.strip("/")
    if _matches(normalized, ASIC_OWNED_PATTERNS):
        return Ownership.ASIC_OWNED
    if _matches(normalized, MIXED_MANUAL_PATTERNS):
        return Ownership.MIXED_MANUAL
    return Ownership.CANDIDATE_GENERIC


def classify_change(paths: Iterable[str]) -> Ownership:
    labels = [classify_path(path) for path in paths]
    if not labels:
        raise ValueError("a change must contain at least one path")
    return max(labels, key=_PRIORITY.__getitem__)
