# RTL Design Lens

Use for SystemVerilog/Verilog implementation and review.

## Check

- Requirements and objectives map to visible RTL behavior.
- Combinational blocks assign every driven output on every path.
- Sequential blocks have one clear clock and reset policy.
- Signals have a single procedural driver unless intentionally resolved by structure.
- Widths, signedness, casts, truncation, and extension are explicit.
- Ready/valid or other protocols preserve data stability, ordering, and backpressure.
- Reset behavior is consistent with the contract and testbench expectations.
- CDC/RDC assumptions are explicit; naming alone does not prove safety.
- Timing-risk structures are visible: deep muxes, priority chains, large compares, arithmetic, fanout, resource sharing.
- Power/area tradeoffs are separated from performance claims.

## Do Not Claim

- Synthesis cleanliness without synthesis/lint evidence.
- CDC/RDC cleanliness without domain-specific evidence.
- Timing closure without STA or synthesis timing evidence.
- Functional correctness from compile success.
