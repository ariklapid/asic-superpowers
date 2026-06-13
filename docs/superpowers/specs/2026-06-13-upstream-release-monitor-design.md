# Upstream obra/superpowers Release Monitor Design

## Problem

ASIC Superpowers is derived from `obra/superpowers`, but its generic baseline
can drift when upstream publishes a new stable release. The repository already
has a safe manual sync report and ownership classification, but maintainers must
remember to look for releases themselves.

The repository needs a low-noise notification mechanism that creates one review
issue for every new stable upstream release. It must identify which inherited
baseline files changed without applying upstream changes or weakening the
existing ASIC-specific protection rules.

## Goals

- Poll `obra/superpowers` weekly for newly published stable GitHub releases.
- Create exactly one issue per stable upstream release newer than the tracking
  floor.
- Compare each release with the immediately preceding stable release.
- Report candidate generic changes separately from protected/manual changes.
- Create an issue even when no baseline files changed.
- Catch up deterministically when multiple releases appear between runs.
- Keep all synchronization decisions manual.

## Non-Goals

- Do not automatically apply patches, create branches, open pull requests, or
  update `.upstream-superpowers.json`.
- Do not monitor drafts, prereleases, untagged commits, or every change to
  upstream `main`.
- Do not use an external webhook service, GitHub App, or runtime dependency.
- Do not infer whether an upstream change is appropriate for ASIC Superpowers;
  the automation only classifies paths and presents evidence for review.

## Architecture

Add a GitHub Actions workflow that runs weekly and supports manual dispatch.
The workflow checks out the repository and invokes a Python standard-library
monitor script. The script reads published releases from the GitHub REST API,
filters out drafts and prereleases, orders releases by publication time, and
processes every release newer than the configured tracking floor that does not
already have a corresponding issue.

For each release, the script compares its tag against the preceding stable
release tag in the upstream Git repository. Local-only ASIC files therefore do
not enter the change set. Changed upstream paths are assigned one of three
review labels using the ownership policy shared with
`scripts/prepare_upstream_superpowers_sync.py`: candidate generic, ASIC-owned,
or mixed/manual.

The script renders an issue proposal and either prints it in dry-run mode or
creates it through the GitHub API. It never changes repository files or the
tracked upstream sync marker.

## Components

### Scheduled Workflow

Create `.github/workflows/upstream-superpowers-release-monitor.yml` with:

- A weekly `schedule` at a non-hour-boundary UTC minute.
- `workflow_dispatch` with dry-run support for manual verification.
- Minimal permissions: `contents: read` and `issues: write`.
- Concurrency that prevents overlapping monitor runs.
- A pinned checkout action and repository-native Python launcher.
- `GITHUB_TOKEN`, source repository, destination repository, and dry-run mode
  passed explicitly to the monitor.

The workflow will fail visibly in GitHub Actions when release discovery,
comparison, or issue creation fails. It will not create a failure issue because
that can generate recursive noise when issue permissions or API access are the
cause of failure.

### Release Monitor

Create `scripts/monitor_upstream_superpowers_releases.py`. Its responsibilities
are:

1. Read configuration for source repository, destination repository, tracking
   floor, token, and dry-run mode.
2. Fetch all relevant published releases from `obra/superpowers`, following API
   pagination.
3. Exclude drafts and prereleases.
4. Establish the tracking floor at upstream `v5.1.0`, matching the current ASIC
   Superpowers baseline marker.
5. Pair every later release with the immediately preceding stable release.
6. Detect existing open or closed destination issues using a hidden release-tag
   marker.
7. Fetch the required upstream tags and compute rename-aware changed paths.
8. Classify changes with the shared `candidate-generic`, `asic-owned`, and
   `mixed-manual` ownership rules.
9. Render the issue title and body.
10. Print proposals in dry-run mode or create missing issues through the GitHub
    API.

The implementation must handle several missing releases in one run and create
their issues from oldest to newest. Failure creating one issue stops the run so
the next execution can safely retry; already-created issues are skipped through
deduplication.

### Shared Ownership Policy

Move or expose the existing protected path patterns and classification helper
from `scripts/prepare_upstream_superpowers_sync.py` in a small importable module,
for example `scripts/upstream_superpowers_policy.py`.

Both the manual sync report and scheduled release monitor must use this module.
This avoids two ownership lists drifting apart.

The manual sync report may preserve its existing two patch artifacts for
compatibility: `candidate-generic.patch` contains `candidate-generic` paths,
while `protected-manual.patch` combines `asic-owned` and `mixed-manual` paths.
The release issue presents all three labels separately because it is a review
index rather than an applyable patch bundle.

The shared policy exposes three explicit labels:

- `candidate-generic`: an upstream path inherited as generic Superpowers
  behavior, such as generic skills, generic tests, or generic supporting
  documentation. This label means "eligible for selective porting after
  review," not "safe to apply automatically."
- `asic-owned`: a path whose local counterpart is owned by ASIC Superpowers,
  including `skills/using-asic-superpowers/**`,
  `skills/hardware-evidence-first-development/**`, ASIC evals and fixtures, and
  ASIC-specific validation or planning documents. An upstream path matching
  this policy must not overwrite the local counterpart; reviewers may only
  extract a clearly applicable generic idea by hand.
