## 0. Purpose of this repository

This repository develops, evaluates, debugs, and packages an Agent Harness for the GOSIM Agentic Factory / ARC-Bench competition.

The repository has two different kinds of agents. Do not confuse them:

1. Coding Agent
    * The agent reading this file.
    * Its job is to develop and maintain this repository.
    * It edits Harness source code, tests, experiment definitions, trace infrastructure, packaging logic, and documentation.
2. Competition Harness / Runtime Agent
    * The system produced by this repository.
    * Its job is to receive an unseen software requirement package and generate a runnable application.
    * It may internally invoke Pi, Codex, other coding agents, planners, test generators, repair agents, or deterministic tools.

This file is guidance for the Coding Agent.

The primary engineering objective is not to build one clever agent implementation. It is to build a reproducible Harness experimentation platform where multiple strategies can be composed, executed, traced, compared, and packaged without creating divergent codebases.

## 1. Core engineering principles

> List after "such as" are just examples

### 1.1 Optimize for experiments, not one-off implementations

We expect to try combinations such as:

* direct generation;
* planner + coding agent;
* Pi-based execution;
* Codex-based execution;
* generated training tests;
* TDD / Red-Green repair;
* build-error repair;
* browser-driven repair;
* different requirement compilation strategies;
* different model allocation strategies;
* different context, retry, budget, and stopping policies.

Do not create separate forks or duplicated implementations for these combinations.

Harness behavior must primarily be expressed as:

shared components
        +
versioned configuration
        =
Harness variant

A new experiment should usually require a new config file, not a copied source tree.

### 1.2 Every run must be explainable

A score without a trace is insufficient.

For every meaningful run, we should be able to answer, such as:

* Which Harness configuration was used?
* Which model/provider/runtime policy was used?
* Which requirement input was used?
* What decisions did the Harness make?
* What prompts were sent?
* Which tools were called?
* Which files changed?
* Which commands ran?
* Which tests failed?
* What repair action followed each failure?
* How many model calls and tokens were consumed?
* How long did each stage take?
* Why did the Harness stop?
* What application was ultimately produced?
* What did the external evaluator report?

Observability is part of the Harness architecture, not optional debugging instrumentation.

### 1.3 Separate generation from evaluation

Maintain a hard conceptual and module boundary:

```
requirement
    │
    ▼
Harness
    │
    ▼
generated application
    │
    ├───────────────┐
    │               │
internal checks     external benchmark evaluation
/train tests        /validation
    │               │
may drive repair    must not silently drive repair
```

For fair benchmark runs, external ARC-Bench validation tests and their detailed results must not automatically become model context.

Local development may intentionally run public benchmark tests after generation. That is evaluation.

If an experiment deliberately feeds validation information back into the Harness, label it explicitly as an oracle/dev-only experiment. Such a mode must never be confused with a competition-valid Harness configuration.

The runtime Harness package must not depend on the benchmark evaluation implementation.

### 1.4 One source of truth

Do not maintain separate “development Harness” and “submission Harness” implementations.

The submission entrypoint must be a thin adapter around the same runtime package used locally.

Bad:

```
src/my_good_harness.py
submission/completely_different_harness.py

Good:

submission/main.py
        │
        ▼
src/factory_harness/runtime/...

Packaging selects and copies production code; it does not reimplement it.
```

### 1.5 Prefer explicit contracts over implicit conventions

Paths, runtime inputs, model configuration, budgets, events, results, and component interfaces should have typed representations.

Avoid code whose behavior depends on:

* current working directory;
* arbitrary global environment variables;
* module-level mutable state;
* undocumented directory names;
* implicit subprocess side effects.

Use explicit RunContext, configuration models, and path objects.

## 2. Recommended repository structure

Following structure are recommended.

