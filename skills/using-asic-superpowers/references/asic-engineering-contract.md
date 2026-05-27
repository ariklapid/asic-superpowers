# ASIC Engineering Contract

Use this contract during intake, planning, and review. Do not ask every question at once; select the lane-relevant gaps.

## Common Intake

- Intent: what problem the change or analysis should solve.
- Scope: block, hierarchy, testbench, constraint file, report set, or backend stage.
- Artifacts: RTL/DV files, filelists, packages, interfaces, constraints, reports, logs, waveforms.
- Evidence: commands run, report provenance, failing seed/test, mode/corner, tool version when available.
- Toolchain: simulator/lint/synthesis/formal/CDC/RDC/STA/PD/signoff commands, report dialects, waiver policy, and flow stage when relevant.
- Claims: what the user wants proven, and what cannot be proven from available evidence.
- Unresolved assumptions: protocol, reset, timing, power, DFT, low-power, clocking, ECO, or signoff gaps.

## RTL Lane

- Clocks, resets, reset polarity, release assumptions.
- Interfaces, protocols, ready/valid stability, ordering, backpressure.
- Latency, throughput, configuration, status, error handling.
- PPA target: performance, power, area, with tradeoffs separated.
- Microarchitecture assumptions and cycle behavior.
- Compile/lint/sim/formal evidence available or missing.
- Project filelists, include paths, compile/elab target, and waiver policy.

## DV Lane

- Verification objective and traceability ID.
- Failing test, seed, waveform/log, assertion, or coverage hole.
- UVM component scope: sequence, driver, monitor, agent, scoreboard, reference model.
- Expected vs observed behavior.
- Regression command and pass/fail scope.
- Simulator/regression launcher, seed syntax, waveform and coverage database format when visible.
- Coverage bins, assertions, exclusions, and waivers.

## Physical Design / Backend Lane

- Flow stage: synthesis, floorplan, place, CTS, route, signoff, ECO.
- Design version, netlist/DEF, library, SDC/MMMC context.
- Mode/corner/path group and report provenance.
- Toolchain stage, run directory, database/netlist/DEF, library setup, and report command when visible.
- WNS/TNS, startpoint/endpoint, fanout, congestion, utilization, power, IR/EM.
- Floorplan constraints, blockages, clock/reset tree assumptions.
- ECO boundary and signoff boundary.
