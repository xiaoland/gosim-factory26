# `svc double` MVP Impact Handshake, V2

Status: final review boundary amended by [`final-review.md`](final-review.md).
Sir has accepted the command family. No source mutation begins until Sir
confirms this amended handshake and explicitly says to start implementation.

## Address and Object

### Canonical product/technical/runtime truth

- `src/sections/prd.md`: add the observable managed-boundary-harness product
  promise and the Consumer-owned oracle/egress non-claim.
- `src/sections/product-tdd.md`: add BSL IR, compiler/runtime authority,
  responder/event/observer topology, lifecycle control, and compatibility
  contract.
- `src/sections/deployment.md`: add volatile double-run storage, private control
  capability, active-to-sealed authority transition, loopback/remote-target
  policy, control-unavailable recovery, and no-PID fallback.

`src/sections/unit-tdd.md` and a local `AGENTS.md` remain unchanged unless
implementation reveals expensive internal truth that code/types/tests cannot
preserve.

### CLI/package implementation

- `svc_cli/pyproject.toml`: add the reviewed YAML, JSON Schema, and CEL runtime
  libraries under a `double` optional dependency extra; do not add them to the
  base dependency path and do not add Faker, WireMock, Java, or a provider SDK.
- `pdm.lock`: lock the reviewed optional dependency graph and platform markers.
- `svc_cli/src/svc_cli/cli.py`: add `double validate|start|emit|observe|stop`
  argument grammar and delivery only.
- `svc_cli/src/svc_cli/_execution.py`: admit `double` only as a private
  mechanical launch domain so isolated carrier startup/release reuses existing
  POSIX/Windows process evidence. No shared public lifecycle is introduced.
- `svc_cli/src/svc_cli/double/__init__.py`: package boundary.
- `svc_cli/src/svc_cli/double/model.py`: strict surface/IR/run/result models.
- `svc_cli/src/svc_cli/double/compiler.py`: YAML/source-map compiler, local
  OpenAPI 3.1 binding, fidelity/provenance validation, restricted CEL compile.
- `svc_cli/src/svc_cli/double/materialization.py`: value roles, matchers,
  closed generators, managed assets, replay, and external materializer.
- `svc_cli/src/svc_cli/double/runtime.py`: loopback responder/control runtime,
  event injector, bindings, mismatch tree, and bounded journal.
- `svc_cli/src/svc_cli/double/carrier.py`: private detached-process bootstrap and
  authenticated readiness/settlement entry point when keeping it separate makes
  runtime authority clearer.
- `svc_cli/src/svc_cli/double/service.py`: validate/start/emit/observe/stop and
  workspace/run authority.
- `svc_cli/src/svc_cli/cli_output/double.py`: Human/Agent and compact JSON
  projections.
- `svc_cli/src/svc_cli/output_schema.py` and generated
  `svc_cli/src/svc_cli/data/output-schemas/double-*.json`: registered machine
  output contracts.
- root `pyproject.toml`: add the new typed modules to mypy coverage and add
  `svc_cli.double` to the existing import-linter neutrality contracts.
- `.github/workflows/ci.yml` and `.github/workflows/publish.yml`: install the
  double extra only in the jobs that exercise/type-check it, retain an explicit
  base-wheel smoke, and add an extra-installed wheel smoke. No release trigger,
  permission, or publishing authority changes.

### Tests and release evidence

- `svc_cli/tests/test_double_language.py`
- `svc_cli/tests/test_double_contract.py`
- `svc_cli/tests/test_double_runtime.py`
- `svc_cli/tests/test_double_cli.py`
- existing `_execution`/`dev`/`run` tests: prove the added domain does not
  change their coordination, owner-loss, release, or process behavior.
- base-install tests: prove core CLI import/help and the exact optional-extra
  continuation without importing a double-only library; double output-schema
  discovery must also work in the base install.
- `svc_cli/tests/fixtures/double/`: bounded source/conformance fixtures.
- `changes/`: additive CLI and Corpus minor-release facts with migration marked
  not required; generated release projections updated by existing tooling.

Exact filenames may be collapsed when one deep module preserves the same
authority more clearly. Any new owner, project-config change, engine adapter,
or materially broader dependency returns to review before mutation.

## Implementation Slices

Implementation remains one admitted product change but proceeds through
verifiable vertical slices:

1. canonical product/technical/deployment truth, pure output models, and the
   valid/invalid BSL fixture corpus;
2. optional-runtime availability plus strict parser/compiler/IR and
   `double validate`;
3. in-process materialization, strict responder, bindings, journal, OpenAPI,
   events, and materializer conformance without detachment;
4. carrier bootstrap, ready receipt, authenticated control, sealed stop, and
   all five CLI commands;
5. real Consumer acceptance, base/extra installed-wheel smoke, release facts,
   and full regression gates.

A slice may be internally red while being built, but no partial public claim is
handed off as the MVP. New evidence that changes the approved boundary returns
to review rather than being hidden in a later slice.

## State Diff

