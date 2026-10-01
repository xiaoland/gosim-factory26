# Case Card: `WIN-G`

## Boundary and Provenance

- **Case scope**: One selected short Windows read-only investigation of a
  cross-platform path/lifecycle issue.
- **Packet relation**: Not observed.
- **Known selection/context limits**: This is a single coherent episode with no
  persistent mutation, runtime acceptance test, or later user confirmation.
  Semantic claims from external sources are represented only as participant
  reports because source payloads are outside audit scope.
- **Outcome confidence**: The investigation and its source/local probes are
  observed. The technical conclusion is reported-only; a workaround and its
  persistence are unknown.

## Trajectory

| Episode | Boundary rationale | Control-loop summary | Outcome evidence status | Outcome / uncertainty | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| `W1` | One bounded user request ends with a read-only conclusion | Human fixes the three investigative questions and prohibits mutation; Agent researches external and local evidence, then reports a risk-bounded conclusion | interaction-evidenced (read-only authority); observed execution (research/probes); reported-only (technical conclusion); unknown (runtime acceptance) | Investigation closes without a write; no workaround, persistence check, or user acceptance is observed | `WIN-G · W1 · lines 4–119 · dialogue/web-search/local inspection/task-complete` |

## Observable Coordination

| Dimension | Observed mechanism | Boundary or alternative explanation | Evidence pointer |
| --- | --- | --- | --- |
| Intent and authority | Human explicitly limits the task to read-only investigation and asks for evidence/references | No authorization exists to test or repair the suspected condition | `WIN-G · W1 · dialogue` |
| Shared state | Path representation, current working context, local configuration, and upstream documentation form the available state | Source semantics are reported rather than independently audited from payload | `WIN-G · W1 · web-search/local inspection` |
| Coordination | Agent separates an upstream behavior question from a project-local workaround question | The archive does not show whether the reported workaround fits the actual project lifecycle | `WIN-G · W1 · dialogue/tool outcome` |
| Observability | External research and local shell probes produce read-only signals | No later execution/acceptance signal tests their operational relevance | `WIN-G · W1 · web-search/local inspection/task-complete` |
| Recovery and continuity | The conclusion explicitly frames a manual change as temporary/risky rather than silently applying it | No evidence shows whether a future activity recreates the condition | `WIN-G · W1 · assistant closure/task-complete` |

## Within-Case Inferences

- **This investigation treats cross-platform path representation as a
  collaboration-relevant state, not merely a string value.**
  - **Why the evidence supports it**: the investigation separates canonical
    location, literal representation, working context, and upstream lifecycle
    behavior before proposing any action.
  - **What remains uncertain / competing explanation**: the relevant upstream
    entry point may already normalize the representation, or the project may
    have a different lifecycle rule.
  - **Evidence pointer**: `WIN-G · W1 · dialogue/web-search/local inspection`
- **This read-only diagnosis must not be recorded as a verified repair.**
  - **Why the evidence supports it**: the trace ends after research and a
    recommendation without any authorized mutation or later runtime test.
  - **What remains uncertain / competing explanation**: a later thread may
    have performed the verification outside this archive.
  - **Evidence pointer**: `WIN-G · W1 · task-complete`

## SVC Relation

- **Classification**: Within-case candidate hypothesis.
- **Reasoning**: SVC can make platform, working-context representation,
  diagnostic source, evidence level, and persistence check explicit in a task
  report. It cannot own upstream lifecycle behavior or project-specific
  workarounds.
- **Smallest testable intervention, if applicable**: add an optional
  cross-platform diagnostic record with `platform`, `representation`,
  `read-only evidence`, `runtime acceptance`, and `persistence recheck` fields.
- **Scope boundary**: one read-only short case cannot prove a generic
  cross-platform defect or the correctness of any workaround.
