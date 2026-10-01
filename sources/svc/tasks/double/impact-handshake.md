# Impact Handshake: First Scenario-Double Slice

Status: superseded, not an approval candidate. It predates the application-
practice evidence reset and cannot authorize source mutation. Sir removed
`svc double check` and all Consumer run-entry orchestration from the MVP after
this draft was written. It will be replaced only after the V2 boundary is
aligned. SVC source mutation remains paused.

## Decision Requested

Admit an optional CLI behavioral MINOR whose product nucleus is a deterministic,
isolated **scenario double**:

- the Consumer passes a local `*.double.yaml` artifact explicitly to
  `svc double`; `svc.json` remains schema v3 and unchanged;
- a local OpenAPI 3.1 or 3.2 document owns provider HTTP shape, while the double
  definition owns only bounded test behavior, state, captures, examples,
  callbacks, and completion expectations;
- each serve/check instance owns one scenario state and one bounded business
  flow, with a provider listener and a separate control listener on loopback;
- `serve` is attached development runtime; `check` runs one existing committed
  `run` entry against a fresh instance and qualifies only the declared double
  interaction, not the entire product requirement;
- cryptography, arbitrary code, remote inputs, production serving, a general
  entity store, and shared background lifecycle remain outside the first slice.

The exact proposed grammar is:

```text
svc double validate DEFINITION [--repo REPO] [--json|--json-schema]
svc double serve DEFINITION --scenario NAME [--repo REPO] \
  [--provider-port PORT] [--control-port PORT]
svc double check DEFINITION --scenario NAME --run ENTRY [--repo REPO] \
  [--json|--json-schema]
```

`REPO` defaults to the current directory. A relative definition path resolves
from the resolved workspace root; referenced OpenAPI/fixture files resolve from
the definition directory. All admitted files must remain inside that workspace,
all references must be local, and both listeners bind only `127.0.0.1`.
`serve` intentionally has no JSON mode in this slice because it is a live
attached process, not one terminal machine result.

## Address and Object

Only the following source addresses are in scope. Discovery that requires a
different durable owner, configuration schema, framework, or workflow returns
to discussion before mutation.

### Canonical product and operational owners

- `src/sections/prd.md`: add the observable external-system scenario-double
  promise, explicit non-promises, and first-slice product boundary.
- `src/sections/product-tdd.md`: add authority topology, definition/compiler /
  runtime/control/check contracts, qualification semantics, and the two
  state-changing pressure-test oracles.
- `src/sections/deployment.md`: add loopback-only lifetime, exact readiness,
  callback egress, interruption, cleanup, and ephemeral-state recovery rules.
- `src/index.md`: route readers to the new double guidance.
- `README.md`: add concise installed-CLI discovery and example commands without
  becoming a second contract owner.
- `changes/unreleased/double-corpus.yaml` and
  `changes/unreleased/double-cli.yaml`: record respectively one optional corpus
  MINOR (`Migration: not-required`) and one CLI MINOR
  (`Migration: not-applicable`).

### Package, dependency, and architecture boundary

- `svc_cli/pyproject.toml` and `pdm.lock`: admit bounded runtime dependencies on
  `openapi-core>=0.23.1,<0.24` and `PyYAML>=6,<7`. Werkzeug arrives through
  `openapi-core`; no Flask/ASGI/server framework is added.
- root `pyproject.toml`: register every new module with mypy and extend existing
  import-linter domain lists so shared workspace/execution/file/release modules
  remain independent of `svc_cli.double`, while the double application service
  remains independent of CLI projection and output-schema registry modules.

### Runtime and command implementation

- `svc_cli/src/svc_cli/double/__init__.py`: narrow public application-service
  exports only.
- `svc_cli/src/svc_cli/double/definition.py`: strict Pydantic declaration
  models, YAML/JSON loading, workspace-contained path resolution, and stable
  definition digest inputs.
- `svc_cli/src/svc_cli/double/openapi.py`: OpenAPI document admission,
  `operationId`/named-example index, official adapter validation, local-ref-only
  enforcement, and request/response construction data.
- `svc_cli/src/svc_cli/double/compiler.py`: pure compilation of one named
  scenario, closed value references, capture/patch type checks, transition
  determinism, exports, callbacks, and completion expectations into immutable
  intent.
- `svc_cli/src/svc_cli/double/runtime.py`: one lock-protected ephemeral state,
  atomic transition commits, bounded semantic history/mismatches, reset/action
  operations, callback outcome recording, and completion qualification.
- `svc_cli/src/svc_cli/double/server.py`: separate threaded Werkzeug WSGI
  provider/control applications, loopback listeners, readiness identity,
  deterministic diagnostics, graceful shutdown, and the admitted
  commit-then-disconnect fault.
- `svc_cli/src/svc_cli/double/service.py`: `validate`, foreground `serve`, and
  isolated `check` orchestration. `check` resolves one existing committed run
  entry, applies only declared runtime-URL exports to that child, starts a fresh
  uncoordinated attempt, qualifies the double result, and always tears down the
  exact instance.
