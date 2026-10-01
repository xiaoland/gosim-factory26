# User Objections And Open Design Pressure

## MVT Core

- Objective & Hypothesis: Preserve the user's current objections as first-class design pressure so v9.6 does not solve multi-repo cleanliness by breaking real agent workflows.
- Guardrails Touched: Do not trade maintainability for tidy theory; do not let physical repo boundaries redefine durable ownership incorrectly.
- Verification: The final v9.6 proposal must answer each objection with a concrete rule, pause point, or routing mechanism.

## Objection 1: Mid-Execution Shared Truth Discovery

Observed pressure:

- A spoke-side agent may be implementing code, hit a concrete pain point, and discover that PRD or shared cross-unit guidance is incomplete.
- Forcing an immediate switch to a separate hub-repo workflow risks losing the exact code-local evidence that revealed the gap.

Design pressure on v9.6:

- The framework needs a handoff step that preserves the code-local trigger before shared-doc mutation begins.
- Source-first mutation must stay intact, but the transition from spoke execution into shared-doc solidification cannot depend on agent memory alone.

Questions to resolve:

- What minimal local capture is required before leaving the current spoke slice?
- Does the shared-doc protocol need an explicit pre-pause note inside the active task packet?
- How should local execution resume after the shared change without mixing commits?

## Objection 2: `20-product-tdd` Versus `30-unit-tdd` Becomes Easier To Misplace

Observed pressure:

- In single-repo work, the boundary between Product TDD and Unit TDD can be fuzzy but still recoverable.
- In multi-repo work, the physical isolation makes it easier for an agent to store cross-service payload contracts in spoke-local `30-unit-tdd`, or to move spoke-internal naming rules into hub-level `20-product-tdd`.

Design pressure on v9.6:

- The framework needs sharper placement tests for cross-unit versus unit-local truth.
- Multi-repo guidance should include explicit anti-examples, not just folder names.

Questions to resolve:

- What exact test distinguishes a cross-unit payload contract from an implementation detail of one unit?
- When a truth is read by multiple repos but authored by one unit, does that make it shared or still local?
- Should v9.6 define a shared-admission gate before a statement can move from spoke-local design into hub-owned Product TDD?

## Objection 3: Multi-Repo Must Not Burden Mono-Repo Users

Observed pressure:

- Not all target users manage multiple units through multi-repo.
- If v9.6 makes Hub/Spoke, `docs/_shared/`, and shared-ref mutation part of the default mental model, mono-repo users pay ongoing cognitive cost for a minority scenario.

Design pressure on v9.6:

- Multi-repo should exist as a pressure-driven optional extension, not as the default startup shape.
- Core templates and default reading order should stay mono-repo-friendly unless the repo actually opts into the extension.
- The operational complexity of submodule-safe editing should be absorbed mainly by a dedicated skill, not by the default framework prose.

Questions to resolve:

- Which multi-repo rules belong in core as tiny extension pointers, and which belong only in extension guidance?
- Which templates should remain clean for mono-repo users?
- How much of the submodule workflow should move from framework prose into `edit-svc-shared-docs`?

## Working Criteria For The Next Iteration

- Preserve code-local evidence before any required repo switch.
- Keep shared/local mutation order auditable.
- Clarify authority using scope and dependency direction, not filesystem convenience.
- Add only the minimum durable rules needed to prevent repeated placement mistakes.
- Keep mono-repo as the default low-friction path.
