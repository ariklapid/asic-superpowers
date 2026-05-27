# Tool Evidence

Use this reference when consuming EDA reports, MCP output, simulator logs, or generated fixtures.

Pair this with `eda-toolchain-profile.md` when commands, report dialects, filelists, waivers, modes/corners, or flow stages matter.

## Required Provenance

- Tool or report name when visible.
- EDA stage and toolchain context when visible.
- Command if freshly run.
- File path and timestamp when available.
- Design/block/hierarchy scope.
- Mode, corner, path group, seed, test, or regression scope when relevant.
- Known limitations: truncated report, stale run, missing filelist, unavailable tool, generated fixture, or source-only review.

## Evidence Boundaries

- Parser diagnostics prove parser status only.
- Tool-specific diagnostics prove only the configured checks for that toolchain stage.
- Lint reports prove only the configured lint scope.
- Simulation proves only the tests/seeds run.
- Formal proves only the properties and bounds/configuration used.
- STA proves only the design, constraints, modes/corners, and analysis type in scope.
- CDC/RDC reports prove only the configured domain analysis.
- DRC/LVS/antenna/IR/EM reports prove only the stated signoff checks and versions.

## Handling Missing Tools

Prefer project-local commands, plain files, and reports. Optional MCPs and EDA tools may improve evidence, but the skill must still work without them.

Do not invent a simulator, linter, synthesizer, STA tool, CDC tool, regression launcher, waiver format, library setup, or report syntax. Ask for the user's toolchain context when it is needed.

When a tool is missing, write:

- `Evidence available: ...`
- `Evidence unavailable: ...`
- `Supported claim: ...`
- `Unsupported claim: ...`
- `Toolchain context: ...`
