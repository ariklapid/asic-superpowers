# Installing ASIC Superpowers for OpenCode

## Current Status

Status as of 2026-05-23:

- OpenCode loads `.opencode/plugins/asic-superpowers.js`.
- The plugin injects `using-asic-superpowers` at session start.
- Local syntax and deterministic validation pass.
- A clean OpenCode transcript still needs to be captured before release.

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## Installation

For local development from this checkout, point OpenCode at the package path:

```json
{
  "plugin": ["/path/to/asic-superpowers"]
}
```

For a published repo, use the git package form:

```json
{
  "plugin": ["asic-superpowers@git+https://github.com/ariklapid/asic-superpowers.git"]
}
```

Restart OpenCode. The plugin registers the local `skills/` directory and injects
the `using-asic-superpowers` bootstrap.

Verify by asking:

```text
Tell me about your ASIC Superpowers
```

## Usage

Use OpenCode's native `skill` tool:

```text
use skill tool to list skills
use skill tool to load using-asic-superpowers
use skill tool to load hardware-evidence-first-development
```

## Tool Mapping

When skills reference Claude Code tools:

- `TodoWrite` maps to `todowrite`
- `Task` with subagents maps to OpenCode subagents / `@mention`
- `Skill` maps to OpenCode's native `skill` tool
- file operations map to native OpenCode tools

## Troubleshooting

1. Check logs: `opencode run --print-logs "hello" 2>&1 | grep -i "asic\\|superpowers"`
2. Verify the plugin line in `opencode.json`
3. Restart OpenCode after plugin or skill changes
4. Run `scripts/validate.sh` from this repo

## Future Plan

- Run the RTL, DV, Physical Design, and EDA toolchain-discovery prompts in a
  clean OpenCode session.
- Save sanitized transcript summaries under `evals/` once available.
