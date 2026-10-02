# Planning Topology

Use this depth when a Task needs more control than one short linear Plan.
It defines shared management units, not a universal hierarchy.
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
