# Working Note — Task Map and Cell-Owned Files

- **State**: accepted task-local direction through `D-036`; later real-task
  indexing, roll-up, and early-shape cost may reopen it
- **Sources**: `D-027..D-035`; `V-054..V-068`; correction of the former
  `plans/ + tracks/ + phases/` projection in [`24`](24-task-packet-module-grammar.md)
- **Use**: Project the accepted Track/Phase/Cell/Plan semantics into files
  without making Task axes into directories or separating a Plan from its owner

## Correction

The former candidate tree was semantically wrong:

```text
task-map.md
plans/
tracks/
phases/
```

It treated four different things as peer collections:

- Track and Phase are Task-level decomposition axes
- Cell is the derived Track × Phase control unit
- Plan is owned by the applicable Task/Track/Phase/Cell coordinate

When both axes are active, placing Plans in a peer `plans/` directory separates
the current route from the Cell that owns its state, Phase contribution, and
integration. Giving Track and Phase directories by default also mistakes a
classification mechanism for enough persistent content to justify storage.

## Ownership Before Files

The accepted Plan-owner rule remains:

| Active Task topology | Plan owner |
| --- | --- |
| no Track or Phase | Task |
| Track only | each active Track |
| Phase only | each active Phase |
| Track and Phase | each participating Cell |

The file projection must follow this table. A Plan is content of its owner, not
an independently classified task-level collection.

## Shape Activation: Topology, Not File Length

Three activation strategies have different costs:

| Strategy | Benefit | Failure |
| --- | --- | --- |
| universal scaffold at Task start | shape is always predictable | simple Tasks pay for empty/fake structure; early guesses harden into wrong topology |
| wait until files become long | minimum initial structure | LLMs commonly postpone cleanup; late moves break links, mix owners, and repeatedly load/edit irrelevant state |
| stabilize when semantic topology becomes credible | structure appears before substantial work under stable owners | requires one early topology judgment and occasional correction when evidence changes |

The revised recommendation is the third strategy. Start with `packet.md` only
when the work is genuinely still simple/unknown. As soon as the Lead can defend
Track, Phase, and participating Cell semantics—or the request already makes
them obvious—perform a **shape preflight** before detailed Plans and evidence
accumulate:

1. declare the active axes and real participating coordinates
2. choose the corresponding stable Plan-owner entries
3. create those entries immediately, even while a Plan ends at TBC
4. keep later growth local to those owners unless the Task topology materially
   changes

For a Task whose request already exposes several continuing obligations,
barriers, or independently controlled fronts, this preflight occurs at Task
opening. For a deceptively small Task, it occurs atomically with the first
Track/Phase admission. Declaring two-axis topology is incomplete until every
real participating Cell has its owner entry and `packet.md` has the current
Human projection; growth is therefore part of the semantic transition rather
than an optional cleanup reminder.

The trigger is semantic ownership, not current depth. A real Cell already has
an exit contribution, current state, Plan owner, and integration return; that
is sufficient management value for a stable file. This avoids relying on a
future Agent to notice that an inline map needs refactoring.

A task-packet-growth reminder or sub-agent may later audit shape drift, but it
is a secondary detector with delegation/verification cost. The primary method
should make the correct shape the ordinary result of topology admission. A
mechanical rule or linter is only justified later where the contract can be
checked without semantic guessing.

## Human Projection in `packet.md`

When `task-map.md` exists, `packet.md` should contain one compact table or list
that projects the current Task map in the Human-Agent communication language.
It is not a link index. Each row must carry enough integrated meaning for Sir
to switch back to the Task and understand what is moving, waiting, or needs
attention:

```text
| Cell / Plan owner | State against current barrier | Current return / next | Human attention |
```

The projection shows every currently active, blocked, or required-pending Plan
owner whose disposition affects the active barrier or Task outcome. Completed
historical detail is collapsed to the Phase/result level unless it remains
material to a decision or reopening.

Links to `task-map.md` or Cell entries are optional depth. The body still owns
the meaningful status. The update sequence is:

```text
Cell Plan return
  -> Lead integrates Cell and Phase state in task-map.md
  -> consequential one-row/list projection updates packet.md
  -> Human reviews/decides from packet.md
```

Different resolution is intentional: Cell owns executable detail, Task map
owns Agent routing/integration, and `packet.md` owns the Human current picture.

## Minimal Task Map

Once Track or Phase activates, the Task root needs one Agent control surface:

```text
packet.md
task-map.md
```

`task-map.md` owns only the current Task-space projection:

- Track declarations and their continuing obligations
- Phase declarations, scope, entry/exit meaning, and current barrier state
- participating Cell addresses
- current Plan front/return for each Plan owner
- material dependencies, authority boundaries, conflicts, and integration
  relations

