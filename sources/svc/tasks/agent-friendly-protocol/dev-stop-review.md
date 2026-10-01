# `svc dev stop` Lifecycle Review

## Why the topology is reopened

The reduced command tree was frozen as a baseline, not an axiom. A released dev
capability is intentionally independent of the terminal that started it. The
question “how do Human and Agent stop the same capability?” therefore exposes
a lifecycle need rather than a desire for command symmetry.

The need is real:

- InKCre client-web exposes `pnpm dev:stop`. It resolves the current SVC
  worktree instance, identifies only matching Portless routes, checks their
  current commands before signaling them, and invokes exact database cleanup.
  Its retained review already records a portability defect in its Unix-only
  `ps` ownership check.
- The same real workflow proves that one worktree's stop left another
  worktree's routes, Compose project, volumes, ports, and tunnel intact.
- InKCre core-py exposes an instance-scoped stop that removes the exact Compose
  project, volume, local runtime state, credentials, and SSH control tunnel.
  An attached client-web runtime is explicitly forbidden from stopping the
  core-owned runtime.

These are capability-identity and ownership problems already inside `svc dev`'s
domain. Leaving every Agent, Human, IDE Task, and CI carrier to rediscover a
project-specific stop command loses the collaboration convergence supplied by
`ensure`.

## Existing persistence contract

Current canonical contracts already say:

- dev provisioners are isolated, have null stdin, and use merged file output;
- after readiness, SVC records `released` and relinquishes its process handle;
- later authority comes from capability probes, not the historical PID;
- owner loss and PID observation never grant takeover or kill authority.

