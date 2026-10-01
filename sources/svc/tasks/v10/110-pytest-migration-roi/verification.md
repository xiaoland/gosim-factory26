# Verification Matrix

| ID | Claim | Required proof |
| --- | --- | --- |
| PYT-01 | Collection is reconciled | The migration baseline reconciled 208 source functions to 268 pytest items; the later cost/value hard cut retained 222 items from 194 source functions; the integrated candidate collects 224 from 196 after two observability release-audit regressions. No count is a quality target. |
| PYT-02 | Runner migration has operational value | Local PDM command and a single CI lane use the same lock and selection semantics. |
| PYT-03 | Every case has a decision | The migration ledger accounts for every original method; the later topology audit records retain, reshape, transfer, or delete using each test's expected value and total cost. |
| PYT-04 | Dynamic safety stays intact | Focused negative security/archive/redaction/TUI/harness tests and the full suite pass. |
| PYT-05 | Packaging remains real | Build, installed-wheel smoke, and selected black-box acceptance still run outside the checkout. |
| PYT-06 | The dependency is intentional | `pytest>=9,<10` and the bounded async plugin are only in a test group, the lock is reproducible, and every CI job that invokes `pdm run test` installs that group. |
| PYT-07 | No false performance claim | Timing is recorded as operational evidence, while migration acceptance is based on collection and retained behavior rather than a one-run speed comparison. |
| PYT-08 | The hard cut-over is real | Ruff TID251 bans `unittest` in `tests/`; a final `rg` additionally finds no `TestCase`, `IsolatedAsyncioTestCase`, `self.assert`, or `subTest`, and the PDM test command does not invoke `unittest`. |

## Runner-Slice Checks

1. `pdm lock --check`
2. `pdm run lint-tests` (native pytest hard-cut static gate)
3. `pdm run test` (every retained behavioral proof)
4. Focused high-risk tests: TUI, Codex rollout, archive, release, and the
   installed-wheel harness
5. `pdm run typecheck`
6. `pdm run build-monolith`, `pdm build`, and `pdm run svc --help`
7. CI workflow contract tests, including that every test-running workflow
   installs the test group before invoking the one authoritative command
