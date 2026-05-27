---
name: hardware-evidence-first-development
description: Use before changing RTL, DV collateral, constraints, backend artifacts, HDL parsers, or hardware workflow fixtures when the task needs evidence before implementation.
---

# Hardware Evidence-First Development

Define the evidence before editing hardware artifacts.

This is the ASIC adaptation of TDD discipline. Use the strongest practical evidence available for the task, without pretending that unavailable evidence exists.

## Workflow

1. Classify the work lane: RTL, DV, Physical Design / Backend, tool parser, docs, or fixture.
2. Read local project overlays before editing: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, README/developer docs, flow docs, and local source-control instructions.
3. Identify the user's EDA toolchain context: configured commands, report dialects, filelists, constraints, waivers, libraries, modes/corners, regressions, and signoff stage when available.
4. Name the claim the work must support.
5. Choose the minimum evidence for that claim within the user's toolchain.
6. Capture or reproduce the current state before editing.
7. Make the smallest scoped change.
8. Re-run the evidence command or re-check the evidence artifact.
9. Report what is proven, what is not proven, what toolchain context was used, and what remains unresolved.

## Local Overlays, Source Control, And Generated RTL

Before modifying hardware artifacts:

- Follow local overlays even when they are stricter than this plugin.
- If the project uses Perforce, run the local `p4 opened`/status check when available and use `p4 edit` or `p4 add` before changing tracked files. Do not work around read-only files with chmod/copy tricks unless the user explicitly authorizes it.
- If local guidance requires MCP-backed source verification, HDL indexing, elaboration context, or generated-source checks, run those before RTL/DV edits and record the evidence scope.
- For generated Verilog, generated netlists, or checked-in generated collateral, identify the generator/source and review the generated output before editing. Prefer changing the generator and regenerating unless the project explicitly treats the generated file as hand-maintained.
- If these local prerequisites cannot be run, state that the review or edit is blocked or limited before proceeding.

## Evidence By Lane

**RTL**

- New behavior: requirement, interface contract, reset/clock assumptions, compile/lint/sim/formal evidence.
- Bug fix: failing test, waveform/log, assertion, lint/compile diagnostic, or minimal reproducer.
- Timing-aware change: structural path evidence or STA/synthesis report; preserve cycle behavior unless approved.
- Toolchain context: filelist format, package/include paths, compile/elab target, simulator or frontend, lint target, waiver policy.

**DV**

- Scoreboard/debug: failing test/seed, observed vs expected transaction, reference-model expectation, monitor sampling point.
- Assertions: assertion source, failure/vacuity/pass report, reset disable condition, bound hierarchy.
- Coverage: objective ID, coverage report before/after, bins/coverpoints, exclusions or waivers.
- UVM collateral: affected agent/driver/monitor/sequence/scoreboard and regression command.
- Toolchain context: regression launcher, simulator, seed syntax, waveform format, coverage database/report format, assertion enablement, UVM library/version if visible.

**Physical Design / Backend**

- Timing: report provenance, design version, mode/corner, path group, WNS/TNS, startpoint/endpoint, constraints.
- Constraints: SDC/MMMC diff, affected clocks/exceptions/modes/corners, syntax/tool check or timing evidence.
- Congestion/utilization: report or heatmap provenance, region, utilization, overflow, blockage/floorplan context.
- ECO/signoff: ECO boundary, equivalence evidence, DRC/LVS/antenna/IR/EM report scope when relevant.
- Toolchain context: flow stage, run directory, design database/netlist/DEF, library set, SDC/MMMC setup, extraction/parasitic status, report command, signoff scope.

## Claim Boundaries

- Compile clean is not lint clean.
- Lint clean is not simulation clean.
- Simulation pass is not formal proof.
- Structural timing risk reduction is not STA timing closure.
- CDC/RDC review is not CDC/RDC tool closure.
- DRC/LVS/antenna/IR/EM claims require the relevant signoff report.
- Tool-specific messages prove only what that tool and configured flow stage check.
- If evidence is unavailable, state the gap instead of upgrading the claim.

## When Evidence Cannot Be Run

Ask for the missing artifact only when needed. Otherwise proceed with a source/report review and label the result as review-only.

Use this wording shape:

> Evidence available: [files/reports/commands]. Evidence unavailable: [missing item]. Supported claim: [narrow claim]. Unsupported claim: [closure/signoff claim].

Also include:

> Toolchain context: [known commands/reports/tool stages]. Toolchain gaps: [unknown vendor/version/setup/mode/corner/waiver/regression details].
