# Planning and Dependencies

Begin with the outcome, current design or explanation, applicable constraints, and observations needed to judge completion.
Choose the next coherent return and the action that can produce it; identify its owner, prerequisites, feedback, and consumer when they affect the route.
A short sequence in the packet can be enough.
Plan only as far as current knowledge supports, then state what result or decision makes further planning possible.
When feedback changes a premise, revise the route rather than keeping an obsolete step as a current obligation.

Use the depth below when a task needs more control than one short linear plan.
It defines available management units, not a universal hierarchy or a prerequisite to starting work.
Every admitted unit must lower planning, recovery, coordination, or integration cost compared with leaving it implicit.

| Unit | Management meaning |
| --- | --- |
| **Task** | the complete outcome obligation and packet boundary |
| **Track** | a persistent concern or obligation axis that may advance across several barriers |
| **Phase** | a real shared barrier across an explicitly declared set of Tracks |
| **Cell** | one Track's obligation inside one Phase; the local Plan owner when both axes exist |
| **Plan** | one linear, partial route owned by the Task, a Cell, or another bounded unit |
| **Slice** | an ordered Plan return with a meaningful integration boundary |
| **Step** | a concrete action inside a Slice |
| **Assignment** | bounded work placed with an actor or mechanism; not another planning level |

Track and Phase are optional Task axes.
Track preserves concern continuity; Phase exists only when a shared barrier materially coordinates named Tracks.
A Phase's scope may omit unaffected Tracks.
It exits only when every required Cell in that scope satisfies its obligation; never manufacture a barrier or empty Cell for matrix symmetry.
Refer to a Cell as `<track>-<phase>` or another declared unambiguous handle.

A small Task may own one Task Plan.
Retire that single Plan when Track or Phase topology makes the Task non-linear; each admitted Cell or bounded owner then holds its own linear Plan.
Allow one Plan by default and multiple Plans only when their effects or feedback are independently controllable and their integration relation is explicit.

A Plan is honest about limited foresight.
State the current route, ordered Slices, and a to-be-continued condition where later work depends on evidence or feedback not yet available.
Slice identity is globally ordered within its Plan; an optional return tag follows the number, for example `01-IQ`, `02-DS`, `03-IM`, or `04-VR`.
The tag describes what the Slice returns, not how every Step works and not a separate numbering sequence.

Use relations such as `blocks`, `consumes`, `invalidates`, `integrates into`, or `waits for` only when they change control.
Coordination is this relation view of work topology; it does not require a separate coordination object.

A dependency delays the work that consumes it, not unrelated work by the same coordinator.
When a prerequisite becomes available, revisit work it enables before extending unrelated integration or review.
Choose parallel work when its effects and feedback can remain independent; separate worktrees alone do not make services, mutable data, or computing resources independent.

## Example: Coordinate a Real Dependency

Suppose one task changes a shared configuration format used by an editor and an importer.
A single plan is enough while one owner can make and verify the change coherently.
If the two consumers require independent work, preserve their common dependency explicitly:

```text
Agree on the shared format and compatibility behavior
  ├─ Editor: adapt the UI and its local checks
  └─ Importer: adapt parsing and its local checks
       Both returns → verify the connected import-and-edit journey
```

The editor and importer can become separate work units with their own plans; agreeing on the format is the relevant shared barrier.
Document the format once in [project documentation](../../svc-documentation/SKILL.md), and link each unit to the agreed revision.
While the format is unresolved, unrelated exploration can continue; work that assumes the format waits or remains explicitly provisional.
Use Cells if Track/Phase coordination helps manage these obligations, not because this diagram requires a matrix.
The packet entry only needs the outcome, active owners, dependency state, evidence links, and next action; each owner's detailed notes stay with its work.
