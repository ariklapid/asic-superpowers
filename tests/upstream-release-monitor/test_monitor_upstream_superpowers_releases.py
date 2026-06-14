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
