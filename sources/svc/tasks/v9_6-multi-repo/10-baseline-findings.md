# Baseline Findings

## What v9.5 Still Cannot Explain

v9.5 already explains typed ownership and pacing layers, but it does not yet explain how those truths survive repo boundaries.

Current gaps:

- where shared slow truth should physically live in a multi-repo topology
- how a spoke agent should consume shared truth without leaving the local worktree
- what exact boundary separates shared Product TDD from spoke-local Unit TDD when physical repos diverge
- how a shared-doc edit should be sequenced so the source repo stays authoritative
- how shared-doc freshness should be preserved without relying on human memory

## What The Live Reference Case Proves

The `InKCre/core-py` reference case is useful because it does not stop at folder layout. It makes the operational boundary explicit.

Evidence snapshots:

- `tasks/product-docs-repo-submodule/00-phase-map.md` shows that transport, reliability, and mixed-doc splitting had to be decided separately.
- `tasks/product-docs-repo-submodule/20-phase-1-source-boundary.md` shows that shared-doc export needs an allowlist boundary, not a vague "anything cross-repo" rule.
- `tasks/product-docs-repo-submodule/30-phase-2-strategy-decision.md` shows that `git submodule` was chosen as a transport strategy after evaluating rollback, reproducibility, and operator error surface.
- `tasks/product-docs-repo-submodule/40-phase-3-submodule-reliability-pack.md` shows that submodule alone is not enough without SOP, checks, and CI guardrails.
- `docs/_shared/00-meta/skills/edit-shared-docs/SKILL.md` shows the need for an explicit shared-vs-local admission decision before any promotion into shared docs.

## Candidate v9.6 Core Rules

The current leading model is:

1. Hub-and-spoke topology is a physical deployment of existing layers, not a new layer.
2. Shared truth is authored once in the Hub and consumed locally in the Spoke through a nearby mount such as `docs/_shared/`.
3. Shared promotion requires an admission gate before mutation: "is this truly shared, or only locally painful?"
4. Shared-doc mutation follows source-first sequencing: capture spoke evidence, update Hub truth, then update Spoke pointer.
5. Freshness must be machine-verifiable.

## What Should Not Become Framework Law

Some details from the reference case are implementation tactics, not durable framework rules:

- one specific git remote URL or org naming convention
- repo-root skill wrappers used only for one tool's auto-discovery behavior
- one shell script shape or one CI vendor syntax
- one commit message convention for pointer bumps

SVC v9.6 should preserve the invariant and let concrete repos implement it locally.
