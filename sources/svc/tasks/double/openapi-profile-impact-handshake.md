# Double OpenAPI-Profile Impact Handshake

## Address and Object

- add `svc_cli/src/svc_cli/double/openapi_profile.py` as the single owner of
  the admitted OpenAPI 3.1 selected-operation profile, selected local-reference
  reachability, request/response JSON Schema selection, stable resource-URN
  projection, dialect checks, and schema graph admission;
- keep workspace containment, bounded file reads, immutable snapshots, authored
  BSL diagnostics, HTTP method/path grammar, and interaction coverage in
  `compiler.py`;
- connect the profile to compiler-owned artifacts through two narrow callbacks:
  load one contained local document relative to an admitted document, and
  return its immutable snapshot identity;
- retain `schema_registry.py` as the lower-level reference/validation authority;
  the profile composes it instead of recreating JSON Pointer semantics;
- add the module to the explicit mypy surface and update task evidence.

## State Diff

```text
compiler owns BSL + artifacts + OpenAPI selected profile + schema projection
->
compiler owns BSL/artifacts -> OpenAPI profile -> immutable schema registry
```

## Blast Radius

- Only the selected operation and its reachable local references enter profile
  authority, as before.
- Remote references, non-Pointer fragments, missing targets, custom dialects,
  invalid schemas, unsupported response keys, and absent selected operations
  retain their stable fail-closed projections.
- Snapshot ordering, resource URI identity, selected request/response schema
  payloads, and runtime registry inputs remain byte-for-byte compatible.
- Local path failures continue to originate from compiler artifact policy, not
  from the OpenAPI profile.

## Invariants

- The representative serialized projection SHA and scenario digest remain
  unchanged.
- Recursive cross-file validation and the final no-retrieval registry retain
  the reference-authority evidence.
- Unselected remote references do not become scenario authority.
- Structured-only contract coverage remains a compiler/BSL cross-boundary
  check; raw and empty bodies do not gain JSON Schema obligations.
- No dependency, BSL surface, runtime, CLI, fixture, or output-schema changes.
- Base wheel import isolation and unrelated working-tree changes remain intact.

## Verification

- Run all OpenAPI, contract-runtime, compilation, model identity, language,
  carrier, and Consumer cases, followed by the complete repository and all
  quality/artifact/lock/workflow gates.
- Build the wheel and repeat clean base/extra isolation and payment validation.

## Authorization

Sir authorized continued implementation and one commit per migration stage on
2026-08-11. This document bounds the OpenAPI-profile convergence stage and its
commit; publishing and release remain outside scope.

## Completion Evidence

- `openapi_profile.py` now owns selected-operation lookup, reachable local
  reference traversal, request/response schema selection, stable resource-URN
  projection, dialect admission, and schema graph checks. It composes the
  existing immutable registry adapter for pointer/reference mechanics.
- `compiler.py` supplies only contained, bounded, snapshotted document loading
  and snapshot identity callbacks. HTTP authoring grammar and structured-body
  interaction coverage remain at the BSL/compiler boundary. The compiler falls
  from 2,762 to 2,356 lines and no longer imports JSON Schema or `referencing`.
- All eight OpenAPI cases, recursive runtime contract validation, carrier and
  black-box Consumer paths pass. Remote refs fail closed, missing pointers keep
  their stable diagnostic, and an unselected remote ref remains outside
  authority. Authored `source` diagnostic identity is explicitly preserved.
- The representative projection SHA remains
  `1d37a65c3a522b114b4050d009086af621c41a5f943f7ed98bc949e696433a7e`
  and the scenario digest remains
  `ea0dc6f0cf80c007fb6b14914a4a676a9853673bd49d5c446020b51086684d75`.
- The complete repository suite is 242 passed; all 84 current double cases are
  mapped and the historical identity digest remains
  `8c0b2e1b78328b5c4d46c5afecd578244d6e2b0bb1770650ca0348db27325231`.
  Type, lint, import-contract, document, release-projection, CLI-schema,
  workflow, lock, whitespace, and clean base/extra wheel checks pass.
