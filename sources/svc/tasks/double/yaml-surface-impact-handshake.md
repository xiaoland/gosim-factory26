# Double YAML-Surface Impact Handshake

## Address and Object

- add `svc_cli/src/svc_cli/double/yaml_surface.py` as the single adapter for
  strict YAML 1.2 parser construction, UTF-8/BOM handling, event-level admitted
  feature/resource guards, parse diagnostics, and ruamel source coordinates;
- update `compiler.py` to consume parsed authored objects and source locations
  without owning YAML parser/event mechanics;
- preserve compiler exports for the public test bounds, add the adapter to the
  explicit mypy surface, and update task evidence;
- rely on the existing YAML corpus and representative timestamp assertion; add
  no alternative parser or duplicate structural schema.

## State Diff

```text
compiler orchestration + embedded YAML parser/event/source-coordinate mechanics
->
compiler orchestration -> one strict YAML-surface adapter -> ruamel.yaml
```

The event guard remains SVC policy because aliases, tags, merge keys, document
count, depth, and node count define the admitted BSL surface and resource
boundary. `ruamel.yaml` remains the syntax/parser authority; the adapter does
not reimplement YAML tokenization or object construction.

## Blast Radius

- Module and local OpenAPI YAML/JSON parsing use a fresh identically configured
  parser through one function.
- Compiler diagnostics continue to report the same module/source/path,
  one-based line/column, stable code, message, and bounded parser diagnostic.
- YAML source locations used by BSL semantic failures come from the same ruamel
  `lc` metadata through the adapter.
- No IR, runtime, CLI, dependency, fixture, or generated schema changes.

## Invariants

- YAML 1.2 timestamp-looking scalars remain strings.
- Duplicate keys, anchors/aliases, explicit tags, merge keys, multiple
  documents, empty documents, invalid UTF-8/BOM, excessive depth, and excessive
  nodes retain their current outcomes and diagnostics.
- Representative projection SHA and scenario digest remain unchanged.
- Existing 84 mapped double cases retain their outcomes and historical digest.
- Base wheel import isolation and unrelated working-tree changes remain intact.

## Verification

- Run the complete YAML/language/OpenAPI corpus, representative projection and
  digest checks, then all repository tests and quality/artifact/lock/workflow
  gates.
- Build the wheel and repeat base/extra isolation, including validation of the
  payment fixture whose unquoted RFC3339 query value proves timestamp handling.

## Authorization

Sir authorized continued implementation and one commit per migration stage on
2026-08-11. This document bounds the YAML-surface convergence stage and its
commit; publishing and release remain outside scope.

## Completion Evidence

- `yaml_surface.py` is now the only owner of parser construction, YAML 1.2
  timestamp handling, event guards, parser diagnostics, and ruamel source
  coordinates. `compiler.py` consumes authored objects and no longer imports
  the parser, YAML errors, or event classes.
- Module and local OpenAPI parsing both use a fresh identically configured
  parser. The 11-case YAML corpus, eight OpenAPI cases, representative timestamp
  assertion, and stable diagnostics pass unchanged.
- The representative projection SHA remains
  `1d37a65c3a522b114b4050d009086af621c41a5f943f7ed98bc949e696433a7e`
  and the scenario digest remains
  `ea0dc6f0cf80c007fb6b14914a4a676a9853673bd49d5c446020b51086684d75`.
- The complete repository suite is 242 passed; all 84 current double cases are
  mapped and the historical case-identity digest remains
  `8c0b2e1b78328b5c4d46c5afecd578244d6e2b0bb1770650ca0348db27325231`.
  Type, lint, import-contract, document, release-projection, CLI-schema,
  workflow, lock, whitespace, and clean base/extra wheel checks pass.
