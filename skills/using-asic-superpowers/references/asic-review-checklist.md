# ASIC Review Checklist

Use this checklist when reviewing diffs or handoff artifacts touching RTL, DV, constraints, reports, or backend collateral.

## Findings Must Include

- File and line when source is available.
- The artifact/report scope when reviewing logs or reports.
- The user's EDA toolchain stage, command/report path, and visible tool/version context when available.
- Why the issue matters for correctness, verification, timing, constraints, or signoff boundary.
- The narrowest supported claim and any unsupported stronger claim.

## RTL

- Requirement/objective traceability.
- Complete assignment, single-driver discipline, reset consistency.
- Width, signedness, truncation, X semantics.
- Protocol stability, backpressure, ordering, reset/error behavior.
- CDC/RDC assumptions and timing-risk structures.

## DV

- Failing seed/test or objective coverage.
- Monitor/driver/sequence/scoreboard/reference-model correctness.
- Assertion clock/reset/vacuity behavior.
- Coverage intent, exclusions, waivers, regression scope.

## Physical Design / Backend

- Report provenance and affected mode/corner/path group.
- Toolchain stage and report dialect are identified without assuming a vendor.
- Constraint intent and affected clocks/exceptions.
- Timing, congestion, utilization, power, ECO, and signoff boundaries.
- Distinction between review-only findings and tool-proven closure.
