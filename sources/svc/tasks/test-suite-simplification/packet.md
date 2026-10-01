# Test Suite Simplification

- **Objective**: Reduce the test suite to the smallest maintainable proof set that protects public behavior, safety boundaries, recovery semantics, and cross-platform process contracts without coverage-driven cases or repeated implementation checks.
- **Guardrails**: Do not weaken an externally observable CLI, project migration, file transaction, workspace, execution, `dev`, or `run` contract. Keep tests for security, concurrency, interruption, rollback, integrity, and platform-specific regressions when no cheaper gate proves them. Unit fixtures may exercise mechanics but never count as product acceptance. Preserve unrelated working-tree changes and do not commit without explicit authority.
- **Verification**: 158 tests pass in about eight seconds: 25 root Corpus/tool cases and 133 CLI-member cases. Enhanced test/source lint passes; mypy passes across 45 source/support files with the Pydantic plugin; all seven import contracts pass; all nine output schemas remain byte-identical to `ab97e97`; release projections, 22 Corpus documents, workflow lint, monolith generation, and member wheel/sdist builds pass. Checkout-direct, checkout-sdist-derived, and repository-external sdist-rebuilt wheels have identical installed payloads and the baseline wheel's exact installed path set. A repository-external venv loads the candidate from site-packages. Baseline and candidate installed wheels match exit code, stdout, and stderr exactly for 20 read-only observations across five real roots. WSL/Python 3.13.5 passes all 158 tests and independently builds the member artifacts. No real Consumer mutation command was run; fixture-only checks are not counted as product acceptance.
- **Current Truth**: The reviewed suite collects 158 cases from 143 test functions and contains 5,412 Python lines after the ownership move, down from 198 cases, 174 functions, and 6,420 lines when shared support is counted consistently. Runtime remains about eight seconds. `test_cli.py` has 9 adapter tests: one public protocol matrix now proves compact framing plus resolved-result, usage-error, and service-error routing; the redundant standalone dev-stop channel case was removed while its business behavior remains in runtime tests. Core services now return interface-neutral values and are mechanically forbidden from importing CLI output, delivery, or schema owners. Public Pydantic DTOs/projectors live under `svc_cli/src/svc_cli/cli_output`; one schema registry owns adapters/versions; one ordinary delivery owner selects JSON versus stream-explicit Human presentation; and expected `dev ensure` lifecycle outcomes are returned results rather than serialized errors. `run` native streaming and dev live progress remain deliberate specialized adapters. Analysis and telemetry remain outside this redesign. The repository root is now a non-distribution PDM workspace; `svc_cli/` alone owns the published package, its src-layout runtime/static data, member build hook, and CLI tests. Root `tests/` contains only the four Corpus/repository-tool modules. Canonical Corpus authority remains root `src/`; the member sdist carries a build-input projection, not a second Git authority.
- **Next Step**: Review the completed PDM workspace/source-test layout diff and its acceptance evidence in the independent [implementation plan](pdm-workspace-layout-plan.md). Do not commit without explicit authority.

## Review Rules

A test earns retention when it is the cheapest clear proof of at least one of:

- a public command, serialized protocol, or durable data boundary;
- a security, integrity, ownership, concurrency, interruption, rollback, or platform invariant;
- a non-trivial transformation whose mistake would silently lose or mutate user data;
- a regression that static analysis or a higher-level behavior test cannot express.

A test is removed or narrowed when it only mirrors implementation structure, re-tests a mature library, snapshots current repository data already checked by a dedicated gate, or repeats the same behavior at another layer without proving a distinct adapter boundary.

## Retained Proof Ownership

- CLI adapter and Agent/Human output protocol: 13 cases.
- Init/status/config migration/file transaction/upgrade behavior: 41 cases.
- Corpus lookup/catalog/document/release tooling behavior: 38 cases.
- Workspace/execution/dev/run coordination and process behavior: 37 cases.
- Telemetry and analysis protocols (not redesigned in this unit): 29 cases.

Parameterized boundary matrices account for the difference between 143 test functions and 158 collected cases. They remain only where cases represent different parser forms, migration-loss risks, protocol modes, or release state transitions.

## Machine JSON Contract Redesign — Implemented

The intended authority chain is:

```text
typed output model -> Pydantic serialization -> command JSON
                   -> packaged JSON Schema projection -> consumer discovery
                   -> projection/change gate -> CLI Behavioral SemVer evidence
```

