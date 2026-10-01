# Working Note — Track / Slice Counterfactual

- **State**: supporting field-based derivation; active model is
  [`20-task-axes-and-linear-plans.md`](20-task-axes-and-linear-plans.md)
- **Sources**: `D-022`, `D-023`; `V-044`, `V-047..V-049`; current task packet
  structures previously selected through telemetry
- **Use**: Compare managing the same real task structures with only `Slice`
  versus optional `Track + Slice`

## Admission Principle: Net Management Value

Semantic distinctness is necessary but insufficient. A planning building block
is useful only when it reduces the cost of keeping work under control relative
to its maintenance, synchronization, inference, and misuse costs.

Qualitatively:

```text
net management value
  = control cost without the block
  - maintenance/synchronization/misuse cost with the block
```

“Control” includes understanding current state, predicting consequences,
selecting next work, preserving coherence, assigning bounded work, detecting
conflict, resuming context, and integrating returns. A block with no decision
or control consequence is empty even when its description is semantically
correct.

## What Product/Unit Ownership Duplication Means

A durable product or technical owner answers questions such as:

- what behavior and boundary the system promises
- which component owns authoritative state or a contract
- which invariants survive beyond the current task

A task-local Track should instead answer:

- which slices contribute to one continuing obligation
- what cross-slice pressure or unresolved consistency issue remains
- which return is current and how the next one is selected
- what has been learned across returns and where durable truth is referenced

Repetition is useful when a Track forms a selective task-local snapshot or
stages candidate durable changes. The risk appears when it becomes a complete,
unlabelled shadow owner whose provenance, freshness, difference from durable
truth, and later promotion cannot be understood. Durable owners remain the
long-lived authority; Track may cache the subset and working delta needed to
coordinate several returns. This correction is accepted in `D-024` and
developed in [`design/20`](20-task-axes-and-linear-plans.md).

## Case A — InKCre Knowledge Lifecycle

### Observed structure

The program has three task-local Tracks—Collection, Organization, and
Application—and several vertical implementable units. The Collection Track is
45 lines and currently relates at least six completed or queued slices. It also
owns a per-source design card, a two-real-unit abstraction rule, and current
slice selection. The other two Track files are 34 and 37 lines.

The durable product corpus already owns collection, organization, retrieval,
indexing, authority, and unit-boundary claims. The task capability map also
repeats the three trunks and program queue.

### Counterfactual: Slice only

Represent every implementable unit as a Slice and annotate it with a concern:

```text
Memos extension       concern=collection
RSS hardening         concern=collection
Semantic retrieval    concern=application
```

This is sufficient for isolated delivery and dependency ordering. It is not
cheap for questions that span several returns:

- which collection pressures have repeated across Memos and RSS?
- when is a shared abstraction admitted rather than copied?
- which queued source best exposes the next missing capability?
- what must remain coherent across all future collection slices?

Without a Track, those answers must be reconstructed from unit packets, placed
in the root capability map, or repeated in every slice.

### Counterfactual: Track + Slice

Collection Track can own the member/coverage projection, unresolved
cross-slice pressures, next-selection rule, and references to shared durable
constraints. Each Slice still owns one independently returnable unit.

Management gain is plausible for Collection because several returns accumulate
learning and influence future selection. It is weaker for Organization and
Application while they have few actual slices; pre-creating all three Track
files may be taxonomy ahead of management pressure.

The current files also demonstrate the duplication risk: some Track objectives,
design cards, and guardrails overlap the capability map and durable PRD/Product
TDD. Those claims should be referenced or promoted, not independently owned by
the Track.

### Disposition

`Track` and `Slice` have different jobs here. Admit a Collection Track by
pressure; do not infer that every capability trunk deserves a Track file.

## Case B — Workbench Coding Surface

### Observed structure

Twelve Sub-task directories behave mostly as independently startable delivery
slices with explicit dependencies. Product, architecture, experience, remote
contract, reliability, acceptance, and implementation already have substantive
semantic owner files. Eight Human feedback iterations contain their own phased
correction work.

