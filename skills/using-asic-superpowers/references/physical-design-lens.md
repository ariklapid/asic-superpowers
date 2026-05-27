# Physical Design / Backend Lens

Use for timing, constraints, congestion, utilization, power, ECO, and backend report review.

## Check

- Report provenance: tool, run ID, design version, mode, corner, path group, report date when available.
- Toolchain stage: synthesis, STA, floorplan, place, CTS, route, ECO, power, or signoff. Do not assume a stage from filename alone.
- Timing claims include WNS/TNS/path evidence and distinguish setup, hold, recovery/removal, or pulse width.
- Constraint changes identify affected clocks, generated clocks, IO delays, false paths, multicycle paths, and modes/corners.
- Congestion/utilization claims cite region, utilization, overflow, placement/floorplan context, or report/heatmap evidence.
- ECO suggestions preserve functional behavior and name equivalence/signoff evidence when available.
- Power/IR/EM claims cite the relevant report scope and activity assumptions.
- DRC/LVS/antenna claims cite the relevant signoff report.

## Do Not Claim

- Timing closure from source review alone.
- Constraint validity from syntax alone.
- Congestion improvement without before/after backend evidence.
- Signoff cleanliness without the relevant signoff run.
- Vendor-specific behavior unless the user's toolchain or report states it.
