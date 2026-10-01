# v9.6 Multi-Repo Task Packet

## MVT Core

- Objective & Hypothesis: Define SVC v9.6 so mono-repo remains the default mental model, while multi-repo exists as a pressure-driven optional extension with explicit shared/local ownership, source-first mutation, and freshness rules. Hypothesis: v9.5 can absorb multi-repo without adding a new truth layer and without imposing Hub/Spoke cognition on mono-repo users.
- Guardrails Touched:
  - Keep typed ownership intact; multi-repo changes physical topology and execution protocol, not the durable truth taxonomy.
  - Do not centralize spoke-local implementation details into shared docs, and do not smuggle cross-repo contracts into spoke-local docs.
  - Do not add daily cognitive overhead to mono-repo users just to support a smaller set of multi-repo teams.
- Verification:
  - The task produces a file-level v9.6 rollout plan with a clear durable owner for each new rule.
  - The task resolves the current objections with explicit protocol adjustments or boundary tests.
  - The task explains how multi-repo stays progressively loaded rather than silently becoming the default framework posture.
  - The eventual implementation can regenerate `build/monolith.md` and keep tests passing.

## Exploration Scaffold

- Perturbation: The user wants SVC v9.6 to support multi-repo systems and provided both a proposed architecture and a live reference case in `InKCre/core-py`.
- Input Type: Intent
- Active Mode or Transition Note: Explore now; move to Solidify only after shared/local admission rules and spoke interruption flow are clear.
- Governing Anchors:
  - `src/index.md`
  - `src/sections/filesystem.md`
  - `src/sections/meta-engine.md`
  - `src/sections/ontology.md`
  - `src/sections/product-tdd.md`
  - `src/sections/unit-tdd.md`
  - `src/sections/tasks.md`
  - `src/assets/mappings/durable-destination-map.md`
- Impact Hypothesis: v9.6 will affect filesystem topology, ontology, task routing, Product TDD placement, Unit TDD boundary examples, root/mode templates, and the dedicated shared-doc safety skill.
- Temporary Assumptions:
  - `git submodule` is the default reference transport, but the framework should preserve more general invariants than one git feature.
  - Shared truth should stay limited to `00-meta`, `10-prd`, `15-alignment`, and `20-product-tdd`.
  - Spoke-side execution must preserve local evidence and code pain before any shared-doc mutation flow resumes.
  - Multi-repo should be modeled as an optional extension, not a new default startup shape.
- Negotiation Triggers:
  - A proposed rule blurs Product TDD and Unit TDD ownership instead of clarifying it.
  - A proposed rule depends on one toolchain, one host, or one repo setup rather than a durable framework invariant.
  - Source-first mutation would make spoke-side diagnosis too lossy unless an explicit capture step is added first.
  - A core template starts assuming `docs/_shared/` or Hub/Spoke even when the repo is ordinary mono-repo.
- Promotion Candidates:
  - Optional multi-repo topology guidance for `src/sections/filesystem.md`
  - Extension load rules for `src/sections/meta-engine.md`
  - Shared vs local admission tests for `src/sections/product-tdd.md` and `src/sections/unit-tdd.md`
  - `edit-svc-shared-docs` as a submodule safety rail under `.agents/skills/`

## Execution Notes

- key findings:
  - v9.5 lacks explicit hub/spoke topology, shared-doc mutation sequencing, freshness rules, and global vs local task routing.
  - `InKCre/core-py` validates source-first mutation, pointer bumps, allowlist boundaries, and deterministic checks, but it also shows the risk of overfitting framework rules to one repo's tooling.
- decisions made:
  - Record existing thinking and user objections in `tasks/v9_6-multi-repo/` before further framework edits.
  - Absorb the two new objections into v9.6 itself instead of treating them as edge-case notes.
  - Accept the additional task files in this container as part of the exploration record.
  - Reframe multi-repo from "new default posture" to "pressure-driven optional extension".
  - Narrow `edit-svc-shared-docs` so its main job is protecting Spoke agents from unsafe submodule edits and reducing Git submodule complexity.
- final outcome:
  - v9.6 redesigned so mono-repo remains the default path, multi-repo moves into an optional extension, and `edit-svc-shared-docs` is narrowed to submodule-safe shared-doc editing.
