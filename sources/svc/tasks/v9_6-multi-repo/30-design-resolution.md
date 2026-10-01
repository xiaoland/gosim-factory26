# Design Resolution

## Resolved Direction

SVC v9.6 should keep multi-repo support small by treating it as an optional extension rather than a new default posture:

1. Mono-repo remains the default startup and default cognitive model.
2. Hub-and-spoke is a physical topology for existing shared layers, loaded only when the repo actually uses it.
3. Spoke execution treats `docs/_shared/` as read-only during ordinary local work.
4. If Spoke execution exposes a shared gap, the agent must first capture local pressure in the Spoke task.
5. Product TDD vs Unit TDD stays separated by authority scope, not by folder proximity.
6. `edit-svc-shared-docs` exists primarily as a submodule safety rail, so Git complexity does not spill into the default framework path.

## Objection 1 Resolution: Preserve Code Pain Before Shared Promotion

The framework now requires a spoke-side capture step before shared-doc mutation.

Minimum capture:

- local code path or seam
- missing shared rule or ambiguity
- local consequence if unresolved
- verification pressure after return

This lets source-first mutation stay intact without losing the concrete evidence that justified the shared change.

## Objection 2 Resolution: Keep 20 vs 30 Sharp

The framework now uses a concise boundary rule:

- if another unit must rely on it to interoperate safely, it belongs in Product TDD
- if one unit can change it without forcing another unit to update, it stays in Unit TDD or local `AGENTS.md`

Minimal examples:

- payload format between two services -> Product TDD
- one service's internal DB table naming -> Unit TDD

## Objection 3 Resolution: Keep Multi-Repo Optional

The framework should be split conceptually into:

- core default: mono-repo-friendly, no mandatory Hub/Spoke mental model
- optional extension: multi-repo topology, shared-doc mutation, and freshness rules
- operational skill: submodule-safe editing and Spoke protection

That keeps the 90 percent path simple while still giving the 10 percent path a full protocol.

## Verification Snapshot

- `pdm run build-monolith` passed after the redesign.
- `pdm run test` passed after the redesign.
- The current draft keeps mono-repo in the default path and moves multi-repo detail into an optional extension plus the dedicated skill.
