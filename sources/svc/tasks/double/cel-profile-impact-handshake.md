# Double CEL-Profile Impact Handshake

## Address and Object

- add `svc_cli/src/svc_cli/double/cel_profile.py` as the single adapter for the
  admitted CEL environment, expression byte bound, JSON-result type policy,
  binding/request source inspection, compilation, evaluation, and RE2 matching;
- update `compiler.py` to retain source-aware diagnostics and phase/binding
  policy while delegating CEL mechanics to the adapter;
- update `materialization.py` to retain context-size and operation diagnostics
  while using the same environment and regex behavior as compilation;
- add adapter characterization without changing the existing eight CEL
  language cases, BSL surface, dependencies, or serialized IR;
- include the adapter in the explicit mypy surface and update task evidence.

## State Diff

```text
compiler CEL profile + scanner + compiler + regex helper
and materialization CEL profile + evaluator + regex helper
->
one CEL-profile adapter with compiler/runtime diagnostic projections
```

The adapter is deliberately narrow. `cel-expr-python==0.1.3` owns CEL parsing,
type checking, evaluation, and RE2 execution. SVC owns the admitted variables,
macro exclusions, expression/context byte bounds, phase availability, declared
binding order, stable diagnostics, and JSON-value result boundary.

## Scanner Boundary

The current binding exposes no public checked AST or reference map. The v0
grammar admits `bindings.NAME` and `bindings['NAME']`, so availability cannot be
proved by CEL's dynamic map type alone. The existing lexical inspection is
therefore moved intact behind the adapter, frozen by direct characterization,
and explicitly remains a limitation. Dynamic binding access stays rejected.
No opaque serialized CEL representation is decoded.

## Blast Radius

- Compile-time and runtime CEL environments use the same variable types and
  macro exclusions.
- Regex authoring checks, example checks, and runtime matching use one RE2
  execution path.
- Compiler error locations/codes/details and runtime error codes remain caller
  projections and do not leak library exceptions.
- The optional dependency/import boundary is unchanged: the adapter is loaded
  only after the existing `double` extra guard.

## Invariants

- No new CEL syntax, functions, macros, variables, or dynamic binding access.
- The representative scenario projection SHA and scenario digest remain
  unchanged.
- All existing CEL, language, matching, materialization, carrier, and Consumer
  cases retain their observable outcomes.
- Source locations and stable diagnostics remain unchanged for too-large,
  invalid, unavailable-binding, dynamic-binding, unavailable-request-context,
  and invalid-regex failures.
- Base wheel help/schema discovery remains extra-free.
- Unrelated working-tree changes remain untouched.

## Verification

- Characterize static binding extraction, string/comment exclusion, dynamic
  access detection, request-token detection, JSON/non-JSON return types,
  invalid RE2, and evaluation through the shared profile.
- Recheck projection SHA and scenario digest, full tests, type, lint, import
  contracts, schemas, documents, release projections, workflows, lock,
  topology, whitespace, and base/extra wheel isolation.

## Authorization

Sir authorized continued implementation and one commit per migration stage on
2026-08-11. This document bounds the CEL-profile stage and its commit;
publishing and release remain outside scope.

## Completion Evidence

- `cel_profile.py` now owns the one admitted environment, variable types,
  macro exclusions, expression bound, JSON return-type admission, compile/eval
  path, and RE2 execution. The compiler and materializer no longer construct
  their own CEL environments.
- The lexical inspector is isolated and directly characterized. It ignores
  comments and ordinary string contents, recognizes both `bindings.name` and
  static `bindings['name']`, reports request use, and identifies computed-key
  binding access as dynamic. This also closes the prior implementation gap in
  which the documented static bracket form was accidentally blanked as an
  ordinary string before availability analysis.
- Invalid RE2 is explicitly detected from CEL's returned ERROR value and still
  projects as `invalid-double-regex`; runtime failures retain the existing
  runtime diagnostic. No CEL grammar or admitted feature changed.
- The representative projection SHA remains
  `1d37a65c3a522b114b4050d009086af621c41a5f943f7ed98bc949e696433a7e`
  and the scenario digest remains
  `ea0dc6f0cf80c007fb6b14914a4a676a9853673bd49d5c446020b51086684d75`.
- The complete repository suite is 242 passed. The current topology is 84/84
  mapped cases while the historical 78-case identity digest remains
  `8c0b2e1b78328b5c4d46c5afecd578244d6e2b0bb1770650ca0348db27325231`.
  Type, lint, import-contract, document, release-projection, CLI-schema,
  workflow, lock, whitespace, and clean base/extra wheel checks pass.
