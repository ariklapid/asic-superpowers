# Upstream obra/superpowers Release Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a weekly, dependency-free GitHub Actions monitor that creates one deduplicated review issue for every new stable `obra/superpowers` release and classifies changed upstream paths as `candidate-generic`, `asic-owned`, or `mixed-manual`.

**Architecture:** A shared Python policy module owns path classification. The existing manual sync script imports that policy while preserving its two-patch interface. A new monitor uses GitHub's REST API for release and issue discovery, a temporary Git repository for adjacent-tag comparison, and the REST API for issue creation. A scheduled workflow invokes the monitor with least-privilege permissions; deterministic `unittest` coverage runs without network access.

**Tech Stack:** Python 3.7+ standard library, Git, GitHub REST API, GitHub Actions, Bash, `unittest`

**Spec:** `docs/superpowers/specs/2026-06-13-upstream-release-monitor-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `scripts/upstream_superpowers_policy.py` | Create | Three-way ownership labels and conservative rename classification |
| `scripts/prepare_upstream_superpowers_sync.py` | Modify | Import shared policy while preserving current report and patch artifacts |
| `scripts/monitor_upstream_superpowers_releases.py` | Create | GitHub API client, release selection, tag comparison, issue rendering, and CLI orchestration |
| `tests/upstream-release-monitor/test_upstream_superpowers_policy.py` | Create | Ownership label unit tests |
| `tests/upstream-release-monitor/test_prepare_upstream_superpowers_sync.py` | Create | Manual sync compatibility regression tests |
| `tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py` | Create | API, pairing, Git comparison, rendering, deduplication, dry-run, and failure tests |
| `tests/upstream-release-monitor/test_workflow_contract.py` | Create | Dependency-free workflow contract checks |
| `.github/workflows/upstream-superpowers-release-monitor.yml` | Create | Weekly and manually dispatched monitor job |
| `scripts/validate.sh` | Modify | Run the new deterministic unit tests |
| `package.json` | Modify | Add monitor and focused-test commands |
| `README.md` | Modify | Document notification, labels, dry-run, and manual sync boundary |

The implementation is generic repository automation. No RTL, DV, constraints, reports, or backend artifacts change, so ASIC evidence fields do not apply.

---

### Task 1: Create The Shared Three-Way Ownership Policy

**Files:**
- Create: `scripts/upstream_superpowers_policy.py`
- Create: `tests/upstream-release-monitor/test_upstream_superpowers_policy.py`

- [ ] **Step 1: Write the failing policy tests**

Create `tests/upstream-release-monitor/test_upstream_superpowers_policy.py`:

```python
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
```

- [ ] **Step 2: Run the policy tests and confirm RED**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_upstream_superpowers_policy.py -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'upstream_superpowers_policy'`.

- [ ] **Step 3: Implement the shared policy**

Create `scripts/upstream_superpowers_policy.py`:

```python
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
```

- [ ] **Step 4: Run the policy tests and confirm GREEN**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_upstream_superpowers_policy.py -v
```

Expected: `Ran 5 tests` and `OK`.

- [ ] **Step 5: Commit the shared policy**

```bash
git add scripts/upstream_superpowers_policy.py tests/upstream-release-monitor/test_upstream_superpowers_policy.py
git commit -m "feat: define upstream ownership policy"
```

---

### Task 2: Refactor The Manual Sync Without Changing Its Interface

**Files:**
- Modify: `scripts/prepare_upstream_superpowers_sync.py:6-97,330-375`
- Create: `tests/upstream-release-monitor/test_prepare_upstream_superpowers_sync.py`

- [ ] **Step 1: Write failing compatibility tests**

Create `tests/upstream-release-monitor/test_prepare_upstream_superpowers_sync.py`:

```python
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
        self.assertEqual([change.ownership for change in candidate], [Ownership.CANDIDATE_GENERIC])
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the compatibility tests and confirm RED**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_prepare_upstream_superpowers_sync.py -v
```

Expected: import failure for `partition_changes`.

- [ ] **Step 3: Refactor the manual sync script**

In `scripts/prepare_upstream_superpowers_sync.py`:

1. Remove the `fnmatch` import, `PROTECTED_PATTERNS`, and `is_protected`.
2. Add:

```python
from upstream_superpowers_policy import Ownership, classify_change
```

3. Replace `Change.protected` with:

```python
    @property
    def ownership(self) -> Ownership:
        return classify_change(self.paths)

    @property
    def protected(self) -> bool:
        return self.ownership is not Ownership.CANDIDATE_GENERIC
```

4. Add after `changed_path_set`:

```python
def partition_changes(changes: list[Change]) -> tuple[list[Change], list[Change]]:
    candidate = [
        change
        for change in changes
        if change.ownership is Ownership.CANDIDATE_GENERIC
    ]
    protected = [
        change
        for change in changes
        if change.ownership is not Ownership.CANDIDATE_GENERIC
    ]
    return candidate, protected
