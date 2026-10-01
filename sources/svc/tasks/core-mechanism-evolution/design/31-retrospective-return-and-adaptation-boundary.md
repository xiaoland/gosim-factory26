# Working Note — Retrospective Return and Adaptation Boundary

- **State**: corrected task-packet boundary; procedural model deferred to the
  Working Protocol cluster
- **Sources**: `D-008..D-042`; `V-017..V-020`, `V-036`, `V-052`;
  Sir's correction of the automatic-retrospective gleaning; existing Agent Task
  Analysis; [`design/08`](08-agent-work-system-retrospective.md),
  [`design/09`](09-adaptive-control-reference-triage.md), and the historical
  two-case pilot retrospective
- **Use**: Decide whether Retrospective/Adaptation is a semantic task-packet
  module, how it enters a Plan without blocking ordinary completion, and how a
  completed trajectory can change future Agent behavior without creating an
  append-only rule system

## Human Correction to the First Proposal

The first Lead proposal made an invalid inference:

```text
cross-Cell or longitudinal scope
  -> independently completable objective
  -> nested/follow-up Task
```

Scope and duration do not establish an independent Task boundary. RT can remain
a task-level activity after Track/Phase work, and the accepted absence of a
global Task Plan cannot be used to remove a legitimate Task activity. If its
planning placement reveals tension in the current topology, that topology must
be refined rather than forcing RT into a new Task.

The exact RT SOP must also precede a fixed return contract. Unlike an ordinary
Slice consumed by a current integration owner, adaptation may principally shape
a future Agent decision path. Whether the current consumer is the Lead, Human,
an intervention owner, or only the future Agent depends on how diagnosis,
selection, mutation, and later evaluation are separated. This is a Working
Protocol question, not something the task-packet file grammar can settle.

## Two Different End-of-Task Concerns

“沉淀复盘” currently hides two returns that must remain separate:

| Concern | Question | Return |
| --- | --- | --- |
| project truth consolidation | What product, technical, operational, or implementation truth changed, and which normal owner must now express it? | planned/verified mutation of the existing semantic owner |
| Agent work-system retrospective | Which avoidable Agent move, feedback delay, context sink, retry, or coordination failure affected this trajectory, and what could make recurrence less likely? | no intervention, or a bounded behavior-shaping intervention hypothesis |

The first is ordinary owner resolution. Discovering a durable delta may occur
during closing work, but the actual mutation still belongs to an authorized
`IM` Slice and its normal owner. A document path written in advance is not
consolidation and remains prohibited by `D-025`.

The second is the distinctive retrospective gleaning. Its target is the
Agent-in-project work system:

```text
Agent policy/context
  + instructions and methods
  + tools and interfaces
  + mechanical constraints
  + feedback/verification
  + delegation/integration boundaries
  -> task trajectory and result
```

A script, linter, diagnostic, Skill, protocol rule, or delegation contract is
only a possible intervention. The retrospective does not own those assets and
does not authorize their creation.

## Why Retrospective Is Not a Default Completion Stage

The primary task result, its verification horizon, and the observed trajectory
must be available before a useful counterfactual can be formed. But semantic
task completion is not the same as a host `Stop`, idle timeout, successful test,
or conversation end.

At a verified result, bounded handoff, cancellation, or meaningful failure, the
Lead can perform a cheap close-screen:

> Did this trajectory expose a material, plausibly avoidable work-system loss
> for which a changed future Agent decision path may repay its own cost?

- **No** is the normal answer for `S-SIMPLE`; create no Slice or artifact.
- **Unclear but immaterial** also closes without investigation.
- **Yes or materially uncertain** activates retrospective work.

The screen is not a new Phase barrier. The original product/task result does not
become unaccepted merely because work-system improvement remains optional. If a
task explicitly includes adaptation as an objective, that work is of course
part of its declared completion contract.

## Field Signal

The task corpus contains only one independently named historical
`pilot-retrospective.md`. It was not an experience diary: it compared two case
results against exit criteria, corrected the evidence protocol, preserved
unknowns, and returned concrete revisions before the larger audit continued.
It behaved like one bounded return inside an existing Plan.

No recurring corpus shape demonstrates an independently maintained
`retrospective.md` owner. The absence is not outcome proof, but it supplies no
reason to pre-create such a module. The more detailed current retrospective
note is itself design work in this dedicated SVC-evolution Task, not a reusable
module attached automatically to every completed Task.

## Alternatives

| Alternative | Benefit | Cost/failure |
| --- | --- | --- |
| mandatory `retrospective.md` for every Task | predictable location; easy automation hook | creates summaries without intervention value, blocks closure, and accumulates self-rationalized “lessons” |
| pressure-created Retrospective semantic module | supports deep local diagnosis | its lifecycle normally ends in one return; evidence already belongs to the completed Task, and the intervention immediately routes elsewhere |
| no packet representation | zero ceremony | material trajectory loss is easily forgotten or discussed without a return/authority boundary |
| **optional task-level RT activity with pressure-created supporting material** | preserves the original Task boundary without a permanent module | exact SOP, Plan placement, return, and future consumer remain to be derived |

The fourth alternative best fits the current task-packet evidence. It does not
yet decide that every material RT is a Slice or when independent Task boundaries
are useful.

## SOP-Dependent Output Questions

The following is useful input to the later SOP, not an accepted `RT` return
schema. A retrospective should probably reason about:

- **episode and outcome boundary**: the relevant task objective, terminal or
  handoff result, and evidence horizon
- **observed trajectory loss**: concrete stall, blind search, repeated retry,
  rework, context reload, Human correction, delegation/integration failure, or
  verification detour
