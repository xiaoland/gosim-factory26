# Native Pytest Hard Cut-Over — Impact Handshake

## Proposed Change

Replace stdlib `unittest` discovery and all `unittest` test code with native
pytest, while retaining every non-duplicated behavioral oracle.

| Surface | From | To |
| --- | --- | --- |
| Test dependency policy | No test dependency group | A bounded `test` group containing pytest, pytest-asyncio, and the Ruff hard-cut gate |
| Local command | `python -m unittest discover -s tests -p 'test_*.py'` | `pytest tests` behind the same `pdm run test` entry point |
| CI/release test jobs | Install `release` before running tests | Install both `release` and `test` wherever that job invokes `pdm run test` |
| Test source | `unittest` classes, including TUI async class | Native pytest functions, fixtures, explicit async marks, and direct assertions |

## Owners and Blast Radius

- **Dependency/runtime owner:** `pyproject.toml` and `pdm.lock`; pytest is a
  development-only test dependency and must not enter the distributed runtime
  package.
- **Automation owner:** CI, release-PR, and publish workflows that actually
  execute tests; release-tag does not invoke tests and is outside this slice.
- **Developer workflow owner:** `CONTRIBUTING.md`, PDM script contract, and
  the workflow test that asserts the install-before-test sequence.
- **Behavior owner:** each current test method is accounted for in the ROI
  ledger. No product or telemetry behavior is in scope.

## Invariants

1. One authoritative command remains `pdm run test`; no permanent dual test
   runner is added.
2. Every original test method has a retain/merge/delete ledger outcome; every
   retained failure mode continues to collect and pass.
3. Existing temporary-directory, mock, async TUI, race, and black-box
   semantics remain intact even though their implementation style changes.
4. No `unittest` compatibility layer, dual runner, coverage gate, or runtime
   dependency remains or is added.
5. CI installs exactly the dependencies required by the jobs it runs; no
   unrelated workflow is broadened.
6. Ruff TID251 bans `unittest` in `tests/`, so the cut-over is mechanically
   protected without a custom script.

## Intended Files

- `pyproject.toml`
- `pdm.lock`
- `.github/workflows/ci.yml`
- `.github/workflows/release-pr.yml`
- `.github/workflows/publish.yml`
- `CONTRIBUTING.md`
- `tests/test_workflows.py`
- every other `tests/test_*.py` module
- `tasks/v10/110-pytest-migration-roi/` evidence files

## Acceptance

Use PYT-01 through PYT-08 in [`verification.md`](verification.md), inspect
the lock diff, and verify the selected installed-wheel acceptance on the
existing Windows/WSL environments when the observability change is ready for
that broader acceptance run.

## Explicit Start Required

Sir explicitly started this cross-owner hard cut-over on 2026-07-28.
