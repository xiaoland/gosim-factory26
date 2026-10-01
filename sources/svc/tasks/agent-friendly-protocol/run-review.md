# `svc run` Command and Output Review

## Evidence horizon

`svc run` is newly implemented and not yet a demonstrated Consumer interface.
A bounded scan of the available real projects found no committed `run` map and
no operational `svc run` call in InKCre client-web, InKCre core-py, SFP7
Camera, or Beluna. The SVC repository also currently has no `svc.json`.
Beluna supplied the real command-level handoff problem used for product
admission, but it did not subsequently execute `svc run`.

There is one persisted real SVC implementation-acceptance execution to inspect:

```text
entry: repository-tests-installed
argv: pdm run test
execution: 2ebdc656-8c86-414b-9b14-675af88a13e8
state: exited 0 in 6.277s
native logs: stdout 2,464 bytes; stderr 0 bytes
```

Its default `run --follow` faithfully replayed the native pytest session and
preserved the wrapper lifecycle on stderr. Its compact inspect receipt retained
entry, argv, cwd, caller role, execution identity, effective-entry digest,
timestamps, duration, and exit code. This is implementation evidence, not
evidence that real Consumer callers prefer the current presentation.

The current default inspect result is only:

```text
svc run inspect: exited 0 in 6.3s 2ebdc656-8c86-414b-9b14-675af88a13e8
```

It omits the entry, command, cwd, caller relationship, workspace qualification,
and native-output references. It also goes to stderr despite inspect having no
native stream to preserve. The current compact receipt has no log paths; the
actual files are present in the execution store and can only be reached through
full `--follow` replay or knowledge of SVC's private runtime layout.

Current `svc run --help` exposes only argparse grammar. It does not explain
convergence, execute/follow/inspect differences, native channels, JSON
suppression, execution-ID scope, exit projection, or Ctrl+C behavior.

## Information service

The existing product definition remains valid. `svc run` executes one named,
project-owned bounded command and lets independent local callers converge on
one observable execution. It does not interpret the command's output or claim
that the project/task was accepted.

The three forms serve different interactions:

1. `svc run <entry>` resolves the current effective entry, owns a fresh
   execution or joins the same active intent, preserves native streams, and
   waits for settlement.
2. `svc run --follow <execution-id>` replays captured native stdout/stderr and
   waits for that exact run-domain execution.
3. `svc run --inspect <execution-id>` returns current execution facts without
   native replay or waiting.

The execution ID is the collaboration identity. The entry name is intent, not
a cache key for settled truth: a later explicit entry invocation starts a new
execution after the prior attempt settles.

## Input candidate

Keep the existing grammar unchanged:

```text
svc run <entry> [--repo <repo>] [--json]
svc run --follow <execution-id> [--repo <repo>] [--json]
svc run --inspect <execution-id> [--repo <repo>] [--json]
```

- Exactly one of entry, follow, or inspect is required.
- `--repo` defaults to the current directory and qualifies both entry
  resolution and execution-ID access.
- No arbitrary argv, dependencies, background mode, cancel, timeout, cache,
  readiness, artifact discovery, or output parser is added.
- An unknown entry error includes the bounded committed entry names. This
  closes the immediate input-recovery loop without adding a list command.
- Follow and inspect remain valid from the published execution record after
  configuration changes; they do not re-resolve the current run declaration.

## Default presentation candidate

### Execute and follow

Native stdout and stderr remain on their original streams. SVC-owned selection,
command, lifecycle, and terminal receipt lines remain on stderr so SVC never
contaminates a project command's stdout protocol.

The live owner header becomes:

```text
svc run repository-tests-installed: owner 2ebdc656-8c86-414b-9b14-675af88a13e8
cwd: /Volumes/WorkSSD/Development/svc
$ pdm run test
logs: stdout /.../stdout.log; stderr /.../stderr.log
```

A same-intent entry caller or explicit follow says `follower` and references
the same execution/logs before replaying or following native streams. There are
no heartbeats or SVC summaries of native output.

After native settlement, the terminal receipt is self-contained with respect
to the lifecycle result even if the live header is no longer visible:

```text
svc run repository-tests-installed: exited 0 in 6.3s (owner)
execution: 2ebdc656-8c86-414b-9b14-675af88a13e8
logs: stdout /.../stdout.log (2,464 bytes); stderr /.../stderr.log (0 bytes)
```

The follower form says `(follower)`. Failure states retain their bounded
`reason` after the receipt. Native failure diagnostics were already streamed;
SVC does not duplicate or reinterpret them.

### Inspect

Inspect has no native stream to protect, so its default result uses stdout. It
is a compact handoff view rather than a content-free lifecycle line:

```text
svc run inspect: repository-tests-installed — exited 0 in 6.3s
execution: 2ebdc656-8c86-414b-9b14-675af88a13e8
$ pdm run test
cwd: /Volumes/WorkSSD/Development/svc
logs: stdout /.../stdout.log (2,464 bytes); stderr /.../stderr.log (0 bytes)
```

