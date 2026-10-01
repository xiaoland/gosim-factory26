# Pytest Migration and Test-Topology ROI

- **Objective**: Complete a hard cut-over from `unittest` to native pytest,
  while evaluating every current test case's retained failure-mode value and
  deleting cases whose own expected value does not justify their total cost.
- **Guardrails**:
  - The cut-over is complete only when `tests/` has no `unittest` import,
    `TestCase`, `IsolatedAsyncioTestCase`, `self.assert*`, or `subTest`
    surface. Do not retain a compatibility stratum.
  - Preserve the current high-value dynamic contracts: filesystem and SQLite
    safety, canonical bytes, ZIP publication, redaction, installed-wheel
    isolation, and real TUI interaction.
  - Preserve one authoritative test command. Do not leave permanent dual
    `unittest`/pytest CI lanes that prove the same behavior twice.
  - Keep dependencies small. Add pytest plugins only where stdlib-compatible
    collection cannot retain the contract and the plugin's measured benefit
    exceeds its lock/CI/maintenance cost.
  - Test count is not an objective. A test may be deleted when its likelihood,
    impact, incremental detection, and diagnostic clarity do not justify its
    runtime, maintenance, flake, and cognitive cost; substitution is only one
    possible reason.
  - Sir explicitly authorized this cross-owner hard cut-over on 2026-07-28.
    No production/runtime behavior is in scope.
- **Verification**:
  - An ROI ledger records the current and proposed runner/dependency/CI cost,
    collection compatibility, timing, conversion effort, and distinct defect
    class for every proposed wave.
  - A temporary external pytest probe proves whether the current suite collects
    and passes before any repository mutation.
  - The completed cut-over passes the retained suite locally and in CI,
    package/build checks, and selected installed-wheel acceptance.
  - A per-case ledger names every original test's verdict: retained and
    migrated, reshaped later when the marginal return is positive, transferred
    to a mature static gate, or deleted with a specific cost/value rationale.
- **Current Truth**:
  - The pre-cut baseline was 208 `unittest` methods across 22 modules. Native
    pytest initially retained 208 source functions and collected 268 execution
    items; the corrected cost/value hard cut had 194 source functions and 222
    execution items. The integrated release candidate has 196 source functions
    and 224 execution items after two observability release-audit regressions
    were added under the authoritative `pdm run test` command. The historical
    extra items were former `subTest` matrix rows made separately addressable,
    not new behavioral proofs.
  - `tests/` now has no `unittest`, `TestCase`, `IsolatedAsyncioTestCase`,
    `self.assert*`, or `subTest` surface. Native async TUI tests use the
    bounded pytest-asyncio test dependency; explicit temporary-directory,
    race, and black-box lifecycle proofs remain where they are the contract.
  - The separate model/type-safety slice now provides bounded mypy coverage;
    it does not replace test-runner or behavioral-test evidence.
  - Existing test-topology work has removed three proven duplicate cases but
    intentionally did not decide a framework migration.
  - The first per-case inventory accounted for all 208 migration-baseline methods by
    non-subsumption. It incorrectly treated that necessary condition as a
    sufficient ROI decision. The corrected cost/value audit and resulting
    removal/transfer decision live in
    [`../90-test-topology-convergence/roi-reassessment.md`](../90-test-topology-convergence/roi-reassessment.md).
  - A clean, external `pytest 9.1.1` probe collected all 208 migration-baseline test
    methods and passed them, including 69 reported `subTest` cases, with no
    test-source rewrite. A directly comparable pair measured 12.78 seconds
    for `unittest` and 14.84 seconds for pytest. Later samples varied because
    of the real Textual interaction tests, so this is evidence of no speed
    benefit rather than a performance estimate.
- **Decision**: Sir selected option D, a complete native pytest hard cut-over.
  The prior runner-only recommendation is superseded. `pytest-asyncio` is in
  scope solely to migrate the existing real Textual async tests without a
  `unittest` compatibility layer.
- **Next Step**: The pytest migration is complete. Broader observability work
  may still require hands-on terminal acceptance, but no migration code,
  automation, or test-framework verification remains.

## Supporting Material

- ROI model: [`roi-model.md`](roi-model.md)
- Mechanical inventory: [`mechanical-inventory.md`](mechanical-inventory.md)
- Migration options: [`migration-options.md`](migration-options.md)
- Verification matrix: [`verification.md`](verification.md)
- Hard cut-over handshake: [`hard-cutover-handshake.md`](hard-cutover-handshake.md)
- Per-case result: [`roi-summary.md`](roi-summary.md)
- Per-case cost/value decision: [`../90-test-topology-convergence/roi-decision-ledger.md`](../90-test-topology-convergence/roi-decision-ledger.md)
- Core ledger: [`roi-core.md`](roi-core.md)
- Telemetry ledger: [`roi-telemetry.md`](roi-telemetry.md)
- Boundary ledger: [`roi-boundaries.md`](roi-boundaries.md)
- Tooling evidence: [`tooling-evidence.md`](tooling-evidence.md)
- Installed-wheel acceptance: [`acceptance.md`](acceptance.md)
- Related topology task: [`../90-test-topology-convergence/packet.md`](../90-test-topology-convergence/packet.md)
