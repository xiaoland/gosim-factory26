# Shared Execution Architecture and Vocabulary Review

## Accepted design law

Sir established the implementation requirement on 2026-08-08:

- one semantic fact has one canonical owner and one canonical vocabulary;
- the same fact is named consistently across `run`, `dev`, storage, receipts,
  and tests;
- different facts remain visibly different even when they share private
  mechanics;
- names must be accurate, self-explanatory, and not leak one domain's language
  into another.

This does not require a common public schema. Public `run entry` and `dev
target` remain different domain terms; only genuinely shared facts share code
types and vocabulary.

## Current concrete drift

The current private record violates this law in several places:

```text
ExecutionRecord.entry
ExecutionRecord.workspace_id
ExecutionRecord.effective_entry_digest
ExecutionRecord.slot_key
```

- `entry` stores a run entry name in `run`, but a dev target name in `dev`.
- `workspace_id` stores `WorkspaceIdentity.instance`, not the repository,
  worktree, or complete workspace identity.
- `effective_entry_digest` stores an effective run-entry digest in `run`, but
  the effective dev declaration digest in `dev`.
- `slot_key` is used as a convergence identity, lock filename key, active
  pointer key, and dev capability boundary. With `dev stop`, same-intent join
  and opposite-intent serialization can no longer be described by that one
  accidental storage term.

The dev identity layer has parallel leakage:

- `CapabilityIdentity.lock_key` names one consumer of the identity rather than
  the capability boundary itself;
- `runtime_key` is projected despite having no demonstrated runtime consumer;
- `coordination_subject` does not say that it is the scope-selected
  worktree/repository/host identity;
- the accepted removal of profiles has not yet removed `profile` from the
  type, hashes, interpolation, environment, and outputs.

These are not cosmetic inconsistencies. They obscure who owns convergence,
make persisted records run-shaped, and make it easy for stop/ensure to join or
overwrite the wrong lifecycle intent.

## Candidate owner topology

Keep four deep owners with narrow translations:

```text
workspace.py
  owns WorkspaceIdentity and its derivation

run controller                     dev controller
  owns entry/config/receipt           owns target/capability/readiness/result
             \                         /
              neutral execution mechanism
                owns attempt records, launch, capture,
                logs, wait/follow, settlement, owner loss
```

The neutral execution mechanism accepts identities already derived by the
domain controller. It does not decide what a run entry, dev target, readiness
probe, capability, ensure, or stop means. A shared coordination helper may own
lock/pointer mechanics, but domain controllers own the material used to derive
the coordination boundary and intent digest.

`svc_cli/workspace.py` remains the sole workspace owner. `dev.identity` should
not re-export or wrap the resolver merely for import convenience; `run`, `dev`,
and tests import the canonical owner directly.

## Candidate canonical vocabulary

### Workspace facts

| Meaning | Canonical name | Notes |
| --- | --- | --- |
| Complete value | `WorkspaceIdentity` / public `workspace` | One shared type and exact projection owner |
| Canonical directory | `root` | Never infer this from execution cwd |
| Local execution namespace | `namespace_id` inside workspace | Flatten only as `execution_namespace_id` if needed outside the object |
| Repository-scoped identity | `repository_id` | Rename implementation-shaped `repo_common_id`; Git common-dir derivation remains private |
| Concrete worktree identity | `worktree_id` | Never label `instance` as worktree |
| Local Consumer resource key | `instance` inside workspace; `workspace_instance` when flattened | Current 16-hex value consumed by real projects |

The public `dev identity` object should consequently use `repository_id` rather
than `repo_common_id` before this revised protocol is released. The three real
identity consumers read only `workspace.instance`, so the correction does not
conflict with an observed field consumer. `repository_kind` continues to
qualify Git versus non-Git derivation.

### Domain facts

| Run | Dev | Rule |
| --- | --- | --- |
| `entry` / `entry_name` | `target` / `target_name` | Retain domain vocabulary at the controller and public projection |
| `effective_entry_digest` | `effective_target_digest` | Each digest covers the effective declaration relevant to that domain subject |
| execute entry | ensure or stop target | These are different lifecycle intents and never share a public status vocabulary |
| child result/receipt | readiness/capability result | Native exit is the run result input; readiness remains a dev postcondition |

Do not expose a neutral `subject` field in public JSON merely because the
private record needs one.

### Neutral execution-attempt facts

