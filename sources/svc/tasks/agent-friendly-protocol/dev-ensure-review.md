# `svc dev ensure` Command and Output Review

## Owned result

`svc dev ensure <target>` has one bounded intent: make one named development
capability ready, either by reusing readiness, joining an
existing provisioning attempt, starting the declared provisioner, or stopping
at a truthful non-ready boundary.

It is not an all-target launcher, a process manager, or a project-context
discovery command. It does not infer a target or provision command, and it does
not turn `manual` into an SVC-owned action. Once a long-running provisioner has
proved readiness, SVC relinquishes process authority.

The command serves two distinct output moments:

1. **live coordination** while a potentially long start or join is in progress;
2. **terminal capability result** once readiness or a non-ready boundary has
   been established.

These moments should share facts but not one forced presentation shape.

## Real Consumer evidence

### SFP7 Camera: expected manual boundary

The real host-scoped `x86_64-f43-custom-kernel` target uses a bounded exec
receipt probe and a manual provisioner. The default receipt is intentionally
absent.

Current-source real calls on 2026-08-07 produced:

- `--json`: exit `3`, a compact nested `manual-action-required` error carrying
  workspace and capability hashes, `access`, and only probe output length;
- default text: exit `3`, one useful error sentence followed by a 36-line
  prettified JSON details dump;
- the actual Consumer probe: exit `1` with a 194-byte compact JSON diagnostic
  identifying `RECEIPT_MISSING` and the claim ceiling.

The probe diagnostic is the decisive fact, but current SVC discards it and
prints hashes that do not help the immediate recovery. Multiple retained real
handoffs reduce the result to `manual-action-required`, failed probe facts, and
the proof that no executable provisioner ran.

### InKCre client-web: ready reuse and dynamic evidence

The real `database` target was ready during this review. Its declaration has no
static `access` entry because it attaches to a core-py-owned runtime. Its
212-byte successful exec-probe output carries the external provider,
attachment identity, runtime instance, owner repository, contract revision,
and Consumer runtime profile. That native field is not an SVC configuration
profile.

Current `dev status --json` reports only that 212 bytes existed. It discards
the content. Calling `ensure` would return `reused`, but default text would only
say `SVC dev ensure: reused`. That loses both the selected target and the
Consumer evidence needed to understand what was reused.

Historical real acceptance also records cold `web` and `webext` starts as
`started`, later healthy status, and the concrete per-worktree Portless routes.
The started-versus-reused distinction is therefore consumed operationally; it
is not decorative lifecycle data.

### InKCre core-py: diagnostic output prevents a wrong start

The real `database` probe returned exit `1` and 1,633 bytes. Its native JSON
said the existing runtime itself was ready and converged, but its source
fingerprint no longer matched the worktree. Current SVC reduces this to
`nonzero-exit`, byte count, and truncation false.

`ensure` was deliberately not invoked: it owns an executable provisioner and
could reconcile or replace Consumer runtime state. The read-only probe already
proves why output content, exit code, and native presentation are part of the
readiness result rather than optional debug detail.

## Input disposition

Keep the current public grammar:

```text
svc dev ensure <target> [--repo <repo>] [--json]
```

- Require exactly one target. Bulk ensure would combine independent startup,
  readiness, timeout, and failure horizons and would obscure which capability
  the caller intended to use.
- Keep `--repo .` as the default and do not add invocation-time provision,
  timeout, env, cwd, detach, or takeover overrides.
- On an unknown target, include the bounded available target names. This closes
  a simple input-recovery loop without adding a list command.

`--json` selects a compact exact terminal projection for CI, scripts, and other
deliberate field consumers. It does not mean “Agent mode,” and generated Agent
guidance should not require it for ordinary use. An Agent may still choose it
when acting as a field consumer; the audience distinction is about the
interaction, not the caller's identity.
Layered help must state that the command may execute the selected target's
Consumer-owned provisioner, waits for declared readiness, does not take over an
unhealthy responder, and leaves a ready long-running capability running after
the CLI exits. It must also state the default/JSON channel and exit behavior;
this command's side-effect boundary cannot be inferred from its grammar.