- `svc_cli/src/svc_cli/_execution.py`: extend the private execution-domain
  literal to `double` and reuse generic foreground capture/settlement mechanics;
  do not add double policy to this shared module.
- `svc_cli/src/svc_cli/run/runtime.py`: expose the minimum already-resolved run
  launch data needed by `double check`; preserve ordinary `svc run` convergence,
  environment precedence, receipt, and follow/inspect behavior exactly.
- `svc_cli/src/svc_cli/cli.py`: add only parser, validation, dispatch, exit-code,
  text, and typed-delivery wiring for the three subcommands.

### Machine projections

- `svc_cli/src/svc_cli/cli_output/double.py`: strict result models for
  `double-validate` and `double-check`. Results expose identity/digests,
  scenario/run names, terminal state, counts, callback/completion summaries,
  execution identity and child result, but never captured values, raw requests,
  fixture values, or environment values.
- `svc_cli/src/svc_cli/output_schema.py`: register the two terminal JSON output
  unions.
- `svc_cli/src/svc_cli/data/output-schemas/double-validate.json` and
  `double-check.json`: generated packaged schemas.

### Executable proof

- `svc_cli/tests/svc_cli_test_support/double_contract.py`: builders and HTTP
  helpers for strict test artifacts; no second production parser.
- `svc_cli/tests/fixtures/double-project/`: one small committed fake-payment
  project containing OpenAPI, definition, `svc.json`, and a standard-library
  black-box run entry used from both source and an installed wheel.
- `svc_cli/tests/test_double_definition.py`: strict grammar/path/ref/example /
  ambiguity/closed-expression validation.
- `svc_cli/tests/test_double_runtime.py`: transition atomicity, captures,
  patches, reset, bounded observations, callback settlement, completion, and
  same-instance concurrency.
- `svc_cli/tests/test_double_server.py`: provider/control separation, JSON and
  form handling, state-incompatible diagnostics, callback allow policy,
  readiness identity, port isolation, shutdown, and commit-then-disconnect.
- `svc_cli/tests/test_double_check.py`: existing run resolution, runtime export
  precedence/names-only receipt, fresh attempts, child-exit passthrough,
  qualification failure, interruption, and unconditional cleanup.
- `svc_cli/tests/test_cli.py`: public grammar/help/text/JSON/schema/error and
  no-`serve --json` contracts.
- `.github/workflows/ci.yml` and `.github/workflows/publish.yml`: run the same
  fixture's validate/check path through the freshly installed wheel in existing
  wheel smoke-test jobs. No new external service or credential is introduced.

No changes are admitted to `svc.json` schemas, `config.py`,
`config_migration.py`, project init/upgrade/status projections, `svc dev`,
ordinary `svc run` grammar, telemetry/analysis, release mechanics, or Anana.

## State Diff

### Product state

```text
From: SVC can start Consumer dev capabilities and execute declared commands,
      but cannot materialize or qualify an external-system test behavior.

To:   A Consumer can explicitly validate and serve one local scenario-double
      artifact, or execute one existing run entry against a fresh isolated
      double and receive a deterministic terminal qualification.
```

### Behavioral authority

```text
From: OpenAPI or hand-written fake-server code is interpreted outside SVC;
      provider protocol, behavior, control, and observations have no SVC owner.

To:   OpenAPI remains provider-shape authority; a strict double file owns a
      deliberately partial scenario graph; one ephemeral instance owns current
      state; generated provider/control surfaces and the check receipt are
      deterministic projections of those authorities.
```

### Configuration and compatibility

```text
From: Published project configuration is strict schema v3.
To:   Published project configuration remains strict schema v3. No existing
      project must migrate and no existing default or obligation changes.
```

### Runtime/check sequence

```text
validate local intent -> bind two random loopback ports -> prove exact readiness
-> resolve existing run -> overlay declared URL exports -> execute fresh child
-> observe/qualify scenario -> tear down exact listeners -> emit terminal result
```

Provider/action transitions commit state before a callback is attempted.
Callback delivery occurs without holding the state lock; its terminal outcome is
then recorded. Callback failure never rolls provider state back, but it can make
the declared completion expectation fail.

## Blast Radius

- **Installed CLI size and dependency resolution**: two direct dependencies and
  a substantial OpenAPI/JSON-Schema/Werkzeug transitive graph enter the runtime
  wheel environment. Lockfile, all supported Python/platform installs, import
  boundaries, and wheel smoke tests may move.
- **New network behavior**: `serve` and `check` open two local TCP listeners;
  declared actions may make synchronous HTTP callbacks, but only to numeric or
  name-resolved loopback origins. Ordinary lookup/init/status/dev/run commands
  do not gain network behavior.
- **Process lifecycle**: `check` owns listeners and a Consumer child together.
  Signals, child start failure, callback timeout, malformed traffic, and test
  failure all exercise cleanup paths.
