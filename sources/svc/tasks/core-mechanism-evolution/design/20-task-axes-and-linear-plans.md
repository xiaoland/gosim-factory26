# Working Note — Task Axes and Linear Plans

- **State**: supporting prior model; `D-025..D-028` refine promotion, TBC,
  Task-Plan, and Phase semantics in
  [`21-phase-track-cells-and-partial-plans.md`](21-phase-track-cells-and-partial-plans.md)
- **Sources**: `D-016`, `D-017`, `D-020..D-023`; `V-044`, `V-048..V-051`;
  field counterfactual in [`19`](19-track-slice-counterfactual.md)
- **Use**: Test `Track` and `Phase` as Task decomposition axes, with `Slice`
  and `Step` as the internal building blocks of a linear `Plan`

## Correction: Task-Local Snapshot Is Useful

The previous Track/Slice analysis treated repeated durable product or unit
content too strongly as ownership duplication. A selective task-local snapshot
has positive management value:

- it creates a local working set instead of requiring repeated discovery in
  durable docs
- it can contextualize truth from several owners for one Task or Track
- it can hold candidate durable deltas while discussion and evidence mature

The risk is not repetition itself. The risk is an unbounded, provenance-free
copy whose authority and freshness cannot be understood.

A useful cache distinguishes:

| Content | Meaning |
| --- | --- |
| baseline snapshot | selected durable truth relevant to this task, with owner reference or freshness boundary |
| working delta | proposed or accepted task-local change that is not yet durable truth |
| retired context | detail no longer needed for current control and safe to remove from the working set |

Track may own this selective working set when it reduces cross-Slice retrieval
and synthesis cost. It still should not reproduce the complete product/unit
corpus or make an unlabeled snapshot look like durable authority. Per `D-025`,
promotion targets are not cache metadata; retrospective/consolidation plans
meaningful durable changes only after discovering them.

## Candidate Topology

The proposed model separates Task decomposition from Plan composition:

```text
Task space
  horizontal axis: Track — continuing concern/obligation
  longitudinal axis: Phase — ordered control horizon

Plan(scope, horizon)
  linear route: Slice and/or Step -> Slice and/or Step -> ...
```

`Track` and `Phase` answer where work sits in the Task. `Slice` and `Step`
answer what the current Plan intends to do. `Plan` is the Human-readable route
through part of the Task space.

This is not necessarily a stored rectangular matrix. A simple Task can have one
Plan and no named Track or Phase. Coordinates appear only under management
pressure.

## Meaning of the Two Task Axes

### Track — horizontal decomposition

A Track keeps one continuing obligation coherent across several returns. Peer
Tracks expose materially different directions that can progress partly
independently, compete for attention/resources, or meet at integration points.

Its management value comes from coverage, continuity, task-local snapshots,
cross-Slice pressure, roll-up, and next-selection—not approximate size.

### Phase — longitudinal decomposition

A Phase gives work an ordered control horizon. It answers which class of work
is currently admitted and which exit condition allows the next horizon to
become active.

Its management value comes from limiting active possibility, exposing long
migrations/reviews, and aligning Human expectations. It is not a working
posture, a date bucket, or an automatically linear software lifecycle.

## What “Plan Is Linear” Must Mean

A Plan is a finite ordered projection for one declared scope and evidence
horizon:

```text
Plan P(scope=S, based_on=X)
  item 1 -> item 2 -> item 3
```

The guarantee is:

- one unambiguous current/next item in that Plan
- no hidden branch or unordered sibling inside the Plan
- later items are intentions, not authorization or proof
- new evidence may replace the unexecuted suffix
- a conditional fork ends the current certain route at a decision/gate; the
  selected branch becomes a new linear suffix or Plan after evidence arrives

Linearity belongs to the control projection, not reality. The Task may have
multiple Plans, cross-Plan dependencies, concurrent Tracks, reopened Phases,
and failed/replaced Slices.

## Slice and Step Inside a Plan

| Item | Plan contract |
| --- | --- |
| `Slice` | one bounded return with an integration/disposition target; may own a local linear Plan when its internal control cost justifies it |
| `Step` | one local executable action whose observation is consumed by the owning Plan or Slice and needs no independent integration |

