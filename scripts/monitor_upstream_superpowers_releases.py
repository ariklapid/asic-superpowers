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
            raise RuntimeError(
                "GitHub API %s %s failed with HTTP %s" % (method, url, error.code)
            )
        except URLError as error:
            raise RuntimeError(
                "GitHub API %s %s failed: %s" % (method, url, error.reason)
            )
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "GitHub API %s %s returned invalid JSON" % (method, url)
            ) from error

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
