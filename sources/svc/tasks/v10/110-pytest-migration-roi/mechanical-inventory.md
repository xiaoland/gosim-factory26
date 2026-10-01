# Mechanical Inventory

## Baseline and Current Runner Surface

Before the cut-over, `pyproject.toml` defined:

```text
python -m unittest discover -s tests -p 'test_*.py'
```

The current sole command is:

```text
pytest tests
```

CI installs the bounded `test` group before every job that invokes that
command. Pytest, pytest-asyncio, and the narrow Ruff hard-cut gate are
development-only dependencies.

## Measured Shape

| Surface | Evidence | Consequence |
| --- | ---: | --- |
| Test modules | 22 | Collection naming already matches pytest defaults. |
| Baseline `unittest` classes | 26 `TestCase`, 1 `IsolatedAsyncioTestCase` | All removed by the hard cut-over. |
| Native source test functions at migration baseline | 208 | Exactly matched the original source-method ledger before the independent ROI hard cut. |
| Pytest execution items at migration baseline | 268 | 60 former `subTest` matrix rows were independently addressable; no new behavioral proof was added. |
| Current source test functions | 196 | The hard cut removed/transferred 14 low-value functions; a later observability release audit added two high-value regressions. |
| Current pytest execution items | 224 | A diagnostic collection count, not a quality target. |
| Baseline `self.assert*` calls | 935 | Replaced with direct pytest assertions. |
| Lifecycle hooks | One `setUp` / `tearDown` pair, in Codex rollout | Replaced with a function-scoped pytest fixture. |
| Baseline `subTest` sites | 10 | Replaced with direct assertions or parametrisation; none remains. |
| Native async tests | Eight Textual tests | Explicit pytest-asyncio tests under strict, function-scoped loops. |

The external probe found no `load_tests` hook, which pytest would not collect.

## Collected Evidence

- Baseline class, assertion, lifecycle, temporary-directory, mock, subtest,
  capture, and async shapes were audited before mutation.
- Historical native pytest collection: 268 items; the migration-baseline full
  run passed 268 items.
- Current integrated collection: 224 items from 196 source functions. The hard
  cut itself ended at 222/194; the three per-case ledgers remain the
  migration-baseline record, and the later cost/value decision is in the
  topology packet.
- Ruff TID251 bans `unittest` in `tests/`; an explicit final grep additionally
  proves no legacy framework surface remains.

## Post-Cut Topology Decision

All retained families are now native pytest. The migration audit did not make
the later cost/value decision: complex lifecycle in TUI, SQLite/race, release,
and installed-wheel tests remain explicit because they are part of the proof,
while the separate topology audit removed or transferred fourteen lower-value
source functions without reducing those boundaries.
