# ASIC Superpowers

ASIC Superpowers is a lean Superpowers-style methodology plugin for ASIC
engineering agents. It helps agents plan, debug, review, and verify claims
across:

- RTL design and implementation
- Design Verification (DV), assertions, coverage, scoreboards, and regressions
- Physical Design / Backend timing, constraints, reports, ECO, and signoff-boundary work

It is not an EDA tool, simulator, synthesis runner, signoff flow, or replacement
for specialist ASIC workflows. It makes the agent work like a careful hardware
engineer: clarify intent, name the evidence, avoid unsupported claims, and state
what remains unresolved.

ASIC Superpowers is also toolchain-aware. The agent should identify your
project's configured simulator, lint, synthesis, formal, CDC/RDC, STA, physical
implementation, power, regression, and signoff/report flow when that context is
available. It stays vendor-neutral: it should not assume a specific EDA vendor,
command syntax, report dialect, waiver format, or signoff recipe unless your
repo or reports provide it.

## Quickstart

Install the plugin in your agent harness, start a clean session, and ask a
hardware-specific prompt.

### Codex

For local development from this checkout, install or load the plugin from this
repo path:

```text
/plugins
```

Then choose the local `asic-superpowers` plugin if your Codex environment exposes
local plugin sources.

### Claude Code

Use the local plugin path while developing:

```text
/plugin install /home/arik/projects/asic-superpowers
```

### OpenCode

Add this checkout to `opencode.json`:

```json
{
  "plugin": ["/home/arik/projects/asic-superpowers"]
}
```

Restart OpenCode.

### Gemini

From this repo:

```bash
gemini extensions install /home/arik/projects/asic-superpowers
```

If your harness does not support local plugin installs, use the repo's `skills/`
directory as a local skill source and make sure `using-asic-superpowers` is
loaded at session start.

## First Prompts

Use one of these after install.

### RTL

```text
Help me modify this RTL block. Start by checking what evidence you need before editing.
Files: rtl/counter.sv, filelist.f
Available evidence: lint.rpt, sim.log
Toolchain context: use the repo Makefile targets if present; otherwise ask before inventing commands.
Goal: add a programmable threshold interrupt.
```

Expected behavior:

- asks about clock/reset, interrupt clear policy, latency, interface semantics,
  and DV acceptance criteria
- identifies compile/lint/sim commands or asks for the project's toolchain
- uses `hardware-evidence-first-development` before editing
- does not claim timing, CDC/RDC, or signoff closure without reports

### DV

```text
Debug this UVM scoreboard mismatch.
Failing test: packet_smoke
Seed: 12345
Files: tb/packet_scoreboard.sv, tb/packet_monitor.sv
Evidence: sim.log, fail.wdb
Toolchain context: use the existing regression launcher and seed syntax.
```

Expected behavior:

- uses systematic debugging before proposing a fix
- asks for observed vs expected transaction behavior
- identifies simulator/regression command, waveform format, and coverage/assertion report context when available
- distinguishes DUT, monitor, scoreboard, sequence, and reference-model root causes
- does not claim full regression or coverage closure from one passing seed

### Physical Design / Backend

```text
Review this setup timing issue and SDC.
Reports: reports/report_timing.rpt
Constraints: constraints/top.sdc
Toolchain context: use the report headers, run directory, and repo flow scripts; do not assume a vendor.
Goal: reduce setup WNS on the control path group.
```

Expected behavior:

- asks for report provenance, design version, mode/corner, path group, and WNS/TNS
- identifies the backend flow stage, report dialect, SDC/MMMC setup, and run context when available
- separates structural timing-risk suggestions from STA-proven timing improvement
- preserves cycle behavior unless a latency/ECO change is explicitly approved
- does not claim signoff clean without signoff reports

## What The Plugin Adds

Core ASIC skills:

- `using-asic-superpowers` - session bootstrap and ASIC skill priority rules
- `hardware-evidence-first-development` - evidence-first workflow for RTL, DV,
  constraints, reports, and backend artifacts

ASIC reference lenses:

- `asic-engineering-contract.md` - intake contract for RTL, DV, and backend work
- `rtl-design-lens.md` - RTL implementation/review checklist
- `dv-verification-lens.md` - DV, assertion, coverage, and scoreboard checklist
- `physical-design-lens.md` - timing, SDC/MMMC, congestion, ECO, and signoff-boundary checklist
- `asic-review-checklist.md` - review rubric for hardware diffs
- `hardware-claim-discipline.md` - claim-to-evidence table
- `eda-toolchain-profile.md` - vendor-neutral toolchain discovery and context capture
- `tool-evidence.md` - how to treat tool, MCP, and report output

The plugin keeps the upstream Superpowers lifecycle: brainstorming, planning,
systematic debugging, code review, verification before completion, worktrees,
and branch finishing.

