---
name: syncing-upstream-superpowers
description: Use when manually syncing or pulling changes from the original upstream Superpowers repository into ASIC Superpowers while preserving ASIC-specific skills, plugin identity, evals, and metadata.
---

# Syncing Upstream Superpowers

Use this skill for the weekly manual upstream sync. The goal is to import useful generic Superpowers improvements without erasing ASIC-specific behavior.

## Non-Negotiables

- Do not run a wholesale copy, rsync, or merge that overwrites this repo with upstream.
- Do not replace `asic-superpowers`, `using-asic-superpowers`, `hardware-evidence-first-development`, ariklapid repository URLs, ASIC eval fixtures, or vendor-neutral EDA language.
- Do not treat upstream manifests, README, hooks, package metadata, or bootstrap files as safe to take wholesale.
- Do not open an upstream Superpowers PR from this repo.

## Weekly Flow

1. Start from a clean `main` and create a branch:

```bash
git switch main
git pull --ff-only
git switch -c sync/upstream-superpowers-$(date +%Y%m%d)
```

2. Generate the upstream sync report:

```bash
npm run sync:upstream
```

3. Open the reported `triage/upstream-superpowers-sync-*/summary.md`. Treat it as the source of truth for the sync window.

4. Inspect `candidate-generic.patch`. If it is non-empty and only updates inherited generic Superpowers code, apply it with the exact report path printed by the script:

```bash
git apply --3way triage/upstream-superpowers-sync-YYYYMMDD-HHMMSSZ/candidate-generic.patch
```

If it conflicts, stop and hand-merge. Never resolve by taking upstream wholesale.

5. Inspect `protected-manual.patch` and hand-merge only the pieces that still belong in ASIC Superpowers. Preserve local ASIC behavior and identity.

6. Run validation:

```bash
scripts/validate.sh
rg -n "github.com/obra/superpowers|using-superpowers|asicdesign-ai" . --hidden --glob '!node_modules/**' --glob '!.git/**'
```

Justify any intentional grep hits, such as third-party provenance or inherited generic skill names.

7. After the sync is reviewed and validation passes, update the upstream marker:

```bash
npm run sync:upstream:mark
```

8. Review the complete diff before committing:

```bash
git diff --stat
git diff
```

Commit as one focused upstream-sync change.

## Review Heuristics

- Generic skills such as planning, debugging, worktrees, code review, and verification can usually receive upstream fixes after inspection.
- ASIC skills and references are locally owned. Upstream should not modify them.
- Harness integration files are mixed ownership. Port generic bug fixes manually while preserving ASIC bootstrap names and plugin metadata.
- Documentation is mixed ownership. Keep ASIC status, release caveats, and evidence discipline intact.
- If upstream changes skill behavior-shaping language, be conservative and keep this repo's ASIC-specific trigger discipline unless there is clear evidence the upstream change improves it.
