# Spike Result

Status: completed on 2026-08-10. This is local feasibility evidence, not an
admission of product syntax, dependencies, or runtime.

## Environment and Reproduction

- host: macOS 15.4.1, arm64;
- Python: 3.12.10;
- Java: 17.0.15;
- Docker: not installed;
- disposable Python packages: `PyYAML==6.0.2`, `Faker==40.1.0`, and
  `cel-expr-python==0.1.3`;
- WireMock: standalone `3.13.2`, 19,530,671 bytes, SHA-256
  `d097b19bd483c5038479b13a5c71e9faf8f2f5106584f0c120a7770ab0bdb367`.

The retained reproduction script is [`spike.py`](spike.py). Binary and Python
environments were disposable and are not repository dependencies. After the
final sequential and two-process parallel reproductions, the complete temporary
environment (including the WireMock JAR and inspected CEL source checkout) was
moved to Trash as one recoverable directory.

## Result Summary

| Question | Observed result | Consequence |
| --- | --- | --- |
| Can one value keep its roles separate? | Yes. The typed node compiled example/matcher/bind and generator/matcher/bind into distinct normalized facts. | Keep a local typed authoring node and path-indexed IR; do not admit the `$bsl` spelling yet. |
| Does a semantic generator name establish validity? | No. Faker's `en_GB license_plate()` produced `IC10 YNI` at seed `123`; the independent DVLA-syntax validator rejected it. | Generator capability, authority, locale, version, and post-validator are all normative. |
| Can generation replay? | Yes. The spike adapter produced `BJ16 JDB` twice at seed `123`, and the validator accepted the declared narrow syntax claim. | Replay identity is feasible but remains version-bound. |
| Can CEL perform bounded derivation? | Yes. Capture lookup/concatenation worked; a string-plus-integer error carried line/column diagnostics; undeclared `env()` was rejected. | CEL remains suitable only under an explicit BSL environment/profile. |
| Can standard CEL exceed the intended v0 profile? | Yes. The standard environment compiled `map`; an `exclude_macros` profile rejected `map`, `filter`, `all`, `exists`, and `exists_one`. | BSL must normatively configure CEL and bound expression/input size; the library default is not the language. |
| Can native and WireMock responders execute one IR? | Yes. Both returned the same materialized response and response hash; retry returned the same named outcome. | BSL semantics can remain executor-independent for this slice. |
| Do strict failures work? | Yes. Invalid UUID and undeclared route both returned `404` in both executors. | Fail-closed projection is feasible. |
| Are failures useful? | WireMock returned 1,327 bytes of near-miss diagnostics for the invalid UUID; the toy native responder returned an empty body. | A native executor must budget for first-class mismatch diagnostics; WireMock is a useful behavior reference. |
| Can callback remain independent? | Yes. The test explicitly emitted the event after the outbound request; the Consumer receiver returned `204`; correlation and exact emitted bytes matched. | Event injection needs no provider lifecycle or timer. |
| Can runs remain isolated? | Two concurrent full probes used different external UUIDs and produced different callback hashes; each WireMock journal saw only its own two matching requests. | Per-run process/root/journal isolation is mechanically feasible. |

The normalized IR hash for the final provenance/contract-bearing reference run
was `454074b653761845d24c7e4083ce01ce17983a928c91444996bf8942db8dc4e8`.
The native and WireMock response SHA-256 was
`7b579ee8ccbe7ae29166f2b9f7201a3d549278df87c3d29636bb972a9ca25732`.
The callback raw-body SHA-256 was
`3afdb0dfe99aeaaa36e59130eac25f0ff4eb641bb0a982204a6ee0663d7524a6`.

## Semantic Generator Counterexample

