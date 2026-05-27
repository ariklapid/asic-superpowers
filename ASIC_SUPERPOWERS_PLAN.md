# ASIC Superpowers Plan

Date: 2026-05-18

Scope correction after clarification: this plan now treats `asic-superpowers` as
a lean Superpowers-style methodology plugin for ASIC engineering work across RTL
design, Design Verification (DV), and Physical Design / VLSI Backend. It should
not become a large catalog of specific ASIC analysis skills.

Workspace:

- Target repository: `/home/arik/projects/asic-superpowers`
- Upstream reference clone: `/home/arik/projects/superpowers`
- Upstream reference commit inspected: `f2cbfbe` on `main`
- Markdown corpus inspected under `/home/arik/projects/*`: 173 `.md` files, about 29,421 lines

## Current Status

Status as of 2026-05-23:

- The repository has been converted from a generic Superpowers baseline into an
  ASIC Superpowers plugin baseline.
- Plugin metadata, OpenCode bootstrap, session-start hook, Gemini bootstrap, and
  README now identify ASIC Superpowers.
- `using-asic-superpowers` and `hardware-evidence-first-development` have been
  added.
- ASIC references now cover RTL, DV, Physical Design / Backend,
  hardware-claim discipline, tool evidence, and vendor-neutral EDA toolchain
  profiling.
- Core Superpowers skills have light ASIC adaptations in brainstorming,
  planning, code review, and verification-before-completion.
- Eval fixtures and trigger scenarios exist for RTL, DV, Physical Design,
  reports, SDC, lint, timing, power, and toolchain-discovery behavior.
- Deterministic validation passes with `npm run validate`.
- System plugin validation and system skill validation have passed for the new
  ASIC skills when PyYAML is supplied on `PYTHONPATH`.
- Live harness transcript evals remain the main blocker before claiming an
  industry-grade release.

## Executive Decision

Build `asic-superpowers` as a lean ASIC engineering methodology variant of
`obra/superpowers`, not as a bundle of many ASIC point skills.

The goal is to apply the Superpowers mindset to hardware work:

1. Clarify intent before implementation.
2. Preserve an explicit design contract.
3. Plan small, reviewable edits.
4. Define evidence before changing RTL, DV collateral, constraints, reports, or
   backend flow artifacts.
5. Review for correctness, DV observability, and physical-design impact.
6. Verify claims with fresh evidence before calling work complete.

The first-cut plugin should be a hardware-aware way of working, not a catalog of
CDC, RDC, timing, UVM, UPF, DFT, and synthesis mini-tools. Those deeper flows can
remain in `asic-ai-workflows` and related MCP projects. `asic-superpowers`
should link to them as optional reference material only when they are useful.

The adaptation should be conservative:

1. Keep the Superpowers lifecycle: skill bootstrap, brainstorming, worktree
   isolation, planning, implementation, review, debugging, and completion.
2. Retune that lifecycle for RTL implementation, DV/debug/coverage work, and
   Physical Design / Backend analysis and artifact changes.
3. Add only a small number of ASIC-specific support skills or references where
   generic software assumptions would produce bad hardware behavior.
4. Preserve the plugin's low-dependency posture. Do not turn this plugin into an
   EDA tool, simulator, synthesis runner, MCP server, or full ASIC workflow
   library.

The right product is an ASIC engineering discipline plugin for RTL, DV, and
Physical Design practitioners. The wrong product is a monolithic "AI chip
designer" persona, a copy of `asic-ai-workflows`, or a half-built EDA platform
inside a skills plugin.

## Source Context Read

### Upstream Superpowers

The upstream plugin is a skills-driven methodology for coding agents. Its core
shape is:

