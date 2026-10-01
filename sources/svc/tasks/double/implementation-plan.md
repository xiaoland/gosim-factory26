# `svc double` MVP Implementation Plan

Status: implementation-ready task evidence. This plan does not authorize source
mutation. It becomes executable only after Sir confirms
[`impact-handshake-v2.md`](impact-handshake-v2.md) and explicitly starts the
implementation.

## Inputs and Decision Order

Implementation uses this precedence when task evidence differs:

1. [`final-review.md`](final-review.md) resolutions;
2. [`bsl-v0-contract.md`](bsl-v0-contract.md) concrete language contract;
3. [`design-v2.md`](design-v2.md) runtime and product design;
4. [`impact-handshake-v2.md`](impact-handshake-v2.md) admitted mutation scope;
5. V2 requirements and research as rationale, not a license to add behavior.

An inconsistency inside the first four inputs stops implementation and returns
to review. Historical V1 material is not an implementation input.

## Execution Rules

- Preserve every unrelated worktree change. Record the initial status and never
  use whole-tree restore, reset, clean, or broad staging operations.
- Change canonical product/technical/runtime truth before claiming the new
  behavior in code. Generated schemas and release projections are outputs, not
  editing sources.
- Keep the base CLI importable without the `double` extra. Parser grammar,
  output models, output-schema discovery, and the unavailable-runtime
  continuation may import only base dependencies.
- Build one authority per fact: immutable compiled snapshot for BSL-owned
  behavior, carrier memory for active bindings/journal, and the carrier-sealed
  snapshot after graceful stop. `_execution` remains launch evidence only.
- Keep every slice independently diagnosable. Run its focused gate before
  opening the next slice; do not bury a failed boundary in later glue.
- Do not add project configuration, automatic events, mutable scenario state,
  a provider SDK, Faker, WireMock/Java, a new network dependency, or a broader
  code escape. Any such need returns to review.
- Do not commit, publish, or release without separate explicit authority.

## Slice 0: Baseline and Mutation Boundary

### Preconditions

- Re-read the root instructions, working protocol, implementation taste, this
  plan, the final review, BSL contract, design, and Impact Handshake.
- Capture `git status --short` and identify all pre-existing changed/untracked
  paths.
- Run `pdm lock --check`, focused existing CLI/execution/workspace tests, and
  the current document/output-schema checks. Record any pre-existing failure
  instead of attributing it to `double`.

### Dependency proof before code structure

1. Add exactly the reviewed `double` optional dependency group in
   `svc_cli/pyproject.toml`:
   `ruamel.yaml>=0.19.1,<0.20`, `jsonschema>=4.26,<5`, and
   `cel-expr-python==0.1.3`.
2. Regenerate the workspace lock from the workspace root and inspect markers
   and artifacts for Python 3.11 and 3.14 Linux.
3. Prove the exact repository install selection for the member-package extra.
4. Build an early wheel and prove both:
   - base install: `svc --help`, every `svc double ... --help`, and every double
     `--json-schema` work while a double operation returns
     `double-runtime-unavailable` with exit 3;
   - extra install: all three optional libraries import before implementation
     tests depend on them.

### Gate

Stop before product code if the lock cannot cover the admitted Python/platform
matrix, if the base wheel pulls any double-only dependency, or if PDM/pip cannot
select the wheel extra unambiguously.

## Slice 1: Durable Contract, Public Results, and Corpus

### Mutation pass

1. Update `src/sections/prd.md` with the claim-scoped managed-boundary promise,
   Consumer-owned product oracle, and egress non-claims.
2. Update `src/sections/product-tdd.md` with the BSL-to-IR authority path,
   responder/event/control topology, active-to-sealed state authority, and
   public compatibility boundary.
3. Update `src/sections/deployment.md` with volatile run storage, private
   capability, loopback/remote-target policy, graceful sealing, and
   control-unavailable/no-PID recovery.
4. Add strict base-dependency-only result models in
   `svc_cli/src/svc_cli/cli_output/double.py` for validate, start, emit,
   observe, and stop. Distinguish resolved non-success from infrastructure
   error without inventing a product verdict.
5. Register five additive machine-output schemas, generate their packaged JSON
   projections, and add the valid/invalid fixture corpus directly from
   `bsl-v0-contract.md`.

### Gate

