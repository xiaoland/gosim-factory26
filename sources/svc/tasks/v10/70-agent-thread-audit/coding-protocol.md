# Draft Multi-Resolution Coding Protocol

## Before Coding: Keep the Units Separate

One native event is not automatically a turn; one turn is not automatically a
work episode; and one thread is not automatically one task. Record the
boundary rationale whenever a sequence is promoted to a work episode:

| Boundary candidate | May support | Cannot prove by itself |
| --- | --- | --- |
| user-message trigger / linked turn ID | request-response cycle | stable objective or task completion |
| compaction or session change | context-window boundary | collaboration discontinuity |
| tool completion / call ID | observable attempted action | success, acceptance, or causal effect |
| task-packet association | parallel work artifact | that it was current, read, or followed |
| explicit handoff / verification signal | outcome checkpoint | durable convergence without later evidence |

An episode must have a recorded objective, a boundary rationale, an
outcome-evidence status, and an outcome or explicit uncertainty. It may span
several turns; a thread may contain several episodes.

## Case Card

Create one non-quoting card per archive:

1. **Case boundary**: opaque archive ID, host context, provenance, and known
   selection bias.
2. **Trajectory**: ordered work episodes and context-window limitations.
3. **Human moves**: framing, constraint, approval, correction, evidence
   request, escalation, or handoff.
4. **Agent moves**: clarification, proposal, execution, delegation, evidence
   report, recovery, or closure claim.
5. **Artifact/environment moves**: task packet, repository/worktree, dev
   server, release, tool, or platform state that mediates collaboration.
6. **Outcome signal**: verified convergence, partial result, recovery,
   unresolved ambiguity, or handoff.
7. **SVC relation**: supported mechanism, missing affordance, non-SVC concern,
   or candidate experiment.

## Episode Trace

Use this compact trace before assigning explanatory codes:

| Field | Record without quoting private content |
| --- | --- |
| Objective and authority | What outcome was sought, who could approve or change it |
| Cue / constraint | What new evidence, rule, failure, or human instruction shaped the next move |
| Coordination move | Human, Agent, artifact, or environment action category |
| Externalized state | Relevant task packet, plan, repository/worktree, service, tool, or platform state |
| Verification / handoff | Observable acceptance, test, inspection, release, deferment, or transfer signal |
| Outcome | converged, recovered, partial, deferred, unresolved, or unknown |
| Outcome evidence status | observed execution, locally evidenced, externally evidenced, reported-only, blocked, or unknown |
| Alternative / boundary | A plausible non-SVC explanation or reason this case should not generalize |

The trace describes observable coordination. It does not attribute intent or
private reasoning to either participant.

## Outcome-Evidence Status

Do not use a task-complete marker, a successful command invocation, or an
Agent's closure statement as an interchangeable success signal. Record the
strongest status actually supported by the permitted trace:

| Status | Minimum meaning |
| --- | --- |
| Interaction-evidenced | a relevant human decision, acceptance, deferral, or handoff is explicit in the permitted dialogue; no implementation/runtime result is implied |
| Observed execution | an action was attempted or completed at the runtime-record level; no result is implied |
| Locally evidenced | a relevant local verification outcome is observable |
| Externally evidenced | an observation from the relevant deployed/external boundary is observable |
| Reported-only | a participant reports an outcome without matching permitted outcome evidence in the archive |
| Blocked | a known precondition or environment prevents the observation |
| Unknown | the archive has no adequate outcome record, including a truncated terminal action |

An episode may carry more than one status when its evidence horizons differ;
write every status as `<canonical status> (<scope>)`. `deferred`, `superseded`,
and `reopened` describe work state or later history, not outcome-evidence
statuses; record them in the outcome/uncertainty column. An external signal may
still be incomplete or non-independent. Never silently promote a status to a
stronger one.

## Collaboration-Diagnostic Dimensions

When evidence permits, use these dimensions to locate a fault mechanism rather
than to score a participant or a thread:

| Dimension | Evidence to seek | A negative finding must mean |
| --- | --- | --- |
| Intent and authority | goal/constraint, mutation or approval gate, accountable owner | the required information or authority was not visible in this episode—not that it never existed |
| Shared state | current plan/task packet, environment, worktree, service, or release state | the state was not accessible or trustworthy at the observed decision point |
| Coordination | ownership handoff, concurrency rule, collision avoidance, delegation state | the observed protocol did not settle responsibility for this action |
| Observability | test, inspection, probe, release evidence, or explicit uncertainty | the next decision lacked enough observable evidence in this trace |
| Recovery and continuity | detection, containment, safe retry/rollback, later handoff | the observed episode lacks a demonstrated recovery or transfer path |

These are diagnostic questions, not an all-or-nothing checklist. A missing
trace may be outside the exported thread; record that limitation instead of
calling it a product failure.

## Evidence Pointer

Use a pointer of this form, never an excerpt:

`<archive opaque ID> · <context/turn or indexed time span> · <record classes> · <claim scope>`

For example, a recovery claim must point to its triggering turn, the attempted
action category, and the later verification/handoff signal. If the evidence
does not establish an outcome, label it unknown.

For every non-observation claim, pair the pointer with the stated inferential
step: why this sequence supports the claim and what competing explanation
remains possible.

## Cross-Case Claim Ladder

| Level | Requirement | Permitted wording |
| --- | --- | --- |
| Observation | Directly evidenced in one segment | “Observed in this case” |
| Within-case inference | Coherent sequence with uncertainty stated | “Suggests within this case” |
| Candidate hypothesis | One useful but unreplicated causal shape | “Candidate to test” |
| Recurring pattern | At least two independent cases plus boundary search | “Recurring pattern in this corpus” |
| SVC gap | Pattern or high-impact case, clear SVC ownership, and testable intervention | “Proposed SVC gap” |

## Initial Codes

| Family | Codes |
| --- | --- |
| Human control | goal framing, constraint, authority gate, correction, acceptance evidence, handoff |
| Agent control | clarification, plan, execution, evidence report, delegation, closure, recovery |
| Coordination state | task boundary, shared context, worktree/service ownership, external dependency, release state |
| Friction | ambiguity, scope drift, hidden state, stale state, concurrency interference, regression, weak verification |
| Outcome | converged, recovered, partially converged, deferred, unresolved, falsely complete |

Codes are prompts for comparison, not labels to apply mechanically. Add a code
only when it distinguishes a collaboration mechanism or a likely owner.

## Default Reading Boundary

The semantic pass reads user/assistant dialogue and tool category/outcome only.
It excludes Agent reasoning, attachment payloads, and sensitive operational
values. Any hypothesis that genuinely requires a broader source must name the
specific additional record class, its necessity, and a privacy-preserving
recording method before review.

## SVC Gap Test

A friction becomes an SVC candidate only when the audit can state:

1. the collaboration mechanism that failed or was expensive;
2. why a reusable SVC contract/tool/measurement could reasonably own it;
3. the smallest change or experiment;
4. an observable success/failure measure; and
5. a counterexample or scope boundary where SVC should not intervene.
