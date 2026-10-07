# Unit TDD and Local Instructions

Unit TDD is an optional owner for expensive internal design truth of one logical technical unit. A unit is a stable responsibility boundary, not a directory name.

Admit Unit TDD only when the truth:

- can change without forcing another unit to update
- describes internal authority, storage, sequencing, naming, technology, or contracts
- should survive physical directory refactors
- is not cheaply preserved by code, types, schemas, tests, or assertions

Cross-unit dependencies belong in Product TDD when its admission rule is met.

## Local `AGENTS.md`

A local `AGENTS.md` is physical, tactical memory for a subtree. Create one only for a repeated fragile seam, non-obvious authority path, dangerous shortcut, or mandatory local verification that nearby instructions are likely to prevent.

It should name scope, invariants, allowed write paths, hazards, recurrence signals, and required checks. It must not restate root policy or become a general architecture document. Use [the local template](../assets/AGENTS.local.template.md).

A Reality lens does not automatically create local instructions. Diagnose the cause first; add a local tripwire only when the diagnosed seam is local and recurrence risk justifies it.