- **necessity test**: why this was plausibly avoidable rather than required
  exploration, an unavoidable external failure, or a one-off accident
- **work-system cause and alternatives**: which affordance, constraint,
  feedback, context, strategy, or boundary shaped the Agent move; preserve
  plausible competing explanations
- **behavioral counterfactual**: if the candidate intervention already existed,
  exactly which future Agent decision or feedback loop would differ
- **smallest intervention direction**: simplify/remove, deterministic action,
  constraint/preflight, diagnostic feedback, working method, context/delegation
  boundary, or no intervention
- **quality and total-cost invariant**: how terminal quality remains protected,
  plus simple-task context, false-positive, maintenance, and lifecycle cost
- **future evidence**: what later matching work could show to keep, revise, or
  retire the intervention
- **continuation/disposition**: no action, current-Task work, later observation,
  or another route selected by the eventual SOP

Metrics such as tokens, elapsed time, command count, retries, or errors are
navigation signals. They become evidence of waste only through a trajectory
link and a credible counterfactual. Same-context Agent self-description is a
causal hypothesis, not privileged introspection.

## Task-Level Placement Remains Open

RT may be local, cross-Cell, task-wide, or longitudinal and still remain an
activity of the original Task. The task-packet conclusion is only:

- no `retrospective.md` module is pre-created
- an inactive close-screen creates no artifact
- while RT is material and active, `packet.md` must be able to show its
  consequential current state and Human attention like any other task activity
- supporting material may be added under the Plan/current-work owner selected
  by the later SOP, using the accepted artifact grammar
- nested/follow-up Task admission continues to require its ordinary independent
  objective, authority/guardrails, verification, resume, and terminal-return
  test; RT scope or duration alone is insufficient

The later Working Protocol discussion must decide whether task-wide RT uses a
bounded task-level Plan, a closing operation, a scoped Slice, or another
existing primitive—and whether that requires refining `D-027`'s “no global Task
Plan” wording. The packet file model should carry that answer, not dictate it.

## Intervention Routing

Route by diagnosed cause, not by the attractiveness of an asset:

| Cause | Likely direction, subject to normal design |
| --- | --- |
| unnecessary product/process obligation | remove or simplify the obligation first |
| stable project fact repeatedly unavailable | repair its existing owner/retrieval path; no parallel memory system |
| deterministic operation repeatedly reconstructed | tested script, task command, codemod, or transformation |
| expressible invalid move discovered late | existing type/schema boundary, linter, preflight, or static check |
| feedback cannot distinguish likely causes | clearer error, diagnostic command, observability, or narrower query surface |
| judgment strategy repeatedly poor | Working Protocol, SOP, Skill, taste guidance, or specialized role |
| context/review cost dominates | different task boundary, delegation contract, certificate, or no delegation |
| necessary exploration/one-off/external limitation | no durable intervention |

The candidate becomes normal `DS`/`IM`/`VR` work under its semantic owner and
mutation authority. A successful script execution or linter fixture proves the
artifact's mechanics, not the behavioral counterfactual. Later matching work
must still be able to show that the intervention is unused, harmful, redundant,
or no longer worth its cost.

## Progressive Human Projection

Most tasks show nothing retrospective in `packet.md`. Project it only when a
material candidate changes the current collaboration:

- the observed avoidable pattern and why it matters
- the proposed future behavior change, not merely the asset name
- expected benefit and added ongoing cost
- whether Sir must choose, authorize, or review anything
- later evidence needed to keep/revise/retire it

Do not ask the Human to review every generated lesson. Do not show a waste score
or activity summary as a proxy for a candidate decision.

## Relationship to Packet Closure and Retention

1. Reach a verified primary return, bounded handoff, cancellation, or meaningful
   failure.
2. Resolve any actual task-local durable delta through normal Plan work; do not
   postpone known owner updates until deletion.
3. Run the cheap work-system close-screen.
4. If no material candidate exists, close the packet normally.
5. If local and bounded, run an `RT` Slice and route its return.
6. Route further work according to the later RT SOP; do not infer a new Task
   from cross-Cell scope or duration.

Deleting the original task packet remains retention discipline. It is not
forgetting, promotion review, or proof that an intervention was learned.

## Failure Modes and Falsifiers

- every Task generates a plausible but non-discriminating lessons list
- task completion is blocked on optional work-system optimization
- activity volume is labeled waste without a counterfactual
- necessary exploration is optimized away and terminal quality falls
- an intervention encodes a transient workaround as permanent policy
- a rule, linter, script, Skill, or role has no discovery/default/enforcement
  path at the future Agent decision point
- retrospective owns project facts or becomes a second promotion registry
- the main Agent approves its own causal story and intervention with no
  proportional independent evidence
- “learning” only adds mechanisms and provides no revision/retirement path
- Plan topology silently removes a legitimate task-level RT activity

Reopen the module-negative conclusion if repeated Tasks need one independently
maintained retrospective state with its own consumer/cadence and supporting
artifacts cause material duplication, loss, or conflicting intervention
decisions.

## Lead Recommendation

1. Do not admit `retrospective.md` as a default or pressure-created semantic
   module yet.
2. Use a cheap semantic close-screen with no artifact by default.
3. Allow RT to remain an activity of the original Task regardless of whether
   it is local, cross-Cell, or longitudinal; do not infer a nested/follow-up
   Task from scale.
4. Defer RT SOP, exact return/consumer, and Plan placement to the Working
   Protocol cluster; let the task packet carry that result later.
5. Keep project-truth consolidation separate; actual durable changes use their
   normal owners and `IM`/`VR` contracts.
6. Require a behavioral counterfactual, preserved terminal quality, total-cost
   reasoning, and a later keep/revise/retire path before treating an
   intervention as learning.
