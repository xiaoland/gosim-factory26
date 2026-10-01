# Double Test-Topology Impact Handshake

## Address and Object

- Replace the flat double test modules:
  - `svc_cli/tests/test_double_cli.py`
  - `svc_cli/tests/test_double_output.py`
  - `svc_cli/tests/test_double_language.py`
  - `svc_cli/tests/test_double_runtime.py`
- Introduce the ownership tree under `svc_cli/tests/double/` with explicit
  `interface/`, `language/`, `runtime/`, `support/`, and `fixtures/` owners.
- Move the existing double fixtures without changing their bytes, except for
  paths in tests and spike probes that address them.
- Keep the two shared execution-mechanism cases in
  `svc_cli/tests/test_execution.py`.
- Update the reuse/convergence topology probe and task packet evidence.

## State Diff

```text
four flat modules mixing interface, language, runtime, lifecycle, and helpers
->
one package whose test modules follow semantic owners and whose reusable
builders, HTTP helpers, run cleanup, and projection facts each have one owner
```

## Blast Radius

- Pytest collection node paths intentionally change.
- Test imports and fixture paths change.
- No production module, dependency, generated output schema, CLI behavior, BSL
  grammar, runtime behavior, assertion, or test parameter is permitted to
  change.

## Invariants

- The normalized function-and-parameter identity digest remains identical for
  all 78 double-related cases, including the two shared execution cases.
- The invalid-fixture parametrization may be split by semantic owner, but every
  existing parameter case retains its function name, parameter id, and
  assertion.
- `conftest.py` does not become a helper dumping ground; importable helpers
  remain in named `support/` modules.
- Carrier/process cleanup retains one lifecycle authority.
- Unrelated working-tree changes remain untouched.

## Verification

- Run the collection-derived topology probe and require exactly 78 unique,
  mapped cases with the pre-move normalized identity digest.
- Run all reorganized double tests and the complete repository test suite.
- Run lint, type, import-boundary, output-schema, document, release-projection,
  workflow, and whitespace gates used by the completed MVP.

## Authorization

Sir explicitly said “同意，开始” on 2026-08-11 after reviewing the
reuse/convergence spike and its recommendation to land the behavior-preserving
test-topology slice first.