## Candidate terminal result

### Content

Every resolved ensure result should carry:

- selected target;
- a direct ready boolean plus the outcome `reused`, `started`, `joined`, or a
  specific non-ready status;
- the capability scope and workspace identity needed to qualify readiness;
- resolved declared `access` values;
- provision kind and, for exec provision, mode;
- the final readiness observation;
- for exec probes, exit code and bounded merged native output, in addition to
  captured byte/truncation facts;
- an attempt identity, caller relationship, resolved argv/cwd, merged startup
  log reference, and terminal attempt state when an exec provision attempt
  existed;
- cleanup disposition when SVC attempted cleanup.

Do not expose environment values. Do not promote the child PID as the primary
continuation: after readiness SVC has relinquished authority, and a PID invites
callers to bypass Consumer-owned cleanup. Exact internal evidence may retain it
only if a demonstrated diagnostic consumer needs it.

The three successful outcomes are deliberately distinct:

- `reused`: readiness existed before this call selected a provisioning attempt;
- `started`: this caller owned the attempt that produced readiness;
- `joined`: this caller waited on another caller's already-published attempt.

This preserves the collaboration fact that two callers converged rather than
silently making both terminal results look like unrelated reuse.

### Default text

One target and one terminal result do not need a table. Lead with usable state,
target, outcome, and scope. Show full derived hashes only in JSON.

For a ready target:

```text
svc dev database: ready (reused); instance 4ac9df364b54706e; scope worktree
Probe: exec exit 0
Probe output:
  {"ready":true,"identity":"4ac9df364b54706e",...}
```

Non-empty healthy exec output is shown when no declared `access` exists,
because real Consumers use it for dynamic attachment facts. When resolved
`access` is present, show that instead and omit routine probe output from the
default projection:

```text
svc dev web: ready (started); instance 4ac9df364b54706e; scope worktree
Access: https://client-web-4ac9df364b54706e.localhost/
Startup log: /.../output.log
```

For a non-ready result, lead with the boundary and put decisive native evidence
before derived hashes or generic explanation:

```text
svc dev x86_64-f43-custom-kernel: manual-action-required; instance fc804c7cb2752f5f; scope host sfp7-f43-x86_64-builder-v1
Probe: exec exit 1
Probe output:
  {"claim_ceiling":{...},"code":"RECEIPT_MISSING",...}
Declared access: offline-receipt, builder-output-manifest
No SVC command can provision this target; follow the Consumer project's guidance.
```

Default native-output presentation preserves Consumer bytes as text rather
than parsing and rewriting an unknown schema. It uses a small diagnostic
preview and states omitted/truncated content. `--json` retains the complete
Consumer-declared bounded capture. This avoids treating a configurable limit
of up to 1 MiB as automatically suitable for an Agent context while preserving
an exact opt-in result.

### Compact JSON

The JSON result remains one command-specific object, not a common CLI envelope.
An illustrative successful shape is:

```json
{"schema_version":1,"command":"dev ensure","ready":true,"status":"joined","target":"database","workspace":{...},"capability":{...},"access":[],"provision":{"kind":"exec","mode":"run"},"probe":{"kind":"exec","healthy":true,"reason":"zero-exit","exit_code":0,"output":"...","output_bytes":212,"output_truncated":false},"attempt":{"caller_role":"follower","execution_id":"...","state":"released","argv":[...],"cwd":"...","log_path":"..."}}
```

Expected non-ready capability outcomes should use the same result projection
with `ready: false` and their specific status, rather than nesting the entire
result under `error.details`. Invalid grammar, unknown targets, malformed
configuration, unsafe paths, and SVC execution/integrity failures remain
structured command errors.

This is command-local semantic consistency: callers inspect one path for an
ensure outcome. It is not a universal schema for unrelated SVC commands.

## Live coordination presentation

An exec provision may wait up to 3,600 seconds; current `ensure` is silent until
terminal state. Default mode should emit only state changes to stderr:

```text
svc dev web: starting `node scripts/dev.mjs web`
Waiting up to 90s for readiness; startup log: /.../output.log
```

