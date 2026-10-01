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

## Example: Complexity Introduced by a Product Assumption

Suppose the requirement is to restore a user's saved preference at the next login.
A proposal adds live synchronization across every open tab, then accumulates conflict rules and retries when two tabs write at once.

```text
Observed conflict
  → Which promise requires live synchronization?
      → No such promise: reconsider the added behavior before building coordination.
      → It is required: define conflict semantics, state ownership, and evidence first.
```

Removing an unneeded live-sync obligation can eliminate the race without another abstraction.
It does not remove the actual persistence obligation or permission to ignore explicit concurrency requirements.
If live synchronization is required, a single authority for accepted updates and a defined conflict policy may simplify the design, but must be checked against the actual use cases.
Use this reasoning when complexity grows; it is not a default preference against concurrent features.
