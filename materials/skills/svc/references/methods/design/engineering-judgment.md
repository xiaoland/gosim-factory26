# Engineering Judgment

Use this guidance when a choice changes state ownership, dependencies, boundaries, or the cost of understanding and changing the system.
A mechanical change with an obvious owner needs less analysis.

## Make Responsibility Clear

Give each durable fact and state transition one authoritative owner.
Treat caches, views, and generated output as derived unless the requirement makes them authoritative.
When a copy saves real cost, make its source and freshness clear.
Keep submitted input distinct from facts controlled elsewhere, such as price or eligibility.

Use consistent names for the same concept.
Put coherent complexity behind a small interface when callers would otherwise repeat partial knowledge.
Choose data shapes and ownership that make valid behavior natural.
Handle invalid input and failures at meaningful boundaries rather than duplicating guards across consumers.

## Reconsider Growing Complexity

When timing fixes, retries, or exceptions keep exposing new edge cases, restate the product outcome and its necessary constraints.
Check whether the difficult obligation is a real requirement or a commitment introduced by the current solution.
If it is unnecessary, removing that commitment may remove the problem.

If the obligation remains, examine state authority, resource lifetime, ordering, and responsibility across components before adding another mechanism.
For example, two components independently controlling the lifetime of one resource may need one owner rather than more timing coordination.
Some requirements genuinely need complex coordination; retain it when simpler arrangements cannot satisfy the actual constraints.

Make each layer, state holder, dependency, or special case justify its cost with a concrete behavior or expected change.
Prefer structures that are easy to understand and change over either minimum line count or speculative flexibility.
Use measurements when an uncertain performance constraint drives the choice.
