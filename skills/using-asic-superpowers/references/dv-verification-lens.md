# DV Verification Lens

Use for UVM, assertions, functional coverage, scoreboards, monitors, reference models, and regression debug.

## Check

- Objective IDs map to tests, assertions, coverage, or review checks.
- Failing behavior is reproducible by test/seed or represented by a concrete log/waveform/report.
- Monitors sample at protocol-valid points and handle reset/error cases.
- Scoreboards compare the right abstraction level and preserve ordering assumptions.
- Reference models encode intended behavior, not current DUT behavior by accident.
- Assertions have clear clocks, reset disable conditions, antecedents, and non-vacuity considerations.
- Coverage bins map to real verification intent and avoid meaningless toggle-style closure.
- Regression scope is stated: targeted test, smoke, block regression, nightly, or unavailable.

## Do Not Claim

- Coverage closure without report evidence and exclusions/waivers.
- Assertion proof without formal/simulation assertion evidence.
- Bug fixed without the original failing test/seed or equivalent reproduction passing.
- DUT correctness when only the testbench was changed.
