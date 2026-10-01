# Migration Options

## A — Retain `unittest`

Choose this if pytest only changes syntax or if compatibility adds a dependency
without removing real support complexity. Continue topology pruning and static
gates independently.

## B — Pytest Runner, Retain Existing Test Classes

Use pytest to collect the current `unittest` suite first. This is the smallest
operational migration and establishes compatibility, command ergonomics, and
timing without changing test oracles. It is not sufficient evidence for a
whole native rewrite.

This option is superseded by Sir's selected hard cut-over.

## C — Runner plus One Native Family Pilot

After B is positive, select one family with measurable fixture/parameter or
async complexity. Convert it only when the exact removed duplication and
retained dynamic proof are documented. Use pytest's standard facilities before
adding plugins.

This historical incremental option is superseded by the selected hard
cut-over.

**Gate:** the pilot proposal must name the exact deleted setup/support lines,
the retained failure mode, and its validation. A count of converted tests or
assertions is not evidence of a benefit.

## D — Async Native Migration

Treat the Textual `IsolatedAsyncioTestCase` separately. Pytest alone does not
run native async test functions, and an async plugin introduces a loop-scope
contract. Do not add `pytest-asyncio` until a separately measured async pilot
has enough benefit to pay for that new policy.

This historical deferral is superseded because the hard cut-over requires the
already-existing Textual tests to become native async pytest tests.

## E — Full Native Pytest Hard Cut-Over (Selected)

Convert every retained test to pytest functions, native assertions, fixtures,
and parametrisation where they clarify a shared test shape. Add
`pytest-asyncio` only because the existing Textual tests need a native async
execution contract. Do not leave `unittest` imports, classes, discovery, or
dual CI lanes behind.

Every original test method receives one ledger verdict:

- **retain**: it proves a named failure mode and is migrated;
- **merge**: its named failure mode moves into a specific retained test whose
  setup/action/oracle fully subsumes it; or
- **delete**: it provides no independent failure mode, with the covering test
  named explicitly.

“Shorter syntax” and a lower test count are not sufficient reasons to delete.

## Rejected Shortcut

Do not use an unreviewed mechanical replacement as proof of a migration. The
implemented cut-over used a converter only as an aid, then reviewed lifecycle,
mock, async, parameter, and per-case ROI semantics before retaining each
native test.
