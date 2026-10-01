# Workspace Identity Command Review

## What the identity describes

The current `svc dev identity` result is not target status. It resolves one
executable workspace into:

- canonical root;
- Git versus non-Git repository kind;
- Git common-repository identity;
- private worktree identity;
- local machine/user execution namespace;
- the derived instance used by SVC local execution domains.

The implementation owner is already `svc_cli/workspace.py`, whose contract is
“workspace identity shared by local SVC execution domains.” Both `run` and
`dev` consume it internally. That shared implementation ownership does not by
itself determine the public namespace: the demonstrated external consumers use
the identity to scope development resources and capability lifecycles.

## Why `svc dev status` cannot replace it

Configured dev status executes one or every Consumer-declared readiness probe.
Three real project scripts need identity independently of probes for direct
database ready/reset/status/stop operations and worktree cleanup. Replacing an
exact identity query with dev status would change effects, latency, failure
horizon, and availability.

## Can root `svc status` carry it?

Yes. Root status is declaration-only and already serves environment preflight
and handoff. Workspace identity qualifies that result, costs about 227 bytes in
the exact JSON object, and should be available in healthy, actionable,
malformed, and unadopted results. It does not require a dev declaration.

This corrects the earlier comparison, which considered only `dev status`.

## Why root status should not be the only identity query

Root status owns a broader lifecycle:

- it inspects installed/corpus/adopted versions, configuration, generated
  integration, dev/run declarations, and next disposition;
- it returns exit `3` for a successfully observed but non-healthy project;
- it may be malformed or actionable for reasons unrelated to workspace
  identity.

All three real Consumers currently use APIs that raise on nonzero exit:
client-web uses `execFileSync`; core-py uses `subprocess.run(check=True)`. During
this review, current-source root status returned valid 1,349–1,383-byte JSON
but exit `3` in client-web, core-py, and SFP7 Camera. None of those unrelated
integration dispositions makes their workspace instance invalid.

Eliminating the exact query would therefore move complexity into every
identity consumer: accept status exits `0|3`, distinguish them from
usage/integrity failure, parse a broad result, and ignore unrelated health.
That is not a simpler total interface merely because the CLI has one fewer
verb.

## Accepted command shape

Retain the existing exact query:

```text
svc dev identity [--repo <repo>] [--json]
```

- It is probe-free and exits `0` whenever the workspace identity resolves.
- Default text is a concise Agent/Human workspace/worktree summary.
- Compact JSON is the CI/script exact identity projection.
- It does not require `svc.json`, a healthy adoption, or configured dev.
- It adds no new capability or root-level grammar.

The accepted default text is a short semantic identity chain rather than the
current content-free `completed` receipt:

```text
svc dev identity
instance: 744f70cee31322aa
root: /Volumes/WorkSSD/Development/svc
repository: git aa0f1681e0b01e7b447f
worktree: e5efecf333a45dde1c90
namespace: 13ee6bfda907db280cc4
```

This explicit diagnostic query shows the complete comparison chain. The root
explains which canonical workspace was resolved; repository and worktree
identities explain sharing across linked worktrees; namespace explains
host/user separation; instance is the final value used by current Consumer
runtime scripts. Successful text and JSON go to stdout. Errors remain on
stderr under the shared CLI error contract.

The compact JSON envelope and all six workspace **meanings** remain. The later
accepted shared-vocabulary review corrects the implementation-shaped
`repo_common_id` public key to `repository_id`; Git common-directory derivation
remains private. Three real Consumer scripts parse only `workspace.instance`,
so that demonstrated field remains unchanged and unflattened. JSON does not
gain a content-free `status: completed` field.

Help must state that `--repo` selects the workspace directory and defaults to
the current directory, while `--json` emits compact JSON for scripts and CI.
No field selector, short mode, namespace override, configuration read, or
target probe is added.

`dev status` should also include the same `workspace` object because it
qualifies that readiness observation. Root status may carry the workspace
projection when it materially qualifies preflight, but it is not an exact
identity-query replacement. Fact duplication inside results is cheaper than
forcing callers to make a second query; command fusion across incompatible
lifecycles is not.

The recommended public shape is therefore:

```text
svc status
svc dev identity|status|ensure|stop
```

Root status could be the sole provider only if SVC deliberately required every
identity consumer to treat exit `3` as a valid data result. Current independent
Consumers and the accepted meaningful status exit make that trade worse than
one small exact query.

## Review status

Sir accepted retaining `svc dev identity` on 2026-08-07, then accepted the
input/help/text/JSON contract above on the same date. The earlier root
`svc identity` rename candidate is rejected: internal cross-domain reuse is
insufficient reason to expand the root grammar when real callers express a dev
resource-scoping intent. This is not implementation authorization.
