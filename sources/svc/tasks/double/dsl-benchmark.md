# Mature DSL and Runtime Benchmark

Status: preliminary and superseded as a selection basis. This comparison used
a behavioral surface derived from rejected Anana pressure cases. Its source
notes remain historical only; use
[`runtime-decision-v2.md`](runtime-decision-v2.md). It does not authorize a
runtime dependency, grammar, or source mutation.

## Decision Question

Can SVC adopt a mature authoring language and runtime instead of inventing both
the `*.double.yaml` semantics and their interpreter?

The two Anana pressure cases require all of the following in one coherent
model:

1. OpenAPI remains authoritative for provider request, response, and callback
   shapes.
2. A request can capture values for later requests and effects.
3. Provider behavior can depend on explicit scenario state.
4. A test can perform a separate control action that changes that state.
5. That action can emit a callback using previously captured values.
6. The result is deterministic, locally isolated, inspectable, and usable in CI
   without arbitrary scripts or real provider credentials.

The fifth condition is important. OpenAPI callbacks and most mock-server
webhooks describe an effect associated with the current provider request. The
real examples also need a later test action such as `succeed` to complete an
earlier payment or trip and only then notify the Consumer.

## Candidate Comparison

| Candidate | Useful mature semantics | Material mismatch for SVC double | Disposition |
| --- | --- | --- | --- |
| OpenAPI callbacks | Callback paths, request shapes, examples, and runtime expressions are standardized | No scenario state, cross-request store, test-control action, or runtime | Keep as callback protocol authority, not the complete behavior DSL |
| Arazzo | Describes ordered API calls and dependencies | Models a Consumer workflow, not a reactive provider | Vocabulary reference only |
| SCXML | General event/state-machine model with conditions, data assignment, and sends | XML, broad executable semantics, script/data-model choices, and no OpenAPI binding | Semantic reference, not the authoring format |
| WireMock | Familiar JSON stubs, named scalar scenarios, request matching, journals, and declarative webhooks | OSS has no native OpenAPI import; scenario state is too small for captured cross-request memory; JVM runtime; callbacks normally bind to a served request | Borrow scenario vocabulary if needed; do not select as-is |
| Hoverfly | Simulation schema, state requirements/transitions, state-aware templates, control API | No OpenAPI authority; outbound post-serve actions require a script or a separate remote handler | Strong state reference, incomplete runtime fit |
| MockServer | OpenAPI expectations, OpenAPI callbacks, HTTP before/after actions, faults, and request logs | No simple explicit scenario machine; effects are centered on the matching request; JVM runtime | Strong callback reference, incomplete scenario fit |
| Mockoon | OpenAPI import, templates, mutable variables/data buckets, and callbacks | Ordinary routes are stateless; state is implicit mutation; imported environment can drift from OpenAPI; Node/Mockoon runtime | Close feature list, weak behavioral authority |
| Imposter 5 | OpenAPI plugin, declarative request capture, named stores, store-aware templates/matching, remote HTTP steps, REST store control, native binary | State is generic key/value data rather than a named scenario graph; overrides identify path/method rather than stable `operationId`; full engine permits scripts and other nondeterministic/unsafe surfaces | Closest executable candidate; test as a strict profile before designing a new DSL |

Primary references:

- [OpenAPI callback objects and runtime expressions](https://spec.openapis.org/oas/latest.html#callback-object)
- [Arazzo Specification](https://spec.openapis.org/arazzo/latest.html)
- [W3C SCXML 1.0](https://www.w3.org/TR/scxml/)
- [WireMock stateful behaviour](https://wiremock.org/docs/stateful-behaviour/)
  and [webhooks/callbacks](https://wiremock.org/docs/webhooks-and-callbacks/)
- [Hoverfly simulation schema](https://docs.hoverfly.io/en/stable/pages/reference/simulationschema.html)
  and [post-serve actions](https://docs.hoverfly.io/en/latest/pages/keyconcepts/postserveaction.html)
- [MockServer OpenAPI support](https://www.mock-server.com/mock_server/using_openapi.html)
  and [before/after actions](https://www.mock-server.com/mock_server/before_and_after_actions.html)
- [Mockoon OpenAPI import](https://mockoon.com/docs/latest/openapi/import-export-openapi-format/),
  [global variables](https://mockoon.com/docs/latest/variables/global-variables/),
  and [callbacks](https://mockoon.com/docs/latest/callbacks/overview/)
- [Imposter OpenAPI plugin](https://docs.imposter.sh/openapi_plugin/),
  [data capture](https://docs.imposter.sh/data_capture/),
  [stores](https://docs.imposter.sh/stores/),
  [templates](https://docs.imposter.sh/templates/), and
  [steps](https://docs.imposter.sh/steps/)

## Finding

There is no single standard DSL to adopt without qualification. The closest
answer is not “write a new YAML language now,” but “first test whether a closed
profile of Imposter is sufficient.” This preserves mature syntax, examples,
documentation, and runtime behavior for Humans and Agents while keeping SVC's
product semantics narrower than the underlying engine.

An SVC Imposter profile would admit only:

- local OpenAPI files and local references;
- OpenAPI-backed resources;
- deterministic request matching and response examples;
- declarative capture into an in-memory per-instance store;
- deterministic store reads and updates;
- remote HTTP steps used only for declared callbacks;
- loopback control routes, state inspection, and reset.

It would reject at least:

- arbitrary scripts or plugins;
- random/time-dependent templates unless explicitly frozen;
- remote specifications or remote `$ref` resolution;
- external/persistent stores;
- undeclared outbound destinations;
- ambiguous first-match behavior;
- real credentials.

This profile is still an SVC product contract. Existing engine syntax reduces
language invention and improves Agent priors, but SVC must validate the subset
instead of exposing every engine feature accidentally.

## Callback Boundary

Callbacks should be modeled in two layers:

1. OpenAPI owns the callback HTTP contract: destination expression, request
   shape, examples, and responses.
2. Scenario behavior owns *when* a named callback is emitted and which captured
   provider request supplies its runtime values.

This leaves only a small piece of custom behavior semantics: “control action
`succeed` advances request instance X and emits callback Y.” It avoids copying
the callback body and headers into a second DSL.

Neither OpenAPI nor an off-the-shelf mock engine can make provider-specific
cryptography disappear. WeChat Pay signing and encryption require one of three
explicit choices: committed fake-only fixtures, a narrowly owned transform
adapter, or an admitted escape hatch. Arbitrary embedded code is not the MVP
default.

## Bounded Fit Spike

Before selecting Imposter or writing an SVC-native runtime, encode only these
two executable slices without changing SVC source:

- WeChat Pay: create payment, capture order/callback data, test action marks it
  paid, emit notification, then return paid on query.
- Caocao: create/order progression, capture order/callback data, test action
  advances the trip, emit webhook, then expose the new status.

Use no scripts. Record:

- declarations and duplicated contract facts;
- whether callback bodies can stay in OpenAPI;
- whether a control action can reliably address one earlier request;
- whether reset and parallel-instance isolation are sufficient;
- which engine features the strict profile must prohibit;
- runtime acquisition, pinning, offline, and cross-platform costs;
- equivalent minimal SVC-native notation size and semantic clarity.

Selection rule: adopt the strict existing profile only if both cases are
faithful without scripts and without duplicating callback protocol truth. If
not, the failed encodings become concrete evidence for the smallest necessary
SVC-native language rather than a speculative DSL design.
