# Double Reuse and Convergence Result

## Outcome

The concern is substantiated but narrower than “BSL reimplemented everything.”
The implementation correctly delegates YAML syntax, CEL compilation/evaluation,
and JSON Schema evaluation to libraries. It underuses the already-installed
Pydantic and `referencing` mechanisms, however, and the compiler has become a
second structural validator plus a second reference resolver. CEL binding
availability is the important exception: the selected Python binding does not
expose a checked AST, so preserving the admitted `bindings.NAME` surface cannot
currently eliminate source inspection without a grammar or dependency change.

The implementation follow-up resolves that initial assessment more precisely:
Pydantic is now the tagged IR authority, while a production probe rejects
reusing that IR adapter as the authored YAML authority because doing so would
require a duplicate authoring model and diagnostic grammar. JSON reference and
CEL mechanics now each have one adapter, and YAML parser mechanics have one
authoring-surface adapter.

All 78 double-related pytest cases remain required characterization evidence.
The implemented test topology assigns every collected case exactly once; it
deletes, merges, or silently reclassifies none of them.

No product source, dependency, lock, workflow, release projection, or generated
artifact was changed by this spike.

## Pre-Migration Responsibility Map

The production double package is 6,296 lines excluding `__init__.py`; the
largest concentration is the 3,088-line `compiler.py`:

| Compiler range | Approximate responsibility | Reuse assessment |
| --- | --- | --- |
| 119–238 | orchestration, scenario facts/digest inputs | SVC-owned |
| 239–1490 | host grammar, typed values, matchers, generators, CEL profile | structural validation is too manual |
| 1491–1586 | external materializer declaration | mostly SVC-owned policy |
| 1587–2161 | selected OpenAPI operation and reference graph | overlaps `referencing` |
| 2162–2572 | snapshots, contained paths, source diagnostics | SVC-owned |
| 2573–3088 | YAML event limits, JSON/CEL helpers, digest normalization | mixed; CEL scanner is an unresolved adapter |

The current runtime-neutral models do not encode their tagged invariants.
`Matcher` and `ValueNode` are broad records with many optional fields. The
installed model accepts all of these invalid states:

```python
Matcher(kind="exact", values=(1,))
Matcher(kind="range")
ValueNode(path=(), kind="derived")
ValueNode(path=(), kind="capture", expression="request.body")
```

The compiler and its tests, rather than the model boundary, are therefore the
only authority preventing those states.

Before the first implementation slice, the four flat double test modules
contained 2,537 lines:

| Current module | Lines | Responsibilities mixed together |
| --- | ---: | --- |
| `test_double_language.py` | 1,053 | YAML, JSON surface, typed values, CEL, assets, materializer declarations, provenance, OpenAPI |
| `test_double_runtime.py` | 850 | pure matching, materialization, HTTP, detached carrier, concurrency, cleanup, black-box Consumer |
| `test_double_output.py` | 348 | value projections, authority invariants, schemas, import isolation |
| `test_double_cli.py` | 286 | grammar, text/JSON delivery, schemas, failure classification, help policy |

The runtime test alone imports compiler, materialization, model, runtime, and
service layers and owns HTTP/process cleanup support. `FIXTURES` and scenario
facts are repeated across CLI, language, and runtime; observation/replay facts
are independently rebuilt in CLI and output tests. These are ownership and
change-locality problems, not merely long files.

## Probe 1: Pydantic Discriminated Variants

[`pydantic_probe.py`](pydantic_probe.py) models all matcher and value-node kinds
as strict discriminated variants and validates them with reusable `TypeAdapter`
instances. It proves:

- a valid exact matcher and derived node select one predictable variant;
- an exact matcher with `values`, an empty range, a derived node without an
  expression, and a capture node with an expression all fail structurally;
- a `ruamel.yaml` `CommentedMap` can be validated directly;
- Pydantic's error location can be mapped back to the authored YAML key's line
  and column.

