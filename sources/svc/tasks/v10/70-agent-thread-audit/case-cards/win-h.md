# Case Card: `WIN-H`

## Boundary and Provenance

- **Case scope**: One selected short Windows read-only migration inventory of an
  existing telemetry/request path.
- **Packet relation**: Not observed.
- **Known selection/context limits**: One compaction is a context-window event,
  not a task transition. All repository semantic findings are participant
  reports because tool payloads are outside the audit scope. No migration,
  test, deployment, or user acceptance occurs in the archive.
- **Outcome confidence**: Read-only inspection is observed; proposed migration
  path and coverage gaps are reported-only; implementation success is unknown.

## Trajectory

| Episode | Boundary rationale | Control-loop summary | Outcome evidence status | Outcome / uncertainty | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| `H1` | One continuous diagnostic objective spans repository orientation, call-chain inspection, lifecycle check, and synthesis | Human requests an inventory with no writes; Agent searches local definitions, request paths, lifecycle call sites, and a named migration reference before reporting a minimum path | interaction-evidenced (inventory authority); observed execution (local inspection); reported-only (migration path); unknown (migration outcome) | Read-only inventory closes; no runtime proof or migration acceptance exists | `WIN-H · H1 · lines 4–158 · dialogue/local inspection/context-compaction/task-complete` |

## Observable Coordination

| Dimension | Observed mechanism | Boundary or alternative explanation | Evidence pointer |
| --- | --- | --- | --- |
| Intent and authority | Human fixes the deliverables and prohibits code change | No authority exists to validate or repair the proposed migration | `WIN-H · H1 · dialogue` |
| Shared state | Local definitions, event/call maps, request boundaries, and a migration reference are the diagnostic substrate | Absence of one referenced task item in the repository does not prove no external source of truth exists | `WIN-H · H1 · local inspection` |
| Coordination | Agent expands from core definitions to edge call paths and lifecycle behavior before making a centralization proposal | The archive cannot show whether the identified call graph is complete | `WIN-H · H1 · local inspection` |
| Observability | Many read-only searches have outputs, but there is no test/build/runtime boundary | A task-complete marker only closes the investigation, not the migration | `WIN-H · H1 · local inspection/task-complete` |
| Recovery and continuity | The proposed path explicitly retains compatibility, privacy, cross-origin, and rollback risks | No subsequent thread proves which risk materializes or how handoff occurs | `WIN-H · H1 · assistant closure/task-complete` |

## Within-Case Inferences

- **This inventory points to a coverage matrix, rather than only a central
  integration point, as a candidate migration aid.**
  - **Why the evidence supports it**: the investigation traces central and
    edge request/event paths, lifecycle behavior, and compatibility concerns
    before suggesting a minimum change.
  - **What remains uncertain / competing explanation**: a lower shared layer
    may already provide complete coverage outside the inspected path.
  - **Evidence pointer**: `WIN-H · H1 · local inspection/assistant closure`
- **This read-only migration inventory is an input to execution, not evidence
  of migrated behavior.**
  - **Why the evidence supports it**: the thread contains no mutation or
    runtime acceptance record.
  - **What remains uncertain / competing explanation**: implementation may
    occur in another thread.
  - **Evidence pointer**: `WIN-H · H1 · task-complete`

## SVC Relation

- **Classification**: Within-case candidate hypothesis.
- **Reasoning**: SVC can offer a migration-diagnosis contract that records
  legacy/new entrypoints, coverage matrix, identity/request boundary,
  compatibility, permissions, rollback, and required independent evidence. It
  cannot own a product's telemetry schema, request protocol, or privacy policy.
- **Smallest testable intervention, if applicable**: add an optional migration
  checklist/profile with explicit `inventory-only` status so a discovery result
  cannot be mistaken for an applied migration.
- **Scope boundary**: one repository inventory cannot establish missing
  instrumentation or prescribe a universal request/telemetry architecture.