Track snapshots and Phase declarations may remain inline while compact. The map
integrates each Plan owner's current front/return but does not own Cell Plan
steps, detailed design, exploration, implementation, verification, assignments,
or completed history.

## Cell Externalization Alternatives

When Track × Phase topology is admitted, three shapes are plausible:

| Shape | Benefit | Cost |
| --- | --- | --- |
| root `cell-<track>-<phase>.md` | no collection directory; coordinate is visible at root | root clutters as Cells accumulate; later grouping moves links |
| `cells/<track>-<phase>.md` | one predictable namespace; scales without moving Cell entries | introduces one directory as soon as real two-axis Cells exist |
| `cells/<track>-<phase>/plan.md` | visibly groups Plan and artifacts | directory-first ceremony; hides the Cell's integrated state and encourages `packet.md` recursion |

The Lead recommendation is the second shape:

```text
packet.md
task-map.md
cells/
  collection-p1.md
  application-p1.md
```

`cells/` is not another semantic module and has no required `README.md` or
`cells.md`. It is the namespace owned by `task-map.md` once real two-axis Cell
topology is admitted. Create one entry for every actual participating Cell at
shape preflight, including a required-pending Cell with a meaningful entry/TBC
condition. Do not create coordinates outside declared Phase scope, empty `N/A`
Cells, or future matrix placeholders.

The exact filename delimiter is local until naming examples establish the most
legible convention. The file title and `task-map.md` must always expand the
semantic address; a Human/Agent never has to infer what `A1` means.

## Cell Entry and Plan

The Cell file is the stable current entry for that control unit and owns its
default Plan:

```text
# Collection × P1

Coordinate / obligation
  Track: Collection
  Phase contribution: evidence-backed collection result required by P1

Current state
  active; baseline B; proof horizon H; material unknown U

Current partial Plan
  Slice C1 -> Slice C2 -> TBC
  continue when: return R

Relations and return
  waits for X; returns Y to P1 barrier; integrates into Z
```

The headings are illustrative. The semantic minimum is:

1. Track obligation and Phase contribution
2. current satisfaction/evidence state
3. current partial linear Plan, including TBC condition when present
4. material authority/dependency/conflict relations
5. expected return and how it changes Cell/Phase state

It does not repeat complete Track/Phase definitions, durable owner contents, or
evidence already owned by a concern module. It links those inputs and keeps only
the selective task-local baseline/delta needed by the current Plan.

## Progressive Cell Depth

The accepted sibling-entry grammar applies inside `cells/`:

```text
cells/
  collection-p1.md          # stable Cell state + default Plan
  collection-p1/
    query-corpus.md          # Cell-owned supporting artifact
    acceptance-receipt.md   # immutable Cell-owned return/evidence
```

The same-stem Cell directory is not created merely because the Cell file exists. It appears
when a Plan Slice, return, immutable receipt, or other artifact has independent
depth and is consumed only through that Cell.

Cross-Cell evidence or a concern with its own consumer/cadence belongs to the
applicable inquiry/design/verification module instead of turning the Cell
directory into a dumping ground.

## Multi-Plan Cell Exception

Under `D-032`, a Cell defaults to one Plan. Only the accepted bounded exception
externalizes multiple independently integratable Plan returns:

```text
cells/
  collection-p1.md          # Cell fronts, conflicts, integration rule
  collection-p1/
    plan-source-route.md
    plan-corpus-route.md
```

The Cell entry remains the owner. Each Plan stays partial and linear. The
directory does not contain a super-Plan, and Plan completion only returns state
to the Cell; the semantic Cell predicate still decides Phase contribution.

If the routes share one aggregate return, they are parallel Assignments under
one Slice and remain in the default Cell Plan rather than becoming files.

## One-Axis Cases

When only Track or only Phase is active, there is no Track × Phase Cell to
materialize, but there is still more than one possible Plan owner. Apply the
same topology-triggered stabilization without inventing peer directories:

```text
# Track-only example
task-map.md
track-collection.md
track-application.md

# Phase-only example
task-map.md
phase-host-readiness.md
phase-target-admission.md
```

These owner entries exist because they own Plans, not because every Track or
Phase classification deserves a file. No `tracks/`, `phases/`, or `plans/`
directory is pre-approved. If many one-axis owner entries recur, field evidence
may later justify a namespace or reveal that another axis/Task boundary is
missing.

The no-axis case remains `packet.md` with an inline Task Plan or `plan.md` when
that one Plan needs a stable entry.

## Indexing, Reading, and Mutation Cost

Topology-triggered owner files add paths and roll-up updates, but after multiple
Plan owners exist they reduce three recurring Agent costs:

