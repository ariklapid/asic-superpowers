# EDA Toolchain Profile

Use this reference when a task depends on commands, reports, filelists,
constraints, waivers, regressions, generated collateral, or backend flow stages.

The goal is toolchain awareness, not vendor lock-in. Do not assume a specific
EDA vendor, command syntax, report format, or signoff recipe.

## Discover

Look for project-local evidence:

- README, docs, runbooks, CI jobs, containers, modules, setup scripts.
- Makefiles, shell/Tcl/Python launchers, regression scripts.
- Filelists, include directories, package maps, library maps.
- Constraints, MMMC setup, modes/corners, waiver files, UPF/CPF when present.
- Report directories and naming conventions.
- Tool logs showing version, command, run directory, design, hierarchy, seed, mode, corner, or stage.

## Capture

When relevant, record:

- lane: RTL, DV, Physical Design / Backend, signoff, docs, fixture
- stage: compile, lint, sim, formal, CDC, RDC, synthesis, STA, floorplan, place, CTS, route, ECO, power, DRC, LVS, antenna, IR/EM
- command or report path
- tool name/version only if visible
- design/block/hierarchy
- filelist/source set
- constraints/mode/corner/path group
- test/seed/regression target
- waiver/exclusion policy
- run directory and timestamp if visible
- unavailable context

## Use

- Prefer the project's own commands over invented commands.
- If multiple toolchains exist, ask which one is authoritative for the current task.
- If only reports are available, review reports and state that commands were not run.
- If a report dialect is unknown, infer conservatively from visible fields only.
- If a command could mutate design databases, implementation state, generated collateral, or signoff outputs, ask before running it.

## Report Shape

Use this compact form in responses:

```text
Toolchain context:
- Stage:
- Command/report:
- Scope:
- Mode/corner/seed:
- Known limitations:
```