- **Run reuse**: `check` consumes resolved run intent but deliberately bypasses
  ordinary run convergence. A check never joins, publishes over, or changes the
  coordination pointer for an ordinary `svc run` attempt.
- **Machine consumers**: two new versioned output-schema keys are added. Existing
  keys and their schemas remain byte-stable.
- **Consumer test artifacts**: the new YAML language becomes a public protocol
  once released. Strict rejection and a small first grammar are therefore more
  important than accepting speculative convenience syntax.
- **Security posture**: definitions are trusted Consumer-local test input, not a
  sandbox. Nevertheless, arbitrary scripts, shell strings, remote refs,
  non-loopback listeners/callbacks, and implicit real credentials are rejected
  so ordinary double use cannot silently become an external writer.

## Invariants

- Existing CLI grammar, exit codes, output schemas, configuration semantics,
  root status, `dev`, and ordinary `run` convergence/follow/inspect behavior do
  not change.
- `svc.json` stays at schema v3; double artifacts are never auto-discovered,
  generated into project integration, or loaded by unrelated commands.
- Definition, OpenAPI, and fixtures are explicit local Consumer authority.
  Generated responses/control state never invent undocumented business truth.
- No arbitrary code/template language, remote `$ref`, implicit network fetch,
  real-provider call, shell execution, non-loopback bind, or non-loopback
  callback is admitted.
- Provider traffic cannot invoke control operations. Control traffic cannot be
  mistaken for provider-contract evidence.
- One instance is isolated and ephemeral. Reset returns to exact initial intent;
  process exit destroys runtime state. Concurrent tests use separate instances.
- Requests are validated before transition selection; dynamically resolved
  responses and callbacks are validated before emission. An ambiguous
  transition is a compile error.
- Observations are bounded and semantic. Generic raw-body journals, captured
  values, fixture contents, credentials, and environment values never enter an
  execution receipt or ordinary logs.
- A child nonzero exit passes through. A zero child exit still fails when double
  completion is unmet, a mismatch occurred, or a required callback failed.
- SVC owns cleanup for only the listeners/child it created in that check. It
  never infers process authority from a stale PID.

## Verification

### Declaration/compiler matrix

- valid YAML and JSON definitions; OpenAPI 3.1 and 3.2; JSON and form bodies;
- missing/duplicate operation IDs, unnamed/missing examples, remote/escaping
  refs, ambiguous transitions, invalid pointers/patches/exports, and dynamic
  response incompatibility all fail before binding a port;
- digest stability is independent of input spelling where the resolved intent
  is identical and changes when any authoritative input changes.

### Runtime/server matrix

- two instances of the same scenario obtain distinct identities and ports and
  cannot observe each other's state;
- provider writes, retries, read-only queries, explicit actions, callbacks,
  reset, mismatch counts, completion, and history bounds are deterministic;
- payment callback flow and ride-style commit-then-disconnect/retry flow prove
  state-changing product behavior beyond static OpenAPI examples;
- invalid/state-incompatible requests do not partially mutate state;
- callback target checks reject non-loopback destinations before the request;
- Ctrl+C, exceptions, child start failure, and normal completion leave both
  listener ports reusable.

### Check/CLI matrix

- a fresh check never joins an active ordinary run and never changes its
  coordination record;
- URL exports override only explicitly named child variables after ordinary run
  environment resolution, while output/records expose names only;
- child `0`, child nonzero, unmet completion, mismatch, callback failure,
  startup failure, and interruption map to documented exit/results;
- help, usage errors, text streams, terminal JSON, and both packaged JSON
  schemas validate against strict typed models.

### Repository and distribution gates

```text
pdm run test
pdm run typecheck
pdm run lint-tests
pdm run lint-imports
pdm run lint-workflows
pdm run check-documents
pdm run check-release-projections
pdm run check-cli-output-schemas
pdm run build-monolith
pdm build -p svc_cli
fresh-wheel validate + payment double check fixture
```

The installed-wheel fixture must make no real-provider request and require no
secret. Its product oracle is: create a fake payment, observe pending, trigger a
control action, receive a callback in the Consumer test process, query terminal
state, and finish with the declared double completion satisfied.

## Execution Slices After Confirmation

1. Move the approved product/authority/lifecycle claims into their canonical
   documents and add failing contract fixtures/tests for the strict definition.
2. Admit dependencies and implement the pure definition/OpenAPI/compiler core.
3. Implement the state runtime, provider/control listeners, callback policy,
   and pressure-test flows.
4. Wire `validate`, attached `serve`, and isolated `check`, then generate typed
   machine schemas without changing existing commands.
5. Add installed-wheel CI/publish acceptance, run the full gates, reconcile the
   durable docs with verified behavior, and delete this disposable packet.

If the commit-then-disconnect behavior cannot be made deterministic with the
admitted Werkzeug boundary, or if `openapi-core` cannot enforce the declared
local-ref subset without relying on network resolution, execution pauses for a
new handshake instead of adding another framework or weakening a guardrail.