- targeted retrieval loads one owner/Plan instead of every Cell's steps
- mutation touches one stable state owner instead of editing a shared map
- delegation/resumption can project one Cell without copying unrelated routes

The Task map still provides one bounded join point, and `packet.md` provides one
Human projection. This is cheaper than either a monolithic map or independently
navigated Cell files with no roll-up.

The main new failure risk is roll-up drift. The ownership rule bounds it: Cell
entry owns Plan truth; `task-map.md` owns integrated fronts/barriers;
`packet.md` owns only consequential Human projection. A contradiction is fixed
from the deeper owner outward rather than choosing among peers.

## Relation to Concern Modules

Task map/Cell files answer **where work is controlled and integrated**. Concern
modules answer **what evidence, design, state transition, verification, or
retrospective meaning has depth**.

One artifact has one owner:

- a design alternative belongs to the design module; the Cell consumes its
  selected return
- a verification receipt belongs to the verification module unless it is
  immutable evidence used only by one Cell
- an implementation Slice is planned by the Cell but may link an
  implementation dossier for detailed state-transition reasoning
- an Assignment return changes the owning Slice/Cell only after Lead
  integration

This prevents `task-map.md`, Cell files, and concern modules from maintaining
three copies of progress.

## Rehearsal

### InKCre

The three continuing obligations and active implementable unit can be projected
compactly in a Task map. Existing Track files demonstrate the retrieval/edit
benefit of stable owner entries, while their directory remains a local choice
rather than evidence that all SVC Tasks need `tracks/`. A future cross-Track
Phase would create its real participating Cell entries at Phase admission.

### Workbench

An acceptance Iteration can define a Phase/barrier and affected capability
Tracks. A correction folder is not automatically a Cell; the Cell owns the
Plan that may include diagnosis, repair, rerun, and acceptance Slices. This
would reduce the ambiguity where “Phase 06 reopened” and “Phase 07 repair” act
like peer lifecycle states despite serving one unsatisfied acceptance horizon.

### Surface Camera

A host-only admission Phase could expose Receiver and Evidence Cells. The
receiver repair/audit attempts remain Plan Slices until the unchanged barrier
passes. The two child auditors that jointly produce one aggregate certificate
are Assignments within the appropriate Cell Plan, not independent Cell Plans or
nested Task packets merely because two Agents run.

### This Design Task

At the time of this note, the packet still projected one foreground discussion
route and had not tested whether its five functional clusters were continuing
work obligations. The later full-packet dogfood in `V-091` admitted those five
clusters as task-local Tracks under one real Capability Model Phase and created
`task-map.md` plus five Cell owners. This earlier conclusion is retained as
evidence of late topology recognition, not as current Task state.
`design.md` is an information-module entry, which demonstrates that
semantic breadth alone should not activate work-topology files.

## Failure Modes and Falsifiers

- `task-map.md` can become a monolith if it copies Plan steps and module
  evidence instead of current fronts/relations.
- `cells/` can become a mandatory matrix if Agents create undeclared or future
  coordinates instead of only real Phase participants.
- Cell directories can become nested packets or generic artifact dumps.
- Early shape inference can be wrong and require owner/path supersession.
- Root owner-named one-axis files may clutter or become inconsistent if many
  are needed.
- A fixed coordinate filename can become stale when Track/Phase scope is
  materially redefined; semantic identity and supersession must remain clear.

Reopen `cells/` as the recommended namespace if real packets usually have only
one Cell and root `cell-*` files remain more legible, or if Cell entries
repeatedly need directory-first structure. Reopen topology-triggered shape
stabilization if early misclassification/migration costs more than the indexing,
editing, and recovery cost it prevents.

## Lead Recommendation

1. Project `task-map.md` into one meaningful table/list in `packet.md` whenever
   work topology activates; do not make the Human follow an index.
2. Stabilize the packet shape when semantic topology is admitted, not when
   files later become long or an Agent remembers to reorganize them.
3. Keep Track and Phase declarations/caches in `task-map.md` by default; they
   are axes, not automatic directories.
4. Keep the Plan inside its semantic owner; never create a peer `plans/`
   directory by default.
5. When both axes are active, create `cells/<track>-<phase>.md` for every real
   participating Cell at shape preflight, even when its partial Plan ends TBC.
6. Let the Cell entry own its default partial linear Plan and use the sibling
   Cell directory only for pressure-created artifacts or the bounded multi-Plan
   exception.
7. Give one-axis Plan owners stable root entries at the same topology trigger;
   defer a universal collection namespace until repeated field pressure
   justifies one.

This projects the accepted topology directly: Human sees one compact map,
Task axes live in the Agent map, and each Plan starts in the stable entry of its
current semantic coordinate before substantial task state accumulates.