- `skills/` contains the behavior-shaping skills.
- `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, Gemini, Cursor,
  OpenCode, and hooks expose the same skills to different harnesses.
- Session-start glue injects the `using-superpowers` bootstrap so skills
  auto-trigger.
- OpenCode support registers the skills path and injects bootstrap content via a
  message transform.
- Testing focuses on real agent-session behavior and transcript inspection,
  especially for multi-agent workflows.

Important upstream principles to preserve:

- Skills are mandatory workflows, not optional suggestions.
- Skill descriptions must trigger usage but must not summarize the full workflow.
- Behavior-shaping skill text is treated like code and needs evaluation evidence.
- The system prefers evidence over claims.
- TDD, systematic debugging, and verification-before-completion are deliberately
  strict.
- Subagent-driven development uses fresh context, precise prompts, and two-stage
  review.
- Worktree behavior should detect native harness isolation before falling back to
  raw `git worktree`.

Important upstream constraints:

- Domain-specific skills belong in standalone plugins.
- New dependencies are not acceptable unless supporting a new harness.
- Project-specific or fork-specific changes should not be pushed upstream.
- Skill changes need pressure testing because wording changes agent behavior.

### ASIC Workflow Corpus

The `asic-ai-workflows` repo should inform this plugin, not be copied wholesale
into it.

Useful ideas to reuse as methodology:

- Narrow, evidence-grounded behavior beats broad "expert" personas.
- Deterministic outputs and stable IDs are useful for handoff artifacts.
- Clear scope limits prevent false signoff claims.
- Requirements, PPA, RTL implementation, DV objectives, assertions, coverage,
  timing risk, constraints, backend reports, and handoff assumptions should stay
  connected during ASIC engineering work.

Useful ideas to leave outside the plugin:

- The full current skill catalog for CDC, RDC, timing, DV plan assembly, UVM,
  SVA, coverage, RTL package assembly, and flow-level YAML outputs.
- Schema-backed smoke-eval infrastructure.
- Domain-specific workflow expansion such as low-power and DFT families.

Those belong in `asic-ai-workflows` or focused MCP/tooling repos. In
`asic-superpowers`, they should appear as optional references and review lenses,
not as dozens of auto-triggering plugin skills.

The most important domain habits to carry into Superpowers are:

- Ground every hardware claim in visible source, tool output, or explicit user
  intent.
- Treat naming as a hint, never proof.
- Preserve `REQ-NNN`, `OBJ-NNN`, `TEST-NNN`, `SVA-NNN`, `COV-NNN`, and similar
  traceability IDs.
- Keep power, performance, and area explicit and separate.
- Emit unresolved items instead of inventing hidden microarchitecture, protocol,
  timing, reset, or power intent.
- Never claim synthesis, STA, CDC, RDC, formal, low-power, or signoff closure
  from agent reasoning alone.

### pyslang MCP Corpus

`pyslang-mcp` is a read-only semantic HDL context server for Verilog and
SystemVerilog. It is relevant to this plugin as optional evidence, not as a
dependency.

Usable patterns:

- Require explicit `project_root` and keep paths scoped under it.
- Start from filelists or explicit source files.
- Prefer compiler-backed facts for diagnostics, design-unit inventory,
  hierarchy, symbol lookup, syntax summaries, and project summaries.
- Keep outputs compact, stable, and truncated with metadata when large.
- Treat clean parse diagnostics as parse evidence only, not lint, simulation,
  synthesis, CDC, timing, or signoff evidence.

This plugin should reference `pyslang-mcp` as an optional read-only context
source in HDL skills, while still working from plain files when the MCP is not
installed.

### UPF MCP Corpus

`upf-mcp` is still foundation-stage, but its planning documents are directly
useful for ASIC Superpowers future scope.

Key lessons:

- Power intent should be deterministic rule-engine first, LLM interface second.
- Do not embed restricted IEEE 1801 text or proprietary vendor examples.
- Generate from explicit engineer-confirmed strategy input, not hidden
  inference.
- Unsupported UPF constructs should become diagnostics, not ignored text.
- Tool-specific and vendor-specific behavior belongs in adapters or rule packs,
  not generic core behavior.

ASIC Superpowers should not implement UPF parsing itself. It should initially add
low-power intake and review guidance as skills/rules, then optionally consume
`upf-mcp` when that server becomes runnable.

### Portal And Quiz Corpus

The portal and quiz repos are not plugin source material, but they show the
ecosystem direction:

- Education and practitioner feedback matter.
- RTL design, synthesis, CDC, STA, and related concepts should be taught through
  concrete examples, diagrams, timing sketches, and realistic mistakes.
- The quiz repo uses SystemVerilog-first framing and emphasizes practical
  microarchitecture reasoning over trivia.
- The portal treats `asic-ai-workflows` as source-of-truth for workflow content.

For this plugin, that implies examples and docs should be concrete, hardware
specific, and educational, but the plugin itself should remain an engineering
workflow tool rather than a learning portal.

## What Should Stay From Superpowers

Keep these upstream skills with minimal or no behavior changes:

- `using-git-worktrees`
- `finishing-a-development-branch`
- `requesting-code-review`
- `receiving-code-review`
- `systematic-debugging`
- `verification-before-completion`
- `dispatching-parallel-agents`
- `subagent-driven-development`
- `executing-plans`
- `writing-skills`

The behavior is still useful for hardware repos:

- Branch/worktree isolation protects RTL, DV, constraint, report-analysis, and
  documentation branches and review state.
- Systematic debugging maps well to simulation failures, CI failures, and tool
  diagnostics.
- Review discipline catches overbuilding and spec drift.
- Verification-before-completion is especially important in hardware, where a
  clean compile can be misrepresented as design correctness.
- Subagent-driven execution remains useful when tasks have disjoint write sets,
  such as docs, checklists, tests, independent RTL modules, DV collateral,
  constraint files, or backend report summaries.

## What Needs Light Adaptation

### Bootstrap Skill

Replace upstream `using-superpowers` with `using-asic-superpowers`, or keep a
compatibility alias only if a target harness requires it.

Required additions:

- ASIC tasks must apply the ASIC engineering contract and hardware claim
  discipline before generic coding habits.
- The lean ASIC-specific skill surface is mandatory for RTL, DV collateral,
  Physical Design / Backend artifacts, constraints, filelists, reports, or
  hardware tool evidence.
- Specialist external workflows are escalation paths, not the default response
  to every hardware-related word in a prompt.
- If both generic Superpowers and ASIC Superpowers are installed, the ASIC
  plugin should win for hardware tasks and defer to generic Superpowers for
  non-hardware software tasks.

Do not add a long hardware encyclopedia to the bootstrap. Keep it small and
trigger-oriented.

### Brainstorming

Keep the design gate, but add hardware intake questions and acceptance criteria.

Hardware-specific checklist additions:

- design intent and block scope
- top module or target hierarchy
- interface semantics and protocols
- clocks and resets
- reset style, polarity, and release assumptions
- PPA targets: performance, power, area
- latency and throughput expectations
- configuration and status behavior
- power-domain and always-on assumptions when relevant
- DV acceptance criteria
- available files, filelists, packages, interfaces, and tool reports
- DV scope: failing test/seed, UVM component, monitor, driver, scoreboard,
  reference model, assertion, coverage hole, and regression command when relevant
- Physical Design scope: flow stage, report provenance, netlist/DEF/SDC/MMMC
  context, path group, corner/mode, WNS/TNS, utilization, congestion, floorplan
  constraints, ECO limits, and signoff boundary when relevant

The existing "ask one question at a time" rule remains useful. ASIC questions
should be sequenced, not dumped.

### Writing Plans

Keep the detailed plan format, but add hardware verification steps.

For RTL/DV/Physical Design work, every implementation or analysis task should
specify:

- exact source files and filelists
- required package/interface dependencies
- expected compile command, if available
- lint/static-analysis command, if available
- simulation, unit test, or formal smoke, if available
- DV regression, assertion, scoreboard, or coverage command/report, if available
- Physical Design report, constraint file, mode/corner, path group, ECO, or
  signoff artifact scope, if available
- expected red/green behavior when a test can be written first
- what evidence is sufficient for the claim being made
- what remains unresolved after the task

The generic "write complete code in every plan step" rule should be softened for
large ASIC artifact changes. Plans should still be concrete, but should not paste
huge RTL modules, UVM components, report dumps, or constraint files when the
right task is to modify an existing artifact with line-scoped instructions and
explicit evidence gates.

### Evidence-First Development

Do not delete the upstream TDD skill. It is still right for plugin code,
scripts, parsers, schema validators, and software in this repo.

Add an ASIC-specific companion skill, tentatively:

- `hardware-evidence-first-development`

This skill should say:

- Before changing RTL, DV collateral, constraints, reports, or backend flow
  artifacts, define the evidence first.
- Evidence can be a failing simulation test, an assertion, a lint/compile
  diagnostic, a golden YAML smoke fixture, a coverage report, a scoreboard
  mismatch, a timing/congestion/DRC/LVS report, or a focused review checklist,
  depending on the task.
- For bug fixes, reproduce the failure before editing.
- For new RTL, start from requirements, microarchitecture spec, and acceptance
  checks rather than ad hoc code.
- For DV changes, start from the verification objective, failing seed/test,
  assertion behavior, scoreboard/reference-model expectation, or coverage gap.
- For Physical Design changes, start from the relevant report, corner/mode,
  constraint context, path group, floorplan/congestion evidence, or ECO boundary.
- A clean compile is necessary evidence, not sufficient evidence.

This avoids forcing generic software TDD into places where it would produce
ritualistic or impossible hardware work, while preserving the upstream discipline
of evidence-before-implementation.

### Code Review

Keep upstream review workflow, but provide an ASIC review prompt template.

ASIC review should check:

- requirement and objective traceability
- synthesizable SystemVerilog subset
- single-driver and complete-assignment discipline
- reset style, polarity, and release consistency
- clock-domain and reset-domain assumptions
- width, signedness, truncation, and X semantics hazards
- protocol stability and backpressure behavior
- timing-risk structures such as deep mux, priority, compare, arithmetic, and
  fanout paths
- DV plan gaps: monitors, scoreboards, assertions, coverage, tests, and risks
- DV implementation gaps: stimulus intent, checkers, reference-model behavior,
  race sensitivity, reset/error behavior, coverage closure, and regression scope
- Physical Design gaps: constraint intent, mode/corner scope, path provenance,
  fanout/congestion/utilization impact, ECO safety, and signoff boundary
- tool evidence provenance and limitations
- improper signoff claims

## Domain Content Scope

Do not import the full `asic-ai-workflows` skill library into
`asic-superpowers`.

This plugin should carry a small set of reusable ASIC engineering lenses:

1. **RTL implementation lens**: requirements, clocks/resets, interfaces,
   latency/throughput, PPA targets, and unresolved assumptions.
2. **DV/debug/coverage lens**: controllability, observability, scoreboarding
   surface, assertions, coverage intent, error/reset behavior, and protocol
   checkability.
3. **Physical Design / Backend lens**: timing path evidence, constraints,
   corners/modes, fanout, congestion, utilization, floorplan limits, ECO
   boundaries, clock/reset assumptions, and signoff scope.
4. **Evidence discipline lens**: compile/lint/sim/formal/tool/report evidence
   before claims.

These can live as short reference files and review checklists used by the core
Superpowers skills. They do not need to be separate auto-triggering skills.

### First-Cut ASIC Additions

Add only these new plugin-specific artifacts at first:

- `using-asic-superpowers`: bootstrap and priority rules for ASIC tasks.
- `hardware-evidence-first-development`: hardware adaptation of evidence-before-
  implementation discipline for RTL, DV, and Physical Design artifacts.
- `references/asic-engineering-contract.md`: compact checklist for intent,
  scope, interfaces, clocks/resets, PPA, DV, constraints, backend context, and
  unresolved assumptions.
- `references/rtl-design-lens.md`: compact RTL implementation and review lens.
- `references/dv-verification-lens.md`: compact DV/debug/coverage review lens.
- `references/physical-design-lens.md`: compact Physical Design / Backend
  timing, constraint, report, ECO, and signoff-boundary lens.
- `references/asic-review-checklist.md`: compact review rubric for RTL, DV, and
  Physical Design changes.
- `references/hardware-claim-discipline.md`: claim-to-evidence table.
- optional `references/tool-evidence.md`: how to treat compiler, lint,
  simulation, regression, coverage, STA, CDC/RDC, DRC/LVS, power, and MCP
  evidence without overclaiming.

Everything else should stay outside the first-cut plugin.

### Optional External References

The plan can link to `asic-ai-workflows` for deeper workflows:

- block-level RTL planning
- block DV planning
- pre-synthesis timing risk
- CDC/RDC/timing/DV YAML reports

Those workflows should not be copied into this plugin unless a later usage study
shows that users need one specific workflow to trigger frequently enough to earn
first-class skill status.

## Possible Later Skills

Add later skills only after the lean methodology plugin is working and there is
evidence that a repeated user task needs first-class treatment.

Candidates:

- `simulation-failure-triage`
- `dv-regression-failure-triage`
- `coverage-closure-review`
- `waiver-review`
- `constraint-aware-review`
- `backend-report-review`

Defer standalone CDC, RDC, timing-closure, UVM, SVA, coverage, low-power, DFT,
and protocol-specific skills by default. They are useful domains, but adding all
of them would shift this project away from the Superpowers philosophy layer and
toward a broad workflow catalog.

## Plugin Shape

Recommended repository layout after implementation:

```text
asic-superpowers/
  .codex-plugin/
    plugin.json
  .claude-plugin/
    plugin.json
  .cursor-plugin/
    plugin.json
  .opencode/
    INSTALL.md
    plugins/asic-superpowers.js
  hooks/
    session-start
  skills/
    using-asic-superpowers/
      SKILL.md
      references/
        codex-tools.md
        gemini-tools.md
        copilot-tools.md
        asic-engineering-contract.md
        rtl-design-lens.md
        dv-verification-lens.md
        physical-design-lens.md
        asic-review-checklist.md
        hardware-claim-discipline.md
        tool-evidence.md
    brainstorming/
      SKILL.md
      visual-companion.md
    writing-plans/
      SKILL.md
    test-driven-development/
      SKILL.md
      testing-anti-patterns.md
    hardware-evidence-first-development/
      SKILL.md
  docs/
    examples/
    testing.md
  evals/
    trigger-scenarios/
  scripts/
    check_skill_contracts.py
    check_links.py
    check_trigger_metadata.py
