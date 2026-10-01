# Double Exploration Evidence

Status: superseded as a requirements source. This file records historical
exploration, including Anana-derived observations rejected by Sir as a basis for
the product model. Use [`application-practice-research.md`](application-practice-research.md)
for the active evidence base.

Observed on 2026-08-09 CST. This file records task-local evidence and bounded
inferences; it is not a durable product or technical contract.

## Source Boundaries

- SVC source: `/Users/lanzhijiang/Development/svc` at
  `fc7cbc3c0ba647d41b05e9d5e9bd17977042544c`.
- Anana prior art:
  `wsl.win-ws.localhost:~/development/Anana/mvp-HA` at
  `e8c14ff9b7428588aef9a9f97af8ce81588c00be`.
- Both worktrees contained unrelated pre-existing changes. The repository
  inspection was read-only; no service or real provider was invoked. A later
  dependency feasibility check installed candidate packages only into the
  exact throw-away virtual environment recorded below; it did not change either
  repository or start a network listener.

## Current SVC Capability Boundary

- `svc.json` schema v3 is strict and committed. Its only optional runtime
  declarations are `dev.targets` and `run`.
- `svc dev` coordinates a Consumer-owned long-lived capability through a
  readiness probe, provision action, optional stop action, and scope. Once
  ready, the Consumer capability survives the starter; SVC does not own its
  application behavior.
- `svc run` coordinates one bounded Consumer-owned command and captures native
  output plus an execution receipt. A settled run is invocation evidence, not
  a cached acceptance verdict.
- The private execution store recognizes only `run` and `dev` domains.
- Root `svc status` summarizes declarations without probing or starting them.
- Consequence: neither existing domain owns a generated provider protocol, a
  behavior model, a test control plane, request observations, or test-case
  state isolation. Reusing process mechanics may be valid, but presenting a
  double as merely a `dev` target or `run` entry would hide distinct semantics.
- A top-level declaration in `svc.json` would require a supported schema
  evolution from v3. A separate manifest would avoid that immediate schema
  change only by creating another configuration authority and discovery rule.
- Earlier SVC evidence explicitly states that expanding a published strict
  `svc.json` requires a new schema and migration contract. Because current
  runtime commands require the current schema, a v4-only double declaration
  would impose migration on projects that never use the optional capability.
  The bounded alternative is an explicit Consumer test artifact selected by
  `svc double`, analogous to other explicit CLI inputs rather than a second
  project-integration configuration.

## Anana Prior Art

### Scale and evolution

Excluding installed dependencies:

| Package | TypeScript/OpenAPI/JSON lines | Commits touching package | Observed history |
| --- | ---: | ---: | --- |
| `fake-caocao-server` | 6,678 | 24 | 2026-05-31 through 2026-07-23 |
| `fake-wechatpay-server` | 1,281 | 6 | 2026-05-30 through 2026-07-17 |

Line count is not a direct effort measure, but the repeated changes and the
distribution across protocol, behavior, crypto, control, and tests show that
maintenance cost is not primarily server startup boilerplate.

### Shared shape

Both packages provide:

1. Provider-facing routes used by the application under test.
2. In-memory provider-owned state keyed by business identifiers.
3. Fake-only fixtures/credentials.
4. A separate `__fake_*` control and observation surface.
5. Explicit startup on loopback with an ephemeral port for scenario tests.
6. Package tests for the fake itself and black-box scenario tests for the
   Consumer product.

The control plane is not incidental. Tests and developer UI use it to reset
state, select outcomes, move entities through phases, inject faults, and read
external effects. This yields the practical chain:

```text
Consumer action -> provider request -> provider state/effect
-> explicit test stimulus or callback -> Consumer observation
-> control-state/request evidence
```

### Caocao Mobility

- Provider OpenAPI 3.1 covers the system-tested route subset and one status
  webhook. A separate OpenAPI 3.1 document covers fake control routes.
