# Verification Plan

## Configuration and Init

- Parse valid complete base schemas; reject missing required fields, wrong types, duplicate keys, non-finite JSON values, invalid UTF-8/JSON, and unknown fixed-object keys.
- Treat absent/empty local overlays as no-op; prove nested object merge, scalar/array replacement, `dev.profile` override, and final effective validation.
- Reject local `schema_version`, `svc_version`, unknown or non-overrideable paths, type conflicts, null deletion, symlinks, and non-files without falling back to base values.
- Prove `svc init --plan` creates/appends the `.gitignore` managed section while preserving unmarked LF/CRLF content; an existing unmarked `svc.local.json` rule remains byte-identical beside the generated section; current is no-op; drift/duplicates/symlinks block.
- Prove init never creates or rewrites `svc.local.json`; stale `.gitignore` or config aborts all writes; injected commit/postcondition failure rolls back and preserves an intervening edit.
- Prove legacy v1 and future schemas block writes without an automatic migration, and prove `adopt` surgically changes only `svc_version` in a valid v2 base without losing or reformatting Consumer configuration.

## Worktree Identity

Create a fixture Git repository with main and linked worktrees:

- common identity is equal, private worktree identity differs and survives worktree move;
- same worktree/capability/profile/endpoint serializes and reuses;
- different worktrees default to distinct instances and reject unverified static-endpoint reuse;
- explicit repository scope shares one healthy infrastructure capability;
- different clones and host/WSL/container namespace fixtures remain distinct;
- non-Git root fallback is deterministic; bare/nested/invalid repository cases are explicit.

## Runtime Coordinator

Use small fixture HTTP, TCP, and command probes plus a launch counter:

| Scenario | Expected proof |
| --- | --- |
| Healthy verified target | `reused`; no spawn; repository tree byte-identical. |
| Absent target | Exact provisioner argv starts once; readiness yields `started`; repeated ensure reuses it. |
| Concurrent callers | Exactly one provision attempt; waiters re-probe and reuse. |
| Wrong worktree instance | `worktree-provenance-unverified`; no spawn or takeover. |
| Occupied unhealthy responder | Structured conflict; external PID survives; no provision. |
| Manual absent target | Required-action result; zero process/file mutation. |
| Early exit/readiness timeout | Exit 4; cleanup outcome and log paths reported; no successful record. |
| Invalid probe/argv/interpolation | Structured validation error; zero side effects. |

Probe fixtures cover HTTP method/status/redirect/TLS policy, TCP timeout, bounded exec output, loopback/allowed-address policy, and secret-value non-disclosure. Platform fixtures verify only the cleanup guarantees each supervisor adapter actually supports.

## Setup Plan/Apply

- `--plan` and no-mode planning are byte-stable and write nothing; `--plan` plus `--apply` is CLI usage error; exact apply followed by repeat plan/apply is no-op.
- Existing Tasks JSONC with comments, trailing commas, foreign tasks, formatting, and CRLF receives only a marked task; every unrelated byte remains identical.
- Clean marker is current/refreshable; edited hash, duplicate/malformed marker, reserved label collision, invalid JSONC, duplicate structural key, wrong target type, symlink, or non-UTF-8 blocks.
- Root `package.json` receives only a missing `svc:dev:<target>` key; exact is no-op; conflicting value, missing package, invalid JSON, duplicate key, non-object scripts, symlink, or non-UTF-8 blocks.
- `.vscode/launch.json` remains byte-identical in every setup fixture.
- Base/local config or destination changes after planning produce digest mismatch/stale-plan and zero writes.
- Multi-file injected commit/postcondition failure fully rolls back; rollback never overwrites an intervening Consumer edit.
- Orphan generated entries are reported and never automatically removed.

## CLI, Docs, and Release

- Stable JSON/human contracts cover config status, identity, probe observations, ensure outcomes, setup plans, blockers, and apply results.
- The Codex skill teaches `status`, worktree-safe `ensure`, and setup plan/apply without copying the durable protocol.
- Canonical CLI/config docs, README examples, manifest, migration non-applicability, real MAJOR impact, and the exact one-time 10.0.1 version exception agree.
- Run `pdm run test`, `pdm run build-monolith`, `pdm build`, source/wheel smoke tests, and release verification.
- After those deterministic gates pass, execute the isolated `mvp-HA` worktree acceptance protocol. Preserve an evidence bundle containing commands, versions, plan digests, structured outcomes, relevant diffs, process/log identities, cleanup result, and the primary checkout's unchanged status.
