# CLI Interface / Service Separation Plan

## Status

- **Decision**: Implemented and verified on 2026-08-09.
- **Scope**: Core business commands only: `lookup`, `init`, `status`, `upgrade`, `dev identity|status|ensure|stop`, and `run`.
- **Outside this unit**: `analysis` and `telemetry`; their existing unscoped protocols remain unchanged.
- **Compatibility baseline**: commit `ab97e97` and its nine packaged output schemas.

## Implementation Result

- Neutral strict value models now own workspace, capability, probe, project, upgrade, dev, plan, and failure facts. Core application services do not import `cli`, `cli_output`, `cli_delivery`, or `output_schema`; the forbidden dependency is enforced by import-linter.
- Public Pydantic DTOs and typed projectors live under `svc_cli/cli_output/`. Public command envelopes, schema versions, aliases, omission rules, machine errors, and compact serialization no longer live in service modules.
- `lookup`, `init`, `status`, `upgrade`, and `dev identity|status|ensure|stop` all use one resolved-result delivery path. The same owner selects compact JSON versus a stream-explicit Human renderer and writes resolved results to stdout. One error delivery path owns public error projection and stderr. `run` retains its explicit native-streaming adapter.
- `dev ensure` now returns manual, conflict, timeout, child-exit, owner-loss, and interruption outcomes as `DevEnsureResult`. A private typed unwind signal preserves nested cleanup without allowing an expected result to cross the service boundary as serialized `SvcError.details`.
- One `OutputSchemaSpec` registry owns each command adapter and public result-schema version. One parser helper owns paired `--json` / `--json-schema` registration while preserving existing help order and wording.
- Shared plan signatures are explicit service projections rather than machine-output serialization. Real `init` and `upgrade` plan digests remain byte-identical to the baseline.
- The standalone `dev stop` CLI channel test was removed after the shared protocol matrix gained a settled exit-3 result; dev-stop authority, concurrency, final-probe, and no-PID-fallback behavior remain covered at the runtime boundary.

Verification facts:

- 158 collected tests from 143 test functions pass; test code is 5,392 lines.
- mypy passes across 44 source/support files; Ruff test/source checks and all seven import contracts pass.
- All nine generated packaged JSON Schemas are byte-identical to `ab97e97`; release projections, 22 Corpus documents, workflow lint, and wheel build pass.
- Baseline and candidate installed wheels matched exit code, stdout, and stderr exactly for 26 read-only cases spanning help/version/schema discovery and five real project roots. This includes exact status/init/upgrade/identity JSON and exact init/upgrade plan digests.
- The candidate was loaded from `/private/tmp/.../site-packages/svc_cli`, not from the source checkout. No real Consumer mutation command was run.

## Objective

Make the CLI a one-way interface over application services, then delete tests whose only purpose was to defend repeated CLI delivery branches.

The result must satisfy both directions of the boundary:

1. Services do not know CLI grammar, command envelopes, public output-schema versions, Human presentation, stdout/stderr, or process exit policy.
2. The CLI does not reimplement business decisions; it parses a request, invokes one service operation, projects the returned facts, and delivers the result.

This is a structural refactor. Public JSON instances, packaged JSON Schemas, Human text, terminal channels, exit codes, process ownership, file effects, plan digests, and real-project observations must remain unchanged.

## Non-goals

- Do not build a command plugin framework, controller class hierarchy, dependency-injection container, or universal response schema.
- Do not move config validation, file transactions, readiness, execution coordination, or process lifecycle into the CLI.
- Do not redesign command text or machine output in the same change.
- Do not treat Pydantic as interface-only. Neutral service value objects may use Pydantic when strict validation is useful.
- Do not duplicate a service value object merely to satisfy layering when its complete stable semantic is intentionally exposed unchanged.
- Do not count fixture-only checks as product acceptance or invoke mutating `init --apply`, `upgrade --apply`, `dev ensure|stop`, or `run` against real Consumer projects.

## Current Evidence

The source has no direct service import of `svc_cli.cli`, but the dependency still points the wrong way through protocol types:

