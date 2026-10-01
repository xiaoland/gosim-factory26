# BSL Authoring and Conformance Spike

Status: disposable task-packet experiment, not SVC source or an implementation
contract.

## Question

Can the accepted composite BSL direction express and execute one strict
outbound interaction plus one independently triggered callback while keeping
examples, matchers, generators, captures, derived values, and the Consumer
oracle separate?

The spike also asks whether WireMock `3.13.2` materially reduces the executor
work when BSL, rather than WireMock, owns generation, capture names, event
injection, replay metadata, and diagnostics.

## Falsifiable Conditions

The direction needs revision if any of these occur:

1. one normalized value cannot preserve example, matcher, generator, binding,
   and provenance as separate facts;
2. a semantically named generator is accepted without an independent
   validator;
3. callback delivery requires an implicit provider lifecycle;
4. the WireMock projection must expose Handlebars, response sequencing, proxy
   fall-through, or another engine-specific behavior in BSL;
5. invalid or unexpected traffic produces an ordinary success response;
6. a derived value needs arbitrary code or I/O inside CEL.

## Deliberately Narrow Scenario

The scenario is not based on either Anana fake server. A Consumer sends a
`POST /v1/rides` request with an RFC UUID. The responder returns a generated
opaque provider token and a syntactically valid current-style DVLA vehicle
registration mark. The conformance driver later and explicitly emits a
`ride.accepted` callback into the Consumer, deriving correlation values from
the isolated run.

The vehicle-registration claim is intentionally narrow: it means a string
conforming to the current-style DVLA syntax and published character
restrictions. It does **not** claim that DVLA issued the registration or that a
real vehicle exists.

## Contents

- [`typed-node.double.yaml`](typed-node.double.yaml): candidate YAML surface
  using local typed value nodes;
- [`authoring-surfaces.md`](authoring-surfaces.md): comparison with YAML tags
  and adjacent path maps;
- [`spike.py`](spike.py): task-only compiler/executor probe for a native Python
  responder and a pinned WireMock standalone JAR;
- [`openapi-3.1.yaml`](openapi-3.1.yaml) and
  [`contract_probe.py`](contract_probe.py): a local-only OpenAPI 3.1 operation
  and JSON Schema 2020-12 validation probe;
- [`result.md`](result.md): observed evidence and decisions after execution.

The script expects a disposable Python environment containing
`PyYAML==6.0.2`, `Faker==40.1.0`, and `cel-expr-python==0.1.3`. The WireMock path
is passed explicitly; the JAR is not stored in this repository.

The contract probe additionally uses `ruamel.yaml==0.19.1` and
`jsonschema==4.26.0`; neither is a repository dependency.
