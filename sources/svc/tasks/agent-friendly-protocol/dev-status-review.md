# `svc dev status` Review

## Information Service

`svc dev status [target]` is a readiness snapshot over one selected development
capability or every declared dev target. It executes each declared
readiness probe, including a Consumer-defined `exec` probe, but never invokes
the provisioner or takes over a process. It must let an Agent or Human answer:

1. Which exact project/worktree capability was observed?
2. Which targets are ready now, and which are not?
3. What observation proves each disposition?
4. When ready, where can the consumer use it?
5. When not ready, what diagnostic or valid SVC continuation exists?

This is a volatile observation, not project adoption state, a provision
attempt, or proof that a broader test/acceptance claim passed. SVC itself makes
no project/runtime mutation in this command, but it cannot guarantee that an
arbitrary Consumer-declared exec probe is side-effect-free; the project owns
that probe contract.

## Real Evidence

Current-source calls were run read-only against three actual Consumers:

| Consumer | Observed result | Default text | Compact JSON |
| --- | --- | ---: | ---: |
| SFP7 Camera | 0/1 ready; host-scoped exec probe reports missing builder receipt | 32 bytes | 1,043 bytes |
| InKCre client-web | 1/4 ready; database ready, web/web-ui/webext nonzero | 32 bytes | 2,508 bytes |
| InKCre core-py | 0/1 ready; database exec probe nonzero | 32 bytes | 973 bytes |

All three default-text results were only:

```text
SVC dev status: action-required
```

The current-source JSON result retains target names and the old
profile/workspace/capability identity, plus probe kind, endpoint identity,
stable reason, output byte count, and truncation state. It does not retain the
exec-probe exit code or output, declared access, provision kind, or a
target-specific continuation. The accepted flattened configuration removes
the profile field and identity component from the future result.

The discarded output is materially useful, not hypothetical noise:

- SFP7 Camera emitted one compact 194-byte JSON diagnostic identifying
  `RECEIPT_MISSING` and its claim ceiling.
- InKCre core-py emitted a 1,633-byte structured diagnostic. It reported the
  database runtime as ready and converged, including URLs and migration head,
  but exited nonzero because `source_matches` was false. SVC reduced this to
  `nonzero-exit` and `output_bytes: 1633`.
- InKCre client-web's failed web probe emitted no diagnostic, which is itself
  useful to distinguish from discarded or truncated output.

A bounded scan of August 2026 Codex trajectories found 13 operational
`svc dev status ... --json` tool calls; three other matches were help/review
calls rather than runtime observations. Fourteen current real-project task
files mention the command. Retained handoffs repeatedly compress JSON to target
name, readiness, probe reason, output size/truncation, and side-effect horizon.
One InKCre preflight claims a migration head from the database observation,
although the current `dev status` payload cannot carry that native fact; the
underlying project probe or another command must have supplied it.

## Current Failures

### Text loses the service

The generic text emitter prints only command and aggregate status. It does not
identify target, ready count, probe, reason, access, diagnostics, or
continuation. Human/Agent callers are effectively forced into JSON, contrary
to the semantic-form contract established by this unit.

### JSON preserves implementation identity but drops decision evidence

The exact object includes several derived coordination hashes and an exec
`endpoint_identity` encoded as a NUL-separated command, yet discards the
already bounded native output that explains a failed readiness predicate. This
is the wrong information priority for diagnosis. The hashes may remain useful
for exact coordination diagnosis, but they cannot substitute for the probe's
own evidence.

### Readiness is not connected to use or continuation

The target declaration already owns optional consumer-facing `access` and an
`exec` or `manual` provisioner. Status returns neither. A ready result therefore
does not tell the caller where to connect; a not-ready result does not
distinguish an available `svc dev ensure` continuation, a manual provision
boundary, or an occupied-but-unhealthy responder that ensure will refuse.

### Other paths hide decisive reasons

Invalid configuration returns a structured `reason`, but the generic text
emitter drops it. Per-target `SvcError` values are retained only inside JSON.
The command's aggregate `action-required` is therefore insufficient both for
configuration failure and runtime observation failure.

## Three-Pressure Reading

