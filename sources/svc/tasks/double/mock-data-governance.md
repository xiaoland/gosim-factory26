# Mock Data Governance

Status: active research addendum, not an implementation contract. This corrects
the overly broad rejection of mocks and the misleading “fixture-first” wording
in the earlier V2 documents.

## Correction

Mocking is not the problem. Mature matchers, generators, interceptors, contract
tools, and fake-data libraries are valuable. The dangerous pattern is a
**test-local answer fixture**:

- a large payload is hard-coded beside one test;
- its source, provider version, ownership, and refresh path are absent;
- it simultaneously defines the external stimulus and the expected product
  result;
- arbitrary type-correct values are mistaken for semantically valid values;
- the test passes because the implementation and its “exam answer” were authored
  from the same invented example.

The active design therefore moves from “fixture-first” to
**contract-, matcher-, and generator-led data**, with managed fixtures as one
explicit value source.

## Useful Precedents

### Matchers and examples are different things

[Pact matching](https://docs.pact.io/getting_started/matching) separates an
example value returned by the mock server from the rule used to verify the
provider. Pact V4 stores matching rules and generators independently for HTTP
body, header, path, query, metadata, and status
([specification](https://github.com/pact-foundation/pact-specification/blob/version-4/README.md)).

[Spring Cloud Contract](https://docs.spring.io/spring-cloud-contract/reference/project-features-contract/dsl-dynamic-properties.html)
similarly distinguishes Consumer/stub and producer/test values, and represents
dynamic fields through matchers rather than forcing every test to freeze an ID
or timestamp.

SVC does not need to adopt either product wholesale. It should preserve this
semantic separation:

```text
example instance != matching contract != generation rule != product oracle
```

### Structural type is weaker than field semantics

[JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation)
explicitly states that structural validation can be insufficient and uses
`format` to carry semantic information. It also warns that format validation
support varies and may be annotation-only. A `string` type therefore cannot
justify a generated value by itself.

WireMock's documented `randomValue` helper can generate an alphanumeric string,
UUID, number, and related primitives
([response templating](https://wiremock.org/docs/response-templating/)). That is
appropriate for an explicitly opaque token; it is not a valid vehicle
registration generator merely because both values are strings.

Semantic fake-data libraries are a better source when their scope matches the
field. Python Faker exposes `license_plate()` and `vin()` through an automotive
provider ([documentation](https://faker.readthedocs.io/en/master/providers/faker.providers.automotive.html));
Faker.js distinguishes a vehicle registration mark and VIN
([vehicle API](https://fakerjs.dev/api/vehicle.html)). This still does not prove
provider validity: locale, implementation version, and an independent matcher
or validator remain necessary.

The BSL conformance spike supplied a concrete counterexample. Faker `40.1.0`'s
`en_GB license_plate()` declares only the shapes `??## ???` and `??##???` and
cites Wikipedia. At seed `123` it generated `IC10 YNI`; official DVLA guidance
for current-style marks excludes `I` and `Q`, and excludes `Z` from the first
two letters. An independently sourced validator rejected the output. In a
deterministic 10,000-value probe, only 3,100 values passed the canonical-display
syntax validator; 3,250 contained `I` or `Q`, 527 placed `Z` in the memory tag,
and 3,123 were otherwise valid only after inserting the canonical space. See
[`spikes/bsl-authoring-conformance/result.md`](spikes/bsl-authoring-conformance/result.md).

This does not make Faker categorically unsuitable. It proves that a semantic
method name and locale are not authority. A registry capability must state its
actual semantic scope and authority; the compiler must reject a declared field
semantic when the selected generator does not claim that capability, even if a
post-validator might catch many outputs at runtime.

### Randomness must be replayable and versioned

[Faker.js reproducibility guidance](https://fakerjs.dev/guide/usage.html) allows
a seed but warns that identical seeds can produce different values after a
library upgrade and that relative-date generators also need a fixed reference
clock. Therefore a seed without generator identity/version and clock is not
reproducibility.

## Data Roles

Every dynamic or nontrivial leaf value in a boundary response/event has one
role. Roles are language semantics, not comments:

| Role | Meaning | Example |
| --- | --- | --- |
| `constant` | Exact value is part of the documented contract | Enum `SUCCESS`, error code `INVALID_REQUEST` |
| `example` | Concrete value used to materialize one interaction; not itself the contract | One documented payment identifier |
| `captured` | Sanitized value or payload observed from a real/test provider | Webhook body captured at a stated provider version |
| `derived` | Deterministic value computed from request/run context | Callback correlation ID copied from an outbound request |
| `generated` | Value produced by a named semantic generator and checked by a matcher | Locale-specific vehicle registration |
| `synthetic` | Artificial value/effect used only for a resilience claim | Invalid signature or overlong field |

Bare literals remain valid for small `constant` or documented `example` values.
Large response bodies and events should not silently collapse all leaves into
untyped literals.

## Semantic Value Contract

A generated value needs four independently visible parts:

```text
semantic intent + generator implementation + constraints/matcher + replay context
```

### 1. Semantic intent

The field declares what it means, not only its storage type. Names are
namespaced to avoid false universality:

- standards: `rfc.uuid`, `rfc.date-time`, `iso.currency-code`;
- intentionally opaque values: `opaque.provider-token`;
- library-owned semantics: `faker.vehicle.vrm`;
- provider/project semantics: `provider.caocao.vehicle-registration`.

SVC must not infer authority from a field name such as `license_plate`. An Agent
may suggest a semantic type, but the descriptor must select it explicitly and
cite its authority.

### 2. Generator implementation

The language references a generator capability, not an unqualified `random`:

- provider/library and exact version;
- operation name;
- locale/region where applicable;
- arguments and permitted output type.

SVC can own a very small portable set such as UUID, bounded integer/decimal,
fixed-clock timestamp, and opaque token. Domain libraries remain adapters or
project/provider extensions so SVC does not become the owner of every country's
vehicle, address, payment, and identity rules.

### 3. Constraints and matcher

Generated output is validated after generation against all available layers:

- JSON/OpenAPI type and structural constraints;
- standard `format` when assertion support is known;
- explicit regex/enum/range/predicate;
- a provider/project semantic validator where needed.

Generation success without validation is a runtime failure. `string` plus a
generator name is insufficient.

### 4. Replay context

Every run records:

- generator identity and version;
- locale;
- seed;
- fixed reference clock/time zone when time is involved;
- resulting value hash or sanitized value, depending on redaction policy.

The deterministic PR/CI lane uses an explicit replayable seed. A later challenge
lane may vary seeds, but failures must print a complete replay context.

## Managed Fixture Contract

Fixtures are permitted when they are the honest representation—for example, a
captured webhook envelope, binary body, or provider-documented error. They are
managed assets rather than anonymous test literals.

Each managed fixture has:

- stable logical name and content hash;
- owner and consumers;
- `captured`, `documented`, or `contract` provenance;
- source URL/provider environment/version and capture time where applicable;
- sanitization statement;
- schema/operation identity;
- semantic fields it intentionally fixes;
- refresh/probe command or an explicit “no automated refresh” statement;
- last successful structural/semantic validation result.

Small exact constants may remain inline. Larger reusable payloads live outside
individual test bodies and are imported by logical name. Centralization alone
does not solve drift; validation and an independent provider-backed lane remain
necessary.

## Preventing the Double from Writing Its Own Exam

SVC cannot prove epistemic independence, but the language and reports can make
self-confirming tests harder to create and easier to review.

### Authority separation

- The scenario defines external boundary conditions and stimuli.
- The Consumer test defines product assertions.
- The provider contract/probe validates boundary truth where possible.
- The scenario file cannot declare the Consumer's expected UI, database, or
  product-domain result.

### Example/matcher/generator separation

The runtime reports which response fields were fixed examples, which were
generated, and which contract/matcher validated them. A large literal body with
no matcher/provenance is visible technical debt, not an ordinary green path.

### Assertion-coupling report

If a Consumer test obtains a generated value from the double and asserts that
the same value is displayed, that can be a legitimate propagation claim. It
must be reported as such; it does not prove independent business correctness.
The language should distinguish:

- `propagation`: Consumer preserves/displays a provider value;
- `interpretation`: Consumer maps provider input to independently specified
  product behavior;
- `resilience`: Consumer remains safe under an artificial fault.

This claim class belongs in scenario metadata and clarifies what a pass means.

### Challengeability

The same scenario should be materializable with another valid seed or another
contract-valid example without rewriting the Consumer assertion, except where
the claim intentionally concerns one exact constant. This becomes a valuable
future lint/challenge check; it is not an excuse to add nondeterminism to the
default CI lane.

## Required Guardrails

| ID | Guardrail |
| --- | --- |
| D1 | No generic random string for a field with declared or inferable domain semantics; an explicitly opaque token is allowed. |
| D2 | Generated values must declare semantic intent, generator/version, replay context, and matcher/validator. |
| D3 | Generator locale and reference clock are explicit when applicable. |
| D4 | Generator upgrades invalidate prior replay identity and require conformance regeneration. |
| D5 | Managed fixtures carry provenance, ownership, sanitization, validation, and refresh metadata. |
| D6 | Scenario artifacts cannot encode Consumer product verdicts. |
| D7 | Reports distinguish fixed example, captured, derived, generated, and synthetic values. |
| D8 | A contract-valid variation must be possible for non-constant fields, even if the MVP only proves it with a second fixed seed. |
| D9 | Inline exact literals are limited to values whose exactness is intentional and reviewable. |
| D10 | Structural/schema validity never implies provider business validity. |

## Impact on the Product Direction

- Mock libraries are implementation resources, not a rejected category.
- “Fixture-first boundary harness” is withdrawn.
- The first slice should be described as a **managed boundary interaction
  harness** driven by contracts, matchers, semantic generators, captures, and
  managed examples.
- The actual authoring language must make these roles first-class. YAML alone
  cannot do that; the language decision is recorded in
  [`language-decision.md`](language-decision.md).