- 67 classes outside telemetry/analysis inherit the CLI-specific `MachineModel`.
- `WorkspaceIdentity`, `CapabilityIdentity`, `ProbeObservation`, and `ResolvedProbe` are service facts coupled to machine serialization.
- Lookup response projection lives in `LookupResponse.as_output()`.
- Init/status and upgrade services construct or return `*Output` models directly.
- Dev runtime owns public `command`/`schema_version` envelopes and embeds `MachineErrorBody` in service results.
- Run runtime owns `RunReceipt`, receipt projection, and process-exit mapping.
- `SvcError.as_output()` imports machine models, so a service failure knows its CLI representation.
- Shared plan facts expose `as_output()` and derive internal plan signatures through public machine projections.
- Nine core parsers separately register `--json` plus `--json-schema`; eleven core result presenters repeat the JSON branch.
- `cli.py` is 1,518 lines and combines parsing, dispatch, projection, Human presentation, delivery, and exit policy.

One especially important mismatch is `dev ensure`: expected settled states such as `manual-action-required`, occupied unhealthy endpoints, readiness timeout, activation failure, and owner loss are raised as `SvcError` with a serialized `DevEnsureOutput` in `details`. The CLI recognizes an error-code allowlist and reconstructs the result. These are resolved business outcomes, not interface errors.

## Target Topology

```text
argv
  |
  v
CLI parser/controller --------------------------------------+
  |                                                         |
  | typed use-case request                                  | interface policy
  v                                                         |
application service                                         |
  |                                                         |
  | neutral result / event / SvcError                       |
  v                                                         v
CLI output projection -> command-owned Human presenter -> terminal delivery
       |                         |                         |
       | public Pydantic DTO     | text semantics          | stdout/stderr + exit
       +-------------------------+-------------------------+
                                 |
                         packaged JSON Schema
```

Dependency rule:

```text
cli + cli_output + output_schema -> service/domain modules
service/domain modules           -X-> cli, cli_output, machine, output_schema
```

## Ownership Rules

### Service-owned

- Use-case inputs and resolved facts.
- Business validation, planning, file effects, readiness, execution coordination, and process ownership.
- Neutral results, observations, attempts, log references, and lifecycle events.
- `SvcError` as `code`, `message`, and neutral diagnostic `details`.
- Config schema versions, private execution-record schema versions, and plan-signature versions owned by those data formats.
- Process output sinks and selected-execution notifications as typed, interface-neutral ports.

### CLI-owned

- `argparse` grammar and help.
- Public `command` and result `schema_version` envelopes.
- JSON field aliases, omission rules, serialization, packaged JSON Schema, and schema-version gate.
- Projection from neutral results/errors to public Pydantic DTOs.
- Human text renderers and continuation wording.
- Resolved-result versus error channel routing and process exit policy.
- Native/live terminal adaptation for `run` and dev lifecycle progress.

### Reuse rule

A neutral service value may be nested directly in a CLI DTO only when the public contract intentionally exposes the complete value unchanged. The type must not inherit `MachineModel`, carry output aliases/exclusion, or include CLI envelopes. Otherwise the CLI owns an explicit typed projection.

This permits one accurate `WorkspaceIdentity`, `CapabilityIdentity`, or `ProbeObservation` semantic while preventing command envelopes and presentation concerns from leaking into their owners. Any later field addition still passes through the committed schema gate before it can become public.

## Intended Source Shape

The smallest source change is preferred over a new framework:

```text
svc_cli/model.py                 neutral strict/frozen value-model base
svc_cli/errors.py                neutral SvcError and error facts only
svc_cli/<service modules>        interface-neutral operations/results
svc_cli/cli_output/
  model.py                       MachineModel, machine error/usage DTO, serializer
  common.py                      shared public projections
  lookup.py                      lookup output DTOs + typed projector
  project.py                     init/status output DTOs + typed projectors
  upgrade.py                     upgrade output DTOs + typed projectors
  dev.py                         dev output DTOs + typed projectors
  run.py                         run receipt DTO + typed projector
svc_cli/output_schema.py         one registry over CLI output DTO unions
svc_cli/cli_delivery.py          shared terminal result/error delivery
svc_cli/cli.py                   parser, thin handlers, Human presenters, live adapters
```

Names are provisional only where filesystem organization has no public effect. Durable semantic names in service results and public JSON fields must remain consistent, accurate, and self-explanatory.

The planned import contracts are:

1. Service/domain modules may not import `svc_cli.cli_output`, `svc_cli.cli_delivery`, `svc_cli.machine`, or `svc_cli.output_schema`.
2. `cli_output` may import service/domain facts but not `svc_cli.cli`.
3. `output_schema` may import only CLI output contracts and neutral library modules, not call services.
4. Shared execution, workspace, plan, and config owners remain independent of `dev` and `run` as already enforced.

