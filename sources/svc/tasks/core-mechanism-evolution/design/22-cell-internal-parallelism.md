# Working Note — Cell-Internal Parallelism

- **State**: accepted task-local direction through `D-032`; later execution
  evidence may reopen the bounded exception
- **Sources**: `D-029..D-031`; `V-055..V-059`; real packet structures in
  InKCre, Workbench Coding Surface, and Surface Camera
- **Use**: Preserve linear Plan semantics while admitting only parallelism that
  has positive management value and does not hide a wrong Task decomposition

## Parallelism Is Not One Thing

The same word can describe different control topologies:

1. several executors perform parts of one return
2. several independent returns converge into one acceptance
3. several independently integratable returns progress concurrently inside the
   same semantic Cell
4. work was placed in one Cell even though it belongs to different Track or
   Phase coordinates
5. tools happen to run concurrently without any task-management consequence

Only the third case creates real pressure for multiple Plans in one Cell. The
others belong to Assignment, Slice integration, axis correction, or ordinary
execution scheduling.

## Field Case A — Surface Camera: One Slice, Parallel Assignments

The `target-transport-receiver-publication-repair-v4-audit` instance registered
two independent child auditors:

- source/Linux semantics
- coverage/evidence

Host-only consumption required both child terminal `PASS` returns plus parent
rechecks and an aggregate verdict. Neither child independently authorized
consumption; the meaningful return was the joined audit certificate.

Candidate interpretation:

```text
Cell Plan
  -> Slice: produce aggregate receiver-consumption audit
       Assignment A: source/Linux audit
       Assignment B: coverage/evidence audit
       Join: parent integration and aggregate verdict
```

The children need bounded context, authority, certificates, and independent
verification. They do not need separate Plans because there is one Slice return,
one acceptance, and one integration owner.

This is a concrete proof-carrying delegation shape: parallel executors are
untrusted producers of bounded evidence; the parent Slice owns the proposition
and aggregate acceptance.

## Field Case B — Workbench: Parallelism Reveals Different Tracks

After the shared Host contract, Windows Host work could proceed while the iPad
route continued through macOS Host and controller capabilities. Each returned
an independently useful platform result and remained coherent under a different
platform/capability obligation.

Candidate interpretation:

```text
Windows Track × current Phase -> Windows Cell Plan
Apple/controller Track × current Phase -> Apple Cell Plan
```

Putting both in one Cell and adding two Plans would hide the horizontal
decomposition already present in their ownership, dependencies, acceptance, and
future evolution.

## Field Case C — Workbench S01: An Over-Broad Slice

Sub-task 01 explored Core, Apple, Thread, Config, Windows, and Email concerns.
Its Stop Line explicitly separated which evidence unblocked S02–S08 and allowed
non-blocking concerns to defer. The later task topology assigned those returns
to different capability slices.

This was useful early inquiry, but as a stable planning shape it mixes several
future consumers and independently meaningful returns. Under the candidate
model, first use parallel Assignments only while uncertainty makes the shape
unknown; once the return topology becomes visible, split the continuing
obligations into Tracks/Cells or independently returnable Slices. Do not keep a
permanent “exploration Cell with six Plans.”

## Field Case D — InKCre: Counter-Pressure

The current knowledge-lifecycle program maintains one active implementable unit
and one foreground Technical question. It has many design concerns but no
visible task-management evidence that they require independently active Plans.
Parallel research or review can return into the current design Slice through
Assignments.

This case supports the default: semantic breadth or many documents do not by
themselves activate multiple Plans.

## Decision Procedure

When parallel work appears inside one Cell, ask in order:

### 1. Does all work contribute to the same Cell exit obligation?

- **No**: Track/Phase scope is wrong. Re-coordinate the work before adding
  Plans.
- **Yes**: continue.

### 2. Is there one meaningful aggregate return and integration owner?

- **Yes**: use one Slice with parallel Assignments and an explicit join/
  verifier. Keep one Cell Plan.
