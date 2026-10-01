# Current Synthesis

## MVT Core

- Objective & Hypothesis: Record the current exploration result before editing framework sources so later promotion decisions stay auditable.
- Guardrails Touched: Do not promote project-specific tooling details as framework ontology; do not define multi-repo by folder names alone.
- Verification: This note should give a stable basis for deciding what belongs in v9.6 and what stays as project-level implementation detail.

## Current Gaps In v9.5

- No physical topology model for hub-and-spoke multi-repo systems.
- No explicit rule for `docs/_shared/` or equivalent nearby consumption paths.
- No shared-doc mutation protocol for spoke-side work that discovers missing shared truth mid-execution.
- No freshness contract that moves pointer drift responsibility from humans to automation.
- No multi-repo clarification of the `20-product-tdd` versus `30-unit-tdd` authority boundary.

## Candidate v9.6 Principles

- Mono-repo remains the default SVC operating posture.
- Hub-and-spoke is a physical topology extension, not a new durable truth layer.
- Shared truth needs an admission gate before promotion; not every repeated detail becomes hub-owned.
- Spoke agents should read shared truth from a nearby mount such as `docs/_shared/`.
- Shared-doc mutation should stay source-first and pointer-second.
- Freshness should be machine-enforced rather than relying on human memory.
- `20-product-tdd` and `30-unit-tdd` should be separated by authority scope and consumer count, not by whichever repo the agent happens to be editing.
- Multi-repo-specific burden should live in an optional extension and in the dedicated shared-doc skill, not in every default template.

## Lessons Extracted From `InKCre/core-py`

- The problem was solved in phases: ownership classification, source boundary, transport decision, reliability pack, pilot rollout, then mixed-doc cleanup.
- The shared-doc source boundary was explicit: `00-meta/`, `10-prd/`, `15-alignment/`, and `20-product-tdd/`.
- `git submodule` was locked as the default transport because it pins provenance and rollback clearly, but the deeper value was the operational discipline around it.
- The project added a dedicated shared-doc skill and deterministic checks; those are good implementations, but SVC should only promote their governing invariants, not their repo-specific wrappers.
- The mixed-doc split problem remained real after transport was chosen; topology alone does not solve ownership drift.

## What Should Enter SVC v9.6

- A concise "topology can extend" rule in core framework docs.
- An optional multi-repo extension that defines Hub/Spoke, `docs/_shared/`, source-first mutation, and freshness.
- A multi-repo authority rule in Product TDD and Unit TDD that stays brief.
- A task-containment rule for hub volatility versus spoke volatility, loaded only when multi-repo applies.
- A dedicated `edit-svc-shared-docs` skill that focuses on submodule safety and protecting Spoke agents from unsafe shared-doc edits.

## What Should Not Enter SVC v9.6

- Project-specific remote URLs or `.gitmodules` values.
- Repo-root skill shims created only for one tool's auto-discovery behavior.
- Vendor-specific CI wiring.
- Concrete shell scripts as framework law.
- Default templates that make mono-repo users think about `docs/_shared/`, Hub, or Spoke on every task.