- New schemas generate deterministically and old schema bytes do not change.
- Base-only imports of `svc_cli.cli`, `svc_cli.output_schema`, and
  `svc_cli.cli_output.double` do not resolve any optional library.
- Documentation checks pass and all public names match the command/BSL
  vocabulary.

## Slice 2: Availability Boundary, Compiler, and `validate`

### Mutation pass

1. Add the `double` parser grammar without importing the runtime:
   - `validate MODULE`;
   - `start MODULE [--seed UINT64] [--clock RFC3339-UTC]
     [--target NAME=ORIGIN]... [--allow-remote-target NAME]...`;
   - `emit RUN_ID EVENT`;
   - `observe RUN_ID`;
   - `stop RUN_ID`;
   - `--json` and command-specific `--json-schema` on every operation.
2. Add one lazy service boundary. Missing optional modules become the exact
   structured `double-runtime-unavailable` result; they never escape as an
   import traceback or fall into the CLI's generic `invalid-release` handler.
3. Implement strict surface and normalized IR models with no parser/runtime
   objects crossing the model boundary.
4. Implement the YAML compiler:
   byte/node/depth bounds; one document; YAML 1.2 scalars; duplicate, tag,
   anchor, alias, merge, unknown-key, and unsupported-surface rejection; source
   locations; phase legality; immutable binding availability; provenance and
   derived fidelity facts.
5. Wrap CEL behind a restricted compiler/evaluator profile. Reject iterative
   macros, undeclared functions, dynamic project functions, and out-of-profile
   types before runtime.
6. Bind only one local OpenAPI 3.1 static operation. Snapshot contained local
   references into an immutable registry; reject remote references, custom
   dialects, path templates, OpenAPI 3.0, and unsupported body shapes.
7. Implement `validate` as compilation/reporting only. It inspects but never
   invokes a materializer.

### Gate

- The parser/BSL/CEL/OpenAPI rows of the MVP verification matrix pass.
- Every invalid fixture produces a stable code and source location where one
  exists.
- `validate` makes no network request, starts no process, and writes no run.
- Repeat the base/extra wheel smoke so lazy loading is proven by packaged code,
  not only the editable repository.

## Slice 3: In-Process Boundary Engine

### Mutation pass

1. Implement deterministic materialization:
   literals/examples, immutable captures/binds, restricted derived values,
   closed generator/validator registries, managed structured/raw assets,
   fixed seed/clock replay, and post-generation validation.
2. Implement a bounded loopback HTTP responder with strict method/path,
   query/header/body matching, selected-operation request validation, exactly
   one matching interaction, deterministic response bytes, and response
   contract validation.
3. Make no-match, ambiguity, malformed/oversized request, contract failure,
   capture conflict, and response/materializer failure separate facts. Disable
   proxying, redirecting, fallthrough, chunked request decoding, and ambient
   server behavior that weakens the contract.
4. Implement the bounded concurrent journal and mismatch tree with redaction,
   hashes, and explicit total/retained/omitted counts.
5. Implement explicit event materialization/delivery through already-bound
   origin targets. Join the declared path/query, follow no redirects, accept
   any 2xx, never retry, and record transport/acknowledgement facts.
6. Implement the external materializer exact stdin/output envelope, executable
   resolution, contained cwd, minimal literal environment, timeout, output
   bounds, strict JSON/base64, and response/event invariant checks. Keep its
   unsandboxed code/egress/determinism/fidelity non-claims visible.

### Gate

- Run all materialization, responder, capture, event, materializer, safety, and
  OpenAPI matrix cases in-process before detachment exists.
- Challenge with a second seed and two concurrent request streams.
- Prove the responder and built-in generator paths cannot initiate undeclared
  network I/O.
- If Python's standard HTTP foundation cannot enforce the documented bounds or
  response semantics without hidden compatibility behavior, stop and review a
  dependency/boundary change instead of silently widening the protocol.

## Slice 4: Carrier, Run Authority, and Five Commands

### Mutation pass

1. Add a private volatile `double` run store keyed by canonical UUIDv4. The
   module selects the workspace at start; later commands locate and validate
   the self-describing run by ID, independent of current working directory.
2. At start, compile and snapshot IR, contracts, and managed assets; derive a
   scenario digest and a separate run-context digest over targets, seed, fixed
   clock, versions, and snapshot hashes.