The [Faker `en_GB` automotive provider](https://github.com/joke2k/faker/blob/v40.1.0/faker/providers/automotive/en_GB/__init__.py)
uses the broad patterns `??## ???` and `??##???` and cites Wikipedia as its
source. The official [DVLA registration guidance](https://dvlaregistrations.dvla.gov.uk/help/search.html?id=1&search_text=%2A)
states that a current-style mark is two letters, two digits, and three letters;
it cannot contain `I` or `Q`, and `Z` cannot appear in the first two letters.

For a deterministic 10,000-value probe at seed `20260810`, the independent
canonical-display validator classified Faker output as:

| Classification | Count |
| --- | ---: |
| Accepted canonical current-style syntax | 3,100 |
| Structurally valid after inserting the canonical space | 3,123 |
| Contained forbidden `I` or `Q` | 3,250 |
| Used `Z` in the two-letter memory tag | 527 |

This is not a statistical quality claim about Faker. It is a deterministic
counterexample to `semantic function name => semantic validity`. It also
clarifies the semantic ID: the spike validates current-style **syntax**, not
issuance, existence, vehicle identity, or provider acceptance. The DVLA adapter
is deliberately a project/spike capability, not a proposed SVC built-in.

## CEL Finding

Official `cel-expr-python==0.1.3` supplied CPython 3.11–3.14 wheels for macOS
x86-64/arm64, manylinux x86-64/aarch64, and Windows amd64; the wheels are
roughly 8–17 MB and no source distribution was published in the inspected
release metadata. The local arm64 wheel compiled and evaluated the required
typed expressions with useful source diagnostics.

The package's own [v0.1.3 environment configuration tests](https://github.com/cel-expr/cel-python/blob/v0.1.3/cel_expr_python/cel_env_test.py)
document `exclude_macros`. The spike used that official mechanism to remove all
iterative standard macros. The repository's conformance target references the
official CEL corpus, but the installed wheel does not bundle that corpus: a
plain installed-package discovery ran zero conformance cases. The upstream
workflow runs Bazel tests on Ubuntu only and its source has explicit skipped
conformance cases, including a macOS double-to-string difference and a Windows
time-zone group.

Conclusion: the semantic choice is stronger than before, but the dependency is
not automatic. BSL v0 should specify a CEL profile with no extensions, no
iterative macros, declared typed variables only, and host limits on expression
length and bound input size. SVC must add its own focused cross-platform corpus
for the exact profile if implementation is authorized.

## Runtime Comparison

WireMock `3.13.2` started in 0.648 seconds in the final local run and used about
108,688 KiB RSS. These are one-machine observations, not benchmarks. It supplied
mature request matching, a journal, stable `404` behavior, and useful near-miss
diagnostics. The BSL projection remained narrow: one static JSON mapping with a
JSONPath/regex request matcher and a pre-materialized response. Response
templating, random helpers, scenarios, webhooks, proxying, and implicit
sequencing were not enabled.

WireMock did **not** eliminate the BSL-owned work: semantic generation and
validation, replay reporting, named captures, event materialization/injection,
egress policy, and normalized diagnostics all remained outside it. It also adds
a Java runtime and a 19.5 MB artifact to a currently Python-only CLI; Docker was
not available on the probe host.

The toy native responder had zero external runtime/distribution cost and passed
the same strict response cases, but its empty mismatch diagnostics demonstrate
that a production native executor is not “just an HTTP server.” Protocol
limits, useful mismatch trees, journals, concurrency, shutdown, and malformed
input remain real product work.

Provisional runtime conclusion: keep WireMock as a pinned conformance/reference
executor and possible opt-in adapter, but do not make it the default MVP
dependency. Continue toward a narrow native executor contract; choosing its
Python HTTP foundation remains an implementation design decision.

## OpenAPI 3.1 Contract Probe

[`contract_probe.py`](contract_probe.py) selected `POST /v1/rides` from a local
OpenAPI `3.1.0` document and used `jsonschema==4.26.0` plus an immutable
`referencing` registry to resolve local component references. The materialized
request and response passed their selected JSON Schema 2020-12 shapes;
replacing the vehicle registration with `random` failed the response pattern.

The same probe showed that `format: uuid` is annotation-only unless the
validator explicitly enables a format checker: `not-a-uuid` passed structural
validation. BSL therefore cannot treat OpenAPI `format` as an automatically
enforced semantic matcher. It must declare which formats are assertions and
keep provider/project semantic validators separate.

The narrow feasible contract is:

- local OpenAPI 3.1 operation selection by method/path;
- local `$ref` resolution only, with remote retrieval absent;
- request/materialized-response Schema Object validation;
- explicit report claim `selected-operation-schema`;
- explicit non-claims for provider behavior and full OpenAPI-document
  conformance.

Supporting OpenAPI 3.0, custom Schema Object dialects, remote references, or
full document conformance needs separate evidence and dependencies. OpenAPI
examples remain examples, never generated business outcomes.

## Callback Body Modes

The callback probe materialized a structured JSON value into declared
`json.compact-utf8/v1-spike` bytes and then proved that the receiver observed
those exact bytes. This does not prove fidelity to provider-captured or signed
bytes.

BSL should therefore make two body modes mutually exclusive:

1. `raw`: managed opaque bytes with provenance and content hash; no typed
   in-place derivation;
2. `structured`: typed values plus a declared serialization identity; no claim
   that provider raw canonicalization is preserved.

If a callback needs both derived fields and provider-specific signing or
canonicalization, it crosses the narrow external materializer boundary. BSL
should not grow signing helpers or an arbitrary byte-template language.

## Surface Syntax Finding

The local typed node won the authoring decision table in
[`authoring-surfaces.md`](authoring-surfaces.md). YAML tags couple the abstract
language to YAML-specific constructors; adjacent matcher/generator path maps
create refactor drift and force reviewers to join multiple trees.

The first run also failed because unquoted `2026-08-10T10:00:00+08:00` was
resolved by `PyYAML.safe_load` as a Python `datetime`. A follow-up parser probe
used pure-Python `ruamel.yaml==0.19.1` in YAML 1.2 mode. It correctly kept
`yes`/`on` as strings, rejected duplicate keys, and exposed key/value source
locations, but also implicitly constructed the timestamp. Installing a local
timestamp constructor that returns the scalar text preserved the clock as a
string while keeping integers and booleans typed.

The inspected `ruamel.yaml` release is a 118,102-byte platform-independent
wheel with a source distribution and no dependencies; its installed pure
Python package occupied about 1.3 MB. It is a stronger parser candidate than a
custom PyYAML source-map/resolver layer, but not yet an admitted dependency. A
product parser must pin and test scalar resolution, duplicate-key rejection,
unknown-key/tag rejection, source locations, byte/node/depth limits, and an
explicit escape for a literal provider object colliding with the reserved
typed-node key. Anchors, aliases, and merge keys should be rejected in v0 to
avoid hidden overrides and expansion hazards.

## Admitted and Not Admitted

Admitted as research direction:

- local typed value nodes compile to a path-indexed normalized IR;
- a restricted, typed CEL profile is feasible;
- semantic generator adapters and validators are separate registry
  capabilities;
- callbacks are explicit independent events;
- raw and structured body modes are distinct;
- a local-only OpenAPI 3.1 selected-operation schema profile is feasible;
- WireMock is a reference/optional adapter, not the default MVP dependency.

Not admitted:

- `$bsl`, `svc.bsl/v0`, or any exact grammar/key spelling;
- a repository dependency on PyYAML, ruamel.yaml, jsonschema, Faker, CEL,
  WireMock, or Java;
- the DVLA generator/validator as an SVC-owned domain capability;
- a concrete native HTTP library, CLI/configuration surface, or source design;
- arbitrary CEL, engine templates, automatic callbacks, state machines, or a
  code-backed service as the ordinary path.