- `mixed-manual`: a path combining upstream functionality with local plugin
  identity or integration behavior, including manifests, hooks, README and
  package metadata, GitHub configuration, bootstrap files, provenance, and the
  local sync machinery. Reviewers must hand-merge relevant upstream changes
  while preserving ASIC naming, repository URLs, trigger discipline, and local
  validation.

Classification is path-based and conservative. It does not infer ownership
from file contents or names outside the policy. When a new ASIC-specific path
is added to the repository, the same change must add it to the shared ownership
policy and its tests. Unknown paths default to `candidate-generic` because they
originate in the upstream-to-upstream release diff, but still require human
review before porting.

## Release And Comparison Semantics

A tracked release is a GitHub release from `obra/superpowers` where both `draft`
and `prerelease` are false. Plain Git tags without a GitHub release are ignored.

Release order is based on `published_at`, with stable API order used only as a
deterministic tie-breaker. Each tracked release is compared with the stable
release immediately before it. For example, if `v5.2.0` and `v5.3.0` are both
published before the next weekly run, the monitor creates:

- A `v5.2.0` issue comparing `v5.1.0...v5.2.0`.
- A `v5.3.0` issue comparing `v5.2.0...v5.3.0`.

The upstream tag names returned by the release API are resolved directly in the
fetched upstream repository. A missing or non-commit tag is an error; the
monitor must not guess a replacement ref.

## Issue Contract

The title format is:

```text
Upstream obra/superpowers <tag> baseline review
```

The body contains:

- New and previous stable release tags, publication dates, links, and resolved
  commit SHAs.
- A GitHub compare link for the two tags.
- A count and list of `candidate-generic` baseline file changes.
- A count and list of `asic-owned` file changes.
- A count and list of `mixed-manual` file changes.
- The upstream release notes link.
- An explicit statement when no baseline files changed.
- A maintainer checklist to inspect upstream changes, selectively port suitable
  changes, run repository validation, and update `.upstream-superpowers.json`
  only after a reviewed sync.
- The hidden marker
  `<!-- upstream-superpowers-release:<tag> -->`.

The marker is the deduplication key. Before creating an issue, the monitor
searches both open and closed issues in the destination repository. Closing an
issue therefore records that the release was reviewed and prevents recreation.
The issue remains open until maintainers close it manually.

## Error Handling

- GitHub API requests use explicit headers and report the endpoint and response
  status without printing tokens.
- Pagination continues until the API returns no next page or an empty page.
- Rate limiting, authentication failure, malformed API responses, unresolved
  tags, and Git failures terminate the run with a nonzero exit.
- Existing issues are detected before cloning or diffing where practical, so a
  routine no-op run stays inexpensive.
- Issue bodies are generated entirely before creation. Partial issue content is
  never submitted.
- Dry-run mode performs discovery, comparison, classification, deduplication,
  and rendering but makes no issue mutations.

## Security

- Grant the workflow only `contents: read` and `issues: write`.
- Use the repository-provided `GITHUB_TOKEN`; require no personal token or
  additional secret.
- Pin external actions to immutable commit SHAs.
- Treat upstream release metadata, tags, and file paths as untrusted data and
  pass Git arguments as discrete process arguments rather than shell strings.
- Do not execute code from the upstream repository.
- Use only Python's standard library and Git, preserving the plugin's
  zero-dependency policy.

## Testing

Add deterministic tests with fixture API responses and temporary Git
repositories. Tests must not require network access or live GitHub state.

Cover:

- Draft and prerelease filtering.
- Tracking-floor behavior.
- Adjacent stable-release pairing, including multiple missed releases.
- Release ordering and pagination.
- Candidate-generic, ASIC-owned, and mixed-manual path classification,
  including renames and the default for unknown upstream paths.
- Hidden-marker generation and open/closed issue deduplication.
- Issue title and Markdown body rendering.
- Explicit no-baseline-change issue rendering.
- Dry-run behavior and API creation behavior.
- API, malformed response, and unresolved-tag failures.
- Continued compatibility of the existing manual sync report with the shared
  ownership policy.

Run the focused monitor tests, new regression tests for the existing manual
sync report, and `npm run validate`. Validate the workflow structure without
adding a new runtime dependency.

## Documentation And Operations

Update the README weekly-sync section to distinguish notification from syncing:

- The monitor only reports new stable releases.
- Maintainers still use the `syncing-upstream-superpowers` skill and
  `npm run sync:upstream` for review and selective integration.
- Manual dispatch with dry-run is the supported operational check.
- `v5.1.0` is the initial release tracking floor.
- Failed scheduled runs are investigated through the Actions log and can be
  retried manually.

## Acceptance Criteria

- A weekly or manually dispatched run detects every stable upstream release
  after `v5.1.0` that lacks a destination issue.
- Each release produces one issue titled
  `Upstream obra/superpowers <tag> baseline review`.
- Each issue compares adjacent stable releases and separates
  `candidate-generic`, `asic-owned`, and `mixed-manual` paths.
- Releases with no baseline file changes still produce an issue stating that
  result.
- Open and closed issues both prevent duplicate creation.
- Dry-run produces complete proposals without mutating GitHub.
- The automation never applies upstream changes or advances the sync marker.
- Deterministic tests and the repository validation suite pass.
