# Case Card: `DIAG-D`

## Boundary and Provenance

- **Case scope**: One selected medium-length live operational-traffic diagnosis,
  mitigation, false-positive recovery, and observation handoff thread.
- **Packet relation**: No resolved packet attachment. A separate control packet
  is visible in permitted interaction, but attachment absence does not establish
  non-use or non-existence.
- **Known selection/context limits**: Remote metrics and services are
  observable only over the captured window; source attribution is limited by
  network topology; long-horizon effect remains outside the trace.
- **Outcome confidence**: Several live probes and bounded service changes have
  external/local evidence. An automated isolation strategy is later retracted
  after a false positive; final immediate mitigation is observed but its
  long-term effect is unknown.

## Trajectory

| Episode | Boundary rationale | Control-loop summary | Outcome evidence status | Outcome / uncertainty | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| `D1` | A read-only anomaly report becomes a multi-layer live diagnosis | Human authorizes observation only; Agent separates periodic traffic, legitimate fixed paths, and likely unwanted traffic through metrics/log/connection evidence | observed execution (remote diagnostics); externally evidenced (live boundary) | Candidate attribution is strong but identity linkage remains incomplete | `DIAG-D · D1 · lines 6–376 · dialogue/tool-completion/remote-observation` |
| `D2` | Human corrects an attribution assumption and establishes safe scope | Agent creates a separate packet/phase plan, preserves unrelated changes, and adopts trustworthy attribution as a long-term goal | interaction-evidenced (scope decision); locally evidenced (packet checks) | Control state converges; no runtime mitigation yet | `DIAG-D · D2 · lines 377–526 · dialogue/patch-completion/task-complete` |
| `D3` | Explicit start permits a narrow, evidence-led configuration change | Agent removes an unsafe exposure but treats a controlled provenance signal as insufficient for trust | locally evidenced (configuration checks); externally evidenced (live probe) | Bounded phases converge; authoritative source visibility remains blocked | `DIAG-D · D3 · lines 527–855 · dialogue/patch-completion/remote-observation/task-complete` |
| `D4` | A temporary low-collateral mitigation is authorized | Agent tests a narrow control, detects a first ineffective formulation, then adjusts it while checking important paths | locally evidenced (configuration checks); externally evidenced (live behavior) | Temporary mitigation converges; root attribution is not solved | `DIAG-D · D4 · lines 856–1088 · dialogue/patch-completion/remote-observation/task-complete` |
| `D5` | Follow-up observation distinguishes immediate control from long-term cause | Agent relates repeated live evidence to control limits and declines to introduce an unsupported automated response | locally evidenced (configuration checks); externally evidenced (live observation) | Diagnosis converges for current limits; long-term enforcement remains a hypothesis | `DIAG-D · D5 · lines 1089–1376 · dialogue/remote-observation/web-search/task-complete` |
| `D6` | A delayed authorization introduces a time-bounded automated control | Agent builds an idempotent, recoverable guard with cleanup and live checks | locally evidenced (deployment mechanics); externally evidenced (immediate live checks); unknown (safety/effectiveness after later counterevidence) | The work state is later superseded: deployment/recovery mechanics are evidenced, but enforcement safety/effectiveness is invalidated by a false-positive incident | `DIAG-D · D6 · lines 1377–2672 · dialogue/coordination/patch-completion/remote-observation/task-complete` |
| `D7` | A real-user impact triggers immediate attribution review and rollback | Human reports harm; Agent determines the available attribution is insufficient for this control, disables the guard, restores affected behavior, and leaves observe-only state | locally evidenced (rollback checks); externally evidenced (live recovery); interaction-evidenced (stop/recovery authorization) | Recovery converges; the episode is a counterexample to source-level enforcement under weak attribution | `DIAG-D · D7 · lines 2673–3614 · dialogue/coordination/patch-completion/remote-observation/task-complete` |
| `D8` | A final localized mitigation is authorized under preserved boundaries | Agent uses fresh live correlation to make a scoped change, validates service/behavior, and records long-horizon follow-up as open | locally evidenced (configuration checks); externally evidenced (immediate live effect); unknown (long-term effect) | Immediate effect is observed; longer-term result and residual edge cases are unknown | `DIAG-D · D8 · lines 3615–4578 · dialogue/patch-completion/remote-observation/task-complete` |

## Observable Coordination

| Dimension | Observed mechanism | Boundary or alternative explanation | Evidence pointer |
| --- | --- | --- | --- |
| Intent and authority | Human starts read-only, corrects attribution, authorizes phased changes, and uses observed harm as a stop/recovery signal | The detailed operator knowledge and live access may be unavailable in ordinary projects | `DIAG-D · D1/D2/D4/D7/D8 · dialogue` |
| Shared state | Packet phases, metrics/log evidence, configuration, guard state, runbook, and observation windows externalize the decision context | No single exported artifact proves all external state was current or complete | `DIAG-D · D2/D3/D6/D8 · patch/remote-observation` |
| Coordination | Read-only → apply → idempotence/recovery checks → observe-only fallback constrains dangerous runtime control | The domain-specific control thresholds and identity semantics cannot be standardized by SVC | `DIAG-D · D3/D6/D7 · coordination/patch/remote-observation` |
| Observability | Live checks distinguish immediate mitigation, trusted attribution, and long-horizon effectiveness | A live metric can still be correlated rather than causal; missing provenance limits enforcement authority | `DIAG-D · D1/D4/D5/D8 · remote-observation` |
| Recovery and continuity | False-positive harm reopens the conclusion, disables the control, restores service, and records observe-only/fail-closed state | The trace does not show a later safe automated strategy | `DIAG-D · D6/D7 · dialogue/patch/remote-observation` |

## Within-Case Inferences

- **This case suggests an attribution-confidence gate before high-impact
  enforcement.**
  - **Why the evidence supports it**: a deployed source-level control is later
    shown to affect legitimate users because the source/semantic correlation was
    insufficient.
  - **What remains uncertain / competing explanation**: a different trusted
    identity boundary could make similar enforcement safe.
  - **Evidence pointer**: `DIAG-D · D6/D7 · coordination/remote-observation`
- **This case distinguishes immediate mitigation from durable effectiveness.**
  - **Why the evidence supports it**: repeated local/live improvements coexist
    with unresolved longer-window evidence and later causal correction.
  - **What remains uncertain / competing explanation**: an extended observation
    period may not be worth its cost for low-impact mitigations.
  - **Evidence pointer**: `DIAG-D · D4/D5/D8 · remote-observation/task-complete`

## SVC Relation

- **Classification**: Within-case candidate hypothesis.
- **Reasoning**: SVC can express read-only-to-mutation authority, attribution
  confidence, reversible/TTL/journalled control, postconditions, observe-only
  fallback, and observation-horizon handoff. Service topology, thresholds,
  identity semantics, and live operations remain project/platform-owned.
- **Smallest testable intervention, if applicable**: add an optional high-risk
  operation record with `attribution confidence`, `blast radius`, `rollback or
  observe-only fallback`, `immediate evidence`, and `follow-up horizon`.
- **Scope boundary**: this does not justify automatic enforcement or let SVC
  infer trusted identity from an operational trace.
