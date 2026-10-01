# Case Card: `REC-E`

## Boundary and Provenance

- **Case scope**: One selected long-running legacy-concept replacement and
  behavior-recovery thread.
- **Packet relation**: No resolved packet attachment. Planning/control
  artifacts occur in the permitted trace, but their currentness or use cannot
  be proven from export association.
- **Known selection/context limits**: Many compactions; validation is reported
  through permitted dialogue/outcome records rather than independently rerun;
  production cutover and deployment are outside the archive's observation
  window.
- **Outcome confidence**: The terminal trace covers a local amendment/closure.
  Several implementation and interaction checkpoints are locally or
  interaction-evidenced; no remote publication or production cutover is
  inferred.

## Trajectory

| Episode | Boundary rationale | Control-loop summary | Outcome evidence status | Outcome / uncertainty | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| `R1` | Concept-removal objective begins with a read-only domain/dependency map | Human asks for project-specific framing; Agent explores ownership and preserves unrelated state | interaction-evidenced (design/reconnaissance) | Design/reconnaissance converges; no runtime outcome is claimed | `REC-E · R1 · lines 10–138 · dialogue/patch-completion/task-complete/coordination` |
| `R2` | Human corrects an overly strong target model and fixes semantic constraints | Agent revises the domain model, ownership boundaries, and packet plan rather than forcing the earlier abstraction | interaction-evidenced (design/control decision) | Design/control state converges; it is not an implementation result | `REC-E · R2 · lines 139–1260 · dialogue/coordination/patch-completion/compaction` |
| `R3` | Explicit start moves the work into destructive-cutover preflight | Agent records data audit, dependency order, ownership, and fail-closed GO/STOP conditions | interaction-evidenced (preflight); blocked (production cutover) | Preflight converges; production data/cutover remains an explicit external gate | `REC-E · R3 · lines 1261–1541 · dialogue/coordination/patch-completion/task-complete` |
| `R4` | Additive owner migration and removal work runs through local gates | Agent migrates behavior/ownership, uses negative-space checks, and exercises isolated migration scenarios | locally evidenced (migration checks); reported-only (interaction checks) | Local release-candidate evidence; production completion is not inferred | `REC-E · R4 · lines 1542–6458 · dialogue/coordination/patch-completion/task-complete/compaction` |
| `R5` | Human detects material behavior regression, creating a recovery episode | Agent restores behaviorally relevant flows under the new ownership model and uses interaction-level scenarios to find mismatches | locally evidenced (bounded scenarios); interaction-evidenced (recovery acceptance) | Recovery converges for bounded scenarios; behavior equivalence outside them remains unknown | `REC-E · R5 · lines 6459–10348 · dialogue/coordination/patch-completion/task-complete/compaction` |
| `R6` | A focused information-architecture behavior is restored with a narrow submit boundary | Agent migrates historical behavior into the new model without reintroducing retired state | locally evidenced (scope checks); interaction-evidenced (behavior review) | Bounded behavior and scope evidence; unrelated work remains excluded | `REC-E · R6 · lines 10349–11251 · dialogue/coordination/patch-completion/task-complete` |
| `R7` | Additional regressions trigger another recovery pass, including an interrupted turn | Agent treats the abort/rollback as state, restores verified flows, and keeps the scope pending further human check | locally evidenced (recovery checks); interaction-evidenced (human review) | Recovery evidence is present; interruption is not misrecorded as success | `REC-E · R7 · lines 11252–12315 · dialogue/coordination/patch-completion/task-complete/turn-abort/rollback/compaction` |
| `R8` | A narrow warning defect is isolated and amended after explicit authorization | Agent adds a regression condition, verifies the narrow change, and amends only that scope | locally evidenced (warning gate); interaction-evidenced (amend authorization) | Local amendment/closure observed; remote publication and deployment are unknown | `REC-E · R8 · lines 12316–12476 · dialogue/patch-completion/task-complete` |

## Observable Coordination

| Dimension | Observed mechanism | Boundary or alternative explanation | Evidence pointer |
| --- | --- | --- | --- |
| Intent and authority | Human narrows/removes overly broad abstractions, starts destructive work explicitly, detects regressions, and controls submit scope | The sustained human review may account for the outcome as much as any reusable protocol | `REC-E · R2/R3/R5/R8 · dialogue/patch` |
| Shared state | Ownership slices, plans, historical behavior references, migration ledger, and verification artifacts externalize state | No resolved attachment means the audit cannot prove an exact artifact version was consumed at each step | `REC-E · R1/R3/R4 · dialogue/coordination/patch` |
| Coordination | Narrow domain ownership, read-model sharing, unrelated-change preservation, and explicit rollback constrain concurrent mutation | The trace cannot prove that a different owner partition would have caused a conflict | `REC-E · R3/R4/R7 · coordination/patch/rollback` |
| Observability | Characterization, negative-space checks, isolated scenarios, and interaction-level flows expose semantic and behavioral regressions | Reported scenario results are not re-executed by this audit; production behavior remains outside the window | `REC-E · R4/R5/R6/R7 · task outcome/patch` |
| Recovery and continuity | Regression detection reopens the work, preserves the target boundary, and adds narrowly scoped repairs rather than restoring retired concepts | Not every legacy behavior should be preserved; the product owner must define the relevant contract | `REC-E · R5/R7/R8 · dialogue/patch/rollback` |

## Within-Case Inferences

- **This destructive migration suggests a role for explicit characterization,
  fail-closed cutover, and negative-space evidence.**
  - **Why the evidence supports it**: the case uses preflight GO/STOP state,
    then finds both unwanted leftovers and behavior lost during migration.
  - **What remains uncertain / competing explanation**: the need may be driven
    by this system's legacy complexity, not all concept-removal work.
  - **Evidence pointer**: `REC-E · R3/R4/R5 · coordination/patch/task outcome`
- **Interaction-level evidence is distinct from structural or unit-level
  validation.**
  - **Why the evidence supports it**: material regressions appear after
    structural migration and are located through full-flow interaction checks.
  - **What remains uncertain / competing explanation**: broad interaction tests
    may be disproportionate for lower-risk behavior changes.
  - **Evidence pointer**: `REC-E · R4/R5/R7 · task outcome/patch/rollback`

## SVC Relation

- **Classification**: Within-case candidate hypothesis.
- **Reasoning**: SVC can provide reusable packet fields for characterization,
  owner/authority boundaries, destructive pre/postconditions, terminal coverage,
  and interaction-evidence status. It should not encode domain behavior,
  component structure, production-data decisions, or platform-specific runtime
  details.
- **Smallest testable intervention, if applicable**: add an optional
  high-risk-migration checklist requiring a named behavior contract, negative
  evidence search, fail-closed cutover preconditions, and one interaction-level
  acceptance signal.
- **Scope boundary**: this is not evidence that all legacy code must retain all
  historical behavior or that SVC should own production migration execution.