```
.
├── AGENTS.md
├── README.md
├── pyproject.toml
├── pdm.lock
├── Makefile
├── .env.example
├── .gitignore
│
├── configs/
│   ├── harnesses/
│   │   ├── direct.yaml
│   │   ├── pi-basic.yaml
│   │   ├── codex-basic.yaml
│   │   ├── pi-tdd.yaml
│   │   └── codex-tdd.yaml
│   │
│   ├── models/
│   │   ├── competition.yaml
│   │   └── local.yaml
│   │
│   └── experiments/
│       ├── smoke.yaml
│       ├── baseline-comparison.yaml
│       └── tdd-ablation.yaml
│
├── src/
│   └── factory_harness/
│       ├── __init__.py
│       ├── cli.py
│       ├── contracts.py
│       ├── config.py
│       ├── orchestrator.py
│       │
│       ├── components/
│       │   ├── requirements/
│       │   ├── planning/
│       │   ├── execution/
│       │   ├── training_tests/
│       │   ├── verification/
│       │   ├── repair/
│       │   ├── budget/
│       │   └── workspace/
│       │
│       ├── backends/
│       │   ├── base.py
│       │   ├── pi.py
│       │   ├── codex.py
│       │   └── subprocess_agent.py
│       │
│       ├── benchmark/
│       │   ├── base.py
│       │   └── arcbench.py
│       │
│       ├── tracing/
│       │   ├── recorder.py
│       │   ├── events.py
│       │   ├── artifacts.py
│       │   ├── redaction.py
│       │   └── summary.py
│       │
│       ├── runtime/
│       │   ├── process.py
│       │   ├── environment.py
│       │   ├── healthcheck.py
│       │   └── cancellation.py
│       │
│       └── utils/
│
├── submission/
│   ├── main.py
│   ├── platform_contract.py
│   ├── manifest.toml
│   └── README.md
│
├── scripts/
│   ├── bootstrap_arcbench.py
│   ├── pack_submission.py
│   ├── unpack_smoke_test.py
│   ├── summarize_runs.py
│   └── redact_run.py
│
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   └── fixtures/
│       ├── requirements/
│       ├── fake_agent/
│       └── traces/
│
├── third_party/
│   └── arc-bench/
│
├── runs/
│   └── .gitkeep
│
├── reports/
│   └── .gitkeep
```

`runs/` must be ignored by Git except for an optional placeholder.

Raw experiment traces may contain large artifacts or sensitive model traffic and should not normally be committed.

Small, redacted, durable experiment summaries belong in reports/.

## 3. Dependency direction

Preserve the following dependency direction:

```
contracts/config
      ↑
components/backends/runtime/tracing
      ↑
orchestrator
      ↑
CLI / submission adapter
```

Benchmark evaluation code is outside the production Harness dependency path:

```
Harness runtime ────────X──────► benchmark validation internals
```

`factory_harness.benchmark.arcbench` may know how to launch a local evaluator.

The Harness itself must not import evaluator tests or validation implementation.

Add an architecture/contract test if necessary to enforce this boundary.

## 4. Harness composition model

A Harness variant should be declarative.

## 5. Core runtime contracts

Define typed contracts early.

At minimum:

RunContext
HarnessSpec
RequirementInput
Workspace
ModelRole
Budget
StageResult
VerificationResult
RunResult
TraceEvent
ArtifactRef

A RunContext should explicitly contain paths such as:

requirement_dir   read-only input
output_dir        generated application
trace_dir         persistent run trace
temp_dir          disposable working data
repo_root         development mode only

Components must not infer these paths from cwd.

## 6. Execution backend contract

Pi, Codex, and future coding agents should be adapters behind a narrow execution contract.

Conceptually:

class ExecutionBackend(Protocol):
    async def execute(
        self,
        task: CodingTask,
        context: RunContext,
    ) -> ExecutionResult:
        ...

The orchestrator should not contain Pi-specific or Codex-specific command construction.

Backend adapters own:

* invocation;
* supported options;
* prompt handoff;
* environment filtering;
* timeout handling;
* stdout/stderr collection;
* backend-specific trajectory collection;
* normalization into ExecutionResult.

Keep backend-native artifacts when useful, but normalize metrics and status for comparison.

## 7. Trace design

Tracing is a first-class subsystem.

7.1 Run directory

Every run receives an immutable unique run directory:

```
runs/<run-id>/
├── run.json
├── config.resolved.yaml
├── events.jsonl
├── metrics.json
├── summary.md
│
├── inputs/
│   ├── requirement-manifest.json
│   └── hashes.json
│
├── prompts/
├── model/
├── tools/
├── commands/
├── diffs/
├── tests/
├── screenshots/
├── browser/
├── errors/
│
├── workspace/
│   └── final/
│
└── evaluation/
```

Do not put large payloads directly in events.jsonl.

Events should reference artifacts.

### 7.2 run.json

Capture enough provenance to reproduce and interpret the run.

Recommended fields:

```json
{
  "schema_version": 1,
  "run_id": "...",
  "parent_run_id": null,
  "started_at": "...",
  "finished_at": "...",
  "status": "success",
  "git": {
    "commit": "...",
    "dirty": false,
    "diff_sha256": null
  },
  "harness": {
    "id": "pi-tdd-v1",
    "config_sha256": "..."
  },
  "benchmark": {
    "name": "arcbench",
    "revision": "...",
    "task": "keep",
    "input_sha256": "..."
  },
  "runtime": {
    "python": "...",
    "platform": "...",
    "container": null
  }
}
```

### 7.3 Event stream

`events.jsonl` is append-only.

Every event should have a common envelope:

```json
{
  "seq": 42,
  "ts": "...",
  "run_id": "...",
  "span_id": "...",
  "parent_span_id": "...",
  "stage": "repair",
  "component": "pi",
  "kind": "model.response",
  "data": {}
}
```

Useful event kinds include:

```
run.started
run.finished
stage.started
stage.finished
decision
model.request
model.response
model.error
agent.started
agent.finished
tool.call
tool.result
command.started
command.finished
file.created
file.modified
file.deleted
workspace.diff
build.started
build.finished
test.started
test.finished
test.case
repair.started
repair.finished
budget.updated
budget.exhausted
checkpoint.created
error
warning
```

A run must remain understandable even if console output is lost.

### 7.4 Large artifacts

Store large objects separately:

* full prompts;
* raw model responses;
* agent transcripts;
* shell output;
* patches;
* Playwright traces;
* screenshots;
* videos;
* generated tests.

The corresponding event should contain an artifact_ref.

Prefer content hashes for artifacts where practical.

Example:
```json
{
  "artifact_ref": {
    "path": "model/0007-response.json",
    "sha256": "..."
  }
}
```

## 8. Metrics

Keep raw facts and derived metrics separate.

At minimum collect:
```
Model usage

request count
input tokens
output tokens
reasoning tokens, when reported
total tokens
provider-reported usage
estimated cost, only when pricing is known
```

Missing token data is null / unavailable, never zero.

```
Runtime

total wall time
time per stage
agent execution time
build time
test time
repair time
```

```
Harness behavior

number of planning passes
number of coding passes
repair rounds
test runs
build attempts
files changed
tool calls
timeouts
retries
```

```
Evaluation

tests passed
tests failed
pass rate
evaluation runtime
```

Do not collapse all of this into one custom “quality score”.

Preserve underlying measurements.

## 9. Console UX

Console output is for humans.

Trace files are for diagnostics.

Do not dump raw structured traces to stdout.

Default output should look approximately like:

```
[run] keep / pi-tdd-v1
[requirements] loaded 32 nodes
[plan] completed in 18.3s
[execute] Pi started
[build] failed
[repair 1/4] fixing build error
[build] passed
[train] 11/14 passed
[repair 2/4] repairing 3 failing tests
[train] 14/14 passed
[done] 04:12, 17 model requests, 186k tokens
[trace] runs/...
```

Use verbose/debug modes for deeper console output.

10. Development CLI

The repository should converge on one developer CLI.

Target experience:

```
pdm i
make doctor
make test
```

Run a Harness:

```
pdm run factory run \
  --task keep \
  --harness configs/harnesses/pi-tdd.yaml
```

Evaluate an existing generated app:

```
pdm run factory eval \
  --run <run-id>
```

Inspect a run:

```
pdm run factory inspect <run-id>
```

Compare runs:
```
pdm run factory compare \
  <run-id-a> \
  <run-id-b>
```

Run an experiment matrix:

