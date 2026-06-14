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
    Change,
    Comparison,
    Config,
    GitHubClient,
    Release,
    compare_tags,
    existing_release_tags,
    issue_marker,
    parse_releases,
    pending_release_pairs,
    render_issue,
    run_monitor,
)
from upstream_superpowers_policy import Ownership  # noqa: E402


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


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    ).stdout.strip()


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

    def test_client_stops_on_empty_page_even_with_next_link(self):
        opener = mock.Mock(return_value=FakeResponse(
            [],
            {"Link": '<https://api.github.com/page/2>; rel="next"'},
        ))
        client = GitHubClient("token", opener=opener)
        self.assertEqual(client.paginate("https://api.github.com/page/1"), [])
        self.assertEqual(opener.call_count, 1)

    def test_client_rejects_cross_origin_pagination_link(self):
        opener = mock.Mock(return_value=FakeResponse(
            [release("v5.2.0", "2026-06-02T00:00:00Z")],
            {"Link": '<https://example.invalid/page/2>; rel="next"'},
        ))
        client = GitHubClient("token", opener=opener)
        with self.assertRaisesRegex(RuntimeError, "outside configured API origin"):
            client.paginate("https://api.github.com/page/1")
        self.assertEqual(opener.call_count, 1)

    def test_client_reports_http_failure_without_exposing_token(self):
        error = HTTPError("https://api.github.com/page/1", 403, "forbidden", {}, None)
        client = GitHubClient("secret-token", opener=mock.Mock(side_effect=error))
        with self.assertRaisesRegex(RuntimeError, "HTTP 403") as raised:
            client.paginate("https://api.github.com/page/1")
        self.assertNotIn("secret-token", str(raised.exception))


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
            (upstream / "skills/using-asic-superpowers/SKILL.md").write_text(
                "upstream collision\n"
            )
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
        previous = Release(
            "v5.1.0",
            "v5.1.0",
            "2026-05-04T00:00:00Z",
            "https://example/v5.1.0",
        )
        current = Release(
            "v5.2.0",
            "v5.2.0",
            "2026-06-02T00:00:00Z",
            "https://example/v5.2.0",
        )
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
        self.assertIn(
            "https://github.com/obra/superpowers/compare/v5.1.0...v5.2.0",
            body,
        )

    def test_render_issue_states_when_no_baseline_files_changed(self):
        previous = Release(
            "v5.1.0",
            "v5.1.0",
            "2026-05-04T00:00:00Z",
            "https://example/v5.1.0",
        )
        current = Release(
            "v5.2.0",
            "v5.2.0",
            "2026-06-02T00:00:00Z",
            "https://example/v5.2.0",
        )
        _, body = render_issue(
            "obra/superpowers",
            previous,
            current,
            Comparison("a" * 40, "b" * 40, ()),
        )
        self.assertIn("No baseline files changed between these stable releases.", body)


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
        self.assertIn(
            "Upstream obra/superpowers v5.2.0 baseline review", output.getvalue()
        )

    def test_creation_failure_stops_before_later_release(self):
        client = FakeClient(self.releases, [])
        client.create_issue = mock.Mock(side_effect=RuntimeError("creation failed"))
        with self.assertRaisesRegex(RuntimeError, "creation failed"):
            run_monitor(
                self.config,
                client,
                comparator=lambda url, base, target: Comparison(
                    "a" * 40, "b" * 40, ()
                ),
                output=io.StringIO(),
            )
        self.assertEqual(client.create_issue.call_count, 1)


if __name__ == "__main__":
    unittest.main()