## Type Ownership Map

| Current owner | Current type/operation | Target service value/result | CLI projection |
| --- | --- | --- | --- |
| `workspace.py` | `WorkspaceIdentity(MachineModel)` | `WorkspaceIdentity` on neutral model | Reuse unchanged inside CLI envelopes |
| `dev/identity.py` | `CapabilityIdentity(MachineModel)` | `CapabilityIdentity` on neutral model | Reuse unchanged |
| `dev/readiness.py` | `ProbeObservation`, `ResolvedProbe` | Neutral observation/resolution values | Reuse `ProbeObservation`; never expose `ResolvedProbe` unless already explicit |
| `errors.py` | `SvcError.as_output()` | `SvcError`; optional neutral `Failure` snapshot for aggregate observations | `MachineError` projector in `cli_output.model` |
| `plans.py` | `*Output`, `as_output()` | Existing `Blocker`, `FileState`, `PlannedFileMutation`, `RollbackReport`; neutral `LocalApplyResult` | Shared file-state/operation/rollback DTO projectors |
| `lookup.py` | output classes + `LookupResponse.as_output()` | Existing `LookupResponse` dataclass | Lookup DTOs and `project_lookup()` |
| `project.py` | `CorpusBaselineOutput`, init/status outputs | `CorpusBaseline`, `InitPlan`, `InitApplyResult`, `ProjectStatusInspection` and nested neutral facts | Init plan/apply and root status DTOs/projectors |
| `upgrade.py` | details/reference/output types | Neutral guide, details, remaining-target, plan, and apply-result values | Upgrade plan/apply DTOs/projectors |
| `dev/runtime.py` | dev outputs and output-shaped expected errors | `DevStatusResult`, `DevEnsureResult`, `DevStopResult` plus neutral attempts/events | Dev identity/status/ensure/stop DTOs/projectors |
| `run/runtime.py` | `RunReceipt`, `receipt()`, `outcome_exit_code()` | Existing `RunOutcome`, execution facts, log refs | Receipt projector and CLI exit policy |

Plan digest and private-record fields named `command` or `schema_version` are not automatically CLI concepts. They remain when they identify a persisted or hashed service intent. Only public command envelopes and output versions move.

## Implemented Sequence

Each stage finished with focused tests, mypy, import contracts, and byte-identical generated output schemas. No public schema version was advanced.

### 0. Freeze differential baselines

1. Record SHA-256 for all nine packaged schemas at `ab97e97`.
2. Build/install the baseline wheel from `ab97e97` in a repository-external virtual environment.
3. Capture exit/stdout/stderr for the read-only real-project matrix below and for CLI help/schema discovery.
4. Record current init/upgrade plan digests on the real projects without applying them.

### 1. Establish neutral primitives

1. Add a neutral strict/frozen Pydantic base with no serialization aliases, exclusion policy, `as_dict()`, command envelope, or schema version.
2. Move `WorkspaceIdentity`, `CapabilityIdentity`, `ProbeObservation`, and `ResolvedProbe` from `MachineModel` to that base.
3. Add a neutral immutable error snapshot for dev aggregate observations; keep `SvcError` an exception with untyped diagnostic input at the service boundary.
4. Prove workspace/capability/probe behavior and exact output-schema parity before continuing.

### 2. Separate machine/error ownership

1. Move machine-only base/error/usage DTOs and compact serializer under `cli_output`.
2. Replace `SvcError.as_output()` with one CLI projector; keep JSON compatibility conversion at the interface boundary.
3. Replace dev uses of `MachineErrorBody` with the neutral error snapshot.
4. Add the forbidden-import contract before migrating command families, so new leakage fails mechanically.

### 3. Migrate the already-neutral command families first

1. **Lookup**: move DTOs and `LookupResponse.as_output()` logic to `cli_output.lookup`; service retains queries and response dataclasses only.
2. **Run**: move `RunReceipt`, receipt/log projection, and `outcome_exit_code()` to `cli_output.run` or the CLI controller; runtime retains execution/follow/inspect behavior and neutral `RunOutcome`.
3. Update `output_schema` imports while preserving public model names and union discriminators.

These slices provide the simplest proof that projection can move without changing behavior before touching plan/apply and dev coordination.

### 4. Neutralize shared file transactions