| Pressure | Consequence for this command |
| --- | --- |
| Content semantics | A comparable target list contains one volatile disposition per target, exact identity qualification, a probe observation, optional bounded native diagnostic, declared access, and a possible continuation. Native exec output remains project-owned evidence and must not be reinterpreted by SVC. |
| Agent characteristics | Agents scan target differences and actionable failures, then may parse exact JSON. Long coordination hashes and escaped NUL argv are poor primary presentation. Missing diagnostics cause extra shell calls and invite unsupported inference. |
| Information-service purpose | The result must support proceed, connect, ensure, perform a declared manual action, diagnose an unhealthy responder/probe, or hand the same qualified snapshot to another participant—without starting anything. |

## Smallest Candidate

Keep the existing command and its text/JSON choice; add no new mode or global
schema.

### Default text

- Lead with ready count and the workspace instance needed to qualify the
  observation. An all-target result has no single capability scope.
- Emit one stable, comparable line per target: ready/not-ready, target,
  capability scope, probe kind, and reason.
- For a ready target, show resolved declared access when present.
- For a not-ready exec target, show its exact exit code and shell-display probe command and a
  bounded native diagnostic preview when output exists. State explicitly when
  output is empty or truncated.
- Show `svc dev ensure <target>` only when it is the mechanically valid next
  SVC operation. Distinguish a manual provisioner and an unhealthy responder
  instead of sending both through ensure.
- Include exact configuration or per-target errors adjacent to the affected
  target. Do not end with a duplicate aggregate status line.

Illustrative multi-target shape from the current InKCre observation:

```text
svc dev status: action-required — 1/4 ready; instance 4ac9df364b54706e
ready      database  worktree  exec zero-exit
not-ready  web       worktree  exec exit 1; no output; ensure
not-ready  web-ui    worktree  exec exit 1; no output; ensure
not-ready  webext    worktree  exec exit 1; no output; ensure
Ensure one: svc dev ensure <target> --repo /Volumes/WorkSSD/Development/InKCre/client-web
```

For a one-target call, `<target>` becomes the exact selected name. For an
all-target call, targets sharing the same continuation may use one final
template while each row still identifies `ensure`, `manual`, or `blocked`.
Target-specific native diagnostics remain directly beneath their row rather
than being grouped away from their source.

### Structured result

- Keep compact JSON as the exact projection for automation and deeper
  diagnosis.
- Retain workspace, capability, and declaration facts provisionally, except
  for the separately accepted removal of the unused profile dimension.
- Add resolved access and provision kind per target so readiness can be
  interpreted and continued without rereading configuration.
- Preserve the exact exec exit code and bounded exec-probe output as native
  text plus byte/truncation facts; do not auto-detect or embed project JSON as
  SVC-owned structure.
- Treat probe output as consumer-owned native evidence. SVC must not inject or
  serialize secret configuration values, but it cannot promise to redact
  secrets printed by a Consumer probe; help must make that boundary clear.

Because configured exec output may be as large as 1 MiB per target, default
text must use a small diagnostic preview rather than blindly copying the full
capture. The structured result may carry the capture up to the already
declared probe limit. If the preview truncates independently, it should expose
that fact and the exact probe command supplies the recoverable full-diagnostic
continuation. Persisting every status probe in the shared execution store would
add lifecycle state without a demonstrated need and is not part of this
candidate.

### Exit and help

Retain exit 0 only when every selected target is ready and exit 3 otherwise;
real scripts and verification paths consume that aggregate gate. Self-sufficient
help must state that status executes declared readiness probes—including
Consumer-owned exec probes—but never invokes the provisioner or takes over a
process. It must explain one-target versus all-target selection plus text/JSON
behavior without falsely promising that arbitrary probe code is read-only.

Resolved readiness snapshots use stdout in both default and JSON modes even
when the aggregate disposition exits `3`. Invalid grammar, invalid project
requests/declarations, and SVC execution or integrity errors use stderr. There
is no live coordination channel because status does not own or join a
lifecycle attempt.

## Native-Output Boundary Recommendation

The proposed native diagnostic changes the original implementation invariant
that machine output never emits secret environment values. Keeping the current
claim would be misleading: a Consumer probe chooses what it writes, and hiding
all output sacrifices the only real failure explanation without making the
probe itself safe.

The recommended boundary is narrower and enforceable: SVC does not inject,
record, or serialize configured/inherited secret values itself; bounded probe
stdout/stderr is Consumer-owned native evidence and is preserved. Consumer
probes must therefore emit only collaboration-safe diagnostics. This matches
`svc run`'s native-output responsibility more closely and should be stated in
help/config guidance rather than marketed as redaction.
