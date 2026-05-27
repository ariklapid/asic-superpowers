# ASIC Superpowers For OpenCode

This plugin uses OpenCode's native plugin system to register ASIC Superpowers
skills and inject the `using-asic-superpowers` bootstrap at session start.

## Current Status

Status as of 2026-05-23:

- The OpenCode plugin file is `.opencode/plugins/asic-superpowers.js`.
- The plugin injects `using-asic-superpowers`, not upstream `using-superpowers`.
- `node -c .opencode/plugins/asic-superpowers.js` passes locally.
- Deterministic metadata, link, trigger, and fixture validation passes via
  `scripts/validate.sh` or `npm run validate`.
- A clean OpenCode live transcript still needs to be captured before release.

## Local Development Install

Add this checkout to the `plugin` array in `opencode.json`:

```json
{
  "plugin": ["/path/to/asic-superpowers"]
}
```

Restart OpenCode, then verify:

```text
Tell me about your ASIC Superpowers
```

## Published Install

After the repo is published:

```json
{
  "plugin": ["asic-superpowers@git+https://github.com/ariklapid/asic-superpowers.git"]
}
```

## Skill Usage

```text
use skill tool to list skills
use skill tool to load using-asic-superpowers
use skill tool to load hardware-evidence-first-development
```

The ASIC bootstrap should trigger methodology guidance for RTL, DV, Physical
Design / Backend, constraints, reports, SystemVerilog, and EDA evidence tasks.

## How It Works

The OpenCode plugin:

1. Adds this repo's `skills/` directory to OpenCode skill discovery.
2. Injects `using-asic-superpowers` into the first user message of each session.
3. Provides tool-name mapping guidance for non-Claude harnesses.

## Validation

Run from the repo root:

```bash
scripts/validate.sh
node -c .opencode/plugins/asic-superpowers.js
```

`node` is only required for the OpenCode plugin syntax/cache tests. The
deterministic repository validation itself uses Python 3.7+.

See `docs/ASIC_PLUGIN_VALIDATION_PLAN.md` for the full RTL/DV/Physical Design
validation flow.

## Future Plan

- Run the RTL, DV, Physical Design, and EDA toolchain-discovery prompts in a
  clean OpenCode session.
- Confirm the bootstrap loads before implementation.
- Save a sanitized transcript summary under `evals/` once available.
