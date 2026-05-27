# ASIC Superpowers Plan Audit

Date: 2026-05-23

## Audit Assumption

`asic-superpowers` should directly fit ASIC engineers across RTL design, Design
Verification (DV), and Physical Design / VLSI Backend. The plugin should not
implicitly assume the coding agent's hardware user is an RTL designer.

Every hardware engineer should get immediate benefit from the Superpowers skill
concepts, lightly tuned toward ASIC engineering:

- clarify intent before implementation or analysis
- preserve explicit engineering contracts
- plan small reviewable changes
- define evidence before changing artifacts
- review work through role-appropriate ASIC lenses
- verify claims with fresh tool, source, or report evidence

## Findings

### Blocking: The Executive Decision Contradicts The New Direction

The plan currently frames the product as a "lean RTL-development methodology
variant." That is too narrow.

Required direction:

> ASIC Superpowers is a lean Superpowers-style methodology plugin for ASIC
> engineering work across RTL design, Design Verification, and Physical Design /
> Backend. It adapts Superpowers' planning, debugging, review, and
> evidence-before-claims discipline to hardware artifacts without becoming an
> EDA tool or a catalog of specialist ASIC workflows.

### Blocking: The First-Cut Skill Surface Assumes RTL Is The Main User

The proposed first new behavior skill is `rtl-verification-first-development`.
That helps RTL authors, but DV engineers and Physical Design engineers need an
equally direct entry point.

Required change:

- replace `rtl-verification-first-development` with
  `hardware-evidence-first-development`
- define role-specific evidence paths:
  - RTL: design contract, compile, lint, simulation, assertion, formal smoke
  - DV: failing test or seed, assertion status, coverage hole, scoreboard or
    reference-model evidence, regression command
  - Physical Design: report provenance, SDC/MMMC context, timing path, WNS/TNS,
    congestion, utilization, floorplan, ECO, DRC/LVS/antenna evidence

### High: DV And Physical Design Are Treated As Lenses, Not First-Class Workflows

The plan says "RTL development lenses." That should become "ASIC engineering
lenses" with equal first-class coverage:

- RTL implementation lens
- DV/debug/coverage lens
- Physical Design/timing/constraints lens
- Evidence and claim discipline lens

### High: Brainstorming Intake Is RTL-Centric

The existing intake questions are good for RTL, but incomplete for DV and
Physical Design.

Add role-aware branches:

- RTL: design intent, block scope, clocks/resets, interfaces, latency,
  throughput, PPA, microarchitecture assumptions, filelists, compile/lint/sim
  commands
- DV: testbench scope, failing test/seed, UVM component, monitor, driver,
  scoreboard, reference model, assertion, coverage hole, regression command
- Physical Design: flow stage, source reports, netlist/DEF/SDC/MMMC context,
  path group, corner/mode, WNS/TNS, utilization, congestion, floorplan
  constraints, ECO limits, signoff boundary

### High: Metadata Undersells The Product

The plugin description should not say "RTL-aware." It should say something like:

> Evidence-first Superpowers methodology for ASIC RTL, DV, and Physical Design
> agents.

### Medium: Claim Discipline Needs DV And Physical Design Claims

The claim-to-evidence table should add claims for:

- regression passes
- coverage improved or closed
- assertion proven, failing, or vacuous
- scoreboard mismatch fixed
- timing QoR improved with WNS/TNS/path evidence
- constraint change validated
- congestion improved
- DRC/LVS/antenna clean
- ECO equivalence preserved

It should also split "Timing improved" into:

- structural timing risk reduced
- STA timing improved

### Medium: Trigger Evals Only Prove RTL Behavior

The trigger scenario list should test RTL, DV, and Physical Design prompts:

- vague "write RTL" request with missing clock/reset/PPA/DV details
- bug fix request against RTL with no reproducer
- request to "clean up" RTL that risks changing cycle behavior
- request to fix a UVM scoreboard mismatch with no failing seed
- request to close a coverage hole without objective mapping
- request to analyze a failing assertion
- request to reduce setup WNS without timing report provenance
- request to review an SDC/MMMC change
- request to explain congestion hotspots from backend reports
- request to mark work done after only editing code

## Required Plan Changes

1. Replace RTL-first product framing with ASIC engineering framing.
2. Rename the first methodology phase from "Lean RTL Methodology Layer" to
   "Lean ASIC Engineering Methodology Layer."
3. Replace `rtl-verification-first-development` with
   `hardware-evidence-first-development`.
4. Replace RTL-only reference names with ASIC-wide references:
   - `asic-engineering-contract.md`
   - `rtl-design-lens.md`
   - `dv-verification-lens.md`
   - `physical-design-lens.md`
   - `asic-review-checklist.md`
   - `hardware-claim-discipline.md`
   - `tool-evidence.md`
5. Expand brainstorming, planning, code review, claim discipline, trigger evals,
   example flows, and definition of done to cover RTL, DV, and Physical Design.
6. Keep the plugin lean: do not import a broad specialist workflow catalog or
   require EDA tools as dependencies.

## Current Status

Status as of 2026-05-23:

- The audit direction has been applied to `ASIC_SUPERPOWERS_PLAN.md`.
- The implementation now treats RTL, DV, and Physical Design / Backend as
  first-class lanes.
- `rtl-verification-first-development` was replaced by
  `hardware-evidence-first-development`.
- ASIC-wide references were added for engineering contract, RTL, DV, Physical
  Design, review, hardware claims, tool evidence, and EDA toolchain profiling.
- README and validation docs now state the current deterministic validation
  status and the remaining live transcript release gate.
- The plugin is vendor-neutral but toolchain-aware: it should discover or ask
  for the user's EDA flow instead of assuming a vendor.

## Future Plan

- Run live harness transcript evals for RTL, DV, Physical Design, and
  toolchain-discovery prompts.
- Add sanitized transcript evidence before claiming an industry-grade release.
- Keep future additions narrow and evidence-driven; do not import broad
  specialist ASIC workflow catalogs into the core plugin.