- **No**: continue.

### 3. Can each return be independently accepted, rejected, parked, or
integrated?

- **No**: it is still one Slice or execution scheduling.
- **Yes**: continue.

### 4. Does a return represent a continuing obligation beyond this Cell?

- **Yes**: create/refine a Track rather than a second Cell Plan.
- **No**: continue.

### 5. Does concurrency materially reduce elapsed time, context interference,
or risk enough to repay integration and synchronization cost?

- **No**: sequence the Slices in one linear Plan.
- **Yes**: admit multiple current linear Plans inside the Cell as an exception.

## Multiple Plans as a Bounded Exception

A Cell owns one current Plan by default. Multiple Plans are allowed only for
several independently returnable routes that share the same Track obligation
and Phase exit, have no more truthful axis split, and benefit materially from
concurrency.

```text
Cell Collection-P1
  Plan P-a: Slice A -> TBC
  Plan P-b: Slice B -> Step B2

  Cell integration:
    consumes P-a return and P-b return
    checks conflicts/shared targets
    evaluates the semantic Phase-exit contribution
```

Each Plan remains linear and partial. The Cell owns only the current Plan fronts,
material relations/conflicts, and integration rule—not a super-Plan that orders
the Plans or duplicates their detail.

Plan completion is not Cell completion. Returned Plans update Cell state; the
Cell satisfies its Phase contribution only when the semantic exit predicate is
observed.

## Assignment Is Not Plan

Assignment relates an executor to one Slice/Step under bounded context,
authority, expected return, proof, and escalation. It may fan out many Agents or
tools without changing Plan topology:

```text
Plan -> Slice
          |- Assignment explorer
          |- Assignment verifier
          `- Assignment executor
       -> Lead integration -> one Slice disposition
```

Create another Plan only when the returned work itself has independent
integration and control—not because another Agent exists.

## Progressive Representation

```text
incidental concurrency
  -> no packet state

one joined return
  -> Slice-local Assignment list / verifier rule

several independent concurrent returns in one true Cell
  -> compact Cell Plan map + material relations

substantial independent content/cadence
  -> separate Plan files under the Cell owner
```

Root `packet.md` exposes only consequential active Cells and Human decisions. It
does not list every Assignment or Plan lane.

## Failure Modes

- Splitting Track whenever two Agents run would turn execution scheduling into
  semantic topology.
- Hiding independently useful returns under one aggregate Slice makes failure,
  acceptance, and integration dishonest.
- Multiple Plans can recreate a local DAG and synchronization system.
- A broad Cell may avoid necessary Track decomposition by claiming every route
  shares one Phase exit.
- A forced single Plan may serialize safe high-value work and waste Agent
  context isolation.
- Parallel Assignments without one integration owner recreate the sub-agent
  trust paradox at the Cell boundary.

## Falsifiers

Reopen the default when real Cells repeatedly require concurrent independent
returns and the decision procedure either creates artificial Tracks or serializes
material safe work. Reopen multiple-Plan admission when Humans cannot predict
which Plan return changes Cell state, or Lead synchronization cost approaches
the work saved by concurrency.

## Accepted Contract

1. Keep one current partial linear Plan per Cell as the default.
2. Treat executor/sub-agent parallelism as Slice/Step Assignments when one
   aggregate return and integration owner exist.
3. Correct Track/Phase decomposition when parallel returns expose distinct
   continuing obligations or exit horizons.
4. Allow multiple current linear Plans in one Cell only for independently
   integratable returns sharing one true Cell, after an explicit concurrency
   benefit and integration/conflict rule are visible.
5. Never introduce a parallel-group Plan item, DAG Plan, or Cell super-Plan;
   non-linearity remains between linear Plans and is owned by the Cell.

Sir accepted this contract as `D-032`. It retains Plan linearity without
serializing every useful concurrent return, and it gives sub-agent
orchestration a later, precise attachment point:
Assignment under a Slice, not Agent identity as Task topology.