A Plan can operate at different scopes:

- Task plan: the small number of consequential returns Sir should understand
- Track/Phase plan: the current route through one part of Task space
- Slice-local plan: executable refinement needed for Agent recovery or
  delegation

The scope is explicit; these are not three mandatory plan levels.

## Where Non-Linearity Goes

Non-linear structure remains visible without entering the Plan body:

- parallelism: distinct Plans or Track fronts
- dependency: relation between Plan/Slice returns
- convergence: several Slice returns integrate into one later Slice or gate
- feedback: a return reopens an earlier Phase or creates a replacement Plan
- alternatives: captured as a decision problem; only the selected route enters
  a linear Plan
- resource conflict: coordination relation across otherwise linear Plans

This resembles execution control: each route is readable and linear, while the
Task topology may be a graph.

## Rehearsal Against the Field Cases

### InKCre

- Tracks: Collection, Organization, Application are plausible horizontal
  capability directions.
- Phases cannot safely be one global Product/Technical/Execute lifecycle because
  completed Collection units coexist with an Application unit in
  Product/Explore.
- The active implementable unit can have its own ordered gate horizon and
  linear Plan; the program-level Plan can linearly select the next unit return.

Result: the model works if Phase is scoped rather than one mandatory global row.

### Workbench

- Capability/platform concerns form possible Tracks, though existing semantic
  owner modules often make explicit Track activation unnecessary.
- The `00..09` route approximates a linear program Plan, while Windows can
  progress independently after the shared Host contract and Human correction
  iterations reopen earlier design/implementation areas.
- Ordered correction phase folders are local to one acceptance iteration, not
  a global Task phase.

Result: linear Plans are useful; Phase already behaves as a scoped control
horizon. Parallel work must live in another Plan rather than become a branch in
the sequence.

### Surface Camera

- Capability lineages such as A0, target transport, recovery, and evidence are
  plausible Tracks.
- Capability/gate readiness creates longitudinal horizons, but implementation,
  audit, failure, and repair repeatedly reopen them.
- Each bounded implementation/audit/repair chain can be expressed as a linear
  Plan; the large non-linearity is produced by replacement and cross-lineage
  integration relations.

Result: the model can compress the flat instance history, provided a Plan does
not copy all execution/evidence state and Phase reopening remains explicit.

## Main Design Choice: Global or Scoped Phase

### Global Task Phase

One Task-wide current Phase is maximally legible, but falsely synchronizes
Tracks that are at different maturity or control horizons. It fits migrations
with a real global cutover gate, not mixed programs by default.

### Scoped Phase — Lead recommendation

A Phase belongs to a declared scope, usually Task or Track. Task-wide Phase is
used only when one exit condition genuinely gates all material Tracks. This
preserves the longitudinal-axis idea without forcing every Track into the same
row.

## Costs and Guardrails

- Linear Plans may proliferate if every local action creates a new Plan.
- Moving every branch outside the Plan can hide the overall alternatives unless
  the current decision point is visible in `packet.md`.
- Track/Phase coordinates can become taxonomy without management decisions.
- Nested Slice-local Plans need a clear return to their containing Slice.
- Cached durable truth needs selective scope, provenance/freshness, delta
  marking, promotion, and retirement; otherwise locality becomes stale shadow
  documentation.

## Current Lead Recommendation

Adopt the direction provisionally:

1. `Track` and `Phase` are optional Task-space decomposition axes.
2. `Plan` is a linear, revisable control projection for one declared scope.
3. `Slice` and `Step` are Plan-internal work items distinguished by independent
   return/integration value.
4. Task non-linearity lives in multiple Plans and explicit relations, not
   branches hidden inside one Plan.
5. Phase is scoped by default; it becomes Task-global only under a real shared
   exit gate.
6. Task-local selective snapshots and candidate deltas are valid cache content;
   complete shadow copies without provenance or promotion behavior are not.

The smallest unresolved judgment is whether scoped Phase still matches the
intended “longitudinal Task axis,” or whether Sir intends one global Phase
coordinate for the whole Task.
