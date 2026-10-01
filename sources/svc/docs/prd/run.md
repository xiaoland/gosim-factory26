# Shared Declared Runs

Use this [Product Truth](index.md) projection when a project exposes one named,
bounded command to cooperating callers. It owns the caller-visible convergence,
follow, inspect, and completion promise; shared process mechanics and runtime
records remain with Product TDD and Deployment.

SVC provides a narrow bounded-run collaboration surface for project-owned
development and acceptance commands. A project names one exact command; local
Human and Agent callers expressing that same effective intent converge on one
observable execution instead of rerunning it merely to share progress or a
handoff. The starter remains the foreground owner, while other callers can
follow captured native output or inspect the execution receipt.

The observable outcome is one execution ID, recoverable command output, and
honest terminal facts that survive caller handoff while local runtime storage
survives. A settled receipt is evidence about that invocation, never a cached
freshness claim or an acceptance verdict. Project tools continue to own test,
build, lint, and artifact semantics; SVC does not add a workflow graph,
dependency system, background runner, readiness model, or command interpreter.

Declared bounded runs and long-lived dev capabilities remain separate public
domains. Both may reuse private process-attempt mechanics, but `svc dev` alone
owns capability readiness, scope, reuse, and release after readiness.

## CLI Contract

Use a separate `run` map for bounded project-owned commands that Humans,
Agents, editor carriers, or CI should invoke through the same project name:

```json
{
  "schema_version": 3,
  "corpus_version": "15.0.0",
  "run": {
    "check": {
      "argv": ["pdm", "run", "test"],
      "env_files": [".env.shared"],
      "env": {"PYTHONUTF8": "1"}
    }
  }
}
```

```bash
svc run check --repo /path/to/project
svc run --follow <execution-id> --repo /path/to/project
svc run --inspect <execution-id> --repo /path/to/project --json
```

One caller owns the foreground process; concurrent local callers of the same
effective worktree entry follow that execution instead of starting it again.
The execution ID addresses captured stdout/stderr and a bounded receipt for
handoff. A later explicit entry invocation runs again—settled receipts are not
freshness or acceptance claims. Text mode preserves native stdout/stderr and
puts SVC lifecycle facts on stderr; `--json` suppresses native display and
returns one compact receipt.

`svc.local.json` may replace argv, cwd, and env-file arrays and merge inline env
for an existing committed entry. Relative paths resolve from the workspace
root. Environment files are strict and load in order before inline env; raw
environment values are never stored in the receipt. `run` has no shell string,
dependency graph, arbitrary arguments, background mode, readiness, cache,
artifact model, or project-result verdict.
