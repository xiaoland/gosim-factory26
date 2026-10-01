# Reference Findings

## Consumer Reference: `mvp-HA`

The reference repository makes `pnpm dev:ensure` its agent-facing entry point. It owns two static routes:

| Service | Stable URL | Start command |
| --- | --- | --- |
| frontend | `https://partner-up.localhost` | `pnpm --filter @partner-up-dev/frontend dev` |
| backend | `https://api.partner-up.localhost` | `pnpm --filter @partner-up-dev/backend dev` |

`scripts/ensure-dev-servers.mjs` first calls `portless list`, regards a route as unavailable if it is absent or its `HEAD` request returns an error or `>=500`, starts each unavailable route detached, and polls until both are ready. Logs go to `.codex-tmp/dev-servers/`.

`portless` itself allocates a child port, owns the proxy at HTTPS port 443, registers a named route, and supplies `PORT`, `HOST`, and `PORTLESS_URL` to the child. It is useful consumer infrastructure, but it is not SVC infrastructure: SVC cannot assume Node, `pnpm`, a global installation, a proxy, or stable `.localhost` naming.

## VS Code Is a Consumer, Not the Authority

`.vscode/launch.json` invokes `dev:portless:backend` directly for the backend and uses a pre-launch task for the frontend. `.vscode/tasks.json` supplies background readiness patterns and a task-termination hook. These files demonstrate editor integration, but they are neither portable nor sufficient to prevent an Agent from starting an independent server. The reusable boundary is the explicit startup command plus health contract, not VS Code task ownership.

## Reference Limitation Rejected by v1

When a route is registered but its probe is unready, the reference invokes `portless --force`. `--force` kills the existing process before taking the route. That is suitable only when the caller has deliberately delegated forceful route ownership to `portless`; it is unsafe as a default cross-project SVC operation. `svc dev ensure` will report an existing unhealthy endpoint and leave it intact.

## SVC Baseline Before This Sub-task

- Published SVC 10.0.0 accepts exactly `schema_version` and `svc_version` in `svc.json`; expanding it requires an explicit new schema and migration contract.
- Current `svc init` does not manage `.gitignore`, so a bounded local-config ignore block is a new default output and consumer-layout change.
- Earlier runtime design reserved `svc dev ensure` for caller-declared argv, port/health input, and transient evidence. Discussion replaced repeated inline declaration with a committed base config plus local overlay while retaining Consumer authority.
- `svc_cli.plans` applies to project filesystem integration. Starting a process is a distinct side effect and should be explicit in the direct command contract rather than disguised as a project-file plan.

## Worktree Finding

Git linked worktrees share a common repository identity but have private admin identities. A static healthy URL proves capability readiness, not which worktree's source is running. Reliable per-worktree testing therefore needs a unique endpoint/route or a probe-visible instance marker. Lock names alone cannot supply that provenance.

## Setup Finding

VS Code Tasks are a useful generic bridge because they can invoke `svc dev ensure <target>` as a process task. `launch.json` remains debugger/browser/extension-specific. Root `package.json` scripts can expose the same stable target without serializing stack-specific provisioner argv, provided reserved-key conflicts block and the editor preserves unrelated bytes.

## Deduced Model

```text
effective project/local config declares target + scope + probe + provisioner
                         |
                         v
per-user runtime lock --> probe target/instance -- healthy --> reused (no spawn)
                         | unresponsive
                         v
                 run declared provisioner, no inferred shell
                         |
                         v
            poll health URL --> healthy --> started + transient record
                         | timeout / child exit
                         v
                  terminate only this process group; report logs
```

The current declared probe plus required instance provenance—not a PID, open port, command-line resemblance, or persisted record—is the reuse authority. The runtime record is only diagnostic evidence for an SVC-started attempt.
