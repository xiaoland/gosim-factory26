<!-- Create only after real Track/Phase topology is admitted. Do not create for a linear one-owner Task, parallel assignments without a shared barrier, or filename-derived hierarchy. This file owns integrated routing, not detailed Plan state. -->
# Task Map: <Task>

## Admitted Tracks and Phases

<!-- Declare only semantic axes with continuing obligations or real shared barriers. -->

- Tracks: <admitted horizontal obligations>
- Phases: <admitted scoped barriers>

## Current Barrier

<!-- State the barrier that currently governs integration or phase exit. A missing barrier is a reason not to create this map. -->

- Barrier: <state, predicate, and owner>
- Exit condition: <observable condition>

## Participating Plan Owners / Cells

<!-- List every real participating owner or Track × Phase Cell, including one whose Plan currently ends TBC. -->

| Plan owner / Cell | Obligation or contribution | State | Return needed |
| --- | --- | --- | --- |
| | | | |

## Current Fronts

<!-- Show the active front at each admitted coordinate; link to the owner entry rather than copying its detailed route. -->

| Owner / Cell | Current front | Next integration point |
| --- | --- | --- |
| | | |

## Material Relations

<!-- Record only relations that alter ordering, ownership, or integration. -->

- Depends on: <decision, evidence, or external boundary>
- Integrates: <Plan/Cell returns>
- Feeds: <next barrier or consumer>