```

The important point is the small skill surface. The plugin should mostly be
upstream Superpowers plus ASIC-aware adaptations and compact reference lenses
for RTL, DV, and Physical Design work. Deep task workflows should remain
external references until proven necessary.

## Metadata And Branding Changes

Update the plugin metadata, but do not spend early effort on visual polish.

Required:

- plugin name: `asic-superpowers`
- display name: `ASIC Superpowers`
- description: Evidence-first Superpowers methodology for ASIC RTL, DV, and
  Physical Design agents
- keywords: `asic`, `rtl`, `systemverilog`, `dv`, `uvm`, `cdc`, `rdc`,
  `timing`, `physical-design`, `synthesis`, `verification`
- repository URL: this repo once published
- skills path: `./skills/`

Optional later:

- icon and logo assets
- website URL under `asicdesign.ai`
- screenshots for marketplace listings

Keep package scripts close to upstream. Do not add runtime dependencies for
domain analysis.

## Tool And MCP Policy

ASIC Superpowers should be tool-aware but not tool-dependent.

Required policy:

- Prefer plain file reads and `rg` for simple questions.
- Use optional read-only MCPs only when they materially improve evidence.
- Record tool evidence and limitations.
- Non-mutating evidence commands such as compile, lint, simulation, report
  parsing, and read-only timing/coverage queries are allowed when they prove the
  current task.
- Do not call destructive, implementation-changing, database-mutating,
  synthesis/place/route/signoff execution, or artifact-editing tools unless the
  user explicitly asks and the active flow supports that phase.
- Do not hard-code vendor EDA tool availability.
- Do not treat parse success as design correctness.

Initial optional tool references:

- `pyslang-mcp` for compiler-backed SystemVerilog context.
- future `upf-mcp` for UPF and power-intent evidence.

## Hardware Claim Discipline

Add this principle to ASIC-specific skills and completion checks:

| Claim | Minimum Evidence |
| --- | --- |
| RTL compiles | Fresh compiler/frontend command and zero errors |
| Lint clean | Lint command or deterministic lint report, plus scope |
| Simulation/regression passes | Fresh simulation or regression command, seed/test scope, and zero unexpected failures |
| Scoreboard mismatch fixed | Original failing test/seed reproduced, fix applied, same test/seed passes, regression scope stated |
| Assertion status known | Formal/simulation assertion report, pass/fail/vacuity status, and scope |
| Coverage improved or closed | Coverage report before/after, mapped objective, exclusions/waivers stated |
| CDC clean | CDC-specific analysis over the relevant clock domains |
| RDC clean | RDC-specific analysis over the relevant reset domains |
| Structural timing risk reduced | Source/report-backed structural change, affected paths, and unchanged behavior evidence |
| STA timing improved | Fresh STA/synthesis timing report with mode/corner/path group, WNS/TNS/path evidence, and scope |
| Constraint change validated | SDC/MMMC diff plus syntax/tool check or timing/report evidence over affected modes/corners |
| Congestion improved | Backend report or visualization evidence before/after, region/scope, and tradeoffs stated |
| DRC/LVS/antenna clean | Relevant signoff tool report for the stated block/version/scope |
| ECO equivalence preserved | Equivalence or formal check report, ECO scope, and unresolved exceptions |
| DV plan complete | Objective traceability, tests, assertions, coverage, unresolved list |
| Ready for handoff | Required artifacts exist, blocking issues are zero, limits are stated |
| Signoff clean | Only from the relevant signoff tool flow, never from the agent alone |

## Implementation Phases

### Phase 0: Baseline Import

Goal: create a working ASIC Superpowers plugin skeleton.

Tasks:

1. Copy upstream Superpowers content into this repo, excluding upstream `.git`
   and avoiding unrelated local changes.
2. Update plugin metadata and package names.
3. Rename or adapt bootstrap glue to load `using-asic-superpowers`.
4. Keep upstream core skills present so existing methodology still works.
5. Add a source provenance note for the upstream commit copied.

Acceptance:

- Skills are discoverable in at least the Codex plugin metadata shape.
- The plugin still has a session bootstrap path.
- No domain content has been mixed into upstream core files unnecessarily.

### Phase 1: Lean ASIC Engineering Methodology Layer

Goal: add just enough ASIC context to make the Superpowers workflow safe and
useful for RTL design, DV, and Physical Design / Backend work.

Tasks:

1. Add `hardware-evidence-first-development`.
2. Add compact reference files for the ASIC engineering contract, RTL design
   lens, DV verification lens, Physical Design lens, ASIC review checklist,
   hardware claim discipline, and optional tool evidence.
3. Tune `brainstorming` so vague RTL requests collect clocks/resets,
   interfaces, latency/throughput, PPA, physical-design constraints, and DV
   acceptance criteria before implementation.
4. Tune `brainstorming` so vague DV requests collect testbench scope, failing
   seed/test, UVM component, assertion, scoreboard/reference-model, coverage,
   and regression evidence before implementation.
5. Tune `brainstorming` so vague Physical Design requests collect flow stage,
   reports, SDC/MMMC context, mode/corner, path group, WNS/TNS, utilization,
   congestion, ECO limits, and signoff boundary before analysis or edits.
6. Tune `writing-plans` so ASIC tasks name role-appropriate evidence,
   commands/reports, filelists or artifact scope, and review gates.
7. Tune review prompts so RTL, DV, and Physical Design edits are checked against
   the relevant ASIC lens, not only local code style.

Acceptance:

- A vague RTL request produces focused intake questions instead of immediate
  code.
- A vague DV request asks for failing seed/test, assertion, scoreboard, coverage,
  or regression evidence before editing testbench or checker code.
- A vague Physical Design request asks for report provenance, mode/corner/path
  scope, constraints, and signoff boundaries before claiming analysis results or
  changing artifacts.
- A plan for ASIC work contains evidence gates, not only file edits.
- Review catches RTL timing/fanout/reset concerns, DV-observability gaps, and
  Physical Design constraint/report risks without invoking a separate
  domain-specific skill catalog.

### Phase 2: External Workflow Bridge

Goal: make deeper ASIC workflow repos discoverable without making them part of
the plugin's normal skill surface.

Tasks:

1. Add a short reference that points users to `asic-ai-workflows` for deeper
   block RTL planning, DV planning, CDC/RDC/timing reports, and structured YAML
   handoffs.
2. Add guidance that those workflows are optional escalation paths, not the
   default response to every ASIC coding, DV debug, or backend report request.
3. Add wording for when to recommend an external workflow: broad planning,
   handoff packaging, formal report generation, or multi-domain audits.

Acceptance:

- Ordinary ASIC engineering tasks stay in the lean Superpowers loop.
- The agent can still suggest deeper workflow tools when the user clearly asks
  for a report, handoff package, or specialist audit.
- The plugin does not duplicate the `asic-ai-workflows` catalog.

### Phase 3: Validation And Trigger Evals

Goal: protect skill behavior with deterministic checks first, then live agent
pressure tests.

Tasks:

1. Add frontmatter validation for every `SKILL.md`.
2. Add local markdown link validation.
3. Add trigger scenarios:
   - vague "write RTL" request with missing clock/reset/PPA/DV details
   - bug fix request against RTL with no reproducer
   - request to "clean up" RTL that risks changing cycle behavior
   - request to fix a UVM scoreboard mismatch with no failing seed or test
   - request to close a coverage hole without objective mapping
   - request to analyze a failing assertion without assertion report scope
   - request to optimize timing without timing evidence
   - request to review an SDC/MMMC change without affected mode/corner scope
   - request to explain congestion hotspots from backend reports
   - request to mark work done after only editing code
4. Add live agent transcript tests only after deterministic checks are stable.

Acceptance:

- CI can catch broken skill metadata and references.
- Trigger scenarios show the ASIC engineering methodology activates before
  implementation or unsupported claims.
- The plugin does not load many domain skills for ordinary ASIC engineering
  tasks.

### Phase 4: Documentation And Release

Goal: make the plugin usable without requiring users to know the sibling repos.

Tasks:

1. Write README with scope, install paths, examples, and limitations.
2. Document optional `pyslang-mcp` integration.
3. Document what the plugin cannot claim.
4. Add contribution rules based on upstream Superpowers and ASIC workflow
   quality standards.
5. Publish only after at least one harness works end to end.

Acceptance:

- A new user can install and ask for an RTL, DV, or Physical Design workflow.
- The docs distinguish ASIC Superpowers from `asic-ai-workflows`,
  `pyslang-mcp`, and `upf-mcp`.
- The plugin is honest that it is a methodology layer, not a replacement for
  specialized ASIC workflow repos or EDA tools.

## Trigger Design

Good skill descriptions are critical. They should describe when to use the skill
without summarizing the whole process.

Examples:

```yaml
name: using-asic-superpowers
description: Use when starting any session that may involve RTL, ASIC design,
  Design Verification, Physical Design / Backend, SystemVerilog, constraints,
  EDA tool output, or hardware verification evidence.