The POSIX implementation uses `start_new_session=True`. Windows currently uses
`CREATE_NEW_PROCESS_GROUP`; [Microsoft documents that
flag](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)
as a console process-group/control-event mechanism, not as a new or detached
console. [Python exposes the two mechanisms on their respective
platforms](https://docs.python.org/3/library/subprocess.html). Cross-platform
survival of terminal-window loss is therefore a product requirement still
needing real Windows acceptance, not a fully proved current behavior.

Operational logs may survive and continue growing after `ensure` exits, but
they are local runtime evidence rather than archival storage.

## Rejected stop mechanisms

### Stop on starter exit

Reject. It would make readiness persistence depend on one transient caller,
break reuse by later Human/Agent participants, and conflate explicit Ctrl+C
with terminal loss.

### Kill the recorded PID or process group later

Reject. After release SVC deliberately has no live child handle or process
authority. The recorded PID may be reused, may identify only a wrapper, and
cannot describe Portless routes, Docker Compose resources, volumes, tunnels,
remote processes, or Consumer ownership rules.

### Leave stop entirely outside SVC

This is current reality and remains a valid fallback for undeclared targets,
but it is not the preferred complete interface. Real Consumer code must
reconstruct SVC identity and ownership, and different callers no longer share
one declared intent or observable bounded stop execution.

### Reuse `svc run` as the public command

Reject as the default. A project may still expose an unrelated cleanup run,
but making dev teardown a run-entry convention would reconnect the two public
namespaces and hide the target/capability identity that makes the stop safe.
`dev stop` may reuse the private execution mechanism without becoming `run`.

## Smallest candidate

Add one explicit, one-target command:

```text
svc dev stop <target> [--repo <repo>] [--json]
```

Do not add implicit all-target stop. Cleanup can be materially destructive and
must name one capability. A Consumer-owned package or IDE Task may remain an
explicit aggregate carrier when the project owns ordering across targets.

Add an optional target-local `stop` declaration. It is either a bounded exec
action or `manual`; it uses `${dev.instance}`, `${dev.worktree.id}`, and
`${dev.target}` plus their remaining `SVC_DEV_*` environment projections
without emitting environment values. `stop` is preferred over `deprovision` or
`teardown` in the public grammar because it names the caller's ordinary intent
without claiming whether the Consumer retains or removes underlying data.

The accepted configuration location is the target itself:

```text
svc.json:       dev.targets.<target>.stop
svc.local.json: dev.targets.<target>.stop
```

It is a sibling of `scope`, `probe`, `provision`, `access`, and timing. There is
no root-, dev-, or separate stop map. The earlier
`dev.profiles.<profile>.targets.<target>.stop` path was superseded when Sir
accepted removing the unused profile layer; see
[`dev-config-review.md`](dev-config-review.md).

The controller should:

1. resolve the same workspace, target, and capability identity as
   status/ensure;
2. acquire the capability's coordination boundary;
3. execute only the Consumer-declared stop action—never derive a kill from an
   old execution record;
4. converge concurrent stop callers on one bounded execution and one log;
5. serialize an opposite concurrent ensure intent rather than merging the two;
6. report the stop command's exit plus the final readiness observation;
7. treat exit zero followed by still-healthy readiness as a failed
   postcondition, not as stopped;
8. make no stronger process/resource-absence claim than the declared action
   and final probe prove.

Do not skip the declared stop action merely because an initial readiness
observation is false. A non-ready capability may still retain a Compose
project, volume, tunnel, route, or runtime state. The Consumer-owned stop action
must therefore be target-scoped and safe to repeat; SVC executes it, then uses
the final probe as the postcondition. This requires the current raw core-py
database stop to make missing runtime state a successful no-op or gain an
equivalent thin idempotent carrier.

The private `run` machinery can own execution ID, wait/follow, capture, owner
loss, and receipt facts. `dev` retains authority over target selection,
capability locking, stop declaration, readiness postcondition, and result
wording.

Ensure and stop enter the same per-capability intent boundary before ensure
may return `reused`. Same-intent callers join one published execution;
opposite intents serialize and then re-evaluate. The current implementation's
pre-lock ensure probe cannot remain an early-return path once stop exists.

## Accepted live presentation

Default mode emits only coordination state changes to stderr. An owner sees:

```text
svc dev web: stopping
$ node scripts/stop-dev.mjs web 4ac9df364b54706e
Stop log: /.../output.log
```

A same-intent caller joins the published attempt instead of executing another
stop:

```text
svc dev web: joining stop 8d32...
Stop log: /.../output.log
```

A stop waiting behind an active ensure states that opposite-intent wait, then
publishes or joins the stop selected after the coordination boundary. It never
merges ensure and stop into one execution. There are no periodic heartbeats.

Consumer cleanup stdout/stderr is captured into one shared merged log rather
than streamed into every caller's terminal. The full resolved argv is shown
with platform-appropriate quoting as execution evidence; compact JSON carries
the lossless argv array. Secrets belong in environment values, which are never
rendered. On terminal failure, default text may include only a small labeled
tail while retaining the complete log at the returned path.

`--json` suppresses all live presentation and native display so successful
stderr is empty and stdout contains exactly one compact terminal object.

## Accepted terminal result

The terminal result is self-contained even when earlier live output was not
retained. A successful default result is:

```text
svc dev web: stopped; instance 4ac9df364b54706e; scope worktree
$ node scripts/stop-dev.mjs web 4ac9df364b54706e
Execution: 8d32... (joined), exit 0 in 1.4s
Final probe: exec exit 1 — not ready
Stop log: /.../output.log
```

An action failure preserves both the failure and whatever final capability
state the probe can still establish:

```text
svc dev database: stop-failed; instance 4ac9df364b54706e; scope worktree
Execution: 8d32..., exit 1
Stop output (tail):
  ERROR: runtime is owned by core-py
Final probe: exec exit 0 — ready
Stop log: /.../output.log
```

Capability disposition and caller relationship are independent dimensions.
`caller_role` is `owner` or `follower`; joining never becomes a capability
status. The deliberately small terminal status set is:

- `stopped`: the declared action exited zero and the final readiness
  evaluation is false;
- `manual-action-required`: the stop declaration is absent or manual, so SVC
  performs no mutation but still evaluates current readiness once;
- `stop-failed`: SVC launched the Consumer action and it exited nonzero, timed
  out, or was interrupted;
- `still-ready`: the action exited zero but the final probe remains ready;
- `stop-unverified`: the action exited zero but the final probe itself could
  not produce a trustworthy readiness disposition.

In this command, `stopped` means only that the Consumer-declared stop action
succeeded and declared readiness no longer holds. It does not independently
claim that every process, volume, tunnel, route, or remote resource is absent.
An absent or manual declaration never falls back to a recorded PID kill.
Its result still carries `ready: true|false|null` plus the readiness evidence,
but remains `manual-action-required` even when readiness is false: a probe
cannot prove that undeclared cleanup occurred.

Compact JSON is the CI/script projection. Its command-specific shape carries
the exact target, effective declaration evidence, workspace/capability
identity, terminal status, tri-state `ready`, stop kind, final probe, and an
attempt when one existed:

```json
{"schema_version":1,"command":"dev stop","status":"stopped","ready":false,"target":"web","workspace":{...},"capability":{...},"stop":{"kind":"exec"},"attempt":{"caller_role":"follower","execution_id":"8d32...","state":"exited","argv":[...],"cwd":"...","duration_ms":1400,"exit_code":0,"log_path":"/.../output.log"},"probe":{...}}
```

`ready` is `true`, `false`, or `null` when verification is unavailable. Omit
`attempt` when no executable action existed rather than emitting an empty
object. Do not include environment values, a historical PID, or a copy of the
complete native log.

## Channels, exits, and interruption

- Resolved terminal text and JSON results use stdout, including expected
  exit-3 capability outcomes. Live coordination uses stderr. Grammar, invalid
  project requests/declarations, and SVC execution/integrity errors use
  stderr.
- Exit `0` means `stopped`; exit `2` is invalid CLI grammar; exit `3` covers
  manual action, an executed Consumer action failure, still-ready, unverified,
  unknown target, and configuration conflict; exit `4` means SVC could not
  create, publish, launch, capture, coordinate, or trust the execution. A
  launch-mechanism error is not fabricated as `stop-failed` because no
  trustworthy Consumer attempt exists.
- Stop does not pass through the Consumer child's exit code because that exit
  is only one input to the domain result; the exact value remains in the
  attempt.
- Caller Ctrl+C returns `130`. If the caller owns the stop action, SVC
  interrupts that still-owned action and records `stop-failed`; followers
  observe the same interrupted domain attempt but do not inherit `130`. A
  follower Ctrl+C returns `caller_role: "follower"` and
  `caller_status: "detached"` plus the shared execution/current-state/log
  reference, without terminating the attempt. If stop is still waiting behind
  ensure, no stop attempt or log exists: the receipt identifies the wait
  boundary and omits fabricated `status`, `ready`, `probe`, and `attempt`
  fields. Default and JSON detach receipts use stdout; prior live coordination
  remains on stderr.
- Uncatchable owner loss never authorizes a follower or later caller to signal
  the historical PID. The attempt becomes owner-lost/uncertain; a later
  explicit stop may safely retry only because the Consumer action is required
  to be idempotent.

## Review status

Sir accepted the command direction on 2026-08-07 and the flattened target
configuration plus live/terminal output contract on 2026-08-08. The accepted
dev-family consistency pass on 2026-08-08 clarified identity labels, channels,
failure boundaries, manual readiness, interruption receipts, and opposite
intent coordination. This is not implementation authorization. SVC's shared
dev capability contract supplies the one explicit Consumer-declared stop path
required by durable background capabilities; implementation still requires
an impact handshake, reviewed plan, mental rehearsal, and real-project
acceptance.
