# Test Topology Convergence

- **Objective**: Make SVC's test suite a small, high-signal set of independent
  failure-mode checks. Reduce duplicate fixtures, internal implementation
  coupling, and schema copies while adding the right static gates; preserve the
  dynamic safety, packaging, and cross-platform evidence that static analysis
  cannot supply.
- **Guardrails**:
  - Test count is not a target. Retain a test only when its expected defect
    prevention value exceeds its runtime, maintenance, flake, and cognitive
    cost. Non-subsumption is evidence of incremental detection, not a
    sufficient retention rationale.
  - Static typing, linting, and structural checks supplement rather than replace
    runtime evidence for filesystem races, SQLite privacy, ZIP safety,
    sensitive-output redaction, installed-wheel isolation, and real TUI
    interaction.
  - Keep the existing 11.0.0 agent-observability candidate behavior and its
    release/acceptance evidence intact. This task owns test topology, not a
    covert product-contract change.
  - Preserve a black-box installed-wheel acceptance boundary, but do not make
    its harness a second implementation of trajectory, analysis, or UI schemas.
  - The 2026-07-29 hard-cut authorization covers the recorded test, quality,
    CI, and task-evidence changes; it does not authorize a product-contract
    change.
- **Verification**:
  - A test-family ledger assigns every retained family a consumer-visible or
    safety-relevant failure mode, owner, test layer, and cost/value reason to
    exist; every removed case records why its expected value no longer clears
    its total maintenance cost, whether or not another test replaces it.
  - A static-gate decision records its exact tool, scope, exclusion policy,
    owner, and CI/local invocation. It catches representative structural/type
    defects without weakening dynamic boundary tests.
  - Refactored tests retain the important negative cases: no private SQL
    projection/output, no unsafe path or archive publication, schema-v1
    fail-closed behavior, deterministic trajectory/analysis, installed-wheel
    isolation, and TUI keyboard/terminal restoration.
  - Each approved slice passes its focused suite and `pdm run test`; the final
    change passes build/package gates and demonstrates that black-box acceptance
    still runs against an installed wheel rather than the checkout.
- **Current Truth**:
  - The historical topology baseline was 213 `unittest` cases. The native
    pytest migration then had 208 source functions and 268 execution items;
    the completed cost/value hard cut had 194 source functions and 222
    execution items. The integrated release candidate has 196 source functions
    and 224 execution items after the observability release audit added two
    high-value diagnostic-bound contract tests. These counts are diagnostics,
    not success metrics.
  - The current topology replays some source/normalization scenarios at provider,
    trajectory, archive, CLI, and installed-wheel layers. The clearest examples
    are recorded in [`evidence.md`](evidence.md).
  - The standard-library acceptance harness intentionally has no checkout
    dependency, but it duplicates substantial trajectory schema/policy detail.
    A recent classification drift in that duplicate expectation demonstrated
    the maintenance risk without exposing a product bug.
  - Several tests still call private helpers, assert widget internals, or
    inspect source text. These may make safe refactoring expensive even where
    the public behavior is unchanged; Import Linter is the selected mature
    replacement for the navigation import assertions.
  - The 14 source-function removals/transfers follow a per-test expected-value
    decision, rather than a claim that every non-overlapping behavior must be
    retained. The 71 reshape candidates remain only where a future local
    change makes improving their proof shape worthwhile.
  - Pydantic and bounded mypy/Ruff gates now exist, but they do not cover
    dynamic filesystem, privacy, archive, package, or TUI behavior. The
    remaining structural decisions are recorded in
    [`roi-reassessment.md`](roi-reassessment.md).
  - The observability implementation is awaiting only human terminal acceptance;
    this is a separate future task and does not reopen or alter its packet.
- **Next Step**: The hard cut and its automated verification are complete.
  Leave remaining reshape ideas dormant until their own refactoring return
  exceeds their cost; the separate observability task still awaits human
  terminal acceptance.

## Supporting Material

- Evidence and classification: [`evidence.md`](evidence.md)
- Full family ledger: [`family-ledger.md`](family-ledger.md)
- Static-gate decision: [`static-gate-decision.md`](static-gate-decision.md)
- Cost/value reassessment: [`roi-reassessment.md`](roi-reassessment.md)
- Per-case cost/value decision ledger: [`roi-decision-ledger.md`](roi-decision-ledger.md)
- Impact handshake: [`impact-handshake.md`](impact-handshake.md)
- Staged topology proposal: [`refactoring-plan.md`](refactoring-plan.md)
- Completion matrix: [`verification.md`](verification.md)
- Related completed product task: [`../80-agent-observability-analysis/packet.md`](../80-agent-observability-analysis/packet.md)
