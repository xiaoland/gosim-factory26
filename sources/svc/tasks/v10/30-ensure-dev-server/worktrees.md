# Git Worktree Strategy

## Identity Model

SVC distinguishes:

- `repo_common_id`: canonical Git common-dir identity shared by linked worktrees;
- `worktree_id`: the private Git admin identity for one main/linked worktree, never branch, HEAD, or a display path;
- `capability_id`: stable target name such as `frontend`;
- `profile`: resolved `dev.profile`;
- `endpoint_id`: canonical probe endpoint or explicit custom-probe coordination identity;
- `process_owner`: current launch token plus live handle/group, used only during that attempt.

Non-Git projects fall back to one canonical workspace-root identity. Bare repositories are not runnable workspaces. Runtime locks and evidence hash identity material into a private per-user OS runtime directory while retaining safe diagnostic fields in structured output.

## Scope and Reuse

| Scope | Identity included | Intended use | Default reuse |
| --- | --- | --- | --- |
| `worktree` | common repo + worktree | app code built from one worktree | current worktree instance only |
| `repository` | common repo | shared DB, proxy, stable mock | all linked worktrees |
| `host` | explicit host capability key | deliberately global local infrastructure | explicit opt-in only |

`worktree` is the default for application targets. Different clones remain distinct even if they share a remote. Host/WSL/container execution namespaces are distinct even when they share a mounted repository.

Lock isolation alone cannot prove source provenance. A worktree target therefore declares one instance proof:

1. an endpoint/route containing `${dev.instance}`; or
2. a probe predicate that verifies an instance token from a response/header/custom check.

Without either proof, a static healthy endpoint can serve another worktree's code. Strict worktree reuse blocks with `worktree-provenance-unverified`; the consumer may instead declare `scope: repository` when sharing is intentional.

## Consumer Interpolation

SVC exposes deterministic, non-secret tokens to configuration interpolation and the provisioner environment:

- `${dev.instance}` / `SVC_DEV_INSTANCE`;
- `${dev.worktree.id}` / `SVC_DEV_WORKTREE_ID`;
- `${dev.profile}` / `SVC_DEV_PROFILE`;
- `${dev.target}` / `SVC_DEV_TARGET`.

Interpolation is token substitution within existing scalar/argv elements, never shell expansion. SVC does not allocate ports or configure proxies. A consumer may use these values to derive a portless hostname, a port from `svc.local.json`, a browser-profile directory, or an application health identity.

For the reference project, worktree isolation means routes such as `partner-up-${dev.instance}.localhost`, not one static `partner-up.localhost`. Shared infrastructure remains explicitly repository-scoped.

## Coordination Key

The lock/record key includes:

```text
runtime namespace
+ declared scope
+ repo common identity
+ worktree identity when scoped to worktree
+ capability
+ profile
+ canonical endpoint identity
```

The endpoint component prevents two differently named targets from racing for the same concrete capability. A waiter re-probes under the same key before it may provision. A stale record never authorizes reuse or termination.
