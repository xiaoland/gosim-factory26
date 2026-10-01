# 2026-07-29 ROI Hard-Cut Impact Handshake

## Address and Object

- low-value source tests in `tests/test_catalog.py`,
  `tests/test_framework_contract.py`, `tests/test_lookup.py`,
  `tests/test_release.py`, `tests/test_telemetry_cli.py`,
  `tests/test_telemetry_navigation.py`, and `tests/test_workflows.py`;
- quality configuration and lock in `pyproject.toml` and `pdm.lock`;
- CI/developer invocation in `.github/workflows/*.yml` and `CONTRIBUTING.md`;
- the test-topology and pytest-migration task evidence.

## State Diff

From 208 native pytest source functions with a false all-retain ROI claim and
ad-hoc AST/regex structural tests, to 194 source functions plus two
development-only mature gates: Import Linter for the navigation import boundary
and offline zizmor for GitHub Actions security policy.

## Blast Radius

Local quality setup, the CI quality job, release workflows' checkout security,
and the source-test collection change. Wheel runtime dependencies and product
behavior do not.

## Invariants

1. No dynamic privacy, filesystem-race, archive, release-integrity,
   installed-wheel, or real TUI behavior is removed or delegated to lint.
2. No custom parser, checker, or runtime dependency is added.
3. The release workflows retain their required branch/tag push credentials;
   any intentionally persisted checkout credential is narrowly documented.
4. The resulting gates run under the lockfile and on CI, not only locally.

## Verification

1. `pdm lock --check`, `pdm run lint-tests`, `pdm run lint-imports`, and
   `pdm run lint-workflows` pass.
2. `pdm run test`, `pdm run typecheck`, `pdm run build-monolith`, `pdm build`,
   and the installed-wheel CLI smoke pass.
3. A temporary forbidden import breaks Import Linter; a temporary unpinned
   action breaks zizmor, without committing either probe.
4. `git diff --check` passes and wheel metadata contains no quality dependency.