| From | To |
| --- | --- |
| SVC has no external-system double capability. | SVC can compile and run one strict claim-scoped HTTP boundary scenario and explicitly inject named callbacks. |
| YAML is not a project language surface. | A versioned BSL YAML surface compiles into runtime-independent normalized IR under strict parser/profile conformance. |
| External response data has no SVC role model. | Literal/example/capture/derived/generated/managed values, matchers, provenance, and replay are separate boundary authorities; product assertions remain outside BSL. |
| Callbacks would require Consumer-specific fake service code. | A test explicitly emits a named event; dynamic signing/canonicalization crosses a narrow external materializer boundary. |
| `svc.json` schema v3 owns only `dev` and `run`. | It remains unchanged; v0 double modules are explicit-path standalone artifacts. |
| SVC's base install is Python-only without YAML/JSON Schema/CEL runtime packages. | A `double` extra admits only the parser, validator, and restricted expression dependencies while the base install remains unchanged. |
| No double runtime state exists. | Each start owns one private volatile run, loopback responder/control capability, bounded journal, carrier-owned active state, and sealed graceful-stop snapshot. |
| Safety could be overclaimed as global egress denial. | SVC proves no responder fallthrough and explicit built-in event targets, while reporting Consumer-process and configured materializer egress as unenforced. |

## Blast Radius

- CLI help, exit codes, compact JSON, and packaged output schemas gain a new
  command family.
- The opt-in double environment's size/platform availability changes materially
  because CEL ships native wheels and JSON Schema adds dependencies; base and
  extra build/install smoke must be separate.
- CI/install commands and the lockfile gain an optional-feature path; the base
  distribution job remains an explicit regression boundary.
- A new long-running local process and volatile runtime tree affect shutdown,
  same-user security, Windows/POSIX process behavior, and test isolation.
- Corpus product, technical, and deployment claims change and require a Corpus
  minor release fact.
- No existing `svc.json`, `svc.local.json`, `dev`, `run`, telemetry, lookup,
  project init, or upgrade syntax changes.
- No Consumer file is created or rewritten by these commands. The Consumer
  explicitly owns module/assets and test routing.

## Invariants

- The Consumer test remains the sole product oracle; SVC does not add `double
  check`, a quality score, or test command orchestration.
- No provider behavior is inferred from OpenAPI, field names, examples, or
  generic generators.
- The responder never proxies/falls through; remote assets/contracts are never
  fetched in the deterministic lane.
- A callback is emitted only by an explicit command. No timer, automatic
  request-to-event transition, retry, duplicate, or order policy appears.
- BSL has no arbitrary code, I/O, randomness, mutable state, or project
  functions inside CEL. Consumer code stays behind the external materializer
  envelope.
- The materializer envelope restricts SVC effects, not the arbitrary process;
  its network/state/side-effect boundary is an explicit non-claim.
- Active BSL-owned behavior comes from one immutable IR snapshot. Runtime
  bindings and journal have one carrier authority; files remain projections
  until the carrier seals a final stopped snapshot. Consumer materializer code
  is an explicit immutability/determinism non-claim.
- Stop/control authority comes from the private run capability, never a stale
  PID or guessed process tree.
- A control-unavailable client never writes an authoritative terminal state.
- Existing command/config/output contracts and unrelated working-tree changes
  remain untouched.
- Generated output and `build/monolith.md` are never edited as sources.

## Verification

Before handoff, implementation must prove:

1. all cases in [`design-v2.md`](design-v2.md)'s MVP verification matrix;
   the valid/invalid authoring corpus is derived directly from
   [`bsl-v0-contract.md`](bsl-v0-contract.md);
2. `pdm run test`;
3. `pdm run lint-tests`, `pdm run lint-imports`, and `pdm run typecheck`;
4. `pdm run check-documents`, `pdm run check-release-projections`, and
   `pdm run check-cli-output-schemas` after generating admitted projections;
5. `pdm run svc --help` and every `svc double ... --help`;
6. `pdm build -p svc_cli`, then one base-wheel smoke proving core commands and
   the optional-extra continuation, plus one extra-installed smoke for validate/
   start/emit/observe/stop without repository imports;
7. Python 3.11 and 3.14 Linux CI; targeted wheel-availability checks for the
   admitted CEL platforms;
8. two parallel isolated runs with distinct seeds/captures/journals and clean
   stop;
9. one black-box Consumer acceptance fixture with outbound response plus
   explicit callback and Consumer-owned public assertion;
10. no real provider endpoint/credential in the deterministic test fixture,
    and reports visibly state `consumer-egress: not-enforced` plus
    `materializer-egress: not-enforced` when applicable.

## Review Decisions Requested from Sir

The command family in item 2 is already accepted. Final confirmation admits the
whole amended implementation target, specifically:

1. explicit-path modules in v0; no `svc.json` schema change;
2. command family `validate|start|emit|observe|stop`; no `check`;
3. local typed `$bsl` nodes and one scenario/HTTP boundary per module;
4. restricted CEL, closed portable generator set, whole-envelope external
   materializer, and optional `double` dependency extra;
5. local OpenAPI 3.1 selected static-operation schema profile only;
6. native loopback executor by default, WireMock only as reference/optional
   future adapter;
7. honest Consumer/materializer egress non-claims, origin-only event targets
   with dual remote consent, and carrier/sealed-snapshot authority instead of
   client-authored `lost` state.
