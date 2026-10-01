# Test Topology Convergence Plan

> Historical planning record. The 2026-07-29 hard cut completed the
> high-return removals and mature static transfers; remaining reshape ideas are
> not a blanket mandate because their own refactoring cost must clear ROI.

## Design Rule

A retained test family must have one named failure mode and one appropriate
layer. Tests that only repeat an already-proven lower-layer detail should be
merged, parameterized, or replaced by a higher-signal scenario. No numeric test
count is a success criterion.

## Proposed Sequence

### Slice 0 — Ledger and Static-Gate Decision

Read-only until Sir approves an implementation handshake.

1. Classify each family as static, pure contract, adapter, integration,
   black-box acceptance, or human-only acceptance.
2. Record consumer, failure mode, fixture owner, execution cost, and overlap
   with adjacent layers.
3. Evaluate the smallest viable type/lint/AST gate against representative
   provider and render-boundary defects.
4. Decide whether schema fixtures should remain an intentionally independent
   golden artifact or be reduced to high-level assertions.

Exit: a reviewable ledger and one bounded first implementation slice; no tests
or runtime behavior changed.

### Slice 1A — Converge Installed-Wheel Success-Path Scaffolding — Complete

Only `tests/test_accept_agent_thread.py` changed. Four successful isolated
slice tests now use one four-subtest matrix and a shared fake isolated-run
helper. The matrix retains one slice-specific assertion each, while the `all`
order test stays dedicated. No harness code, schema fixture, negative case,
runtime behavior, dependency, or CI configuration changed.

Evidence: focused harness 15/15 and full suite 210/210; see
[`evidence.md`](evidence.md#slice-1a-execution-evidence).

### Slice 1B — Thin Installed-Wheel Acceptance Deep Validation

Keep the harness independent of the checkout and standard-library-only. Move
deep trajectory/analysis schema legality to core contract tests, retain an
installed-wheel synthetic golden plus package/wheelhouse/cleanup/privacy
invariants, and parameterize repeated slice scaffolding.

Exit: the harness has a smaller public acceptance surface, every retained
check is black-box-specific, and its error/cleanup security branches remain
tested.

This slice is deliberately deferred. It must first define an independent frozen
golden plus adversarial contract before reducing the harness's duplicate
trajectory/analysis schema details.

### Slice 2 — Separate Provider Mapping from Stream/Core Contracts — Complete

Create a canonical source fixture vocabulary. Keep provider-specific field-path
mapping in the Codex adapter tests; keep canonical record validation, ID,
ordering, and bounded collection in trajectory tests. Remove only scenarios
whose fault model is demonstrably identical at both layers.

Exit: an adapter implementation change and a core collector change each fail a
different, obvious family rather than several copies of the same scenario.

Execution: rollout's explicit-source test now directly asserts native
field-path mapping (workspace/message/reasoning/tool call/result). The
trajectory suite separately proves canonical order, stable source refs and
record IDs. Its orphan-result and sink-rejection cases retain the stronger
identity/diagnostic proof; the two rollout strict subsets were removed. No
cross-file fixture helper was introduced, so each oracle remains local to its
owner. Focused Codex modules passed 41/41 and the full suite passed 208/208.

### Slice 3 — Introduce Import Linter and Replace Incidental Structure Tests

Replace source substring checks and private widget/helper assertions where an
AST rule, public render model, or user-visible interaction expresses the real
contract more directly. Retain direct private tests where the private helper is
itself the security or atomicity boundary.

The selected first static rule is an Import Linter `forbidden` contract for
`svc_cli.telemetry.navigation`. It needs a separate Impact Handshake because it
adds a dev-only dependency, lockfile and frozen CI-install changes, PDM script,
CI invocation, and removes superseded navigation source assertions. See
[`static-gate-decision.md`](static-gate-decision.md).

Exit: safe refactors no longer require updating tests that merely know local
names or widget layout, while negative boundary behavior remains covered.

### Slice 4 — Ratchet and Remove Debt

Add the approved static gate to local/CI commands, document its owner and
failure handling, remove superseded cases, and re-run package/cross-platform
acceptance. Record each deletion's replacement in the ledger.

Exit: the suite has fewer overlapping paths, a visible static/dynamic division
of labor, and no loss of known safety coverage.

## Decision Constraints

- Do not use production validators as the only oracle for their own emitted
  output; retain independent golden/negative evidence where it protects a
  released wire format.
- Do not turn the cross-platform harness into an import of checkout code merely
  to remove duplication.
- Do not add a static tool only to make a metric look better. It must own a
  concrete defect class and have an enforced invocation.
- Do not batch test deletion with a product behavior change; topology evidence
  must remain interpretable.