Replace the run-shaped record vocabulary with:

```text
execution_id
domain                 # run | dev
operation              # execute | ensure | stop
subject                 # domain-owned name, projected as entry or target
workspace_instance
intent_digest
coordination_key
state
argv / cwd / env_files
capture
owner_process_id
child_process_id
timestamps / duration / exit / signal / failure
```

`subject` and `operation` are both required. `domain=dev, subject=web` is
insufficient once `ensure web` and `stop web` are opposite intents. Conversely,
calling the subject `entry` would keep leaking run vocabulary into dev.

`intent_digest` is neutral persisted evidence. The domain projection restores
the self-explanatory public name: `effective_entry_digest` for run and
`effective_target_digest` for dev. For dev, compute it from the selected
effective target declaration rather than an unrelated whole-project digest;
an edit to another target must not make this target's attempt appear to have a
different intent.

`owner_process_id` and `child_process_id` replace the ambiguous PID pair
`owner_pid`/`process_id` internally. Neither becomes ordinary public lifecycle
authority.

## Coordination identity versus execution identity

Keep these concepts distinct:

1. **coordination key** — selects the active boundary on which operations must
   serialize;
2. **intent identity** — `operation + intent_digest`, deciding whether a caller
   may join the active attempt;
3. **execution ID** — identifies one concrete published process attempt.

For run, the coordination key is derived from execution namespace, worktree,
entry, and effective entry intent. There is only one `execute` operation, so an
active equivalent entry invocation joins it.

For dev, the coordination key is the capability identity and deliberately
excludes `ensure` versus `stop` **and the current endpoint/declaration digest**.
It is derived from namespace, scope, scope-selected identity, and target. This
makes opposite operations and changed declarations serialize on the same named
resource boundary. A caller joins only when the active record has the same
operation and intent digest; `ensure` never joins `stop`, and a changed
effective declaration never silently joins the old intent.

The store may continue using files called slots and locks privately. Public and
controller code use `coordination_key`, not `slot_key` or `lock_key`, because
storage mechanism is not the semantic identity.

## Dev capability vocabulary

The post-profile `CapabilityIdentity` should carry only:

```text
scope
target
endpoint_id
scope_id
capability_id
```

- `scope_id` is the identity selected by `scope`: worktree ID, repository ID,
  or derived host identity;
- `capability_id` binds namespace, scope, scope ID, and target and is the dev
  coordination key; the endpoint stays in the operation's intent digest so a
  probe edit cannot create an unsynchronized second lifecycle boundary for the
  same named target;
- `endpoint_id` remains the digest of the resolved readiness endpoint;
- remove `profile`, `lock_key`, `runtime_key`, and `coordination_subject` from
  public/domain vocabulary rather than renaming unused duplication.

The execution mechanism receives `capability_id` as its neutral
`coordination_key`; it does not import `CapabilityIdentity` or interpret scope.

## Log-reference vocabulary

One internal `ExecutionLogReference` owns the shared facts:

```text
stream       # stdout | stderr | merged
path
bytes
```

Domain projections remain semantically distinct:

- run exposes `logs.stdout` and `logs.stderr` because it preserves two native
  streams;
- dev ensure/stop attempt results expose one `log` with `stream: merged`;
- readiness probes expose bounded native `output`, not an execution log;
- no result alternates among `log_path`, `startup_log`, and a bare path for the
  same attempt-log fact.

Default text may label the same reference contextually as `startup log` or
`stop log`; the structured field and internal type remain consistent.

## Migration and compatibility boundary

The shared-run change is unreleased and no real Consumer reads its receipt
fields. The three known identity consumers read only `workspace.instance`.
Therefore the implementation should perform one deliberate record/projection
rename before release instead of adding aliases that preserve misleading
names.

Persisted local execution records are ephemeral coordination evidence, not
project data. The implementation plan must still choose an explicit migration
behavior: read the current schema during a bounded transition or reject old
records with a precise stale-record error. It must not accept both vocabularies
indefinitely inside the main model.

Tests should assert semantic names at owner boundaries, not reproduce private
storage words in domain tests. In particular, dev tests should not fetch
`capability["lock_key"]` merely to discover the private slot.

## Review status

The consistency/accuracy/self-explanation law is accepted from Sir's direction
on 2026-08-08. Sir then accepted the concrete owner topology and vocabulary on
the same date. This is architecture design, not product implementation
authorization.
