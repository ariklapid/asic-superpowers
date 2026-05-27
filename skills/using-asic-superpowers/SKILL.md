---
name: using-asic-superpowers
description: Use when starting any session that may involve RTL, ASIC design, Design Verification, Physical Design / Backend, SystemVerilog, constraints, EDA tool output, or hardware verification evidence.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## Instruction Priority

ASIC Superpowers skills override default agent habits, but user instructions always take precedence:

1. User's explicit instructions
2. ASIC Superpowers skills
3. Default system behavior

If generic Superpowers and ASIC Superpowers both apply, use ASIC Superpowers for hardware tasks and generic Superpowers for non-hardware software tasks.

## Hardware Claim Discipline

For ASIC work, evidence comes before implementation and before claims.

- Do not infer microarchitecture, protocol, timing, reset, power intent, or signoff status from naming alone.
- Do not claim synthesis, STA, CDC, RDC, formal, low-power, DRC, LVS, antenna, ECO, or signoff cleanliness from agent reasoning alone.
- Treat parse success as parse evidence only.
- Use unresolved items when source, report, or user intent is missing.
- Be aware of the user's EDA toolchain: identify the configured simulator, lint, synthesis, formal, CDC/RDC, STA, power, physical implementation, and signoff/report flow when that context exists.
- Record evidence scope: tool/report name, command when available, file paths, mode/corner, seed/test, hierarchy, toolchain stage, and limitations.
- Stay vendor-neutral. Do not assume any specific EDA vendor, command syntax, report format, waiver format, library format, or signoff flow unless the repo or user provides it.

## How To Access Skills

Use the skill-loading mechanism provided by the active harness. Platform mappings live in:

- `references/codex-tools.md`
- `references/gemini-tools.md`
- `references/copilot-tools.md`

## The Rule

Invoke relevant or requested skills BEFORE any response or action. Even a 1% chance a skill might apply means you should invoke it to check.

For ASIC prompts:

- New feature, block change, testbench change, constraint change, or backend artifact change: use `brainstorming` first unless the user provided an approved spec.
- Bug, failing simulation, failing assertion, regression mismatch, lint issue, CDC/RDC finding, timing violation, or unexpected report result: use `systematic-debugging` first.
- Before changing RTL, DV collateral, constraints, reports, or backend flow artifacts: use `hardware-evidence-first-development`.
- Before claiming completion or correctness: use `verification-before-completion`.
- Before review or merge: use `requesting-code-review` with the ASIC review checklist.

## ASIC Reference Lenses

Load these references only when they match the task:

- `references/asic-engineering-contract.md` for initial intake and design-contract gaps.
- `references/rtl-design-lens.md` for RTL implementation and review.
- `references/dv-verification-lens.md` for UVM, assertions, coverage, scoreboards, and regression debug.
- `references/physical-design-lens.md` for timing, constraints, congestion, ECO, reports, and signoff boundaries.
- `references/asic-review-checklist.md` for code/review prompts.
- `references/hardware-claim-discipline.md` before making hardware claims.
- `references/tool-evidence.md` when consuming tool, MCP, or report output.
- `references/eda-toolchain-profile.md` when a task depends on commands, reports, filelists, constraints, waivers, regressions, or backend flow stages.

## Red Flags

STOP if you catch yourself thinking:

| Thought | Reality |
| --- | --- |
| "This is just RTL cleanup" | Cycle behavior, reset behavior, and timing assumptions can change. Use the workflow. |
| "The report says it is clean" | Record report provenance and scope before claiming anything. |
| "This report format is obvious" | First identify the user's toolchain stage and report dialect. |
| "The signal is named sync" | Names are hints, not proof of CDC/RDC safety. |
| "Compile passed" | Compile is not functional, timing, CDC, lint, or signoff closure. |
| "The DV failure is probably the scoreboard" | Reproduce and isolate root cause first. |
| "This timing fix is obvious" | Preserve behavior and distinguish structural risk reduction from STA improvement. |
| "Everyone uses the same EDA flow" | ASIC projects vary by vendor, version, scripts, corners, waivers, and signoff rules. |

## Skill Priority

1. Process skills first: `brainstorming`, `systematic-debugging`, `hardware-evidence-first-development`.
2. Planning and execution skills next: `writing-plans`, `subagent-driven-development`, `executing-plans`.
3. Review and completion skills last: `requesting-code-review`, `receiving-code-review`, `verification-before-completion`, `finishing-a-development-branch`.

## External Workflows

`asic-ai-workflows`, HDL MCPs, UPF MCPs, and EDA tools are escalation paths, not default requirements. Suggest them when the user asks for deeper reports, handoff packages, specialist audits, or tool-backed evidence. The plugin must still work from plain files and provided reports.

## Vendor-Neutral EDA Toolchain Awareness

Before running or interpreting EDA commands, inspect the project for toolchain clues such as Makefiles, scripts, filelists, regression targets, constraints, waiver files, report directories, CI jobs, containers, modules, env setup scripts, and documentation.

If the toolchain is unclear, ask for the command or report provenance instead of guessing. If a report is supplied, infer only the tool stage and report type that the report itself supports.
