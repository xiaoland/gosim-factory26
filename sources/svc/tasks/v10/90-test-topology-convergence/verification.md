# Verification Matrix

## Completion Criteria

| ID | Claim | Objective proof |
| --- | --- | --- |
| TOP-01 | Every retained test family has a distinct reason to exist | Ledger maps each family to owner, consumer, failure mode, layer, and replacement relationship |
| TOP-02 | No count-driven weakening | Every deletion records a negative cost/value decision; a transferred structural rule names its mature gate, while dynamic boundary families remain listed in the evidence file |
| TOP-03 | Static and dynamic responsibilities are explicit | Chosen static tool has a documented local/CI command and representative positive/negative checks; dynamic tests remain for filesystem, privacy, archive, package, and TUI behavior |
| TOP-04 | Core schema validation remains independent enough | Golden and adversarial fixtures catch a validator regression without merely calling the same production validator as oracle |
| TOP-05 | Provider/core overlap is intentional only | Canonical source mapping, stream/collector, and archive publication each have a non-overlapping focused suite |
| TOP-06 | Acceptance remains genuinely black-box | Harness runs an installed wheel in an isolated venv, detects checkout leakage, validates critical CLI/package behavior, and does not reproduce all core schemas |
| TOP-07 | Refactoring freedom improves | A safe rename/layout refactor of non-boundary internals does not require updating source-string, private-helper, or widget-ID assertions |
| TOP-08 | No release regression | Focused tests, `pdm run test`, build/package checks, and any applicable installed-wheel acceptance pass |

## Evidence Required Before Deletion

For every proposed removal or merge, record:

1. the old test/family and its current asserted failure mode
2. defect impact, likelihood, and incremental detection value;
3. runtime, fixture, flake, and cognitive maintenance cost;
4. the retained or new proof when the failure mode remains worth protecting;
5. whether a mature static gate owns a structural portion, and what remains dynamic.

## Executed Slice Evidence

| Slice | Changed owner | Focused proof | Full proof | Result |
| --- | --- | --- | --- | --- |
| 1A: harness success-path scaffolding | `tests/test_accept_agent_thread.py` only | harness discovery: 15 passing | `pdm run test`: 210 passing | Complete; four subtests retain the four individual slice contracts and `all` order remains separate |
| 2: provider/stream proof separation | `tests/test_telemetry_codex_rollout.py`, `tests/test_telemetry_codex_trajectory.py` | retained cases 4/4; both Codex modules 41 passing | `pdm run test`: 208 passing | Complete; adapter field mapping, stream identity, orphan result, and record-limit diagnostics each have one clearer owner |
| 2026-07-29 ROI hard cut | low-value source tests, quality config, and CI | Import Linter/zizmor positive and temporary negative probes | 194 source tests / 222 pytest items after removal | Complete; 14 source tests removed or transferred without weakening dynamic boundary behavior |

## Final Automated Verification — 2026-07-29

| Check | Result |
| --- | --- |
| Source-function / collection reconciliation | The ROI hard cut retained 194 source functions / 222 items; the integrated candidate has 196 / 224 after two observability release-audit regressions. |
| Full behavioral suite | `pdm run test` → 224 passed in 13.01 s. |
| Native pytest hard cut | Final legacy-framework search returned no `unittest`, `TestCase`, `self.assert`, or `subTest` surface. |
| Static gates | `pdm lock --check`, `pdm run lint-tests`, `pdm run typecheck`, `pdm run lint-imports`, and `pdm run lint-workflows` all passed. |
| Package/release checks | `pdm run build-monolith`, `pdm build`, `pdm run svc --help`, and `pdm run release check` all passed. Built wheel metadata contains only runtime dependencies, not pytest/Ruff/mypy/Import Linter/zizmor. |
| Patch hygiene | `git diff --check` passed. |

## Non-Goals

- attaining a predetermined test count or line count
- replacing runtime safety checks with annotations or lint
- broad production refactoring hidden inside test cleanup
- reopening the completed agent-observability product contract
