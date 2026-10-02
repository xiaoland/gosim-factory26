# Technical Design

Use Technical Design to decide how the system will realize the intended behavior and remain understandable and changeable.
Trace the relevant existing implementation, state owners, dependencies, and lifecycle before choosing a new structure.
Check actual interface definitions and documentation for the versions in use; do not base compatibility on remembered APIs.
Route unresolved facts that could overturn implementation to an early [spike](../implementation/index.md#resolve-unknowns-that-could-change-the-route).

Model ordering, concurrency, failure, recovery, and performance where they can change the design.
Keep ordinary changes near the responsibility they affect.
When a change crosses boundaries, make affected consumers, compatibility, migration, and observation needs explicit.
Use [Engineering Judgment](engineering-judgment.md) to assess state authority, boundaries, and the cost of added complexity.