- Strict, frozen Pydantic boundary models own core command results and the shared machine error. Shared workspace, capability, probe, execution-state, log-reference, plan-action, and rollback names are typed once and reused; closed protocol sets use `Literal` rather than opaque strings. Domain controllers may keep simpler internal representations, but no core stdout/stderr JSON is emitted from an arbitrary dictionary.
- One serialization `TypeAdapter` union is registered per public JSON command. Commands with multiple terminal shapes use explicit literal discriminators. `_emit_json` accepts only the registry's result/error union; analysis and telemetry use a separately named unscoped emitter until their independent unit redesigns those protocols.
- `svc <command> --json-schema` exits successfully without executing the command or requiring normal positional arguments and emits that command's compact packaged Draft 2020-12 schema. It is available for `lookup`, `init`, `status`, `upgrade`, `dev identity|status|ensure|stop`, and `run`.
- Packaged schemas are generated from Pydantic's **serialization** mode. The packaged projection, not a dynamically generated schema from whichever compatible Pydantic minor happens to be installed, is what consumers retrieve. Stable protocol model names and schema identifiers are public names.
- A dedicated projection check requires deterministic model generation to reproduce committed schemas. When a packaged schema differs from the comparison ref, the same change must add or modify a `component: cli`, `kind: major` Changie fragment and advance that command family's result-schema version. It compares the stable packaged artifact and deliberately avoids a bespoke semantic-diff engine.
- Treat the first published schema set as a bootstrap projection, not as a change to a previously published schema contract. Its release still needs ordinary CLI change evidence; only later diffs against an existing packaged projection require a new or modified CLI-major fragment.
- Keep a command/family `schema_version` literal and require it to advance with a changed packaged schema. The CLI package version reports the release; the output schema version tells a consumer which machine contract it received.

This replaces per-command field-presence and exact-key assertions. It does **not** replace the smallest CLI adapter proofs for compact one-object framing, stdout versus stderr routing, exit-code mapping, native-output suppression, or follower/owner process behavior. A semantic differential check against the pre-refactor source confirmed unchanged lookup, real-project status/init/upgrade, and workspace-identity output; a mismatch in default-field serialization was fixed in the model layer rather than memorialized with another field assertion.

## CLI Interface Boundary — Accepted Direction

The detailed evidence, type ownership, implementation order, rehearsal, and real-project matrix live in the independent [CLI interface/service separation plan](cli-interface-separation-plan.md).

The dependency and authority direction is:

```text
CLI parser/controller -> application service -> service result/facts
        |                                      |
        +---- CLI projection/presenter <-------+
                         |
                  terminal delivery
          JSON/text, stdout/stderr, exit code
```

- The CLI owns argument grammar, command names, public output-schema versions, JSON aliases/exclusion, Human text, terminal channels, and process exit mapping. A service must not return a CLI `CommandOutcome`, know `--json`, choose stdout/stderr, or carry a public command envelope.
- Services own use-case inputs, business validation, state transitions, coordination, and interface-neutral results/events. Pydantic itself is allowed when it improves those service contracts; inheriting the CLI-specific `MachineModel` is not. Config schemas and private execution-record schemas remain their data owners' formats and are not CLI leakage merely because they also have a `schema_version`.
- Public Pydantic output models are explicit CLI projections over service results. `schema_version` and `command` are added at that boundary. Projection code stays typed and names the same semantic consistently; it must not fall back to arbitrary dictionary assembly.
- `SvcError` remains a service failure with code/message/details; the CLI maps it to the public `MachineError` and terminal exit/channel. The service error type must not expose `as_output()` or import CLI machine models.
- Process-output sinks and selected-execution notifications are valid service ports for execution use cases when they are interface-neutral and typed. CLI callbacks adapt those ports to terminal progress; service code must not import CLI presenters or emit terminal wording.
- A single CLI terminal-delivery path should own compact serialization and resolved-result/error routing. Command-specific text renderers and status-to-exit policy remain at the CLI controller boundary. `run` native streaming and `dev` live progress remain explicit bounded exceptions rather than forcing every command through a general framework.
- Do not introduce a controller/service class hierarchy or plugin framework. The target is a small one-way boundary with one source of truth for shared protocol decisions, not abstraction for its own sake.

The present serialization and packaged-schema behavior remained the compatibility baseline during this migration. Semantic parity was proven before deleting the redundant adapter case; all ordinary core commands now traverse the shared CLI delivery boundary, and one representative matrix owns channel/compact/error routing.
