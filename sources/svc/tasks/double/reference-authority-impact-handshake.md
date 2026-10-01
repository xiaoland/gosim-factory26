# Double Reference-Authority Impact Handshake

## Address and Object

- add `svc_cli/src/svc_cli/double/schema_registry.py` as the single adapter for
  immutable registry construction, JSON Pointer/reference resolution, schema
  graph checks, and instance validation;
- update `compiler.py` to delegate pointer and recursive reference semantics to
  that adapter while retaining SVC-owned contained-file loading and one narrow
  stable-URN address projection;
- update `runtime.py` to use the same registry construction and validation
  adapter;
- declare `referencing` directly in the `double` extra, update the lock, and
  include the adapter in the explicit mypy surface;
- extend OpenAPI/runtime characterization and task evidence.

## State Diff

```text
compiler-owned JSON Pointer + graph validation
and runtime-owned registry + instance validation
->
one referencing-backed adapter shared by compiler and runtime
```

SVC continues to own local-path containment, byte bounds, snapshot identity,
OpenAPI profile selection, dialect policy, and stable resource URI assignment.
One recursive transformation remains solely as a compatibility projection from
local relative addresses to the already-admitted stable URNs. It does not
resolve pointers or decide schema validity. Removing that projection would
change the persisted IR and public scenario digest and is therefore rejected in
this behavior-preserving stage.

## Blast Radius

- Local OpenAPI path-item, operation, request-body, response, and schema refs
  resolve through `referencing` semantics.
- Recursive and cross-file schema validity is checked against the same frozen
  resource set later used by the runtime.
- `referencing>=0.37,<0.38` becomes a direct optional dependency rather than a
  transitive implementation detail of `jsonschema`; the resolved package
  version is already present in the lock.
- Base CLI import isolation remains unchanged because the adapter stays behind
  the existing lazy `double` service boundary.

## Invariants

- The representative payment scenario projection SHA and scenario digest from
  the tagged-model stage remain unchanged.
- `schema_resources`, selected request schema, and selected response schemas
  retain their serialized field names and values.
- The final registry has no retrieval callback; absent or remote resources
  cannot trigger network access.
- Only selected-operation reachable references are admitted and snapshotted;
  unrelated OpenAPI paths do not become scenario authority.
- Existing stable compiler/runtime error codes remain unchanged.
- Base installation does not import or require `referencing`.
- Unrelated working-tree changes remain untouched.

## Verification

- Characterize path-item refs, recursive cross-file refs, missing pointers,
  remote refs, and unrelated remote refs outside the selected operation.
- Prove compiler graph checks and runtime request/response validation use the
  same immutable resources and fail closed.
- Recheck projection SHA, scenario digest, clean base import isolation, double
  wheel extra installation, complete tests, lint, type, import contracts,
  schemas, documents, release projections, workflows, lock, and whitespace.

## Authorization

Sir authorized continued implementation and one commit per migration stage on
2026-08-11. This document bounds the reference-authority stage and its commit;
publishing and release remain outside scope.

## Completion Evidence

- `schema_registry.py` is now the only construction boundary for the immutable,
  no-retrieval registry used by compiler graph checks and runtime instance
  validation. Compiler-owned JSON Pointer parsing and the duplicate runtime
  registry builder were removed.
- The retained recursive transformation only maps already-admitted local
  addresses to the public stable resource URNs. The representative projection
  SHA remains
  `1d37a65c3a522b114b4050d009086af621c41a5f943f7ed98bc949e696433a7e`
  and the scenario digest remains
  `ea0dc6f0cf80c007fb6b14914a4a676a9853673bd49d5c446020b51086684d75`.
- Missing local pointers fail with the existing stable contract diagnostic;
  recursive cross-file schemas validate through the same registry; an
  unselected remote reference does not become scenario authority; and the
  final registry cannot retrieve an absent remote URI.
- `referencing>=0.37,<0.38` is a direct `double` extra dependency. A freshly
  built wheel was checked in clean base and extra virtual environments: base
  help/schema discovery works with YAML, CEL, JSON Schema, and `referencing`
  absent and returns the exact typed installation continuation; the same wheel
  installed with `[double]` imports all four dependencies and validates the
  payment scenario.
- The complete repository suite is 240 passed. Type, lint, import-contract,
  document, release-projection, CLI-schema, workflow, lock, topology, and
  whitespace gates all pass. The historical 78-case identity digest remains
  `8c0b2e1b78328b5c4d46c5afecd578244d6e2b0bb1770650ca0348db27325231`;
  the current mapped surface is 82 cases after the two tagged-model and two
  reference-authority additions.