1. Remove `BlockerOutput`, `FileStateOutput`, `FileMutationOutput`, `RollbackOutput`, and their `as_output()` methods from `plans.py`.
2. Keep plan signatures explicit and service-owned; do not derive digests through CLI output serialization.
3. Add typed CLI projectors for file state, operations, blockers, and rollback evidence.
4. Compare every existing init/upgrade plan digest before and after this stage.

### 5. Migrate project init/status

1. Rename output-shaped service facts such as `CorpusBaselineOutput` to neutral semantic names.
2. Make `apply_init()` return an interface-neutral apply result.
3. Make `inspect_status()` return a neutral status inspection without public envelope or output omission rules.
4. Move init/status DTO construction to `cli_output.project`.
5. Preserve current text by continuing to render from service facts, not by parsing the JSON projection.

### 6. Migrate upgrade

1. Neutralize guide references, details, remaining targets, operations, verification, and apply result.
2. Remove `UpgradePlan.as_output()` and output construction from `apply_upgrade()`.
3. Project plan/apply results at the CLI boundary.
4. Preserve config and Corpus target selection, caller-asserted migration meaning, remaining-target reminders, mutations, and plan digests exactly.

### 7. Migrate dev and correct result/error semantics

1. Neutralize attempts, provision/stop declaration facts, target observations, and status/ensure/stop results.
2. Remove public `command` and `schema_version` fields from service results; add them only in CLI projections.
3. Change the public `ensure_target()` boundary so expected settled outcomes return `DevEnsureResult` instead of serializing a public output into `SvcError.details`.
4. Keep invalid requests and infrastructure faults as `SvcError`.
5. Remove the CLI error-code allowlist and `DevEnsureOutput.model_validate(error.details)` reconstruction.
6. Keep selected-execution callbacks as typed neutral lifecycle events and preserve owner/follower semantics.
7. Preserve stop's declared-action authority, shared capability lock, final readiness qualification, and no-PID-fallback invariant.

Internal dev helpers may use a private typed control signal while unwinding nested lifecycle code, but it must carry a neutral result and must be caught inside the service boundary. No expected outcome may cross into the CLI as serialized error details.

### 8. Consolidate CLI delivery without generalizing services

1. Add one parser helper that registers both `--json` and `--json-schema` from a typed schema key.
2. Replace the separate schema-key tuple, version map, and adapter map with one `OutputSchemaSpec` registry; derive all projections from it.
3. Add one resolved-terminal delivery function: compact JSON to stdout in machine mode, command-owned Human renderer to stdout in default mode, and return the controller-supplied exit code.
4. Add one error delivery function: public error projection to stderr and centralized error-to-exit mapping.
5. Make Human renderers accept an explicit stream rather than relying on ambient `print()` defaults.
6. Keep `run` execute/follow native output and lifecycle text as an explicit stream-aware adapter; inspect text remains stdout. Dev live selection/progress remains stderr while its terminal result uses the common resolved path.
7. Keep status-to-exit decisions in thin CLI handlers. Do not move them into service result types or create a universal business disposition.

### 9. Delete only structurally redundant tests

Do not delete adapter tests until every core command traverses the shared delivery owner and the import contracts pass.

Then:

1. Use one public CLI protocol matrix to prove compact one-object success, settled nonzero result on stdout, usage error on stderr, and service error on stderr.
2. Keep schema-discovery cases that represent different grammar topology: root command, nested dev command, and run's positional-selection bypass.
3. Remove the standalone dev-stop channel test once its only distinct assertion is owned by the common settled-result case; retain dev-stop business behavior in runtime tests.
4. Keep Agent/Human text tests only for decision-bearing content and continuations, not generic headings.
5. Keep run native-channel, child-exit passthrough, owner/follower interruption, and inspect behavior because they do not traverse ordinary terminal delivery.
6. Keep dev live progress and lifecycle ownership tests where they prove a distinct stream or concurrency boundary.
7. Recount cases/functions/LOC and update the parent packet with facts, not a target quota.

## Brain Rehearsal / Failure Matrix

