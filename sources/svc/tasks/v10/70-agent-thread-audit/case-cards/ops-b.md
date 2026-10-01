# Case Card: `OPS-B`

## Boundary and Provenance

- **Case scope**: One selected long-running application-evolution thread with
  no resolved task-packet attachment in its exported archive.
- **Packet relation**: The permitted dialogue shows planning/control artifacts,
  but the export does not resolve an attached packet. The audit records this as
  an association limitation, not absence of a packet or process.
- **Known selection/context limits**: Many context compactions, a shared dirty
  worktree, external services, and platform reachability all affect the trace.
  Local checks and agent-reported results are not independently rerun here.
- **Outcome confidence**: Several delivery slices have local evidence and
  explicit review/checkpoint signals. External-service and deployment
  observations remain bounded or unknown where probes did not yield signal.

## Trajectory

| Episode | Boundary rationale | Control-loop summary | Outcome evidence status | Outcome / uncertainty | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| `O1` | Initial methodology and baseline-control objective | Human asks for a scoped method and low-cost evidence; Agent maps system state, opens a task control plane, and preserves dirty shared state | locally evidenced (baseline); unknown (skipped or indeterminate gates) | Evidence-backed baseline; some skipped/indeterminate gates remain explicitly open | `OPS-B · O1 · lines 11–789 · dialogue/coordination/patch/task outcome` |
| `O2` | Toolchain/system-scenario recovery and target-state decision | A failed or incomplete system proof triggers narrow diagnosis, repair, rerun, then human-guided target-state decisions | locally evidenced (scenario); interaction-evidenced (target-state decision) | Local scenario converges; external dependency fidelity is bounded | `OPS-B · O2 · lines 790–1669 · dialogue/function/custom-tool/patch/task outcome` |
| `O3` | Packet freshness and first delivery-slice control | Human challenges stale planning; Agent rebuilds slice plans, preflight/rehearsal evidence, report-first checks, and bounded delegation | interaction-evidenced (planning); locally evidenced (report checks) | Control plane becomes more explicit; shared-worktree concurrency remains a stated risk | `OPS-B · O3 · lines 1670–2486 · dialogue/coordination/patch/task outcome` |
| `O4` | Delivery execution exposes a plan-topology error, then repair and convergence | Human detects a phase/status mismatch; Agent retracts the claim, distinguishes completed from planned work, repairs the record, and revalidates later slices | locally evidenced (bounded slices); interaction-evidenced (status correction) | Converged delivery evidence for bounded slices; the correction demonstrates one plan/state misread | `OPS-B · O4 · lines 2487–8550 · dialogue/coordination/patch/task outcome` |
| `O5` | Subsequent-stage exploration meets environment/deployment limits | Read-only discovery drives a safety-oriented containment change; local and deployment steps run, but external probes yield no decisive signal | locally evidenced (local/deployment checks); blocked (external observation) | Local/deployment evidence exists; external behavior remains unknown rather than called passing/failing | `OPS-B · O5 · lines 8551–10184 · dialogue/function/patch/deploy outcome` |
| `O6` | Identity/handoff work is iterated through explicit policy and host limits | Human clarifies a product boundary; Agent narrows expected vs undefined failure handling, retains unresolved provider topology, and uses focused/full checks | locally evidenced (focused/full checks); blocked (host precondition) | Bounded local completion; end-to-end host preconditions remain open | `OPS-B · O6 · lines 10185–13965 · dialogue/patch/task outcome` |
| `O7` | Independent review becomes a new review/checkpoint gate | A review finds post-gate risks; Agent records minimal repair plans and declines to submit prematurely | interaction-evidenced (review/defer decision); blocked (pending repair) | Safe defer/block outcome despite earlier green gates | `OPS-B · O7 · lines 13966–14240 · dialogue/coordination/patch/task outcome` |

## Observable Coordination

| Dimension | Observed mechanism | Boundary or alternative explanation | Evidence pointer |
| --- | --- | --- | --- |
| Intent and authority | Human supplies product decisions, phase corrections, and submit/commit authority; Agent makes intermediate implementation decisions within those limits | The trace is an unusually long, engaged collaboration and may not represent ordinary consumer use | `OPS-B · O1/O4/O6/O7 · dialogue/patch` |
| Shared state | Plans, task packets, durable documents, test reports, and staged changes carry control state across many episodes | The export's absent packet attachment prevents proving which artifact was current at every decision | `OPS-B · O1/O3/O4 · dialogue/patch/task outcome` |
| Coordination | Dirty-worktree preservation, narrow delegation, cancellation, and staged allowlists are used to avoid concurrent mutation hazards | Coordination metadata is only a cue; the cause of every avoided collision is not observable | `OPS-B · O1/O3/O4 · coordination/patch` |
| Observability | The work uses a ladder of focused checks, broader scenarios, reviews, and external probes; no-signal probes are retained as unknown | A green local gate does not cover all timing, provider, or deployed-environment behavior | `OPS-B · O2/O5/O7 · tool/deploy/task outcome` |
| Recovery and continuity | Failures and planning errors are made visible, repaired, rerun, or deferred with explicit residual risk | The case does not show whether another person or future thread could recover without the same operator context | `OPS-B · O2/O4/O7 · dialogue/patch/task outcome` |

## Within-Case Inferences

- **A canonical planned-versus-completed state model is a candidate response to
  one packet-state misread.**
  - **Why the evidence supports it**: a detailed plan still permits a phase
    topology/status misread; the human challenge and explicit retraction repair
    the control state before further work continues.
  - **What remains uncertain / competing explanation**: the failure may arise
    from local naming/phase complexity rather than a generic packet weakness.
  - **Evidence pointer**: `OPS-B · O3/O4 · dialogue/coordination/patch`
- **Verification is an evidence ladder, not a single green gate.**
  - **Why the evidence supports it**: local checks, larger scenarios, external
    probes, and independent review expose distinct classes of uncertainty;
    later review finds risks after earlier passes.
  - **What remains uncertain / competing explanation**: additional gates may
    add cost without value in smaller or lower-risk work.
  - **Evidence pointer**: `OPS-B · O2/O5/O7 · tool/deploy/task outcome`

## SVC Relation

- **Classification**: Within-case candidate hypothesis.
- **Reasoning**: SVC may own a reusable control-plane state model, explicit
  evidence-status vocabulary, and safe concurrency/hand-off contracts. Product
  semantics, provider behavior, deployment reachability, and project-specific
  acceptance criteria remain local or platform-owned.
- **Smallest testable intervention, if applicable**: add a machine-readable
  distinction between planned, in-progress, locally evidenced, externally
  evidenced, blocked, and superseded work; require a stated evidence source
  before a high-risk phase is marked complete.
- **Scope boundary**: the evidence supports a within-case inference only. It
  does not show that every project should adopt a large task-packet state
  machine or that more gates always improve delivery.