- A custom 414-line OpenAPI helper parses YAML, indexes operations, resolves
  local references, compiles a restricted JSON Schema subset, and validates
  path/query/form/JSON requests and JSON responses.
- The implementation remains hand-authored: order idempotency; estimates;
  `CREATED -> ACCEPTED -> ARRIVED_AT_PICKUP -> IN_TRIP -> FINISHED` behavior;
  cancellation and fee confirmation; driver movement; route caching; request
  signatures; callbacks; and callback-delivery reporting.
- Failure controls include next-create failure and the more valuable
  "provider accepted the write but the response was lost" case. State exposes
  the provider request count so retry/idempotency behavior can be checked.
- Business phase progression was moved to explicit control routes because
  polling-driven phase changes made intermediate product states impossible to
  inspect deterministically. One narrower read-like operation remains
  stateful: driver-polyline polling advances a movement query counter used to
  project position along a route. The distinction is therefore controlled
  business-state progression versus bounded presentation simulation, not a
  blanket side-effect-free read rule.

### WeChat Pay

- The package does not contain OpenAPI. Zod schemas validate requests and state
  while custom code implements RSA request/response signatures, AES-GCM
  notification payloads, certificates, transactions, and refunds.
- Fake control routes can succeed, close, or fail prepays/transactions and can
  succeed or fail refunds. State is observable and resettable.
- Scenario-browser code replaces `WeixinJSBridge` and uses the control API to
  complete the fake prepay, showing that some external-system behavior occurs
  outside the provider HTTP API itself.
- CI-shaped scenarios start a fresh server on an ephemeral port and inject its
  origin and fake credentials. Long-lived local development instead uses a
  stable fake certificate fixture and stable routed origin so a persisted local
  provider configuration does not drift across restarts.

### Prior-art implications

- OpenAPI can remove duplicated route/schema work and detect some drift, but it
  did not remove the dominant behavioral code in the more valuable double.
- A useful state-changing double needs an explicit test-control surface. Hiding
  control in magic request headers would mix provider protocol with test intent.
- Entity-keyed state and idempotency matter more than one global scenario
  string for payment and booking systems.
- Callbacks must be observable operations with delivery result, not fire-and-
  forget background decoration.
- Determinism requires explicit reset or isolated instance identity. A shared
  long-lived developer double and a per-run CI double need different lifecycle
  policies while preserving the same declared behavior.
- Fake credentials are legitimate committed fixtures only when unmistakably
  fake and restricted to the double boundary. Real credentials are neither
  required nor accepted as ordinary double inputs.

## Standards and Tool Benchmark

Primary sources checked on 2026-08-09:

