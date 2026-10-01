# `svc dev` Command-Family Consistency Review

## Purpose

`dev identity`, `dev status`, `dev ensure`, and `dev stop` serve different
information and lifecycle purposes. They should not be forced into one result
schema. This review applies shared semantics only where the commands expose the
same fact: workspace identity, target scope, a resolved domain result, an
execution reference, or caller interruption.

This refinement was written before Sir's review and accepted on 2026-08-08. It
does not change the product implementation gate.

## Command boundaries

| Command | Unit selected | Consumer code run | Lifecycle mutation | Durable evidence |
| --- | --- | --- | --- | --- |
| `dev identity` | one workspace | none | none | exact workspace identity |
| `dev status [target]` | one or all declared targets | readiness probes | none by SVC | bounded snapshot only |
| `dev ensure <target>` | one target capability | probe and possibly provision | may establish readiness | shared startup execution/log when attempted |
| `dev stop <target>` | one target capability | declared stop and final probe | may remove capability resources | shared stop execution/log when attempted |

The common CLI options remain `--repo <repo>` and `--json`; they do not imply a
common payload. `--repo` defaults to the current directory. Default text is the
Agent/Human projection; compact JSON is the exact CI/script projection.

## Accepted consistency corrections

### Name identity facts accurately

`workspace.instance`, `workspace.worktree_id`, and target `scope` are distinct:

- `instance` is the 16-hex local resource key consumed by real client-web and
  core-py runtime scripts;
- `worktree_id` is the 20-hex identity of the concrete worktree;
- `scope` says whether a target capability is isolated by worktree,
  repository, or host.

The accepted ensure/stop examples currently label an instance value as
`worktree`; this is incorrect. Default target results should instead say, for
example:

```text
svc dev web: ready (started); instance 4ac9df364b54706e; scope worktree
svc dev web: stopped; instance 4ac9df364b54706e; scope worktree
```

An all-target status has no single capability scope because its targets may
use different scopes. Its heading should qualify the workspace with
`instance`; each row should carry that target's scope:

```text
svc dev status: action-required — 1/4 ready; instance 4ac9df364b54706e
ready      database  worktree  exec zero-exit
not-ready  web       worktree  exec exit 1; no output; ensure
```

The exact identity command remains the deliberate exception that prints the
complete repository/worktree/namespace chain. Exact derived fields remain in
each command's compact JSON where they qualify the result.

Use lowercase `svc` consistently for SVC-authored headings and command
examples. This makes emitted text match the invocable command and avoids a
meaningless `SVC`/`svc` distinction.

### Route results by meaning, not success code

A resolved dev-domain result uses stdout in both default and JSON modes even
when its disposition maps to exit `3`. This includes non-ready status,
manual-action-required ensure/stop, failed Consumer actions, still-ready, and
unverified stop results. Live start/join/wait coordination uses stderr.

Invalid grammar, an invalid project request or declaration, and failures that
prevent SVC from producing a trustworthy domain result use stderr. In JSON
mode a completed command emits exactly one compact object on stdout and no
progress/native display.

This replaces the ensure review's provisional exception that allowed
default-text non-ready results to stay on stderr. A resolved domain result is
useful pipeline data because it carries the observation and continuation; its
nonzero exit remains the aggregate gate.

### Keep domain failure separate from execution failure

For stop:

- `stop-failed`, exit `3`, means SVC launched the declared Consumer action but
  it exited nonzero, timed out, or was interrupted;
- failure to create, publish, launch, or capture the action execution is an
  SVC execution error, exit `4`, not a fabricated `stop-failed` result;
- malformed/unknown project declarations and request conflicts are command
  errors, exit `3`, on stderr;
- execution-store, lock, capture, and persisted-record integrity failures are
  exit `4` errors on stderr.

This matches the accepted ensure boundary: an actual Consumer outcome is
domain evidence, while failure to establish a trustworthy attempt is an
execution-mechanism error. `stop-failed` should therefore no longer say that
the action “could not start.”

### Probe even when stop cannot mutate

An absent or `manual` stop declaration produces
`manual-action-required` and performs no mutation, but SVC should still run the
target's readiness probe once. The result carries `ready: true|false|null` and
the probe evidence; it omits `attempt` because no stop execution existed.

The probe reports the current capability state, not proof that cleanup
happened. The status remains `manual-action-required` even when readiness is
already false, because SVC still has no declared cleanup action and cannot
claim that non-readiness means all resources are absent.

### Model Ctrl+C as a caller result

Capability disposition and the current caller's wait disposition are
orthogonal. For shared ensure/stop execution:

- a follower Ctrl+C returns exit `130` with
  `caller_role: "follower"` and `caller_status: "detached"`;
- when the target attempt was already published, the receipt includes its
  execution ID, current state, and shared log path;
- when stop was still waiting behind an opposite ensure intent, no stop
  attempt or stop log exists, so the receipt identifies that wait boundary and
  does not invent `status`, `ready`, `probe`, or `attempt` fields;
- default mode prints the self-contained detach receipt to stdout; JSON mode
  prints one compact receipt to stdout; prior live coordination remains on
  stderr;
- detaching never terminates the shared operation.

If an owner interrupts its still-owned action, that caller exits `130`. Stop
records the interrupted attempt as `stop-failed`; ensure records its existing
interrupted non-ready boundary. Other callers observe the resulting domain
state through their own waits and do not inherit exit `130` unless they also
interrupt their calls. Uncatchable owner loss still grants no PID authority.

### Share coordination, not observation storage

Ensure and stop must enter the same per-capability intent boundary before
ensure can return an early `reused` result. Otherwise an ensure can probe
healthy and return while a concurrent stop is already committed to teardown.
Same-intent callers join one published attempt; opposite intents serialize and
then re-evaluate. The current implementation's pre-lock fast readiness probe
must therefore move inside or behind this boundary during implementation.

`dev status` remains an unlocked volatile snapshot and may race with lifecycle
change by design. Status and final readiness probes return bounded native
evidence inline; they do not create execution records or logs. Provision and
stop actions return shared log references because they may be long-running,
multi-caller executions. No generic log command is added.

### Render commands without leaking environment

Default text for an executed Consumer command prints the full resolved argv
with platform-appropriate quoting. Compact JSON carries the lossless argv
array. Both omit configured and inherited environment values. Native probe
output remains bounded Consumer-owned evidence; provision/stop native output
remains in the referenced shared log except for a bounded failure tail.

## Resulting common rules

The family shares only these rules:

- exact target names and workspace qualification are present whenever they
  determine what was observed or mutated;
- `instance`, `worktree_id`, and capability `scope` are never conflated;
- terminal domain results use stdout, live coordination and command errors use
  stderr;
- compact JSON is one exact terminal projection for scripts/CI, not an Agent
  mode;
- exit `0` means the requested domain condition holds, `2` is grammar, `3` is
  a resolved non-success or project/request conflict, `4` is an untrustworthy
  execution/integrity failure, and `130` belongs only to the caller that
  interrupted;
- execution/log references exist only for actual provision/stop attempts;
- no saved process ID grants later lifecycle authority.

These are presentation and coordination invariants, not a universal dev
result schema.

## Review status

Written from the accepted per-command reviews, current runtime behavior, and
real client-web/core-py identity consumers. Sir accepted the candidate on
2026-08-08; the corrections were synchronized into the status, ensure, and
stop command reviews. Product implementation remains separately gated.