3. Extend `_execution` only enough to launch a merged-log isolated `double`
   carrier. Start keeps the exact child handle until authenticated readiness;
   startup failure terminates only that owned attempt. A ready carrier causes
   the launch attempt to be released, after which `_execution` has no semantic
   authority over the run.
4. Bootstrap responder and control listeners on numeric loopback addresses.
   Keep the random control capability in private runtime state and never emit
   it in logs, results, process arguments, or materializer context.
5. Route `emit`, active `observe`, and first `stop` through the carrier so only
   it mutates bindings/journal/state. Files remain explicitly unsealed
   projections while active.
6. On graceful stop, close the responder, settle pending owned work, atomically
   seal final facts/journal, then finish the control response and exit. A later
   stop reads the sealed authority and succeeds idempotently.
7. On missing/unreachable control authority, report
   `control-unavailable` plus the last explicitly unsealed projection, write no
   terminal state, and perform no PID/process-tree action.
8. Wire Human/Agent and JSON delivery plus exact exit mapping: 0 objective met,
   2 grammar, 3 resolved boundary non-success, 4
   storage/launch/control-protocol/internal infrastructure, and 130 caller
   interruption where the existing CLI convention applies.

### Gate

- Prove ready, early-exit, timeout, control authentication, control-unavailable,
  sealed stop, repeated stop, active/sealed observe, and no-PID fallback.
- Run two simultaneous runs with different replay facts and verify no capture,
  port, journal, run-directory, or stop leakage.
- Re-run every existing `_execution`, `dev`, and `run` test, including record
  validation and owner-loss behavior.

## Slice 5: Consumer Proof, Distribution, and Release Evidence

### Mutation pass

1. Add one subprocess-level Consumer acceptance fixture whose real HTTP client
   routes an outbound write to the returned responder URL and whose real
   callback endpoint receives an explicit `emit`. Its own test asserts only a
   public Consumer outcome.
2. Add CLI end-to-end tests for text/JSON channel placement, help, schemas,
   result/error codes, redaction, replay facts, and absent-extra continuation.
3. Update CI so repository double tests install the extra explicitly while a
   separate base-wheel job remains extra-free. Add an extra-installed wheel
   smoke on the admitted Python/platform matrix.
4. Apply the same base/extra split to the publish preflight without changing
   triggers, permissions, tag authority, or artifact publication.
5. Add CLI and Corpus minor-release facts and regenerate only admitted release
   projections.

### Final gate

Run and report:

```text
pdm lock --check
pdm run test
pdm run lint-tests
pdm run lint-imports
pdm run typecheck
pdm run check-documents
pdm run check-release-projections
pdm run check-cli-output-schemas
pdm run lint-workflows
pdm run svc --help
pdm build -p svc_cli
base-wheel smoke
double-extra wheel smoke
parallel-run acceptance
black-box Consumer acceptance
```

Also inspect `git diff --check`, generated-file provenance, dependency diff,
workflow permission/trigger diff, and the final changed-path set against the
Impact Handshake. Failures remain visible; no unrelated failing test or file is
folded into the feature.

## Stop and Return-to-Review Triggers

Implementation pauses before crossing any of these boundaries:

- an admitted dependency lacks a required target wheel or requires a base
  dependency;
- strict CEL restriction cannot be mechanically proved with the selected
  library;
- local OpenAPI reference resolution requires network retrieval or broader
  document semantics;
- native HTTP requires TLS, chunked decoding, multipart, a proxy, or a new
  protocol dependency to satisfy the acceptance case;
- run lookup needs `svc.json`, a global catalog, or a second mutable authority;
- carrier recovery needs PID takeover or a client-authored terminal state;
- callback delivery needs scheduling, retry, automatic transitions, or mutable
  provider lifecycle;
- the materializer needs to select target/route/status outside its reviewed
  envelope;
- an implementation file needs a new durable owner beyond the admitted
  Address and Object;
- an existing public output schema or `dev`/`run` behavior would change.

## Handoff Evidence

The implementation handoff includes the exact changed paths, slice gates run,
base/extra installation commands, replay tuple for the Consumer acceptance,
known non-claims, and any residual platform evidence that remains CI-only. It
does not call the MVP complete until every final gate and the Consumer-owned
black-box assertion pass.
