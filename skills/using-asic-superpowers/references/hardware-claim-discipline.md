# Hardware Claim Discipline

| Claim | Minimum Evidence |
| --- | --- |
| RTL compiles | Fresh compiler/frontend command and zero errors |
| Lint clean | Lint command or deterministic lint report, plus scope |
| Simulation/regression passes | Fresh simulation or regression command, seed/test scope, and zero unexpected failures |
| Scoreboard mismatch fixed | Original failing test/seed reproduced, fix applied, same test/seed passes, regression scope stated |
| Assertion status known | Formal/simulation assertion report, pass/fail/vacuity status, and scope |
| Coverage improved or closed | Coverage report before/after, mapped objective, exclusions/waivers stated |
| CDC clean | CDC-specific analysis over the relevant clock domains |
| RDC clean | RDC-specific analysis over the relevant reset domains |
| Structural timing risk reduced | Source/report-backed structural change, affected paths, and unchanged behavior evidence |
| STA timing improved | Fresh STA/synthesis timing report with mode/corner/path group, WNS/TNS/path evidence, and scope |
| Constraint change validated | SDC/MMMC diff plus syntax/tool check or timing/report evidence over affected modes/corners |
| Congestion improved | Backend report or visualization evidence before/after, region/scope, and tradeoffs stated |
| DRC/LVS/antenna clean | Relevant signoff tool report for the stated block/version/scope |
| ECO equivalence preserved | Equivalence or formal check report, ECO scope, and unresolved exceptions |
| Ready for handoff | Required artifacts exist, blocking issues are zero, limits are stated |
| Signoff clean | Only from the relevant signoff tool flow, never from the agent alone |

If minimum evidence is unavailable, state the gap and downgrade the claim.