```
pdm run factory experiment \
  configs/experiments/tdd-ablation.yaml
```

Package submission:
```
pdm run factory pack
```

Exact names may evolve, but maintain one coherent CLI instead of accumulating scripts with overlapping behavior.

## 13. Public validation and leakage policy

ARC-Bench development material may contain public Playwright validation tests.

Humans may inspect them while studying the benchmark.

However, maintain a clean measurement path.

Production-valid Harness components must derive behavior from allowed runtime inputs.

Do not accidentally create:

Harness → read benchmark tests → implement exact assertions

through shared path access.

The local evaluator can access validation tests.

The Harness runtime cannot.

Recommended filesystem separation:
```
run/
├── input/
│   └── requirements/      # visible to Harness
│
├── generated/             # owned by Harness
│
└── evaluator/             # owned by evaluation runner
    └── validation-tests/  # not exposed to Harness
```
If detailed validation failures are intentionally fed back during research, set:

experiment_mode: oracle
submission_eligible: false

and surface that status prominently in summaries.

## 19. Submission architecture

Treat submission support as an adapter.

Target conceptual architecture:

platform
   │
   ▼
submission/main.py
   │
   ▼
platform_contract.py
   │
   ▼
factory_harness.orchestrator

Any competition-specific:

* CLI flags;
* environment variable names;
* output conventions;
* runtime port handling;

belong in submission/platform_contract.py.

Do not spread platform-specific environment lookups throughout the Harness.

When the official competition contract changes, this layer should absorb most of the change.

## 20. Submission packaging

Submission packaging must use an explicit allowlist.

Include only what production execution requires.

Conceptually:

```
main.py
runtime package
required configuration
required prompts/templates
runtime dependency manifest
submission metadata
```

factory pack should:

1. validate required files;
2. reject detected secrets;
3. create a manifest;
4. record source Git revision;
5. record Harness config/version;
6. produce the archive;
7. calculate archive SHA-256;
8. unpack it into a temporary clean directory;
9. execute a submission smoke test from the unpacked bundle.

A package that only works from the source checkout is broken.

29. Reports

Raw traces belong in runs/.

Human-readable comparisons belong in reports/.

A report should record:
```
experiment id
date
benchmark revision
repository revision
Harness variants
model policy
number of repetitions
per-run result
aggregate pass/fail statistics
latency
tokens
repair counts
known anomalies
```

Never manually copy leaderboard numbers into reports without recording their provenance.

31. What not to build yet

Do not prematurely build:

* a web dashboard;
* a distributed scheduler;
* a database-backed experiment service;
* a generic agent framework;
* Kubernetes deployment;
* a remote trace SaaS;
* an elaborate plugin marketplace;
* abstractions that only have one implementation.

Files + JSONL + typed Python + reproducible CLI are sufficient initially.

The first goal is rapid, trustworthy iteration.

35. Guiding architecture

The intended long-term shape is:

```
                         Requirement Package
                                 │
                                 ▼
                         Requirement Ingest
                                 │
                                 ▼
                              Planner
                                 │
                                 ▼
                        Execution Backend
                      ┌──────────┴──────────┐
                      │                     │
                     Pi                  Codex
                      │                     │
                      └──────────┬──────────┘
                                 │
                                 ▼
                         Generated App
                                 │
                                 ▼
                         Internal Verify
                                 │
                    ┌────────────┴────────────┐
                  GREEN                      RED
                    │                         │
                    │                  Failure Classifier
                    │                         │
                    │                         ▼
                    │                     Repair
                    │                         │
                    │                         └─────┐
                    │                               │
                    └───────────────────────────────┘
                                 │
                                 ▼
                         Final Application
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
             Run Trace                    External Evaluation
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                        Experiment Results
```

Every block above should be independently observable.

Only blocks for which we have a real need should become interchangeable components.

36. Final priority rule

When choosing between two implementations, prefer the one that makes the next experiment easier to answer correctly.

In this repository:
```
observability
    >
clear component boundaries
    >
fast iteration
    >
architectural cleverness
```
We are building an experimental software-engineering Harness, not merely producing code that happens to pass today’s benchmark.