# Tooling Evidence

## Conversion Aid

`unittest2pytest` 0.5 was run only against a disposable copy of a small test
module. It correctly changed common `self.assert*` forms and exception context
managers to pytest forms, but deliberately retained the `TestCase` class and
its `unittest` import. It is therefore useful as a reviewed mechanical aid,
not sufficient to implement the selected hard cut-over by itself. It is not a
project dependency.

## Durable Gate

Ruff 0.15 is in the project `test` dependency group and `pdm run lint-tests`
runs only TID251. The project configuration bans the `unittest` API within
`tests/`; this is a narrow, mature static gate for the migration invariant,
not a broad style or formatting rollout.

## Async Execution

`pytest-asyncio` 1.4 is in the same test group because the existing Textual
tests become native `async def` tests. The configuration uses strict mode and
function-scoped fixture/test loops; no custom event-loop fixture is introduced.
