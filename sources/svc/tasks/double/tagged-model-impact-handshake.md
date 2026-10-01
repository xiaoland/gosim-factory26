# Double Tagged-Model Authority Impact Handshake

## Address and Object

- `svc_cli/src/svc_cli/double/model.py`
  - replace broad optional-field `Matcher`, `ValueNode`, and `Body` records with
    strict tagged variants and discriminated union aliases;
- `svc_cli/src/svc_cli/double/compiler.py`
  - construct the exact admitted variant after existing BSL semantic checks;
- existing `materialization.py`, `service.py`, and `carrier.py` consumers
  continue to consume the union aliases without source changes;
- focused tests under `svc_cli/tests/double/` and the topology probe;
- this task packet and implementation evidence.

## State Diff

```text
one broad record per algebra whose optional fields admit contradictory shapes
->
one discriminated union per algebra whose selected tag requires its own fields
and fixes every irrelevant field to None or an empty tuple
```

The variants are internal runtime-neutral IR. This slice does not change the
authored BSL grammar or make Pydantic the source-diagnostic adapter yet.

## Blast Radius

- Compiler construction names change to exact variants.
- Materialization and service receive narrower values through their existing
  annotations without a control-flow change.
- Carrier manifest deserialization passes through discriminated unions.
- Tests that directly construct IR use exact variant constructors.
- No CLI, YAML surface, error code/message/location, generated value,
  interaction matching, event delivery, or output schema may change.

## Invariants

- `Scenario.model_dump(mode="json")` for the representative payment fixture
  retains the same keys and values. After replacing only the machine-specific
  `module_path` and `workspace_root`, its sorted payload SHA-256 remains
  `1d37a65c3a522b114b4050d009086af621c41a5f943f7ed98bc949e696433a7e`.
- The payment scenario digest remains
  `ea0dc6f0cf80c007fb6b14914a4a676a9853673bd49d5c446020b51086684d75`.
- JSON null remains distinguishable from an absent required field through
  Pydantic required fields without defaults.
- Existing persisted manifests deserialize without a migration because all
  serialized field names and fixed-null/default values remain present.
- The pre-topology 78-case identity digest remains a preserved subset; new
  tagged-model characterization cases are explicit additions.
- Unrelated working-tree changes remain untouched.

## Verification

- Prove cross-variant fields, missing required fields, and empty ranges fail at
  model construction.
- Compile and round-trip representative, raw, and recursive scenarios through
  JSON validation.
- Check the representative model payload and scenario digest invariants.
- Run all double tests, the complete repository suite, lint, type, import
  contracts, output-schema checks, release/document/workflow checks, lock
  validation, and whitespace checks.

## Authorization

Sir said “你可以继续，每个阶段整理一个提交” on 2026-08-11 after reviewing
the ordered reuse/convergence migration. This authorizes this separately
bounded stage and its commit; publishing and release remain outside scope.

## Completion Evidence

- Compiler output selects exact `Matcher`, `ValueNode`, and `Body` variants;
  direct cross-variant fields, missing required fields, and an empty range fail
  Pydantic validation while required JSON null remains valid.
- The representative payment projection retains portable SHA-256
  `1d37a65c3a522b114b4050d009086af621c41a5f943f7ed98bc949e696433a7e`
  and scenario digest
  `ea0dc6f0cf80c007fb6b14914a4a676a9853673bd49d5c446020b51086684d75`.
- The scenario JSON round-trips through the discriminated unions, and detached
  carrier tests prove manifest deserialization remains compatible.
- The historical 78-case topology digest remains unchanged; two explicit model
  cases bring the double-related collection to 80.
- The complete repository suite is 238 passed. Lint, type, import contracts,
  output schemas, release projections, documents, and workflows pass.
