# Technical Design

Use Technical Design to decide how the system will realize the intended behavior and remain understandable and changeable.
Trace the relevant existing implementation, state owners, dependencies, and lifecycle before choosing a new structure.
Check actual interface definitions and documentation for the versions in use; do not base compatibility on remembered APIs.
Route unresolved facts that could overturn implementation to an early implementation spike.
When a behavior matters to the product decision, design how its relevant state can be constructed, observed, and reset.

Model ordering, concurrency, failure, recovery, and performance where they can change the design.
Keep ordinary changes near the responsibility they affect.
When a change crosses boundaries, make affected consumers, compatibility, migration, and observation needs explicit.
For a shared contract, agree on the smallest usable shape and publish it where consumers can use it before parallel implementation depends on it.
Use [Engineering Judgment](engineering-judgment.md) to assess state authority, boundaries, and the cost of added complexity.
Treat verification cost as a design constraint when it changes state ownership, resource lifetime, or the choice between local and integrated boundaries.
