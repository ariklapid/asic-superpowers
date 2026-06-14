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


def _git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True
    )
    if process.returncode != 0:
        raise RuntimeError(
            "git %s failed: %s" % (" ".join(args), process.stderr.strip())
        )
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
        target_sha = _git(
            root, "rev-parse", "refs/tags/%s^{commit}" % target_tag
        ).strip()
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
            previous.tag,
            previous.html_url,
            previous.published_at,
            comparison.base_sha,
        ),
        "- New stable release: [%s](%s), published `%s`, commit `%s`" % (
            current.tag,
            current.html_url,
            current.published_at,
            comparison.target_sha,
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