- [OpenAPI 3.2.0](https://spec.openapis.org/oas/v3.2.0.html) describes HTTP API
  operations, examples, links, callbacks, and webhooks. A callback can derive
  its target from runtime request/response data. It does not define the
  provider's business state machine or when a test should trigger a callback.
- [Arazzo 1.1.0](https://spec.openapis.org/arazzo/latest.html) describes
  sequences and dependencies across OpenAPI/AsyncAPI operations, carries
  values between steps, and expresses success/failure criteria. Its semantic
  center is how a consumer achieves an outcome; it is not a provider-double
  state implementation. It may become valuable acceptance/workflow input
  without replacing a behavior model.
- [OpenAPI Overlay 1.1.0](https://spec.openapis.org/overlay/latest.html)
  repeatably transforms OpenAPI descriptions. It can add test examples or
  metadata without forking an upstream contract, but does not itself add
  runtime behavior.
- [Prism](https://github.com/stoplightio/prism) serves examples or
  schema-generated responses and validates OpenAPI requests. It demonstrates
  the low-cost contract-only tier, not the full Anana behavior tier.
- [WireMock stateful behavior](https://wiremock.org/docs/stateful-behaviour/),
  [callbacks](https://wiremock.org/docs/webhooks-and-callbacks/),
  [verification](https://wiremock.org/docs/verifying/), and
  [faults](https://wiremock.org/docs/simulating-faults/) confirm that mature
  doubles separately model scenario state, outbound effects, request journals,
  and transport failure. Its global named-scenario model and JVM runtime are
  implementation candidates/benchmarks, not automatically SVC's product model.
- [Pact provider states](https://docs.pact.io/getting_started/provider_states)
  are isolated preconditions for individual consumer interactions. That is
  useful contract-test vocabulary but deliberately avoids dependent multi-step
  integration state, so it does not replace the target end-to-end workflow.

## Candidate Responsibility Model

The evidence supports evaluating five distinct responsibilities rather than
one undifferentiated mock file:

| Responsibility | Candidate authority | Required observable proof |
| --- | --- | --- |
| Provider protocol | OpenAPI/other protocol description | Requests and responses conform to the selected operation contract |
| Behavior and state | Small explicit behavior declaration, extension, or Consumer implementation | Writes, idempotency, transitions, and query results remain coherent |
| Fake fixtures | Committed fake-only data plus optional local overlay | Development and CI get usable non-real credentials without drift or disclosure |
| Control and observation | Generated stable test-control contract | Tests can reset, arrange, act, inject faults, and inspect interactions deterministically |
| Runtime isolation | SVC lifecycle and workspace/run identity | Concurrent tests do not share unintended state; local reuse is explicit |

This table is an evidence-backed decomposition, not yet a decision that SVC
must implement all five layers itself.

## Isolated OpenAPI Runtime Feasibility

An isolated virtual environment under
`/tmp/svc-double-openapi.AhJLQj/venv` installed `openapi-core==0.23.1` and
`PyYAML==6.0.3`. No SVC environment or lockfile changed; the exact 32 MB
temporary directory was moved to Trash after the checks.

The bounded executable checks proved:

- OpenAPI 3.1 JSON request matching, path-parameter extraction, body
  unmarshalling, invalid-body rejection, and response validation through the
  official Werkzeug adapters;
- OpenAPI 3.2 validator selection;
- local component-reference resolution and
  `application/x-www-form-urlencoded` unmarshalling under OpenAPI 3.2.

This is sufficient to reject a custom OpenAPI validator in the first slice.
It is not yet proof for every OpenAPI feature or malformed document class; the
double compiler still needs to admit a deliberately narrow document subset and
test its own operation/example indexing.

Dependency cost is material. `openapi-core` brings Werkzeug plus the
`jsonschema`, OpenAPI schema/spec validator, reference/path, settings, and
support-library families. Several overlap SVC's existing Pydantic and dotenv
stack, but this is still a larger runtime footprint than adding YAML parsing
alone. Dependency admission therefore belongs in the CLI behavioral MINOR and
must be verified through the built wheel on every supported platform.

## Open Questions for the First Slice

1. Is the minimum honest product a contract-only double, or must the first
   release include entity state and explicit transitions to meet the motivating
   product promise?
2. Should behavior be a language-neutral data model, a narrow generated control
   plane over examples, or an adapter to Consumer code? Which option materially
   reduces the 6,678-line Caocao cost rather than moving it?
3. Is OpenAPI 3.1 the initial compatibility floor, with 3.2 syntax accepted
   only when the chosen parser fully supports it?
4. Does Arazzo belong in the first slice as acceptance workflow input, or later
   after the provider behavior/control model is stable?
5. What is the isolation key: process, workspace, test run, named scenario, or
   explicit instance? How does a black-box test discover the provider origin
   and fake fixture values without parsing human logs?
6. What observation contract is sufficient for CI: raw request journal,
   operation/count queries, state snapshots, unmet expectations, or a bounded
   combination?
7. How are callback destinations constrained so a declaration cannot turn an
   ordinary local double into an arbitrary network writer?
