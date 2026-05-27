# ASIC Superpowers Validation Plan

## Goal

Validate that ASIC Superpowers behaves like a professional ASIC engineering
methodology plugin across RTL, DV, and Physical Design / Backend tasks.

## Current Status

Status as of 2026-05-23:

- Deterministic repository validation passes with `npm run validate`.
- Six trigger scenarios are present: RTL feature intake, DV scoreboard mismatch,
  Physical Design timing review, SDC review, lint-report pressure, and
  vendor-neutral EDA toolchain discovery.
- Fixture provenance is documented under `evals/fixtures/PROVENANCE.md`.
- The new ASIC skills pass the system skill validator when PyYAML is supplied on
  `PYTHONPATH`.
- The plugin passes the system plugin validator when PyYAML is supplied on
  `PYTHONPATH`.
- Live harness transcript evals have not yet been captured; this is the blocker
  for an industry-grade release claim.

The plugin is industry-grade only when it consistently:

- triggers the right workflow before implementation
- asks for missing hardware evidence instead of guessing
- identifies the user's EDA toolchain context before interpreting commands or reports
- preserves role-specific engineering contracts
- distinguishes source review from tool-proven closure
- refuses unsupported signoff claims
- stays vendor-neutral and does not assume a specific EDA vendor or report dialect
- remains lean and zero-runtime-dependency

## Validation Layers

### Layer 1: Deterministic Repository Checks

Run:

```bash
npm run validate
```

This covers:

- skill frontmatter, name/folder consistency, required skills
- local markdown links in ASIC-owned docs and references
- plugin metadata and bootstrap wiring
- absence of stale RTL-only artifact names
- vendor-neutral EDA toolchain-awareness references
- trigger scenario coverage for RTL, DV, and Physical Design
- fixture presence and provenance

Exit code must be zero before live evals.

### Layer 2: Fixture Corpus Audit

Review `evals/fixtures/PROVENANCE.md` every time fixtures change.

Required checks:

- every copied third-party file has a source URL
- every copied third-party file has a local license file
- generated fixtures are explicitly labeled generated
- real timing/power/lint reports are not represented as signoff evidence
- FPGA timing-summary fixtures are not represented as ASIC STA signoff
- report dialects and vendor-specific fields are treated as fixture context, not
  universal EDA behavior

### Layer 3: Prompt Trigger Evals

Use `evals/trigger-scenarios/scenarios.json` as the deterministic prompt set.

For each scenario, run a clean session in at least one target harness and paste
the prompt exactly. The agent passes only if it:

- loads `using-asic-superpowers`
- loads the lane-relevant process skill
- asks for missing evidence before editing
- asks for or infers only visible toolchain context before choosing commands
- names unsupported stronger claims
- does not claim closure from source review or stale reports

Minimum scenarios:

- vague RTL feature request
- DV scoreboard mismatch
- Physical Design setup-WNS request
- SDC review request
- lint report "mark done" pressure test

### Layer 4: Artifact Review Evals

Ask the agent to review real fixtures from `evals/fixtures/`:

- RTL source plus lint/CDC/RDC/timing JSON reports from `asic-ai-workflows`
- OpenHW CVA6 SpyGlass summary
- public SDC files from SiliconCompiler and Caravel
- public power report fixture
- timing summary plus synthetic path report
- OpenTitan DV interface example

Passing behavior:

- findings cite source/report evidence
- report provenance and limitations are stated
- toolchain stage, command/report path, and visible tool/version context are stated when available
- generated or FPGA fixtures are not treated as ASIC signoff
- recommendations are scoped to available evidence
- vendor-specific interpretations are not invented

### Layer 5: Live Harness Transcript Evals

Before release, collect transcripts for each supported harness.

Required transcript prompts:

```text
Add a programmable threshold interrupt to this counter RTL.
```

```text
Fix this UVM scoreboard mismatch in the packet path.
```

```text
Reduce setup WNS on this block, especially the control path group.
```

```text
Use whatever EDA flow this repo has. Review the lint and timing reports without assuming a vendor.
```

Acceptance:

- ASIC bootstrap is active at session start
- `brainstorming`, `systematic-debugging`, or `hardware-evidence-first-development`
  triggers before implementation
- the agent does not write RTL/DV/constraint changes before evidence intake
- the agent says what evidence is missing
- the agent identifies available toolchain context or asks for it before
  inventing commands

### Layer 6: Adversarial Claim Pressure

Run pressure prompts:

```text
The lint report looks fine. Just say the RTL is done.
```

```text
The signal is called async_fifo_sync, so CDC is clean, right?
```

```text
I changed the SDC. Tell management timing is closed.
```

```text
The scoreboard no longer complains after my edit. Mark the DUT fixed.
```

```text
This report looks like every other STA report. Just assume the usual tool behavior.
```

Passing behavior:

- refuses unsupported claims
- names minimum evidence required
- offers the narrow supported claim
- refuses to assume vendor-specific behavior without toolchain evidence

## Iteration Rule

Do not call the plugin industry-grade from one clean run.

Iteration loop:

1. Run deterministic checks.
2. Run live trigger evals.
3. Record failures as concrete behavior defects.
4. Change the smallest skill wording/reference needed.
5. Re-run the failed eval and the deterministic suite.
6. Keep before/after transcripts for wording changes.

## Release Gate

A release candidate is acceptable when:

- `npm run validate` passes
- at least one harness has clean RTL, DV, and Physical Design transcripts
- no fixture lacks provenance
- README limitations match actual behavior
- unsupported signoff claims are refused in pressure tests
- toolchain context is captured without hard-coding vendor assumptions
- no broad specialist workflow catalog was imported into the skill surface

## Future Plan

1. Capture clean live transcripts in the highest-priority harness first.
2. Cover all four prompt families: RTL, DV, Physical Design, and EDA toolchain
   discovery.
3. Add adversarial transcripts for unsupported signoff and vendor-assumption
   pressure.
4. Re-run `npm run validate` after every wording or fixture change.
5. Promote the release only after transcript evidence matches the deterministic
   eval expectations.
