# Fixture Provenance

These fixtures exist to evaluate ASIC Superpowers trigger behavior, evidence
discipline, and review prompts. They are not signoff collateral.

## Current Status

Status as of 2026-05-23:

- Fixture provenance is complete for the current deterministic eval corpus.
- Third-party fixture files have source URLs and local license files.
- The generated timing report is explicitly labeled synthetic.
- The corpus supports eight deterministic trigger scenarios, including
  vendor-neutral EDA toolchain discovery, generic tooling, and mixed tooling
  plus hardware-report interpretation.
- No fixture should be treated as design signoff evidence.

## Local Fixtures

- `asic-ai-workflows/*`
  - Source: local checkout of `asic-ai-workflows`
  - Commit: `b8e67e620f7ccb7374fc011c199889017c5ea2e8`
  - License: MIT, copied to `third_party/licenses/asic-ai-workflows-MIT-LICENSE`
  - Purpose: compact RTL, DV, CDC, timing-risk, and JSON report fixtures.

## Third-Party Fixtures

- `third_party/sdc/siliconcompiler_gcd.sdc`
  - Source: https://github.com/siliconcompiler/siliconcompiler/blob/ba5de5a30e3b7b343ab18b6caa8ef4a2ad86b104/examples/gcd/gcd.sdc
  - License: Apache-2.0, copied to `third_party/licenses/siliconcompiler-Apache-2.0-LICENSE`
  - Purpose: compact SDC fixture.

- `third_party/sdc/efabless_caravel_caravan.sdc`
  - Source: https://github.com/efabless/caravel/blob/27cbe49c90ba5362ad52c9968dd98e035c30c74f/signoff/caravan/openlane-signoff/caravan.sdc
  - License: Apache-2.0, copied to `third_party/licenses/efabless-caravel-Apache-2.0-LICENSE`
  - Purpose: open ASIC harness SDC fixture.

- `third_party/reports/openhw_cva6_spyglass_reference_summary.rpt`
  - Source: https://github.com/openhwgroup/cva6/blob/9c2cf60a83a0a6a7fc5dcd973a5a5f6c0f42cb75/spyglass/reference_summary.rpt
  - License: Solderpad Hardware License 0.51, copied to `third_party/licenses/openhw-cva6-Solderpad-0.51-LICENSE`
  - Purpose: real lint/report-summary fixture with warning/error counts and waivers.

- `third_party/reports/rtl_poweroptimization_c432_postsyn_power.rpt`
  - Source: https://github.com/gabrielganzer/RTL-PowerOptimization/blob/7bca532e68eca69ac2a9c1d1689caf115b45e335/synthesis/c432/c432_postsyn_power.rpt
  - License: BSD-3-Clause, copied to `third_party/licenses/RTL-PowerOptimization-BSD-3-Clause-LICENSE`
  - Purpose: compact real post-synthesis power report fixture.

- `third_party/reports/pyrpl_post_place_timing_summary.rpt`
  - Source: https://github.com/pyrpl-fpga/pyrpl/blob/81beee5cf5e3651e66b5dec5103a355fca07fa30/pyrpl/fpga/out/post_place_timing_summary.rpt
  - License: MIT project license copied to `third_party/licenses/pyrpl-MIT-LICENSE`
  - Purpose: real timing summary fixture. This is FPGA/Vivado output, so it must not be used as ASIC signoff evidence.

- `third_party/sv/opentitan_pins_if.sv`
  - Source: https://github.com/lowRISC/opentitan/blob/21f062eb67c8749fec263739cd0f1eea14560a15/hw/dv/sv/common_ifs/pins_if.sv
  - License: Apache-2.0, copied to `third_party/licenses/opentitan-Apache-2.0-LICENSE`
  - Purpose: compact SystemVerilog DV interface example.

## Generated Fixtures

- `generated/report_timing.rpt`
  - Source: hand-authored synthetic fixture for deterministic evals.
  - Purpose: small STA-style path report with WNS/TNS/path group fields.
  - Limitation: not real tool output; do not use as evidence for any design.

## Future Fixture Plan

- Add only small, permissively licensed fixtures with source URLs and license
  files.
- Prefer fixtures that exercise a missing behavior in the validation plan.
- Add live transcript summaries separately from raw proprietary user reports.
- Do not add vendor-specific examples unless they are needed for a
  vendor-neutral behavior test and clearly labeled as one dialect among many.