```

5. In `prepare_report`, replace the two list comprehensions with:

```python
    candidate_changes, protected_changes = partition_changes(changes)
```

Do not rename `candidate-generic.patch`, `protected-manual.patch`, their path-list files, or the summary sections.

- [ ] **Step 4: Run policy and compatibility tests**

Run:

```bash
scripts/run-python.sh -m unittest discover -s tests/upstream-release-monitor -p 'test_*.py' -v
```

Expected: `Ran 7 tests` and `OK`.

- [ ] **Step 5: Run a syntax check**

Run:

```bash
scripts/run-python.sh -m py_compile scripts/upstream_superpowers_policy.py scripts/prepare_upstream_superpowers_sync.py
```

Expected: exit code `0` and no output.

- [ ] **Step 6: Commit the compatibility refactor**

```bash
git add scripts/prepare_upstream_superpowers_sync.py tests/upstream-release-monitor/test_prepare_upstream_superpowers_sync.py
git commit -m "refactor: share upstream ownership policy"
```

---

### Task 3: Implement Release Discovery, Pagination, Pairing, And Deduplication

**Files:**
- Create: `scripts/monitor_upstream_superpowers_releases.py`
- Create: `tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py`

- [ ] **Step 1: Write failing release and API tests**

Create `tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py` with these imports and tests first:

```python
#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from monitor_upstream_superpowers_releases import (  # noqa: E402
    GitHubClient,
    Release,
    existing_release_tags,
    issue_marker,
    parse_releases,
    pending_release_pairs,
)


class FakeResponse:
    def __init__(self, payload, headers=None, status=200):
        self.payload = json.dumps(payload).encode("utf-8")
        self.headers = headers or {}
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.payload


def release(tag, published_at, *, draft=False, prerelease=False):
    return {
        "tag_name": tag,
        "name": tag,
        "published_at": published_at,
        "html_url": "https://github.com/obra/superpowers/releases/tag/" + tag,
        "draft": draft,
        "prerelease": prerelease,
    }


