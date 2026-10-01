# Case Card: `NET-C`

## Boundary and Provenance

- **Case scope**: One selected medium-length, multi-boundary connectivity
  diagnosis and partial repair thread.
- **Packet relation**: No resolved packet attachment. The case is used as a
  contrast for operational work whose authoritative state spans configuration,
  runtime, generated artifacts, publication, and human interaction.
- **Known selection/context limits**: Multiple systems and devices are involved;
  secret values are excluded from review; external client refresh and some
  end-to-end paths have no closing confirmation.
- **Outcome confidence**: Diagnosis and a narrow repair have local and limited
  interaction evidence. One additional path remains explicitly unknown at the
  archive boundary.

## Trajectory

| Episode | Boundary rationale | Control-loop summary | Outcome evidence status | Outcome / uncertainty | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| `N1` | Initial reachability report is decomposed into local, remote, and path hypotheses | Human supplies a counter-hypothesis; Agent uses read-only layered checks rather than treating a target as globally unavailable | locally evidenced (path checks) | A local-path boundary is supported; no user acceptance signal yet | `NET-C · N1 · lines 8–113 · dialogue/tool outcome` |
| `N2` | Peer/hub comparison forms an initial authentication/data-path hypothesis | Agent compares state across boundaries and corrects a misleading aggregate counter before changing configuration | locally evidenced (cross-boundary diagnostics) | Diagnosis narrows; privileged packet capture remains unavailable | `NET-C · N2 · lines 114–483 · dialogue/tool outcome/task-complete` |
| `N3` | Cross-device discrepancy tests configuration against running state | Human challenges the first repair premise; Agent distinguishes source/build state from in-memory runtime behavior and defers a risky secret change | locally evidenced (state comparison); interaction-evidenced (repair constraint) | File/runtime divergence observed; no risky mutation is inferred necessary | `NET-C · N3 · lines 484–646 · dialogue/tool outcome/task-complete` |
| `N4` | Explicit authorization permits a reversible runtime probe | Agent uses a bounded, restorable probe to discriminate competing routing/return-path explanations, then restores temporary state | locally evidenced (reversible probe); interaction-evidenced (authorization) | A routing/return-path hypothesis is supported only for the probed path; no persistent state is left by the probe | `NET-C · N4 · lines 647–1380 · dialogue/tool outcome/web-search/task-complete` |
| `N5` | A second user-visible path requires precise endpoint/route semantics | Agent maps the path at the required granularity and avoids broadening ownership beyond the evidence | locally evidenced (configuration/design checks) | Network-path diagnosis remains primary; service presence alone is not treated as end-to-end proof | `NET-C · N5 · lines 1381–1545 · dialogue/tool outcome/task-complete` |
| `N6` | Human authorizes the minimum persistent repair | Agent changes only the scoped configuration, validates/generates/reloads it, and receives a bounded user success signal | locally evidenced (generated/reload checks); interaction-evidenced (one path) | One target path converges; another path remains open | `NET-C · N6 · lines 1546–1963 · dialogue/tool outcome/task-complete` |
| `N7` | Published artifacts must become observable to the relevant client | Agent builds, publishes, and verifies remote artifact readback without exposing credentials | locally evidenced (publication/readback) | Publication/readback succeeds; client refresh is not assumed | `NET-C · N7 · lines 1964–2038 · dialogue/tool outcome/task-complete` |
| `N8` | A remaining path is separated from the repaired path | Agent applies only the authorized forward-path change and records the unaddressed return-path/user-confirmation condition | locally evidenced (scoped forward path); unknown (end-to-end boundary) | Partial repair only; no claim of full end-to-end convergence | `NET-C · N8 · lines 2039–2156 · dialogue/tool outcome/task-complete` |

## Observable Coordination

| Dimension | Observed mechanism | Boundary or alternative explanation | Evidence pointer |
| --- | --- | --- | --- |
| Intent and authority | Human supplies hypotheses, corrects entity semantics, constrains unsafe changes, and authorizes each mutation/publish step | The high domain expertise of the operator may be essential to this outcome | `NET-C · N1/N3/N4/N6/N8 · dialogue` |
| Shared state | Source configuration, runtime state, generated artifacts, publication record, and client experience are treated as separate states | Their relation is project-specific; SVC should model evidence status, not the domain topology | `NET-C · N3/N6/N7/N8 · tool outcome/task-complete` |
| Coordination | Reversible probes include an authorization boundary and restoration; secret comparisons expose only safe equivalence results | A reversible runtime operation can still carry domain-specific risk absent an appropriate project owner | `NET-C · N3/N4 · dialogue/tool outcome` |
| Observability | Layered diagnosis, readback, and interaction confirmation distinguish local, distributed, and user-visible evidence | Counter values, listener state, and publication success each have false-positive boundaries | `NET-C · N2/N5/N7/N8 · tool outcome` |
| Recovery and continuity | A disproved hypothesis is retracted before risky mutation; partial fixes leave residual conditions explicit | The trace does not establish long-term stability after the final partial repair | `NET-C · N3/N4/N8 · dialogue/tool outcome` |

## Within-Case Inferences

- **This high-risk operational change exposes distinct evidence boundaries across
  source, runtime, artifact, publication, and interaction.**
  - **Why the evidence supports it**: several apparent success signals are
    explicitly insufficient until the next boundary is checked.
  - **What remains uncertain / competing explanation**: such a chain may be
    excessive for a low-risk, single-process change.
  - **Evidence pointer**: `NET-C · N3/N6/N7/N8 · tool outcome/task-complete`
- **Reversible, secret-safe probes are a candidate alternative to premature
  permanent mutation.**
  - **Why the evidence supports it**: a risky hypothesis is tested, narrowed,
    and restored before a persistent repair is selected.
  - **What remains uncertain / competing explanation**: not every system has a
    safe reversible probe or enough authority to run one.
  - **Evidence pointer**: `NET-C · N3/N4 · dialogue/tool outcome`

## SVC Relation

- **Classification**: Within-case candidate hypothesis.
- **Reasoning**: SVC could provide a generic evidence-chain and reversible
  probe/rollback contract, including `unknown` at an unverified boundary. It
  must not encode routing, secret, device, or service-specific semantics, nor
  silently broaden a project's authority scope.
- **Smallest testable intervention, if applicable**: permit a task packet to
  declare named evidence boundaries (`source`, `runtime`, `artifact`,
  `published`, `interaction`) and require each high-risk probe to state an
  authorization, restoration check, and residual unknown.
- **Scope boundary**: this case does not support automating operational repair;
  it supports making its evidence and recovery discipline explicit.
