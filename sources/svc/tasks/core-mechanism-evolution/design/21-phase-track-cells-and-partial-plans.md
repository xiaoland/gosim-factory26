# Working Note — Phase/Track Cells and Partial Linear Plans

- **State**: accepted task-local direction through `D-029`, `D-030`, and
  `D-032`; Cell-internal parallelism is accepted in
  [`22`](22-cell-internal-parallelism.md), while Phase overlap/reopening is
  developed in [`23`](23-phase-overlap-and-reopening.md)
- **Sources**: `D-025..D-028`; `V-052..V-055`; prior model in
  [`20`](20-task-axes-and-linear-plans.md)
- **Use**: Remove the false global Task Plan, admit honest continuation
  boundaries, and test scoped Phase barriers over Track/Phase Cells

## Corrections

### Promotion work belongs in a Plan

Track and other non-Plan packet modules may cache the relevant baseline and
working delta. They do not maintain a `promotion target` field or a list of doc
paths. Promotion is discovered during retrospective/consolidation and becomes
planned work only when there is an actual semantic change to integrate.

A useful promotion Plan item says what accepted truth changes, why, from which
evidence, and how competing/stale truth will be reconciled. A file path alone
does not create management value.

### Plan is linear but incomplete

Limited foresight makes a complete route dishonest. A Plan owns only the
currently justified linear prefix and may stop with `to-be-continued` (`TBC`):

```text
Slice A -> Step B -> Slice C -> TBC
                                reason: unresolved contract X
                                continue when: evidence/decision Y returns
```

The Plan may include a coarse continuation outline, but uncertain future work
is not presented as ordered committed items. `TBC` is a terminal Plan state at
the present knowledge horizon, not a fake work item or failure.

### Large Task has no Task Plan

A Task Plan is available only while the Task remains simple enough that one
linear route faithfully represents it. Activating either Track or Phase admits
that the Task topology has outgrown one line; the root then owns a Task map,
current fronts, and consequential roll-up—not a global Plan.

Plan ownership grows as follows:

| Activated topology | Linear Plan owner |
| --- | --- |
| neither Track nor Phase | Task |
| Track only | each active Track |
| Phase only | each active Phase |
| Track and Phase | each active Track × Phase Cell |

`Next Step` in root `packet.md` remains the next Human/Lead coordination action;
it does not imply a Task Plan.

## Scoped Phase Barrier

A Phase declares the Tracks whose contributions are required for its exit:

```text
Phase P1
  scope = {Track A, Track B, Track C}

  Cell A1 = Track A × Phase P1
  Cell B1 = Track B × Phase P1
  Cell C1 = Track C × Phase P1
```

Each Cell owns the bounded current state and linear Plan for one Track's
contribution to that Phase. Tracks can progress asynchronously inside P1. The
Phase exits only when every required Cell satisfies its declared exit
contribution:

```text
exit(P1) iff every Cell(track in scope(P1), P1) satisfies P1.exit
```

A `TBC`, blocked, or merely inactive Cell does not satisfy the barrier. Human
may explicitly change Phase scope or exit meaning when evidence changes, but
the Lead cannot silently treat unfinished work as phase completion.

Tracks outside the declared Phase scope do not need empty or `N/A` Cells. This
preserves progressive activation and avoids a ceremonial full matrix.

## What Cell Is

Cell is a derived coordinate and management unit, not an approximate-size work
level:

- Track supplies the continuing obligation
- Phase supplies the current control horizon and exit predicate
- Cell supplies one address for their intersection
- the Cell's Plan supplies the current linear route
- Slices/Steps supply the work and observations

Prefer a semantic address such as `Collection × P1` or `Collection-P1`.
`Cell A1` is acceptable only when the packet locally maps `A` and `1`; Human
must never infer anonymous coordinates.

A Cell need not be a directory. It can begin as a matrix entry or section and
gain a local Plan file only when recovery, delegation, or evidence pressure
justifies it.

## Revised Topology

```text
Task
  Task map / current fronts / Human roll-up

  Tracks (horizontal continuing obligations)
      ×
  Phases (scoped longitudinal barriers)
      =
  Cells (addressable control units)
      -> each Cell has at most one current linear Plan by default
          -> Slice / Step / ... / TBC or Complete
```

Task non-linearity is represented by multiple active Cells and the material
relations between their returns. Plan linearity is preserved inside each Cell.

## Rehearsal Against the Cases

### InKCre

A Phase such as “close the first collection-to-use loop” could scope Collection
and Application. The Collection Cell may finish earlier while Semantic
Retrieval remains active in the Application Cell. P1 does not exit until both
contributions meet the shared outcome gate. Organization need not receive an
empty Cell if it is not required.

This is more faithful than calling Product/Technical/Execute global phases.
Phase names an outcome/control horizon, not a posture or maturity label.

### Workbench

Before Track/Phase pressure, the initial `00..04` core vertical can be a Task
Plan. Once platform/capability Tracks and Human acceptance Phases become
material, the root should stop maintaining a synthetic `00..09` global plan.
Each correction iteration can define a Phase scope and Cells only for affected
Tracks; its phase exit waits for every required acceptance contribution.

### Surface Camera

Capability lineages form Tracks; a host-only readiness or target-admission
Phase can require specific capability/evidence Tracks. Implementation, audit,
and repair routes remain Cell-local linear Plans. A failed audit reopens the
Cell and therefore the Phase barrier instead of appending another apparent
global Task-plan item.

## Benefits

- Human can address one unit (`TrackA-Phase1`) without reading the whole graph.
- Linear Plan remains honest and locally controllable.
- Phase creates a real aggregate completion rule instead of a decorative label.
- Tracks may advance asynchronously without producing ambiguous global phase
  completion.
- TBC prevents fabricated foresight while preserving a known continuation
  condition.
- The root packet can stay a short control surface rather than a monolithic
  global schedule.

## Risks and Open Semantics

- A strict barrier can unnecessarily idle a completed Track when safe later
  work could begin. A Phase should exist only when the shared barrier has net
  management value; otherwise use separately scoped Phases.
- Overlapping Phase scopes may create difficult partial orders. Start with one
  active Phase per Track unless a real case requires more.
- A Cell with internally parallel work may exceed one linear Plan. First test
  whether it should split a Track/Cell or sequence bounded returns; do not
  silently turn its Plan into a DAG.
- Phase exit must describe an outcome/evidence condition, not “all Plans say
  done.”
- Cell roll-up can duplicate Slice evidence if it becomes a detailed status
  ledger rather than a control projection.
- TBC needs a continuation condition; a bare “later” marker gives no recovery
  value.

## Accepted Direction and Open Edge

The following task-local structure is accepted:

1. simple Task may own one linear Task Plan
2. activating Track or Phase retires the Task Plan in favor of the Task map
3. Track and Phase form horizontal and scoped longitudinal Task axes
4. their participating intersection is an addressable Cell
5. each active Cell owns one current linear, partial Plan by default
6. Plan contains Slice/Step work and may end honestly at `TBC`
7. Phase exits only after all required Cells satisfy the semantic exit predicate
8. promotion appears only as retrospective/consolidation Plan work, never as a
   generic Track/cache target list
9. Phase exists only for a real shared barrier; matrix completeness has no
   management value

The default Cell Plan contract is accepted by `D-032`. Active Phase overlap and
reopening semantics are the current edge in
[`23-phase-overlap-and-reopening.md`](23-phase-overlap-and-reopening.md).