For an active execution it reports `running`, `started_at`, and current log
byte counts rather than inventing a duration or terminal disposition. Inspect
continues to exit `0` when inspection itself succeeds, regardless of the
observed execution state.

The returned paths let Agents and Humans use ordinary `tail`, `rg`, `sed`, or
file readers for selective evidence. This does not replace follow: follow owns
stream-preserving replay plus wait, while paths support bounded inspection and
handoff without replaying an arbitrarily large log.

### Detachment

Text execute/follow detachment remains on stderr because those modes reserve
stdout for native output. It reports entry, execution/current state when known,
and the shared log paths. JSON detachment remains one caller-local compact
receipt on stdout. `caller_status: detached` is not persisted as execution
state and only the caller that receives Ctrl+C exits `130`.

## Compact JSON candidate

`--json` remains an exact receipt mode for a script or CI step that explicitly
wants fields instead of native display. It suppresses live/native output and
emits exactly one compact object on stdout. Ordinary CI logs should prefer
default mode when native diagnostics are meant for Human review; “CI” alone is
not a reason to hide project output.

The current receipt is already appropriately command-specific. Make two
semantic corrections before this new interface is released:

1. rename public `workspace_id` to `workspace_instance`; the stored value is
   the 16-hex `WorkspaceIdentity.instance`, not the repository/worktree
   identity or a universal workspace ID;
2. add exact stdout/stderr log references and observed byte counts.

Illustrative inspect projection:

```json
{"schema_version":1,"command":"run inspect","caller_role":"inspector","entry":"repository-tests-installed","execution_id":"2ebdc656-8c86-414b-9b14-675af88a13e8","workspace_instance":"744f70cee31322aa","effective_entry_digest":"71bbc171c9105bf23b495b2cd4d8cd0b5612dc06cd6ec86a9b809989238efc5f","state":"exited","argv":["pdm","run","test"],"cwd":"/Volumes/WorkSSD/Development/svc","env_files":[],"logs":{"stdout":{"path":"/.../stdout.log","bytes":2464},"stderr":{"path":"/.../stderr.log","bytes":0}},"started_at":"2026-08-06T12:18:12.430Z","finished_at":"2026-08-06T12:18:18.708Z","duration_ms":6277,"exit_code":0}
```

Log byte counts are an observation at receipt time; `state` determines whether
they are terminal. Optional state-inapplicable fields remain omitted rather
than `null`. Environment values, child PIDs, and native log contents remain
absent. No real external field consumer was found, so correcting the unreleased
field name now is cheaper than preserving misleading public terminology.

## Channels, exits, and help

- Entry/follow native stdout and stderr retain their channels; SVC live and
  terminal wrapper text uses stderr.
- Inspect default text and every completed compact receipt use stdout.
- Grammar, configuration, selection, and execution-domain/workspace mismatches
  that occur before an execution is selected use stderr. A published start,
  capture, or owner-loss outcome remains a receipt (JSON stdout; text wrapper
  stderr). An authority-store failure that prevents a trustworthy receipt uses
  stderr.
- A normally exited entry/follower passes through the child exit code. Usage is
  `2`; configuration/selection/domain conflict is `3`; start, authoritative
  capture, owner loss, or execution-store failure is `4`; caller Ctrl+C is
  `130` (with platform signal projection otherwise). Inspect success is `0`
  regardless of observed state.

Self-sufficient help must explain:

- entry execution versus full replay/wait versus observation-only inspect;
- same-intent convergence and deliberate rerun after settlement;
- native channel preservation and where SVC lifecycle text goes;
- JSON suppression and exact-receipt role;
- execution/log references and workspace-local scope;
- owner Ctrl+C interruption versus follower detachment;
- child exit passthrough and inspect's observation-success exit.

Help does not duplicate run configuration syntax; project configuration and
ordinary tools own entry discovery/details beyond the bounded unknown-entry
recovery list.

## Rejected additions

- No new output mode, JSONL stream, generic logs command, tail flag, or result
  parser.
- No artifact references inferred from native output. Log files are execution
  evidence, not project artifact declarations.
- No unified schema with dev results and no public merger of bounded run with
  long-lived capabilities.
- No CI-only command behavior or second execution policy.

## Review status

Written from the current implementation, the persisted real SVC execution, and
the explicit absence of real Consumer adoption. It does not treat the earlier
Beluna admission case as post-implementation usage evidence. Sir accepted the
candidate on 2026-08-08 and added an implementation-architecture requirement:
shared semantics use canonical, accurate names while distinct run/dev
semantics remain visibly different. That architecture is reviewed separately
in [`execution-vocabulary-review.md`](execution-vocabulary-review.md). Product
implementation remains gated.