class ReleaseDiscoveryTests(unittest.TestCase):
    def test_parse_releases_filters_and_orders_stable_releases(self):
        parsed = parse_releases([
            release("v5.3.0-rc1", "2026-06-03T00:00:00Z", prerelease=True),
            release("v5.2.0", "2026-06-02T00:00:00Z"),
            release("v5.1.0", "2026-05-04T00:00:00Z"),
            release("v5.4.0", "2026-06-04T00:00:00Z", draft=True),
        ])
        self.assertEqual([item.tag for item in parsed], ["v5.1.0", "v5.2.0"])

    def test_equal_publication_times_preserve_api_order(self):
        parsed = parse_releases([
            release("v5.2.1", "2026-06-02T00:00:00Z"),
            release("v5.2.0", "2026-06-02T00:00:00Z"),
        ])
        self.assertEqual([item.tag for item in parsed], ["v5.2.1", "v5.2.0"])

    def test_pending_pairs_are_adjacent_and_oldest_first(self):
        releases = parse_releases([
            release("v5.3.0", "2026-06-03T00:00:00Z"),
            release("v5.1.0", "2026-05-04T00:00:00Z"),
            release("v5.2.0", "2026-06-02T00:00:00Z"),
        ])
        pairs = pending_release_pairs(releases, "v5.1.0", {"v5.2.0"})
        self.assertEqual([(a.tag, b.tag) for a, b in pairs], [("v5.2.0", "v5.3.0")])

    def test_missing_tracking_floor_is_an_error(self):
        releases = parse_releases([release("v5.2.0", "2026-06-02T00:00:00Z")])
        with self.assertRaisesRegex(ValueError, "tracking floor v5.1.0"):
            pending_release_pairs(releases, "v5.1.0", set())

    def test_issue_marker_is_encoded_and_detected_in_closed_issues(self):
        marker = issue_marker("release/5.2.0")
        self.assertEqual(marker, "<!-- upstream-superpowers-release:release%2F5.2.0 -->")
        tags = existing_release_tags([
            {"body": marker, "state": "closed"},
            {"body": "unrelated", "state": "open"},
            {"body": marker, "pull_request": {"url": "https://example.invalid"}},
        ])
        self.assertEqual(tags, {"release/5.2.0"})

    def test_malformed_release_payload_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "tag_name"):
            parse_releases([{"draft": False, "prerelease": False}])

    def test_client_follows_link_header_pagination(self):
        responses = iter([
            FakeResponse(
                [release("v5.2.0", "2026-06-02T00:00:00Z")],
                {"Link": '<https://api.github.com/page/2>; rel="next"'},
            ),
            FakeResponse([release("v5.1.0", "2026-05-04T00:00:00Z")]),
        ])
        opener = mock.Mock(side_effect=lambda request: next(responses))
        client = GitHubClient("token", opener=opener)
        payload = client.paginate("https://api.github.com/page/1")
        self.assertEqual(len(payload), 2)
        self.assertEqual(opener.call_count, 2)

    def test_client_rejects_non_list_paginated_payload(self):
        client = GitHubClient(
            "token",
            opener=mock.Mock(return_value=FakeResponse({"message": "not a list"})),
        )
        with self.assertRaisesRegex(RuntimeError, "non-list payload"):
            client.paginate("https://api.github.com/page/1")

    def test_client_reports_http_failure_without_exposing_token(self):
        error = HTTPError("https://api.github.com/page/1", 403, "forbidden", {}, None)
        client = GitHubClient("secret-token", opener=mock.Mock(side_effect=error))
        with self.assertRaisesRegex(RuntimeError, "HTTP 403") as raised:
            client.paginate("https://api.github.com/page/1")
        self.assertNotIn("secret-token", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the monitor tests and confirm RED**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py -v
```

Expected: import failure for `monitor_upstream_superpowers_releases`.

- [ ] **Step 3: Implement the release model and GitHub client**

Create `scripts/monitor_upstream_superpowers_releases.py` with:

```python
#!/usr/bin/env python3
"""Create review issues for new stable obra/superpowers releases."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen

from upstream_superpowers_policy import Ownership, classify_change

API_VERSION = "2022-11-28"
DEFAULT_API_URL = "https://api.github.com"
DEFAULT_SOURCE_REPO = "obra/superpowers"
DEFAULT_TRACKING_FLOOR = "v5.1.0"
MARKER_RE = re.compile(r"<!-- upstream-superpowers-release:([^ ]+) -->")


@dataclass(frozen=True)
class Release:
    tag: str
    name: str
    published_at: str
    html_url: str


def _required_string(item: dict, key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError("release field %s must be a non-empty string" % key)
    return value


def parse_releases(items: Iterable[dict]) -> list[Release]:
    releases = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("release API entries must be objects")
        if item.get("draft") or item.get("prerelease"):
            continue
        tag = _required_string(item, "tag_name")
        releases.append(Release(
            tag=tag,
            name=item.get("name") or tag,
            published_at=_required_string(item, "published_at"),
            html_url=_required_string(item, "html_url"),
        ))
    return sorted(releases, key=lambda item: item.published_at)


def issue_marker(tag: str) -> str:
    return "<!-- upstream-superpowers-release:%s -->" % quote(tag, safe="")


def existing_release_tags(items: Iterable[dict]) -> Set[str]:
    tags = set()
    for item in items:
        if not isinstance(item, dict) or "pull_request" in item:
            continue
        body = item.get("body") or ""
        if not isinstance(body, str):
            continue
        for encoded in MARKER_RE.findall(body):
            tags.add(unquote(encoded))
    return tags


def pending_release_pairs(
    releases: Sequence[Release], tracking_floor: str, existing_tags: Set[str]
) -> list[Tuple[Release, Release]]:
    floor_indexes = [index for index, item in enumerate(releases) if item.tag == tracking_floor]
    if len(floor_indexes) != 1:
        raise ValueError("tracking floor %s must appear exactly once" % tracking_floor)
    start = floor_indexes[0]
    pairs = []
    for index in range(start + 1, len(releases)):
        previous = releases[index - 1]
        current = releases[index]
        if current.tag not in existing_tags:
            pairs.append((previous, current))
    return pairs


def _next_link(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    for part in value.split(","):
        url_part, *parameters = part.split(";")
        if any(parameter.strip() == 'rel="next"' for parameter in parameters):
            return url_part.strip()[1:-1]
    return None


class GitHubClient:
    def __init__(self, token: str, api_url: str = DEFAULT_API_URL, opener: Callable = urlopen):
        if not token:
            raise ValueError("GITHUB_TOKEN is required")
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.opener = opener

    def request(self, method: str, url: str, payload: Optional[dict] = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=data, method=method)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Authorization", "Bearer " + self.token)
        request.add_header("X-GitHub-Api-Version", API_VERSION)
        request.add_header("User-Agent", "asic-superpowers-release-monitor")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with self.opener(request) as response:
                raw = response.read()
                parsed = json.loads(raw.decode("utf-8")) if raw else None
                return parsed, response.headers
        except HTTPError as error:
            raise RuntimeError("GitHub API %s %s failed with HTTP %s" % (method, url, error.code))
        except URLError as error:
            raise RuntimeError("GitHub API %s %s failed: %s" % (method, url, error.reason))
        except json.JSONDecodeError as error:
            raise RuntimeError("GitHub API %s %s returned invalid JSON" % (method, url)) from error

    def paginate(self, url: str) -> list[dict]:
        items = []
        next_url = url
        while next_url:
            payload, headers = self.request("GET", next_url)
            if not isinstance(payload, list):
                raise RuntimeError("GitHub API %s returned a non-list payload" % next_url)
            items.extend(payload)
            next_url = _next_link(headers.get("Link"))
        return items

    def list_releases(self, repository: str) -> list[dict]:
        return self.paginate(
            "%s/repos/%s/releases?per_page=100" % (self.api_url, repository)
        )

    def list_issues(self, repository: str) -> list[dict]:
        return self.paginate(
            "%s/repos/%s/issues?state=all&per_page=100" % (self.api_url, repository)
        )

    def create_issue(self, repository: str, title: str, body: str) -> dict:
        payload, _ = self.request(
            "POST",
            "%s/repos/%s/issues" % (self.api_url, repository),
            {"title": title, "body": body},
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("html_url"), str):
            raise RuntimeError("GitHub issue creation returned an invalid payload")
        return payload
```

- [ ] **Step 4: Run the release/API tests**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py -v
```

Expected: `Ran 9 tests` and `OK`.

- [ ] **Step 5: Commit release discovery and API support**

```bash
git add scripts/monitor_upstream_superpowers_releases.py tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py
git commit -m "feat: discover upstream stable releases"
```

---

### Task 4: Add Temporary Git Comparison And Three-Section Issue Rendering

**Files:**
- Modify: `scripts/monitor_upstream_superpowers_releases.py`
- Modify: `tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py`

- [ ] **Step 1: Add failing Git and rendering tests**

Extend the monitor test imports with `Change`, `Comparison`, `compare_tags`, and
`render_issue`, then add:

```python
def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    ).stdout.strip()


class GitComparisonAndRenderingTests(unittest.TestCase):
    def test_compare_tags_detects_renames_and_three_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            upstream = Path(temp) / "upstream"
            upstream.mkdir()
            git(upstream, "init")
            git(upstream, "config", "user.email", "test@example.com")
            git(upstream, "config", "user.name", "Test")
            (upstream / "skills/generic").mkdir(parents=True)
            (upstream / "skills/generic/SKILL.md").write_text("base\n")
            git(upstream, "add", ".")
            git(upstream, "commit", "-m", "base")
            git(upstream, "tag", "v5.1.0")

            git(upstream, "mv", "skills/generic/SKILL.md", "README.md")
            (upstream / "skills/using-asic-superpowers").mkdir(parents=True)
            (upstream / "skills/using-asic-superpowers/SKILL.md").write_text("upstream collision\n")
            (upstream / "skills/new-generic").mkdir(parents=True)
            (upstream / "skills/new-generic/SKILL.md").write_text("new\n")
            git(upstream, "add", ".")
            git(upstream, "commit", "-m", "release")
            git(upstream, "tag", "v5.2.0")

            comparison = compare_tags(str(upstream), "v5.1.0", "v5.2.0")

        labels = {change.ownership for change in comparison.changes}
        self.assertEqual(
            labels,
            {Ownership.CANDIDATE_GENERIC, Ownership.MIXED_MANUAL, Ownership.ASIC_OWNED},
        )
        self.assertEqual(len(comparison.base_sha), 40)
        self.assertEqual(len(comparison.target_sha), 40)

    def test_compare_tags_rejects_an_unresolved_release_tag(self):
        with tempfile.TemporaryDirectory() as temp:
            upstream = Path(temp) / "upstream"
            upstream.mkdir()
            git(upstream, "init")
            git(upstream, "config", "user.email", "test@example.com")
            git(upstream, "config", "user.name", "Test")
            (upstream / "README.md").write_text("base\n")
            git(upstream, "add", ".")
            git(upstream, "commit", "-m", "base")
            git(upstream, "tag", "v5.1.0")
            with self.assertRaisesRegex(RuntimeError, "fetch"):
                compare_tags(str(upstream), "v5.1.0", "v9.9.9")

    def test_render_issue_has_exact_title_sections_and_marker(self):
        previous = Release("v5.1.0", "v5.1.0", "2026-05-04T00:00:00Z", "https://example/v5.1.0")
        current = Release("v5.2.0", "v5.2.0", "2026-06-02T00:00:00Z", "https://example/v5.2.0")
        comparison = Comparison(
            base_sha="a" * 40,
            target_sha="b" * 40,
            changes=(
                Change("M", ("skills/systematic-debugging/SKILL.md",)),
                Change("M", ("skills/using-asic-superpowers/SKILL.md",)),
                Change("M", ("README.md",)),
            ),
        )
        title, body = render_issue("obra/superpowers", previous, current, comparison)
        self.assertEqual(title, "Upstream obra/superpowers v5.2.0 baseline review")
        self.assertIn("## candidate-generic (1)", body)
        self.assertIn("## asic-owned (1)", body)
        self.assertIn("## mixed-manual (1)", body)
        self.assertIn(issue_marker("v5.2.0"), body)
        self.assertIn("https://github.com/obra/superpowers/compare/v5.1.0...v5.2.0", body)

    def test_render_issue_states_when_no_baseline_files_changed(self):
        previous = Release("v5.1.0", "v5.1.0", "2026-05-04T00:00:00Z", "https://example/v5.1.0")
        current = Release("v5.2.0", "v5.2.0", "2026-06-02T00:00:00Z", "https://example/v5.2.0")
        _, body = render_issue(
            "obra/superpowers",
            previous,
            current,
            Comparison("a" * 40, "b" * 40, ()),
        )
        self.assertIn("No baseline files changed between these stable releases.", body)
```

Also import `Ownership` from `upstream_superpowers_policy` in the test file.

- [ ] **Step 2: Run the new tests and confirm RED**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py -v
```

Expected: import failures for the comparison/rendering symbols.

- [ ] **Step 3: Implement Git comparison types and helpers**

Add to the monitor script:

```python
@dataclass(frozen=True)
class Change:
    status: str
    paths: Tuple[str, ...]

    @property
    def ownership(self) -> Ownership:
        return classify_change(self.paths)

    @property
    def display(self) -> str:
        if len(self.paths) == 2:
            return "%s %s -> %s" % (self.status, self.paths[0], self.paths[1])
        return "%s %s" % (self.status, self.paths[0])


@dataclass(frozen=True)
class Comparison:
    base_sha: str
    target_sha: str
    changes: Tuple[Change, ...]


def _git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True
    )
    if process.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), process.stderr.strip()))
    return process.stdout


def _validate_tag(root: Path, tag: str) -> None:
    process = subprocess.run(
        ["git", "check-ref-format", "refs/tags/" + tag],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if process.returncode != 0:
        raise ValueError("invalid upstream release tag %r" % tag)


def parse_name_status_z(raw: str) -> Tuple[Change, ...]:
    fields = raw.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    changes = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        paths = tuple(fields[index:index + path_count])
        if len(paths) != path_count:
            raise ValueError("malformed git name-status output")
        changes.append(Change(status, paths))
        index += path_count
    return tuple(changes)


def compare_tags(upstream_url: str, base_tag: str, target_tag: str) -> Comparison:
    with tempfile.TemporaryDirectory(prefix="asic-superpowers-upstream-") as temp:
        root = Path(temp)
        _git(root, "init", "--quiet")
        _validate_tag(root, base_tag)
        _validate_tag(root, target_tag)
        _git(root, "remote", "add", "origin", upstream_url)
        for tag in (base_tag, target_tag):
            _git(
                root,
                "fetch",
                "--quiet",
                "--no-tags",
                "--force",
                "--depth=1",
                "origin",
                "refs/tags/%s:refs/tags/%s" % (tag, tag),
            )
        base_sha = _git(root, "rev-parse", "refs/tags/%s^{commit}" % base_tag).strip()
        target_sha = _git(root, "rev-parse", "refs/tags/%s^{commit}" % target_tag).strip()
        raw = _git(
            root,
            "diff",
            "--name-status",
            "--find-renames",
            "-z",
            base_sha,
            target_sha,
        )
        return Comparison(base_sha, target_sha, parse_name_status_z(raw))
```

- [ ] **Step 4: Implement issue rendering**

Add:

```python
def _render_changes(changes: Sequence[Change], ownership: Ownership) -> list[str]:
    selected = [change for change in changes if change.ownership is ownership]
    lines = ["## %s (%d)" % (ownership.value, len(selected)), ""]
    if not selected:
        lines.extend(["No changes in this category.", ""])
        return lines
    for change in selected:
        safe_display = json.dumps(change.display, ensure_ascii=False)
        lines.append("- `%s`" % safe_display[1:-1].replace("`", "\\`"))
    lines.append("")
    return lines


def render_issue(
    source_repo: str,
    previous: Release,
    current: Release,
    comparison: Comparison,
) -> Tuple[str, str]:
    title = "Upstream %s %s baseline review" % (source_repo, current.tag)
    compare_url = "https://github.com/%s/compare/%s...%s" % (
        source_repo,
        quote(previous.tag, safe=""),
        quote(current.tag, safe=""),
    )
    lines = [
        issue_marker(current.tag),
        "",
        "A new stable upstream release requires baseline review.",
        "",
        "## Release window",
        "",
        "- Previous stable release: [%s](%s), published `%s`, commit `%s`" % (
            previous.tag, previous.html_url, previous.published_at, comparison.base_sha
        ),
        "- New stable release: [%s](%s), published `%s`, commit `%s`" % (
            current.tag, current.html_url, current.published_at, comparison.target_sha
        ),
        "- Compare: [%s...%s](%s)" % (previous.tag, current.tag, compare_url),
        "- Upstream release notes: %s" % current.html_url,
        "",
    ]
    if not comparison.changes:
        lines.extend(["No baseline files changed between these stable releases.", ""])
    for ownership in (
        Ownership.CANDIDATE_GENERIC,
        Ownership.ASIC_OWNED,
        Ownership.MIXED_MANUAL,
    ):
        lines.extend(_render_changes(comparison.changes, ownership))
    lines.extend([
        "## Maintainer checklist",
        "",
        "- [ ] Inspect the upstream compare and release notes.",
        "- [ ] Run `npm run sync:upstream` on a dedicated sync branch.",
        "- [ ] Port candidate generic changes selectively.",
        "- [ ] Preserve ASIC-owned files and hand-merge mixed/manual files.",
        "- [ ] Run `npm run validate` and review the complete diff.",
        "- [ ] Update `.upstream-superpowers.json` only after the reviewed sync.",
        "",
    ])
    return title, "\n".join(lines)
```

- [ ] **Step 5: Run monitor tests**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py -v
```

Expected: `Ran 13 tests` and `OK`.

- [ ] **Step 6: Commit comparison and rendering**

```bash
git add scripts/monitor_upstream_superpowers_releases.py tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py
git commit -m "feat: compare upstream release baselines"
```

---

### Task 5: Add CLI Orchestration, Dry-Run, Creation, And Failure Behavior

**Files:**
- Modify: `scripts/monitor_upstream_superpowers_releases.py`
- Modify: `tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py`

- [ ] **Step 1: Add failing orchestration tests**

Extend the monitor test imports with `Config` and `run_monitor`, then add:

```python
class FakeClient:
    def __init__(self, releases, issues):
        self.releases = releases
        self.issues = issues
        self.created = []

    def list_releases(self, repository):
        return self.releases

    def list_issues(self, repository):
        return self.issues

    def create_issue(self, repository, title, body):
        self.created.append((repository, title, body))
        return {"html_url": "https://github.com/ariklapid/asic-superpowers/issues/99"}


class MonitorOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.releases = [
            release("v5.1.0", "2026-05-04T00:00:00Z"),
            release("v5.2.0", "2026-06-02T00:00:00Z"),
            release("v5.3.0", "2026-06-03T00:00:00Z"),
        ]
        self.config = Config(
            source_repo="obra/superpowers",
            destination_repo="ariklapid/asic-superpowers",
            tracking_floor="v5.1.0",
            upstream_url="https://github.com/obra/superpowers.git",
            dry_run=False,
        )

    def test_run_creates_only_missing_release_issues_oldest_first(self):
        client = FakeClient(self.releases, [{"body": issue_marker("v5.2.0")}])
        compared = []
        def comparator(url, base, target):
            compared.append((base, target))
            return Comparison("a" * 40, "b" * 40, ())
        output = io.StringIO()
        run_monitor(self.config, client, comparator=comparator, output=output)
        self.assertEqual(compared, [("v5.2.0", "v5.3.0")])
        self.assertEqual(len(client.created), 1)
        self.assertIn("Created", output.getvalue())

    def test_dry_run_renders_without_creating(self):
        client = FakeClient(self.releases[:2], [])
        config = Config(**dict(self.config.__dict__, dry_run=True))
        output = io.StringIO()
        run_monitor(
            config,
            client,
            comparator=lambda url, base, target: Comparison("a" * 40, "b" * 40, ()),
            output=output,
        )
        self.assertEqual(client.created, [])
        self.assertIn("DRY RUN", output.getvalue())
        self.assertIn("Upstream obra/superpowers v5.2.0 baseline review", output.getvalue())

    def test_creation_failure_stops_before_later_release(self):
        client = FakeClient(self.releases, [])
        client.create_issue = mock.Mock(side_effect=RuntimeError("creation failed"))
        with self.assertRaisesRegex(RuntimeError, "creation failed"):
            run_monitor(
                self.config,
                client,
                comparator=lambda url, base, target: Comparison("a" * 40, "b" * 40, ()),
                output=io.StringIO(),
            )
        self.assertEqual(client.create_issue.call_count, 1)
```

- [ ] **Step 2: Run the orchestration tests and confirm RED**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py -v
```

Expected: import failures for `Config` and `run_monitor`.

- [ ] **Step 3: Implement orchestration and CLI**

Add to the monitor script:

```python
@dataclass(frozen=True)
class Config:
    source_repo: str
    destination_repo: str
    tracking_floor: str
    upstream_url: str
    dry_run: bool


def run_monitor(
    config: Config,
    client: GitHubClient,
    *,
    comparator: Callable[[str, str, str], Comparison] = compare_tags,
    output=sys.stdout,
) -> int:
    releases = parse_releases(client.list_releases(config.source_repo))
    existing = existing_release_tags(client.list_issues(config.destination_repo))
    pairs = pending_release_pairs(releases, config.tracking_floor, existing)
    if not pairs:
        print("No missing stable upstream release issues.", file=output)
        return 0
    for previous, current in pairs:
        comparison = comparator(config.upstream_url, previous.tag, current.tag)
        title, body = render_issue(config.source_repo, previous, current, comparison)
        if config.dry_run:
            print("DRY RUN: %s" % title, file=output)
            print(body, file=output)
            continue
        created = client.create_issue(config.destination_repo, title, body)
        print("Created %s" % created["html_url"], file=output)
    return 0


def _repository(value: str) -> str:
    if not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", value):
        raise argparse.ArgumentTypeError("repository must use OWNER/REPO format")
    return value


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create ASIC Superpowers review issues for stable upstream releases."
    )
    parser.add_argument("--source-repo", type=_repository, default=DEFAULT_SOURCE_REPO)
    parser.add_argument(
        "--destination-repo",
        type=_repository,
        default=os.environ.get("GITHUB_REPOSITORY", ""),
    )
    parser.add_argument("--tracking-floor", default=DEFAULT_TRACKING_FLOOR)
    parser.add_argument("--upstream-url")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.destination_repo:
        parser.error("--destination-repo or GITHUB_REPOSITORY is required")
    if args.upstream_url is None:
        args.upstream_url = "https://github.com/%s.git" % args.source_repo
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN", "")
    client = GitHubClient(token, api_url=args.api_url)
    config = Config(
        source_repo=args.source_repo,
        destination_repo=args.destination_repo,
        tracking_floor=args.tracking_floor,
        upstream_url=args.upstream_url,
        dry_run=args.dry_run,
    )
    return run_monitor(config, client)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print("ERROR: %s" % error, file=sys.stderr)
        raise SystemExit(1)
```

- [ ] **Step 4: Run all focused tests and syntax checks**

Run:

```bash
scripts/run-python.sh -m unittest discover -s tests/upstream-release-monitor -p 'test_*.py' -v
scripts/run-python.sh -m py_compile scripts/upstream_superpowers_policy.py scripts/prepare_upstream_superpowers_sync.py scripts/monitor_upstream_superpowers_releases.py
```

Expected: all tests pass; `py_compile` exits `0` without output.

- [ ] **Step 5: Commit orchestration**

```bash
git add scripts/monitor_upstream_superpowers_releases.py tests/upstream-release-monitor/test_monitor_upstream_superpowers_releases.py
git commit -m "feat: create upstream release review issues"
```

---

### Task 6: Add The Weekly GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/upstream-superpowers-release-monitor.yml`
- Create: `tests/upstream-release-monitor/test_workflow_contract.py`

- [ ] **Step 1: Write the failing workflow contract test**

Create `tests/upstream-release-monitor/test_workflow_contract.py`:

```python
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
        self.assertIn("--tracking-floor \"$TRACKING_FLOOR\"", text)
        self.assertIn("--dry-run", text)

    def test_workflow_does_not_grant_unneeded_permissions(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for forbidden in ("actions: write", "checks: write", "contents: write", "pull-requests: write"):
            with self.subTest(permission=forbidden):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the workflow test and confirm RED**

Run:

```bash
scripts/run-python.sh tests/upstream-release-monitor/test_workflow_contract.py -v
```

Expected: `FileNotFoundError` for the workflow.

- [ ] **Step 3: Create the workflow**

Create `.github/workflows/upstream-superpowers-release-monitor.yml`:

```yaml
name: Upstream obra/superpowers release monitor

on:
  schedule:
    - cron: '17 6 * * 1'
  workflow_dispatch:
    inputs:
      dry_run:
        description: Render missing release issues without creating them
        required: true
        default: true
        type: boolean

permissions:
  contents: read
  issues: write

concurrency:
  group: upstream-superpowers-release-monitor
  cancel-in-progress: false

jobs:
  monitor:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Check out ASIC Superpowers
        uses: actions/checkout@9f698171ed81b15d1823a05fc7211befd50c8ae0 # v6.0.3
        with:
          persist-credentials: false

      - name: Detect stable upstream releases
        shell: bash
        env:
          GITHUB_TOKEN: ${{ github.token }}
          SOURCE_REPO: obra/superpowers
          DESTINATION_REPO: ${{ github.repository }}
          TRACKING_FLOOR: v5.1.0
          DRY_RUN: ${{ github.event_name == 'workflow_dispatch' && inputs.dry_run || false }}
        run: |
          args=(
            --source-repo "$SOURCE_REPO"
            --destination-repo "$DESTINATION_REPO"
            --tracking-floor "$TRACKING_FLOOR"
          )
          if [[ "$DRY_RUN" == "true" ]]; then
            args+=(--dry-run)
          fi
          scripts/run-python.sh scripts/monitor_upstream_superpowers_releases.py "${args[@]}"
```

- [ ] **Step 4: Run workflow and monitor tests**

Run:

```bash
scripts/run-python.sh -m unittest discover -s tests/upstream-release-monitor -p 'test_*.py' -v
```

Expected: all tests pass, including `Ran 2 tests` in `WorkflowContractTests`.

- [ ] **Step 5: Commit the workflow**

```bash
git add .github/workflows/upstream-superpowers-release-monitor.yml tests/upstream-release-monitor/test_workflow_contract.py
git commit -m "ci: monitor upstream Superpowers releases"
```

---

### Task 7: Integrate Validation, Commands, And Maintainer Documentation

**Files:**
- Modify: `scripts/validate.sh:7-10`
- Modify: `package.json:14-22`
- Modify: `README.md:243-258`

- [ ] **Step 1: Add focused package commands**

Add these entries before `validate:skills` in `package.json`:

```json
"monitor:upstream-releases": "scripts/run-python.sh scripts/monitor_upstream_superpowers_releases.py",
"test:upstream-monitor": "scripts/run-python.sh -m unittest discover -s tests/upstream-release-monitor -p 'test_*.py' -v",
```

Keep the existing sync and validation commands unchanged.

- [ ] **Step 2: Add deterministic tests to repository validation**

Append to `scripts/validate.sh`:

```bash
"$SCRIPT_DIR/run-python.sh" -m unittest discover \
  -s "$SCRIPT_DIR/../tests/upstream-release-monitor" \
  -p 'test_*.py' \
  -v
```

- [ ] **Step 3: Replace the README weekly-sync section with notification plus sync guidance**

Replace `## Weekly Upstream Sync` through the marker command with:

```markdown
## Upstream Release Monitoring And Sync

A weekly GitHub Actions workflow checks published, non-prerelease releases from
`obra/superpowers`. Every stable release after the `v5.1.0` baseline gets one
issue titled `Upstream obra/superpowers <tag> baseline review`, including
releases with no baseline-file changes. Open and closed issues both suppress
duplicates.

The issue compares adjacent stable releases and classifies changed upstream
paths as:

- `candidate-generic`: inherited generic behavior eligible for selective review
- `asic-owned`: local ASIC behavior that upstream must not overwrite
- `mixed-manual`: integration or identity files that require a hand merge

Local-only ASIC files do not appear in the comparison because the monitor diffs
two upstream release tags. Unknown upstream paths default to
`candidate-generic`, but nothing is applied automatically.

To test discovery without creating issues, manually dispatch the
`Upstream obra/superpowers release monitor` workflow with `dry_run` enabled, or
run locally with a GitHub token:

```bash
GITHUB_TOKEN="$(gh auth token)" npm run monitor:upstream-releases -- \
  --destination-repo ariklapid/asic-superpowers \
  --dry-run
```

After an issue is reviewed, ask your coding agent to use
`syncing-upstream-superpowers` and prepare the existing selective sync report:

```bash
npm run sync:upstream
```

The report writes `candidate-generic.patch` plus a combined
`protected-manual.patch`. After the reviewed sync passes validation, update the
tracked upstream marker:

```bash
npm run sync:upstream:mark
```
```

- [ ] **Step 4: Run focused tests and link validation**

Run:

```bash
npm run test:upstream-monitor
npm run validate:links
```

Expected: focused tests pass and link validation prints `PASS`.

- [ ] **Step 5: Commit repository integration and docs**

```bash
git add package.json scripts/validate.sh README.md
git commit -m "docs: explain upstream release monitoring"
```

---

### Task 8: Verify The Complete Feature And Review The Diff

**Files:**
- Verify all files listed in the File Map

- [ ] **Step 1: Run the focused suite from the package command**

Run:

```bash
npm run test:upstream-monitor
```

Expected: all policy, manual-sync compatibility, monitor, and workflow contract tests pass.

- [ ] **Step 2: Run complete deterministic repository validation**

Run:

```bash
npm run validate
```

Expected: skill contracts, links, trigger metadata, ASIC eval fixtures, and upstream monitor tests all pass.

- [ ] **Step 3: Run a live read-only dry run**

Run:

```bash
GITHUB_TOKEN="$(gh auth token)" npm run monitor:upstream-releases -- \
  --destination-repo ariklapid/asic-superpowers \
  --dry-run
```

Expected: either `No missing stable upstream release issues.` or complete `DRY RUN` issue proposals. No issue is created and no tracked file changes.

- [ ] **Step 4: Verify the manual sync still starts normally**

Run:

```bash
npm run sync:upstream
```

Expected: a report is written under `triage/upstream-superpowers-sync-*/summary.md`; it still names `candidate-generic.patch` and `protected-manual.patch`. The ignored `triage/` output must not enter the commit.

- [ ] **Step 5: Review repository state and complete diff**

Run:

```bash
git status --short
git diff --check origin/main...HEAD
git diff --stat origin/main...HEAD
git diff origin/main...HEAD
```

Expected: only the planned monitor, workflow, tests, policy refactor, validation integration, documentation, design, plan, and session-handoff files appear. There are no whitespace errors or generated triage artifacts.

- [ ] **Step 6: Request code review before merge or publication**

Use `asic-superpowers:requesting-code-review` against the approved spec and this plan. Resolve Critical and Important findings, rerun Steps 1-5, and show the human partner the complete diff before any push or PR action.

Do not open an upstream `obra/superpowers` pull request. This automation belongs only in `ariklapid/asic-superpowers`.
