# v9.6 Multi-Repo Task Packet

## MVT Core

- Objective & Hypothesis: Define SVC v9.6 so multi-repo support remains available, but mono-repo stays the default experience and does not inherit unnecessary Hub/Spoke cognitive load.
- Guardrails Touched: Input type decides durable ownership; tasks absorb volatility before promotion; multi-repo topology must not collapse Product TDD and Unit TDD into one bucket; optional extensions must not contaminate the default path.
- Verification: The resulting v9.6 design must explain where shared truth lives when multi-repo is enabled, how spoke agents read it, how shared-doc edits flow source-first, how freshness is enforced, how `20-product-tdd` stays distinct from `30-unit-tdd`, and how mono-repo users avoid extra default burden.

## Exploration Scaffold

- Perturbation: SVC needs a v9.6 release that supports multi-repo systems without copy-pasted product memory or unsafe cross-repo edits.
- Input Type: Intent with Constraint sub-problems.
- Active Mode or Transition Note: Explore first; do not promote into `src/` until the shared/local boundary, optional-extension strategy, and mutation protocol are explicit.
- Governing Anchors: `AGENTS.md`, `src/index.md`, `src/sections/filesystem.md`, `src/sections/meta-engine.md`, `src/sections/ontology.md`, `src/sections/product-tdd.md`, `src/sections/tasks.md`.
- Impact Hypothesis: The change will affect framework topology, task containment, product-tdd authority, root AGENTS templates, mode SOP templates, and the dedicated shared-doc skill.
- Temporary Assumptions: `git submodule` is the default reference transport, but the framework should encode invariants rather than overfit to one project-specific workflow detail; multi-repo should be loaded only when needed.
- Negotiation Triggers: Pause if the proposal weakens readability, overfits to `core-py`, cannot clearly separate shared cross-unit truth from spoke-local design truth, or adds `docs/_shared/` assumptions to mono-repo defaults.
- Promotion Candidates: Optional multi-repo topology guidance, shared-doc mutation protocol, shared/local admission gate, task-routing rules for hub versus spoke volatility, and a submodule-safety skill.

## Execution Notes

- key findings: Current v9.5 lacks an explicit hub/spoke topology, a shared-doc mutation protocol, a freshness contract, and a multi-repo interpretation of the `20-product-tdd` versus `30-unit-tdd` boundary, but it already works well as a mono-repo default.
- decisions made: Capture the current synthesis and objections inside this task container before further framework edits, and reframe multi-repo as an optional extension rather than a universal default.
- final outcome: Redesign implemented; pending commit and later prose-tightening pass.