or:

```text
svc dev web: joining an existing start
Waiting for readiness; startup log: /.../output.log
```

Do not stream the long-running provisioner's native output: it may be noisy or
unbounded and continues after `ensure` returns. The shared log reference lets
Humans and Agents use ordinary tools to inspect or follow the same attempt.
Do not emit periodic heartbeat noise when no state changed.

`--json` suppresses live presentation so stdout contains exactly one compact
terminal result and successful stderr stays empty. It is designed as a stable
CI/script interface: no audience marker, prose hint, progress event, or
prettified duplicate belongs in the object. Ordinary Agent/Human use should
prefer default text, particularly when live progress matters.

## Channels, exits, and interruption

- Exit `0`: the selected capability is ready (`reused`, `started`, or `joined`).
- Exit `2`: invalid CLI grammar.
- Exit `3`: a resolved capability is not ready or needs Consumer action, or a
  project/configuration precondition conflicts with the request.
- Exit `4`: SVC execution storage, launch, or integrity failure prevented a
  trustworthy result.
- Exit `130` for caller Ctrl+C. If this caller owns an in-progress launch, SVC
  cleans up only that launch; if it joined another caller's attempt, it stops
  waiting without terminating the shared attempt.

Resolved terminal text/JSON uses stdout, including expected non-ready results
with exit `3`. Live default-text coordination uses stderr; malformed input,
invalid project requests/declarations, and SVC execution/integrity failures
use stderr.

Caller interruption is separate from capability disposition. A follower
Ctrl+C returns exit `130`, `caller_role: "follower"`, and
`caller_status: "detached"`, plus the published execution ID/current state/log
reference; it does not invent a terminal readiness result. Default mode emits
that self-contained detach receipt to stdout and JSON mode emits one compact
receipt to stdout. If the owner interrupts its still-owned launch, that caller
returns `130` after cleanup; other callers observe the resulting interrupted
non-ready attempt and do not inherit exit `130` unless they also interrupt.

## Rejected additions

- No all-target ensure or dependency graph.
- No `--detach`: successful ensure already returns after readiness while the
  declared long-lived capability continues.
- No generic logs command: the attempt returns an exact native log path that
  ordinary tools can read or follow.
- No provisioner-output streaming or JSONL event protocol.
- No output parser, problem matcher, or automatic reformatting of Consumer
  probe output.
- No new public `dev inspect` command without a real consumer that cannot use
  `dev status`, the terminal result, and the returned log reference.

## Persistence boundary

The long-running provisioner is intentionally independent of the starter CLI.
It has null stdin, writes merged native output to the shared log, and on POSIX
starts a new session. After readiness, SVC persists `released` and relinquishes
the child handle; closing the initiating terminal must not mean “stop this
capability.”

Normal owner Ctrl+C before readiness is different: it is an explicit
interruption and cleans only that caller's launch. An uncatchable owner loss
must not grant a later caller authority to kill or replace the historical PID.
Machine shutdown and platform runtime cleanup remain outside a persistence
guarantee.

Ensure and stop must share one per-capability intent boundary. Ensure cannot
return its current pre-lock `reused` fast path while an opposite stop intent is
already committed. Same-intent callers join one published attempt; opposite
intents serialize and then re-evaluate readiness under the coordination
boundary. Status remains an unlocked volatile observation.

Current Windows realization is not yet proven sufficient for terminal-window
loss. `CREATE_NEW_PROCESS_GROUP` establishes a control-signal group but does
not by itself create a new or detached console. The accepted persistence
contract therefore requires real Windows acceptance and may require a
different launch flag or carrier there.

Stopping a released capability is a separate lifecycle action and cannot be
derived safely from the historical process ID. The focused candidate is
reviewed in [`dev-stop-review.md`](dev-stop-review.md).

## Review status

Sir accepted this candidate on 2026-08-07. This is not implementation
authorization. `ensure` returns one resolved capability outcome across ready
and expected non-ready states, while its default text also provides sparse live
coordination. The accepted design adds no `ensure` input mode; the newly
identified stop lifecycle is reviewed separately.