Pydantic recommends discriminated unions as the more predictable and efficient
union mode, and `TypeAdapter` supports validation without inventing wrapper
models. See the official
[discriminated-union](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions)
and [TypeAdapter](https://docs.pydantic.dev/latest/concepts/type_adapter/)
documentation.

This does not eliminate SVC semantic checks such as phase availability,
generator/validator compatibility, workspace containment, or stable public
error codes. It moves object shape, required fields, forbidden fields, and
tag selection to one existing mechanical authority. A thin diagnostic adapter
must translate Pydantic locations/types to the admitted SVC diagnostics.

## Probe 2: CEL Binding Availability

[`cel_binding_probe.py`](cel_binding_probe.py) produces this distinction:

```text
bindings.external_id              -> compiles as DYN
bindings.missing                  -> compiles as DYN
bindings['computed_' + 'name']    -> compiles as DYN
external_id with an explicit var  -> compiles as DYN
missing with explicit vars        -> compile error: undeclared reference
```

The selected `cel-expr-python==0.1.3` `Expression` exposes only `eval`,
`return_type`, and `serialize` in its public Python surface. Its upstream
documentation describes typed environment variables and checked compilation,
but no Python AST/reference-map API:
[cel-expr/cel-python](https://github.com/cel-expr/cel-python).

Therefore:

- direct CEL variables would let CEL own availability, but changing
  `bindings.external_id` to `external_id` is a public BSL grammar change;
- adding an authored `inputs` list would not prove that the expression reads
  only those inputs while `bindings` remains a dynamic map;
- decoding opaque serialized expressions would add an undocumented coupling and
  likely a protobuf dependency, not reduce risk;
- switching CEL implementations solely for AST access would reopen language
  conformance and distribution evidence.

The v0 decision is **keep but isolate**: move reference inspection behind one
small CEL-profile adapter, retain its exact characterization cases, admit no new
CEL surface, and track upstream checked-AST exposure. Eliminating the scanner is
deferred to a separately reviewed BSL version or dependency decision.

## Probe 3: One Immutable Reference Authority

[`referencing_probe.py`](referencing_probe.py) builds one immutable
`referencing.Registry` with no retrieval callback. It proves all of the
following through the existing payment and recursive OpenAPI fixtures:

- relative cross-file `$ref` resolution;
- recursive in-file references;
- JSON Pointer selection from a complete OpenAPI document;
- valid and invalid request-schema evaluation;
- an absent provider URL fails as `Unresolvable` without network retrieval.

The official API states that registries are immutable, resolve relative
references and pointers, and fail retrieval unless a retrieval callable is
configured: [`referencing.Registry`](https://referencing.readthedocs.io/en/stable/api/#referencing.Registry).

The implementation should keep SVC ownership of contained local loading,
content bounds, snapshot hashes, stable logical URIs, dialect admission, and the
selected static OpenAPI operation. It should delegate recursive graph walking,
pointer resolution, and relative reference semantics to one registry used by
both compiler and runtime. A future source change should declare `referencing`
directly rather than relying on its transitive installation through
`jsonschema`.

The clean target contract stores immutable resources plus selected schema
reference URIs. Runtime validation uses a root `{"$ref": selected_uri}` against
the same registry. It should not detach and recursively rewrite schema objects
into a second reference representation.

## Test Topology

[`topology_probe.py`](topology_probe.py) runs real pytest collection over the
double package and two execution-seam additions, verifies 78 unique cases and
the pre-migration normalized case-identity digest, and assigns all 78 exactly
once to this implemented ownership tree:

```text
svc_cli/tests/double/
├── __init__.py
├── fixtures/
│   ├── language/                       # valid/invalid BSL and contracts
│   └── consumer/                       # black-box Consumer process
├── support/
│   ├── __init__.py
│   ├── scenarios.py                    # authored module builders and constants
│   ├── http.py                         # responder requests/callback listener
│   ├── runs.py                         # start/stop/carrier cleanup ownership
│   └── facts.py                        # reusable replay/observation facts
├── interface/
│   ├── test_cli.py                     # 5 cases
│   ├── test_output_models.py           # 4 cases
│   └── test_output_schemas.py          # 4 cases
├── language/
│   ├── test_compilation.py             # 3 cases
│   ├── test_yaml_surface.py             # 11 cases
│   ├── test_values.py                   # 12 cases
│   ├── test_cel.py                      # 8 cases
│   ├── test_assets_and_materializers.py # 7 cases
│   └── test_openapi.py                  # 6 cases
└── runtime/
    ├── test_matching.py                 # 4 cases
    ├── test_materialization.py          # 4 cases
    ├── test_contract_validation.py      # 1 case
    ├── test_carrier.py                  # 6 cases
    └── test_consumer.py                 # 1 case

svc_cli/tests/test_execution.py          # 2 shared-mechanism cases remain here
```

The generic storage-failure and double launch-seam cases stay with shared
execution because ownership is more important than feature-directory purity.
The currently mixed invalid-fixture parametrization is split by semantic owner
without changing its seven parameter cases.

No `conftest.py` was added because the migrated cases exposed no cross-module
pytest fixture owner. Importable lifecycle/HTTP/building helpers live in
explicit support modules; each helper has one cleanup or construction
authority. The post-move gate requires the exact pre-migration normalized case
identity digest, not just the same count, and then runs the full suite.

Implementation evidence:

- 78 current, unique, and mapped cases; normalized identity digest
  `8c0b2e1b78328b5c4d46c5afecd578244d6e2b0bb1770650ca0348db27325231`;
- interface 13, language 48, runtime 15, shared execution 2;
- all 15 moved fixtures are byte-identical;
- all 61 unique test-function ASTs are equivalent after normalizing only the
  intentional helper and fixture-address renames; the split invalid-corpus
  function has three equivalent definitions owning its original seven cases;
- 236 complete repository tests pass;
- lint, type, import-boundary, document, release-projection, output-schema,
  workflow, and whitespace gates pass.

## Decision Table

| Candidate | Decision | Why | Required compatibility evidence |
| --- | --- | --- | --- |
| `ruamel.yaml` parser plus event-level feature/resource guard | **Keep** | library owns YAML; SVC guard owns the admitted safe subset | current YAML corpus and source locations |
| Pydantic discriminated IR variants | **Adopted** | existing dependency removes representable illegal compiled states | all language/runtime cases; stable serialization/digest |
| Pydantic directly or through duplicate authoring variants | **Rejected for v0 after production probe** | IR collections/fields differ from YAML, `JsonValue` is not the strict JSON boundary, and translation would reproduce phase/key diagnostics | executable authored-shape probe; current diagnostic corpus |
| handwritten `_keys/_mapping/_string` as primary structural schema | **Replace incrementally** | duplicates model validation and expands every new variant | exact errors for missing/unknown/type cases |
| current CEL compiler/evaluator | **Keep** | mature language semantics already delegated | current CEL and platform-wheel gates |
| CEL regex/string source scanner | **Isolate and freeze** | required by v0 surface with current binding; public API cannot replace it | existing eight CEL cases; no CEL expansion |
| compiler-owned recursive `$ref` walker/JSON pointer/rewriter | **Replace** | duplicates the already-used immutable registry semantics | actual payment/recursive fixtures; remote fail-closed |
| SVC local path/snapshot/OpenAPI profile policy | **Keep** | product security/fidelity authority, not library mechanics | containment, bounds, dialect/static-operation tests |
| SVC closed matchers/generators | **Keep for v0** | intentionally narrower than Pact and provider engines | current semantics plus selected upstream conformance vectors after license review |
| flat four-file test layout | **Replaced** | mixed five production layers and hid helper ownership | exact 78-case identity digest and full suite |

Pact publishes a compatibility suite with reusable BDD features and fixtures:
[Pact compatibility suite](https://docs.pact.io/implementation_guides/jvm/compatibility-suite/pact-compatibility-suite).
The spike does not recommend importing Pact runtime/provider-state semantics.
A later implementation may admit only directly corresponding equality/regex
vectors after version, semantic, and license review.

## Ordered Migration

1. **Test topology only — completed.** Move all existing cases and fixtures into the tree
   above, extract narrow support owners, prove the mapped 78 cases plus the full
   suite. Do not alter production behavior in this slice.
2. **Tagged model authority — completed, including authored-shape decision.**
   Discriminated matcher/value/body IR variants preserve serialized field names
   and make compiled illegal states unrepresentable. The production follow-up
   probe rejects applying those strict IR TypeAdapters directly to authored
   YAML: list/tuple representation, fixed-null compatibility fields, non-finite
   JSON, phase-specific names, and compiled-only fields are materially
   different. A separate Pydantic authoring model would add a third structural
   authority plus the same source-diagnostic policy, so v0 retains the existing
   host compiler boundary instead.
3. **Reference authority — completed.** One no-retrieval registry adapter now
   owns JSON Pointer/reference resolution, recursive graph checks, registry
   construction, and runtime instance validation. SVC retains local containment,
   selected-operation reachability, snapshots, dialect policy, and a narrow
   stable-URN compatibility projection because removing that projection would
   change the persisted IR and scenario digest. Payment, recursive, missing
   pointer, remote fail-closed, base-wheel, extra-wheel, and full-suite evidence
   pass with unchanged public scenario identity.
4. **Compiler convergence — completed.** After duplicate authorities are removed, split the
   remaining compiler by deep boundaries—YAML surface, BSL semantics, CEL
   profile, OpenAPI adapter—rather than mechanically slicing the existing file.
   The YAML-surface substage is complete: parser construction, event guards,
   parser diagnostics, and source coordinates now form one adapter over
   `ruamel.yaml`; BSL semantics remain in the compiler. The OpenAPI substage is
   also complete: selected-operation/reference/schema-profile
   semantics live in one adapter over the immutable registry, while compiler
   callbacks retain contained artifact loading and snapshots. `compiler.py` is
   consequently the BSL semantic/diagnostic orchestrator rather than the owner
   of YAML, CEL, and OpenAPI library mechanics.
5. **CEL remains bounded — completed.** One CEL-profile adapter now owns the
   environment, JSON type admission, compilation/evaluation, RE2, expression
   bound, and the isolated scanner. The scanner limitation is explicit and
   characterized; no grammar or CEL feature was added. Compiler and runtime
   retain stable diagnostic projections while sharing the same mechanics.
6. **Conformance follow-up — completed with a product decision boundary.** A
   pinned external checkout at
   `97abd7bfcec15f3532109f984db37bcb5ccfb49c` and its local Apache-2.0 license
   are verified by the executable probe; no upstream files are vendored and no
   dependency is added. Exact and simple body-regex facts align. Pact's
   whole-value query/header regex rejects `9999X` for `\d{1,4}`, while the
   documented CEL substring semantics accepts it. This is reported rather than
   silently changed; a BSL product decision is required.

Each production slice requires a new Impact Handshake and Sir's explicit start.
The test-layout slice is complete and now provides the reviewable ownership
boundaries for later behavior-preserving compiler changes.

## Commands and Evidence

Run from the repository root with the existing double development environment:

```text
pdm run python tasks/double/spikes/reuse-convergence/pydantic_probe.py
pdm run python tasks/double/spikes/reuse-convergence/cel_binding_probe.py
pdm run python tasks/double/spikes/reuse-convergence/referencing_probe.py
pdm run python tasks/double/spikes/reuse-convergence/topology_probe.py
```

Observed evidence:

```text
Pydantic: 4 previously accepted illegal shapes rejected; ruamel path -> line 2, column 1
CEL: bindings.missing and dynamic key compile; explicit missing variable fails
Referencing: payment and recursive valid/invalid counts are [0, 1]; remote is Unresolvable
Topology: current 78; unique 78; mapped 78; pre-migration identity digest preserved
```
