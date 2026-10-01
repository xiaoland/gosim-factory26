# Cross-Case Synthesis

## Scope and Claim Boundary

This synthesis compares the eight accepted, privacy-preserving case cards. The
cases were purposefully selected for useful variation; they are not a
prevalence sample, a controlled intervention, or an evaluation of Agent
internal reasoning. “Recurring” below means recurring in this bounded corpus,
with stated counterexamples—not universal behavior or causal proof.

## Corpus Observations

| ID | Observation in the selected corpus | Supporting cases | Evidence strength | Boundary / counterexample | Relation to current SVC |
| --- | --- | --- | --- | --- | --- |
| `P1` | A completion marker, local check, external observation, interaction decision, and unresolved terminal action carry different evidentiary meanings. | `SVC-A`, `OPS-B`, `REC-E`, `NET-C`, `DIAG-D`, `WIN-F`, `WIN-G`, `WIN-H` | Strong observational coverage across all sizes and work types; no prevalence or benefit claim | A bounded read-only investigation may legitimately end without runtime acceptance; the required evidence depends on the stated objective | Supports the existing Verification/Current Truth principle; exposes that the base packet has no standardized evidence-status vocabulary |
| `P2` | Human authority/constraint setting, narrow scope, and explicit stop/reopen behavior recur around material mutation. | `SVC-A`, `OPS-B`, `REC-E`, `NET-C`, `DIAG-D`, `WIN-F`; read-only authority in `WIN-G`, `WIN-H` | Medium-high observational coverage; strong selection bias toward engaged human control | The corpus cannot show that the gate caused better outcomes, reduced latency, or is needed for low-risk local work | Supports the existing Mutation Gate and Impact Handshake; not a demonstrated new gap |
| `P3` | Recovery is an observable coordination path: a weak hypothesis, regression, review finding, or external failure reopens work, changes state, and retains residual uncertainty. | `SVC-A`, `OPS-B`, `REC-E`, `NET-C`, `DIAG-D`, `WIN-F` | Medium-high observational coverage across diagnosis, migration, delivery, and operations | `WIN-G`/`WIN-H` are read-only and never exercise recovery; successful recovery in one scope does not prove broad resilience | Supports current Diagnose/Execute-and-Verify and runbook recovery guidance; no missing universal contract is established |
| `P4` | Exported task-packet association is not enough to infer that an artifact was current, read, authoritative, or causal; absent resolved association is not evidence that no control artifact existed. | Directly tested by `SVC-A`, `OPS-B`, `REC-E`; consistent with the remaining cases' unresolved/no attachment boundaries | Strong as an inference boundary; not evidence of stale or unused packets | Short read-only cases can remain useful without any packet; a project may maintain state outside the export window | Confirms the existing telemetry rule that archives preserve associated evidence without making it task truth |
| `P5` | One explicit plan/status misread and several evidence/state transitions suggest that free-form task state can become difficult to reconstruct in long work. | Primarily `OPS-B`; contextual signals in `SVC-A`, `REC-E`, `DIAG-D` | Exploratory only; mechanisms are not yet shown to be the same | A rich status model may add cost and simple tasks may need no such structure | Candidate for a future experiment, not a recurring pattern or SVC gap |

## Comparison with Canonical SVC

The current [Working Protocol](../../../src/sections/working-protocol.md) already
requires evidence in the task packet, objective verification, material
uncertainty, a mutation gate, bounded verification, and explicit external
authority. The [task-packet template](../../../src/assets/templates/task-packet.template.md)
deliberately keeps the control surface human-readable and small. The
[diagnostic matrix](../../../src/assets/templates/task-diagnostics-matrix.template.md)
and [deployment runbook](../../../src/assets/templates/deployment-runbook.template.md)
already supply evidence/rollback structures for their specific work shapes.

The audit therefore does **not** establish that SVC lacks verification,
authority, recovery, or task-packet concepts. It identifies a narrower v10
question: whether selected high-risk work would benefit from an optional,
machine-readable projection of existing evidence and control-state discipline.

The current [telemetry contract](../../../src/index.md#local-agent-thread-evidence)
also intentionally keeps task-packet association as separate archived evidence.
`P4` validates that boundary; it is not a reason to make association a source of
task truth.

## Candidate Experiments, Not Approved Gaps

| Candidate | What is missing from the evidence | Smallest safe experiment | Success/failure observation | SemVer and scope boundary |
| --- | --- | --- | --- | --- |
| `H1` — optional evidence-status record | The corpus shows different proof horizons but not that a standardized field reduces mistakes or cost | In two future high-risk, dissimilar consumer tasks, add a sidecar/optional profile that records `interaction`, `observed execution`, `local`, `external`, `reported-only`, `blocked`, and `unknown` with scope | Independent reviewers can identify the strongest proof, residual unknown, owner, and next action without reading raw thread content; measure reopened false-closure claims and reporting overhead | Making it mandatory changes task-packet semantics and is Behavioral SemVer **MAJOR**. An additive optional companion may be compatible, but must not silently become a required consumer obligation |
| `H2` — optional current-work state record | One clear plan/status misread is insufficient to show a generic state-machine benefit | Trial a minimal `proposed → authorized → applied → evidenced → blocked/superseded` record in another long, multi-slice task and one deliberately simple task | Compare whether a handoff/reviewer can reconstruct the current state and distinguish plan from completion; reject it if simple work gains no value or costs more than free-form Current Truth | No broad phase taxonomy; project-specific lifecycles stay local. Required semantics would be MAJOR |
| `H3` — archive terminal-coverage summary | Only one case ends after an action with no captured outcome; the index already allows a careful analyst to detect this | Evaluate whether a non-sensitive manifest/index summary of terminal record class and unresolved terminal actions improves analyst accuracy without parsing content | Analysts correctly identify an archive-ending action with no captured outcome; no sensitive content or invented outcome appears | Telemetry-specific, not a task-packet change. One case is insufficient to schedule implementation |

## What Should Remain Outside SVC

- Product behavior, domain models, endpoint/configuration semantics, design
  values, and acceptance criteria remain consumer-owned.
- Platform accounts, deployment reachability, external providers, operating
  system behavior, and production-data authority remain platform/environment
  owned.
- SVC may record an external boundary and require that it remain visible; it
  must not infer success, invent identity, broaden authority, or automatically
  mutate those systems.

## Audit Decision

No finding currently satisfies the task's threshold for a **proposed SVC gap**:
a reusable SVC owner, a validated minimal intervention, a measurable effect,
and a demonstrated non-intervention boundary. The next legitimate action is a
product decision about whether to run `H1`, `H2`, or `H3` as a separate,
explicitly scoped experiment—not a runtime change in this audit task.