| Risk | Likely cause | Detection | Planned response |
| --- | --- | --- | --- |
| Circular imports | CLI projections import a service that still imports machine/output types | import-linter, import smoke, mypy | Migrate one vertical slice atomically; service loses output import before projector imports it |
| JSON Schema drift | Public class names, union order/discriminator, aliases, defaults, or exclusion changed while moving models | `check-cli-output-schemas --compare-ref ab97e97`, schema SHA-256 | Stop and restore exact projection; do not advance schema version for a refactor |
| JSON instance drift | `Path`, tuple, optional, alias, or `exclude_none` serialization changes | baseline/candidate differential and CLI protocol test | Fix the CLI projector; never compensate in service facts |
| Plan digest drift | Internal signatures depended on `MachineModel.as_dict()` or output-only omission | real-project digest comparison and plan tests | Write explicit service-owned signature projection matching the old canonical bytes |
| Error routing drift | Removing `SvcError.as_output()` loses detail conversion or command context | invalid usage/domain/infrastructure differential | Project errors in CLI with the same `json_compatible` behavior and handler context |
| Dev expected outcome becomes stderr | Existing exception unwinding crosses the public service boundary | manual/occupied/timeout CLI tests | Catch/convert internally and return neutral result; only true faults raise `SvcError` |
| Dev cleanup changes | Refactor modifies nested early-return/exception cleanup | owned timeout/interruption/process-group tests | Separate data projection edits from lifecycle control changes; preserve `finally` and ownership scopes |
| Run exit changes | `outcome_exit_code()` moves away from runtime | subprocess tests for 0, child exit, SIGINT, SIGTERM, owner loss | Move the function verbatim first, then rename only after parity |
| Leaked secrets | Projector exposes environment or process internals | existing receipt/log tests and schema diff | Project from the same bounded execution facts; never serialize ambient environment |
| False DRY abstraction | A registry/framework starts owning command business policies | design review and import graph | Keep exit/status selection in thin handlers and text in command-owned presenters |
| Tests deleted too early | Shared delivery not yet authoritative for every command | stage gate and test diff review | Delete tests only in stage 9 after structural enforcement |

## Verification Gates

Run after every meaningful stage:

```text
pdm run pytest -q <affected tests>
pdm run typecheck
pdm run lint-tests
pdm run lint-imports
pdm run check-cli-output-schemas --compare-ref ab97e97
git diff --check
```

Run before implementation handoff:

```text
pdm run test
pdm run check-cli-output-schemas --compare-ref ab97e97
pdm run check-release-projections --compare-ref ab97e97
pdm run check-documents
pdm build
```

Required static facts at completion:

- No core service/domain module imports machine, CLI output, delivery, or schema-registry modules.
- No service result contains public command envelopes or output-only exclusion/alias rules.
- No service calls `as_output()`, constructs `MachineError`, or serializes an expected dev result into error details.
- No arbitrary dictionary is emitted as a core command machine result.
- One schema registry owns each command adapter and version.
- One ordinary terminal-delivery path owns compact JSON and resolved/error channel routing.

## Real-project Acceptance Matrix

Use built wheels from baseline `ab97e97` and the candidate in separate repository-external virtual environments. Compare exit code, stdout, and stderr exactly for read-only operations.

Real roots:

- `/Volumes/WorkSSD/Development/InKCre/client-web`
- `/Volumes/WorkSSD/Development/InKCre/core-py`
- `/Volumes/WorkSSD/Development/InKCre/docs`
- `/Volumes/WorkSSD/Development/sfp7-camera`
- `/Volumes/WorkSSD/Development/Anana/mvp-HA`

Read-only command coverage, subject to command applicability at each root:

```text
svc --help
svc lookup --list --json
svc lookup --path sections/working-protocol.md
svc status <root>
svc status <root> --json
svc init <root>
svc init <root> --json
svc upgrade <root>
svc upgrade <root> --json
svc dev identity --repo <root>
svc dev identity --repo <root> --json
svc dev status --repo <root> --json       # only where declared probes are safe/read-only
svc <core-command> --json-schema          # all nine schema families across the matrix
```

Acceptance requirements:

- Baseline and candidate output/schema bytes and exit codes match.
- Init/upgrade plan digests match and no project file changes.
- Existing adopted, migration-pending, unadopted, Git/worktree, and non-Git observations remain distinguishable.
- The candidate wheel is imported from site-packages, not the source checkout.
- Fixture and temporary-project tests remain useful implementation checks but are not reported as real-product acceptance.

## Completion Condition

The unit is complete only when:

1. The dependency direction is mechanically enforced.
2. Core services return neutral results and never format CLI output.
3. Public JSON/schema/text/channel/exit behavior is unchanged against the baseline.
4. Expected dev lifecycle outcomes are results rather than serialized errors.
5. Repeated CLI delivery code and only the tests made redundant by that single owner are removed.
6. Full static, test, build, schema, and real-project acceptance gates pass.
7. The parent task packet records final counts and evidence.

No commit is created without explicit Human authority.