It routes by required reasoning, not by the user's job title or repo domain.
Plain software/tooling work by an ASIC engineer should use the inherited generic
Superpowers flow. Tasks that require RTL/DV/EDA interpretation, hardware-safe
behavior, or hardware completion claims use ASIC Superpowers. Mixed tasks split
the boundary: generic flow for the software mechanics, ASIC evidence discipline
for interpreting hardware artifacts or reports.

## Minimum Useful Inputs

You can start with partial context. The agent should ask for what is missing.

For RTL work, useful inputs are:

- RTL files, packages, interfaces, and filelist
- compile/elab/lint/sim targets or scripts
- clock/reset assumptions
- protocol or block spec
- compile, lint, sim, assertion, or formal logs
- waiver files or lint configuration when relevant

For DV work, useful inputs are:

- failing test and seed
- simulation log and waveform path
- UVM component scope: sequence, driver, monitor, scoreboard, reference model
- assertion or coverage report
- regression command
- simulator/regression launcher, seed syntax, coverage database format

For Physical Design / Backend work, useful inputs are:

- timing, congestion, utilization, power, DRC/LVS, or ECO reports
- SDC/MMMC files
- mode, corner, path group, startpoint/endpoint
- netlist/DEF/design version
- signoff boundary and ECO limits
- run directory, flow stage, report command, library/parasitic context when visible

## Evidence Discipline

ASIC Superpowers requires narrow, evidence-backed claims:

- Compile success is not design correctness.
- Lint clean is not simulation clean.
- Simulation pass is not formal proof.
- Structural timing-risk reduction is not STA timing closure.
- CDC/RDC review is not CDC/RDC signoff.
- SDC syntax is not constraint correctness.
- DRC/LVS/antenna/IR/EM claims require the relevant signoff reports.
- Vendor-specific interpretation requires visible toolchain evidence.

When evidence is missing, the agent should say what is unresolved instead of
upgrading the claim.

## Validation Status

Current status as of 2026-05-23:

- ASIC plugin metadata and bootstrap have been renamed from upstream Superpowers.
- `using-asic-superpowers` and `hardware-evidence-first-development` exist and validate.
- RTL, DV, Physical Design, EDA toolchain, review, evidence, and claim-discipline references exist.
- README, OpenCode docs, validation plan, and fixture provenance are current.
- Deterministic validation passes locally.
- Live harness transcript evals are still required before an industry-grade release claim.

Run:

```bash
npm run validate
```

This checks:

- skill metadata and required skills
- ASIC bootstrap wiring
- local markdown links
- RTL/DV/Physical Design trigger scenarios
- eval fixture presence and provenance
- vendor-neutral EDA toolchain-awareness references

The repo also validates the new skills with the system skill validator and the
plugin with the system plugin validator. Live harness transcript evals are still
required before calling a release industry-grade.

## Weekly Upstream Sync

To review new changes from the original Superpowers repo without overwriting
ASIC-specific behavior, ask Codex to use `syncing-upstream-superpowers` and run:

```bash
npm run sync:upstream
```

The script writes a report under `triage/` with candidate generic patches and
protected manual-review patches. After a reviewed sync passes validation, update
the tracked upstream marker with:

```bash
npm run sync:upstream:mark
```

## Future Plan

Next release work:

1. Run clean live transcript evals in at least one target harness for RTL, DV,
   Physical Design, and vendor-neutral EDA toolchain prompts.
2. Add transcript artifacts or summaries under `evals/` without exposing private
   project data.
3. Pressure-test unsupported claim prompts: lint clean, CDC clean, timing
   closed, signoff clean, scoreboard fixed, and generic EDA report assumptions.
4. Iterate only on failures observed in transcripts, then re-run `npm run validate`.
5. Add optional deeper workflow bridges to `asic-ai-workflows` only when a real
   repeated task needs them.
6. Keep the plugin lean and vendor-neutral; do not add mandatory EDA
   dependencies or vendor-specific rule packs to core.

## Fixtures And Evals

The repo includes compact eval fixtures under `evals/fixtures/`:

- MIT-licensed local fixtures from `asic-ai-workflows`
- permissively licensed public SDC, lint, timing-summary, power, and DV examples
- one hand-authored synthetic `report_timing.rpt` fixture for deterministic tests

See `evals/fixtures/PROVENANCE.md` for sources, licenses, and limitations.

Trigger scenarios live in `evals/trigger-scenarios/scenarios.json`.

## Scope Boundaries

Use specialist tools and repos as escalation paths when needed:

- `asic-ai-workflows` for deeper structured handoff/report workflows
- HDL MCPs for compiler-backed source context
- UPF/low-power MCPs when available
- EDA tools only when the user has provided the flow context and the active
  workflow supports that phase
- project-local EDA commands should be preferred over invented commands, and
  mutating implementation/signoff commands require explicit approval

ASIC Superpowers stays zero-runtime-dependency and methodology-focused.

## Full Validation Plan

See `docs/ASIC_PLUGIN_VALIDATION_PLAN.md` for the complete release validation
flow, including deterministic checks, live harness transcript evals, and
adversarial claim-pressure prompts.
