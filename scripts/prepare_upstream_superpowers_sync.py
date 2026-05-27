#!/usr/bin/env python3
"""Prepare a safe upstream Superpowers sync report for ASIC Superpowers."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REMOTE = "superpowers-upstream"
DEFAULT_UPSTREAM_URL = "https://github.com/obra/superpowers.git"
DEFAULT_BRANCH = "main"
MARKER_FILE = ".upstream-superpowers.json"
REPORT_ROOT = "triage"
DISABLED_PUSH_URL = "DISABLED"

PROTECTED_PATTERNS = (
    ".upstream-superpowers.json",
    ".claude-plugin/**",
    ".codex-plugin/**",
    ".cursor-plugin/**",
    ".github/**",
    ".opencode/**",
    "AGENTS.md",
    "ASIC_SUPERPOWERS_PLAN.md",
    "CLAUDE.md",
    "CODE_OF_CONDUCT.md",
    "GEMINI.md",
    "LICENSE",
    "PLAN_AUDIT.md",
    "README.md",
    "gemini-extension.json",
    "hooks/**",
    "package.json",
    "scripts/check_trigger_metadata.py",
    "scripts/prepare_upstream_superpowers_sync.py",
    "scripts/run_asic_evals.py",
    "skills/hardware-evidence-first-development/**",
    "skills/using-asic-superpowers/**",
    "docs/ASIC_PLUGIN_VALIDATION_PLAN.md",
    "docs/README.opencode.md",
    "evals/**",
)


@dataclass(frozen=True)
class Change:
    status: str
    paths: tuple[str, ...]

    @property
    def protected(self) -> bool:
        return any(is_protected(path) for path in self.paths)

    @property
    def display(self) -> str:
        return "\t".join((self.status, *self.paths))


def run(cmd: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and proc.returncode != 0:
        print(f"ERROR: command failed: {' '.join(cmd)}", file=sys.stderr)
        if proc.stdout:
            print(proc.stdout, file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)
    return proc


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], root, check=check)


def git_out(root: Path, *args: str) -> str:
    return git(root, *args).stdout


def repo_root() -> Path:
    proc = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    return Path(proc.stdout.strip())


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def is_protected(path: str) -> bool:
    normalized = path.strip("/")
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in PROTECTED_PATTERNS)


def ensure_remote(root: Path, name: str, url: str) -> None:
    proc = git(root, "remote", "get-url", name, check=False)
    if proc.returncode != 0:
        git(root, "remote", "add", name, url)
    else:
        current = proc.stdout.strip()
        if current != url:
            die(
                f"remote {name!r} points at {current!r}, expected {url!r}. "
                "Use --remote-name or fix the remote before syncing."
            )

    push_proc = git(root, "remote", "get-url", "--push", name, check=False)
    if push_proc.returncode != 0 or push_proc.stdout.strip() != DISABLED_PUSH_URL:
        git(root, "remote", "set-url", "--push", name, DISABLED_PUSH_URL)


def fetch_upstream(root: Path, remote: str, branch: str) -> str:
    git(root, "fetch", "--prune", remote, branch)
    return git_out(root, "rev-parse", f"{remote}/{branch}").strip()


def read_marker(root: Path) -> dict:
    path = root / MARKER_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def marker_base(marker: dict) -> str:
    return (
        marker.get("upstream", {})
        .get("lastSynced", {})
        .get("sha", "")
        .strip()
    )


def short_sha(root: Path, sha: str) -> str:
    return git_out(root, "rev-parse", "--short", sha).strip()


def resolve_commit(root: Path, rev: str) -> str:
    if not rev:
        die(f"{MARKER_FILE} has no upstream.lastSynced.sha; rerun with --since <upstream-sha>")
    proc = git(root, "rev-parse", "--verify", f"{rev}^{{commit}}", check=False)
    if proc.returncode != 0:
        die(f"could not resolve upstream commit {rev!r}")
    return proc.stdout.strip()


def version_at(root: Path, sha: str) -> str:
    proc = git(root, "show", f"{sha}:.codex-plugin/plugin.json", check=False)
    if proc.returncode != 0:
        return "unknown"
    try:
        return str(json.loads(proc.stdout).get("version", "unknown"))
    except json.JSONDecodeError:
        return "unknown"


def parse_changes(raw: str) -> list[Change]:
    changes: list[Change] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        paths = tuple(parts[1:])
        if paths:
            changes.append(Change(status=status, paths=paths))
    return changes


def changed_path_set(changes: list[Change]) -> list[str]:
    return sorted({path for change in changes for path in change.paths})


def write_patch(root: Path, base: str, latest: str, paths: list[str], destination: Path) -> None:
    if not paths:
        destination.write_text("", encoding="utf-8")
        return
    patch = git_out(root, "diff", "--binary", "--find-renames", base, latest, "--", *paths)
    destination.write_text(patch, encoding="utf-8")


def write_marker(root: Path, upstream_url: str, branch: str, sha: str) -> None:
    marker = read_marker(root)
    marker.setdefault("upstream", {})
    marker["upstream"]["repository"] = upstream_url
    marker["upstream"]["branch"] = branch
    marker["upstream"]["lastSynced"] = {
        "sha": sha,
        "short": short_sha(root, sha),
        "version": version_at(root, sha),
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    marker.setdefault("localPolicy", {})
    marker["localPolicy"].setdefault(
        "syncMode",
        "review upstream diffs, apply generic changes selectively, hand-merge protected paths",
    )
    (root / MARKER_FILE).write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")


def shell_quote(path: Path) -> str:
    text = str(path)
    return "'" + text.replace("'", "'\"'\"'") + "'"


def build_summary(
    *,
    root: Path,
    report_dir: Path,
    upstream_url: str,
    remote: str,
    branch: str,
    base: str,
    latest: str,
    changes: list[Change],
    protected_changes: list[Change],
    candidate_changes: list[Change],
) -> str:
    status = git_out(root, "status", "--short").strip()
    log = git_out(root, "log", "--oneline", f"{base}..{latest}").strip()
    stat = git_out(root, "diff", "--stat", base, latest).strip()
    candidate_patch = report_dir / "candidate-generic.patch"
    protected_patch = report_dir / "protected-manual.patch"

    lines = [
        "# Upstream Superpowers Sync Report",
        "",
        f"- Upstream: `{upstream_url}`",
        f"- Remote ref: `{remote}/{branch}`",
        f"- Previous synced commit: `{short_sha(root, base)}` (`{version_at(root, base)}`)",
        f"- Latest upstream commit: `{short_sha(root, latest)}` (`{version_at(root, latest)}`)",
        f"- Local HEAD: `{short_sha(root, 'HEAD')}`",
        f"- Working tree: `{'clean' if not status else 'dirty'}`",
        f"- Report directory: `{report_dir.relative_to(root)}`",
        "",
        "## Change Counts",
        "",
        f"- Total upstream file changes: {len(changes)}",
        f"- Candidate generic changes: {len(candidate_changes)}",
        f"- Protected/manual changes: {len(protected_changes)}",
        "",
    ]

    if not changes:
        lines += [
            "No upstream changes were found since the recorded sync marker.",
            "",
            "Do not update `.upstream-superpowers.json`; it already points at the latest fetched upstream commit.",
            "",
        ]
        return "\n".join(lines)

    lines += [
        "## Report Files",
        "",
        "- `full-upstream.patch`: reference only; do not apply this wholesale.",
        "- `candidate-generic.patch`: upstream-owned paths that may be applied after inspection.",
        "- `protected-manual.patch`: ASIC identity or local policy paths that must be hand-merged.",
        "- `changed-files.tsv`: upstream name-status list.",
        "- `upstream-log.txt`: upstream commits in this sync window.",
        "- `diffstat.txt`: upstream diffstat in this sync window.",
        "",
        "## Upstream Commits",
        "",
        "```text",
        log or "(none)",
        "```",
        "",
        "## Diffstat",
        "",
        "```text",
        stat or "(none)",
        "```",
        "",
    ]

    if protected_changes:
        lines += [
            "## Protected Manual Review",
            "",
            "These paths overlap ASIC-specific behavior, plugin identity, provenance, or local validation. Preserve local ASIC behavior unless the upstream change is clearly generic and still fits this plugin.",
            "",
            "```text",
            "\n".join(change.display for change in protected_changes),
            "```",
            "",
        ]

    if candidate_changes:
        lines += [
            "## Candidate Generic Review",
            "",
            "Inspect this patch before applying it. If it only updates inherited generic Superpowers behavior, apply it on a sync branch:",
            "",
            "```bash",
            f"git apply --3way {shell_quote(candidate_patch.relative_to(root))}",
            "```",
            "",
            "If the patch conflicts, stop and hand-merge the conflicting files. Do not resolve conflicts by taking upstream wholesale.",
            "",
        ]

    lines += [
        "## Required Codex Flow",
        "",
        "1. Work on a dedicated branch such as `sync/upstream-superpowers-YYYYMMDD`.",
        "2. Read this report and inspect both patch files before editing.",
        "3. Apply candidate generic changes only when they do not erase ASIC-specific behavior.",
        "4. Hand-merge protected changes from `protected-manual.patch`; never copy upstream manifests, bootstraps, README, package metadata, ASIC skills, or eval fixtures wholesale.",
        "5. Keep `asic-superpowers`, `using-asic-superpowers`, `hardware-evidence-first-development`, ariklapid repository URLs, and vendor-neutral ASIC language intact.",
        "6. Run `scripts/validate.sh`.",
        "7. Search for accidental identity regressions with `rg -n \"github.com/obra/superpowers|using-superpowers|asicdesign-ai\" . --hidden --glob '!node_modules/**' --glob '!.git/**'` and justify any intentional hits.",
        f"8. After validation, update the marker with `scripts/run-python.sh scripts/prepare_upstream_superpowers_sync.py --mark-synced {short_sha(root, latest)}`.",
        "9. Commit the sync as one focused change.",
        "",
        "Reference-only protected patch:",
        "",
        "```bash",
        f"sed -n '1,220p' {shell_quote(protected_patch.relative_to(root))}",
        "```",
        "",
    ]
    return "\n".join(lines)


def prepare_report(args: argparse.Namespace) -> int:
    root = repo_root()
    marker = read_marker(root)
    ensure_remote(root, args.remote_name, args.upstream_url)
    latest = fetch_upstream(root, args.remote_name, args.upstream_branch)
    base = resolve_commit(root, args.since or marker_base(marker))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    report_dir = root / args.report_root / f"upstream-superpowers-sync-{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=False)

    raw_changes = git_out(root, "diff", "--name-status", "--find-renames", base, latest)
    changes = parse_changes(raw_changes)
    protected_changes = [change for change in changes if change.protected]
    candidate_changes = [change for change in changes if not change.protected]
    protected_paths = changed_path_set(protected_changes)
    candidate_paths = changed_path_set(candidate_changes)
    all_paths = changed_path_set(changes)

    (report_dir / "changed-files.tsv").write_text(raw_changes, encoding="utf-8")
    (report_dir / "protected-paths.txt").write_text("\n".join(protected_paths) + ("\n" if protected_paths else ""), encoding="utf-8")
    (report_dir / "candidate-paths.txt").write_text("\n".join(candidate_paths) + ("\n" if candidate_paths else ""), encoding="utf-8")
    (report_dir / "upstream-log.txt").write_text(git_out(root, "log", "--oneline", f"{base}..{latest}"), encoding="utf-8")
    (report_dir / "diffstat.txt").write_text(git_out(root, "diff", "--stat", base, latest), encoding="utf-8")
    write_patch(root, base, latest, all_paths, report_dir / "full-upstream.patch")
    write_patch(root, base, latest, candidate_paths, report_dir / "candidate-generic.patch")
    write_patch(root, base, latest, protected_paths, report_dir / "protected-manual.patch")

    summary = build_summary(
        root=root,
        report_dir=report_dir,
        upstream_url=args.upstream_url,
        remote=args.remote_name,
        branch=args.upstream_branch,
        base=base,
        latest=latest,
        changes=changes,
        protected_changes=protected_changes,
        candidate_changes=candidate_changes,
    )
    (report_dir / "summary.md").write_text(summary + "\n", encoding="utf-8")
    print(f"Wrote upstream sync report: {report_dir.relative_to(root)}/summary.md")
    if not changes:
        print("No upstream changes since the recorded marker.")
    else:
        print(f"Candidate changes: {len(candidate_changes)}; protected/manual changes: {len(protected_changes)}")
    return 0


def mark_synced(args: argparse.Namespace) -> int:
    root = repo_root()
    ensure_remote(root, args.remote_name, args.upstream_url)
    latest = fetch_upstream(root, args.remote_name, args.upstream_branch)
    target = latest if args.mark_synced == "latest" else resolve_commit(root, args.mark_synced)
    write_marker(root, args.upstream_url, args.upstream_branch, target)
    print(f"Updated {MARKER_FILE} to upstream {short_sha(root, target)} ({version_at(root, target)})")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare an ASIC-preserving report for syncing original Superpowers changes."
    )
    parser.add_argument("--upstream-url", default=DEFAULT_UPSTREAM_URL)
    parser.add_argument("--remote-name", default=DEFAULT_REMOTE)
    parser.add_argument("--upstream-branch", default=DEFAULT_BRANCH)
    parser.add_argument("--since", help="Override the marker base upstream commit.")
    parser.add_argument("--report-root", default=REPORT_ROOT)
    parser.add_argument(
        "--mark-synced",
        metavar="SHA",
        help="Update .upstream-superpowers.json after a reviewed, validated sync. Use 'latest' for the fetched upstream head.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mark_synced:
        return mark_synced(args)
    return prepare_report(args)


if __name__ == "__main__":
    raise SystemExit(main())