One early evidence file names Windows, Email, Markdown, Side Chat, and
configuration as “Deferred, Non-blocking Tracks,” but each becomes a later
numbered Sub-task. The term identifies deferred work, not a continuing
cross-slice management owner.

### Counterfactual: Slice only

The slice dependency topology already answers what can start, what returns, and
what later work consumes. Concern coherence is carried by architecture,
experience, remote-contract, and acceptance owners. A future slice references
those owners.

### Counterfactual: Track + Slice

Possible Tracks such as Apple, Windows, Host contract, UX, security, or Email
would largely reproduce either durable/system ownership or the existing
semantic task modules. Most contain one or a short chain of delivery slices,
so Track maintenance adds another status and navigation projection without a
new recurring decision.

### Disposition

Slice-only planning is cheaper for the visible delivery topology. This case is
a counterexample to universal Track activation. A named “deferred track” should
remain a queued Slice or concern label until cross-slice management pressure
actually appears.

## Case C — Surface Camera Development Loop

### Observed structure

The root packet contains 156 instance directories and a very large delegation
table. Many instances are successive implementation, audit, failure, repair,
and re-audit attempts around a smaller number of capability lineages such as A0
control/smoke, target transport, recovery, and evidence publication.

### Counterfactual: Slice only

Each bounded implementation/audit/repair can be a Slice or Assignment return,
related by `repairs`, `audits`, `replaces`, and `depends-on`. This preserves
precise evidence but leaves a Lead to traverse long chains to answer “where is
this capability now?”

### Counterfactual: Track + Slice

A Track per material capability lineage could roll up current frontier,
accepted return, remaining gate, superseded attempts, and the next selection
rule. That could remove substantial history from the Human entry and reduce
Lead recovery cost.

The danger is equally visible: if the Track copies every instance status,
digest, claim, and gate, it becomes another coordination runtime whose
consistency must be verified. It has value only as a compressed projection with
one canonical underlying slice/assignment owner for detailed state.

### Disposition

This case provides strong pressure for a Track-like roll-up, but not for another
Track status tree. The representation and single-owner rule determine whether
management value is positive.

## Cross-Case Result

`Slice` and `Track` are semantically different:

- a **Slice** owns one bounded return and its integration/disposition
- a **Track** owns the task-local continuity and roll-up of one obligation
  across several Slice returns

They are not necessarily different work-decomposition levels. `Slice` is a
work/result primitive; `Track` is an optional management projection over
slices. A Slice may contribute to multiple Tracks, and a Track may remain open
across several phases.

## Track Activation Test

Activate a Track only when all material conditions hold:

1. at least two actual or imminent Slice returns share a continuing obligation
2. the Lead or Human repeatedly needs a cross-slice answer about coherence,
   coverage, accumulated pressure, current frontier, or next selection
3. dependencies, a concern label, and an existing semantic/durable owner do not
   answer that question cheaply
4. the Track has a named consumer and changes a real planning or review decision
5. any cached product/unit truth is selective and distinguishable from the
   task-local delta, while slice-local evidence retains one detailed owner
6. removing it would measurably increase reconstruction, duplication, missed
   conflict, or recovery cost

Representation also grows progressively:

```text
implicit concern
  -> concern label / one plan-map row
  -> Track section with roll-up and next-selection rule
  -> separate Track module only when independent content and cadence justify it
```

Retire the Track when no future cross-slice decision remains; promote stable
truth to its durable owner and keep only the consequential task roll-up.

## Lead Conclusion

Keep `Track` in the candidate common ground, but classify it as an optional
management primitive rather than a default work item or parent of Slice.
Workbench shows that only Slices can be cheaper; InKCre Collection shows Track
can avoid cross-slice reconstruction; Surface Camera shows both its large
potential benefit and its synchronization failure mode.