```

```yaml
name: hardware-evidence-first-development
description: Use before changing RTL, DV collateral, constraints, backend
  artifacts, HDL parsers, or hardware workflow fixtures when the task needs
  evidence before implementation.
```

```yaml
name: requesting-code-review
description: Keep upstream trigger, but the review prompt should load the ASIC
  review checklist when the diff touches HDL, constraints, DV collateral,
  backend artifacts, reports, or hardware workflow fixtures.
```

Avoid descriptions that say "does X then Y then Z"; agents may follow the
description and skip the body.

## Example User Flows

### New RTL Feature

User asks:

> Add a programmable threshold interrupt to this counter RTL.

Expected agent behavior:

1. Use `using-asic-superpowers`.
2. Use `brainstorming` with ASIC intake.
3. Clarify interrupt clear policy, reset value, latency, configurability,
   clock/reset assumptions, and DV acceptance evidence.
4. Write a plan with a verification-first step, RTL edits, compile/lint/sim
   commands, and review gates.
5. Implement small RTL changes and verify before claiming completion.

### Physical-Design-Aware RTL Cleanup

User asks:

> Clean up this datapath and reduce the critical path risk.

Expected agent behavior:

1. Ask what evidence shows the path is critical, such as STA, synthesis, lint, or
   structural review.
2. Identify candidate RTL changes such as pipeline boundaries, mux restructuring,
   fanout reduction, width trimming, or resource sharing changes.
3. Preserve cycle behavior unless the user explicitly approves a latency change.
4. Require verification evidence that behavior did not change unexpectedly.
5. State whether the result is structural risk reduction or real timing closure.

### DV-Aware RTL Change

User asks:

> Add backpressure support to this streaming block.

Expected agent behavior:

1. Clarify valid/ready semantics, data stability, stall latency, reset behavior,
   and error handling.
2. Define tests or assertions that prove no data is dropped, duplicated, or
   reordered.
3. Plan RTL edits with observability and scoreboard surface in mind.
4. Review the implementation for protocol stability and coverage hooks.
5. Verify the requested behavior before claiming completion.

### DV Scoreboard Debug

User asks:

> Fix this UVM scoreboard mismatch in the packet path.

Expected agent behavior:

1. Ask for the failing test, seed, scoreboard message, relevant waveform/log
   excerpt, and expected reference-model behavior.
2. Reproduce or inspect the failure before editing.
3. Identify whether the root cause is DUT behavior, monitor sampling,
   scoreboard matching, reference model, sequence stimulus, or reset/error
   handling.
4. Implement the smallest fix in the correct layer.
5. Run the targeted test/seed and state the regression scope that was or was not
   covered.

### Physical Design Timing Or Congestion Review

User asks:

> Reduce setup WNS on this block, especially the control path group.

Expected agent behavior:

1. Ask for report provenance: tool, run ID, netlist/design version, mode/corner,
   path group, constraints, and current WNS/TNS/path evidence.
2. Separate structural RTL-risk suggestions from real STA-backed timing
   improvement claims.
3. Identify candidate actions such as constraint review, pipeline boundary
   discussion, mux/fanout restructuring, placement/floorplan guidance, buffering,
   or ECO limits.
4. Preserve functional and cycle behavior unless latency or ECO scope is
   explicitly approved.
5. State whether the result is analysis, structural risk reduction, or verified
   STA/backend improvement.

### RTL Bug Fix

User asks:

> Fix this simulation failure in the FIFO.

Expected agent behavior:

1. Use systematic debugging first.
2. Reproduce the failure and identify the root cause before editing.
3. Add or name the regression evidence before the fix.
4. Implement the smallest RTL change that addresses the root cause.
5. Run the targeted regression and any relevant compile/lint checks.

## What Not To Do

Do not:

- Rewrite the Superpowers methodology from scratch.
- Collapse all ASIC behavior into one broad skill.
- Build an EDA runtime inside the plugin.
- Add mandatory dependencies on `pyslang-mcp`, `upf-mcp`, Verilator, commercial
  EDA tools, or simulator installations.
- Claim signoff, STA, CDC, RDC, formal, low-power, or synthesis cleanliness
  without the relevant tool evidence.
- Copy restricted standards text, proprietary examples, or vendor documentation
  into the repo.
- Add large generated datasets to the plugin.
- Make this plugin a portal, quiz engine, or documentation site.

## Risks And Mitigations

### Risk: Context Bloat

ASIC references can become large. Loading a full workflow catalog every turn
would degrade agent behavior.

Mitigation:

- Keep bootstrap tiny.
- Rely on skill descriptions for discovery.
- Put heavy references behind skill-local files.
- Keep specialist workflows as external references until a repeated task earns a
  dedicated plugin skill.

### Risk: Generic TDD Conflicts With Hardware Work

Strict software TDD can produce awkward behavior for ASIC work, especially when
the right first artifact is a spec, assertion plan, filelist, failing seed,
coverage report, timing report, constraint diff, or backend smoke fixture.

Mitigation:

- Keep generic TDD for software.
- Add `hardware-evidence-first-development`.
- Make hardware plans name the right evidence type for RTL, DV, and Physical
  Design tasks.

### Risk: False Signoff Confidence

Agents may overstate what static review proves.

Mitigation:

- Repeat scope limitations in ASIC references and completion checks.
- Add hardware claim discipline to completion checks.
- Require tool provenance when tool output is used.

### Risk: Skill Trigger Collisions

Generic Superpowers and ASIC Superpowers may both have relevant skills.

Mitigation:

- Use ASIC-specific names for new skills.
- Add clear priority rules in `using-asic-superpowers`.
- Pressure test common prompts.

### Risk: Upstream Drift

Forking Superpowers can make future upstream changes hard to merge.

Mitigation:

- Keep upstream-derived files close to upstream.
- Isolate ASIC additions in new skills and references.
- Record upstream commit provenance.
- Periodically diff against upstream release tags.

### Risk: Tool Availability Differences

Hardware engineers will have different local toolchains.

Mitigation:

- Make tools optional.
- Prefer read-only evidence.
- Ask for filelists and reports when tools are unavailable.
- Emit unresolved items instead of failing silently.

## Near-Term Definition Of Done

The first useful version is currently done when:

- [x] The plugin metadata identifies ASIC Superpowers.
- [x] The session bootstrap loads ASIC-aware skill guidance.
- [x] Core Superpowers workflow skills still work.
- [x] The lean hardware evidence-first skill is discoverable.
- [x] The ASIC engineering contract, RTL design lens, DV verification lens, Physical
  Design lens, review checklist, and claim-discipline references are available
  to the core workflow skills.
- [x] A vague RTL request has a deterministic trigger scenario for intake
  questions instead of immediate code.
- [x] A physical-design-aware RTL request preserves cycle behavior unless latency
  change is explicitly approved.
- [x] A DV-aware RTL request names observability, assertions, tests, or scoreboard
  evidence before implementation.
- [x] A DV debug request asks for failing test/seed, scoreboard/assertion evidence,
  and regression scope before editing.
- [x] A Physical Design request asks for report provenance, mode/corner/path scope,
  constraints, and signoff boundary before claiming results.
- [x] A vendor-neutral EDA toolchain request asks for toolchain context instead
  of assuming a specific vendor or report dialect.
- [x] Deterministic validation scripts pass locally.
- [x] README explains scope, install, examples, optional MCPs, EDA toolchain
  awareness, and limitations.
- [ ] Live harness transcript evals prove the behavior end-to-end.

## Future Plan

Next work after this baseline:

1. Run clean harness transcript evals for RTL, DV, Physical Design, and
   vendor-neutral EDA toolchain discovery prompts.
2. Store sanitized transcript summaries under `evals/` and link them from the
   validation plan.
3. Add a small command/report discovery checklist to live eval prompts for common
   repo structures: Makefiles, CI, filelists, run directories, waiver files,
   report headers, and environment setup scripts.
4. Add no vendor-specific rule packs until real usage shows a repeated need;
   keep vendor adapters external or optional.
5. Periodically diff against upstream Superpowers and port only process fixes
   that preserve ASIC behavior.
6. Consider later focused skills only with evidence: simulation failure triage,
   coverage closure review, waiver review, constraint-aware review, and backend
   report review.

## Recommended First Commit Sequence

1. Copy upstream Superpowers baseline and update metadata.
2. Add `using-asic-superpowers` bootstrap changes.
3. Add `hardware-evidence-first-development`.
4. Add the ASIC engineering contract, RTL design lens, DV verification lens,
   Physical Design lens, ASIC review checklist, hardware claim discipline, and
   tool-evidence references.
5. Tune brainstorming, planning, review, debugging, and completion wording.
6. Add validation scripts and trigger scenarios.
7. Add README and examples.

Keep each commit reviewable. The first implementation should make the plugin
usable for RTL, DV, and Physical Design work before attempting low-power, DFT,
SDC, or protocol-specific expansions.
