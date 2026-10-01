# Per-Case Non-Subsumption Inventory

> Superseded as an ROI decision on 2026-07-29. This inventory established
> that each original method named a distinct failure mode; it did **not** assess
> each test's expected value against its maintenance and execution cost. The
> authoritative cost/value reassessment is in
> [`../90-test-topology-convergence/roi-reassessment.md`](../90-test-topology-convergence/roi-reassessment.md).

## Decision Unit

The unit is one original `unittest` test method, not one eventual pytest item.
When a `subTest` loop becomes parametrised, its source method remains one
ledger decision and each former parameter row remains executable evidence.

## Historical Result

| Domain | Original methods | Retain and migrate | Merge | Delete |
| --- | ---: | ---: | ---: | ---: |
| Core, framework, build, and workflow | 70 | 70 | 0 | 0 |
| Telemetry | 95 | 95 | 0 | 0 |
| TUI, installed-wheel harness, and release | 43 | 43 | 0 | 0 |
| **Total** | **208** | **208** | **0** | **0** |

Each method named a behavioral, security, authority, transaction, packaging,
race, or public-interface failure mode not fully subsumed by a stronger
retained test. That finding is only an incremental-detection inventory; it is
not a claim that all 208 methods justify their total cost.

## Evidence Files

- Core ledger: [`roi-core.md`](roi-core.md)
- Telemetry ledger: [`roi-telemetry.md`](roi-telemetry.md)
- Boundary ledger: [`roi-boundaries.md`](roi-boundaries.md)

## Historical Deletion Rule

A case was previously considered removable only when a retained test subsumed
its entire named failure mode. The later ROI reassessment adds defect impact,
likelihood, static/operational alternatives, fixture cost, flakiness, and
cognitive maintenance cost.
