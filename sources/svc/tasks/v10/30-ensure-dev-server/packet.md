# General Development Runtime

- **Objective**: Add a general, environment-, platform-, and stack-independent `svc dev` protocol that lets Agents and humans share declared development capabilities safely. The first delivery resolves committed configuration plus machine-local overrides, understands Git worktree identity, observes and ensures declared targets without duplicate startup or takeover, and can plan/apply bounded VS Code Task and `package.json` integrations.
- **Guardrails**:
  - `svc.json` is the complete, versioned project configuration. `svc.local.json` is an optional sparse local overlay interpreted under the base schema; it is not specific to `dev` and has no `schema_version` of its own.
  - Schema/adoption fields such as `schema_version` and `svc_version` are not locally overrideable. Every other overrideable path is declared by the base schema rather than hard-coded to one command family.
  - `svc init` never creates or edits `svc.local.json`. It plan/apply-maintains only a bounded, hashed `.gitignore` section containing `svc.local.json`, preserving all unmarked consumer content.
  - The consumer owns configuration values, capability meaning, profiles, startup argv, environment, probes, access URLs, and editor/package choices. SVC owns the schema, coordinator behavior, and marked/reserved generated projections.
  - The default application capability scope is one Git worktree. Cross-worktree reuse is allowed only when the target explicitly declares repository/host sharing or current instance provenance is verifiable; a healthy static endpoint alone cannot prove which worktree's code it serves.
  - Runtime reuse is proved by the declared current probe, never by process names, open-port guesses, stale PID/record state, IDE tasks, or package scripts. SVC never force-takes over a human- or tool-owned process.
  - Transient locks, launch evidence, and logs remain per-user and outside the repository. They are diagnostic provenance, not health or termination authority.
  - Plan/apply is deliberately selective: it protects high-risk writes to `.gitignore`, VS Code Tasks, `package.json`, and other non-SVC-owned content. `status`, `identity`, and probes are read-only; the explicit `dev ensure` command converges runtime state directly and idempotently without a digest.
  - Setup changes are dry-run first through one command surface: `--plan` or exact `--apply <digest>`. Existing Consumer-owned JSON/JSONC bytes outside a bounded generated entry must remain unchanged.
  - The first setup adapters support VS Code Tasks and root `package.json` scripts only. They do not infer or modify `launch.json`, debugger adapters, browsers, package managers, workspaces, proxies, or frameworks.
- **Verification**:
  - Config fixtures prove strict complete-base validation, sparse generic local overlays, deterministic merge, local non-overrideable-field refusal, and zero unintended writes.
  - Init fixtures prove `.gitignore` managed-section create/append/no-op/drift/stale-plan/rollback behavior while never creating or rewriting `svc.local.json`.
  - Git fixtures prove stable main/linked worktree identity, default worktree isolation, explicit repository sharing, instance-bound endpoint resolution, and no cross-worktree false reuse.
  - Runtime fixtures prove healthy reuse, exact single launch, concurrent one-spawn behavior, occupied-unhealthy preservation, bounded readiness, transparent cleanup outcome, and no repository writes.
  - Setup fixtures prove deterministic plan/apply, surgical preservation of unrelated `package.json` and Tasks JSONC content, reserved-entry conflict refusal, no `launch.json` changes, idempotence, pre/postconditions, and rollback.
  - Stable JSON/human output, existing CLI behavior, `pdm run test`, distribution build, and installed-wheel smoke tests pass.
- **Current Truth**:
  - The implementation now accepts strict schema-v2 `svc.json`, resolves optional generic `svc.local.json`, manages a bounded local-config `.gitignore` section, and blocks v1 writes. Adoption replaces only the current-schema `svc_version` JSON span.
  - The initial packet draft modeled one direct `--health-url -- argv` invocation. Discussion superseded it with a consumer-declared capability model, general local overlay, worktree identity, and plan-first setup integrations.
  - The `mvp-HA` reference demonstrates the collaboration need through `pnpm dev:ensure`, `portless`, VS Code tasks, stable routes, detached logs, and health polling. Its static routes and `--force` takeover are consumer-specific and unsafe as SVC defaults.
  - `svc_cli.plans` already provides exact plan digests, filesystem pre/postconditions, atomic writes, rollback, and concurrent-edit preservation. Runtime convergence remains a distinct side effect.
  - Existing no-flag `init`/`adopt`/`self-update` behavior is already plan-only. Adding explicit `--plan` is backward-compatible; `--plan` and `--apply` are mutually exclusive only on commands that own a plan/apply mutation boundary.
  - The plan/apply boundary is resolved: `dev setup` plans non-SVC-owned file edits, while the explicit `dev ensure` command performs direct runtime convergence. This is a scoped pattern, not a requirement that every present or future CLI command use a digest.
  - The actual Behavioral SemVer impact is MAJOR because schema, default init output, runtime behavior, and consumer layout change. The product owner has assigned all remaining v10 changes to 10.0.1 as a one-time exception based on zero known adopted consumers. Release tooling must retain the real impact and machine-check the exact 10.0.0 -> 10.0.1 exception; it must not classify the changes as PATCH or make the exception reusable.
  - The bounded runtime dependency set is Pydantic (external config validation), platformdirs (per-user runtime locations), and filelock (per-capability coordination). HTTP/HTTPS transport, process supervision, Git identity, TCP/exec probes, CLI parsing, and surgical JSON/JSONC edits retain narrow stdlib/protocol-owned implementations.
  - Local verification passes: 85 tests, monolith build, wheel/sdist build, CLI smoke, release check, and release plan. The staged plan remains `10.0.0 -> 10.0.1` with real MAJOR impact. Terminal interruption of a current owned launch also reports its cleanup result rather than leaving that launch group behind; HTTP connects only to its policy-validated address, and setup plans recheck parent paths against post-plan symlink swaps.
  - A wheel was exercised in `/home/yyh/development/Anana/mvp-HA-svc-acceptance` over `wsl.win-ws.localhost`: init, base/local resolution, identity, real `pnpm + portless + Vite` worktree route start/reuse, and both setup adapters passed. WSL's proxy uses `.arpa`; the acceptance exec probe used `curl --resolve` to prove the exact instance without changing host DNS. The known launch group was stopped; the primary checkout's pre-existing dirty state was unchanged. The detached acceptance worktree remains as inspectable evidence rather than being force-removed.
- **Next Step**: Review the integrated diff, decide any follow-up around cancellation cleanup/evidence retention, then explicitly authorize the task-relevant commit.

## Supporting Material

- Evidence: [`evidence.md`](evidence.md)
- Consolidated command/runtime proposal: [`proposal.md`](proposal.md)
- Base/local config contract: [`configuration.md`](configuration.md)
- Git worktree strategy: [`worktrees.md`](worktrees.md)
- VS Code/npm setup protocol: [`setup.md`](setup.md)
- Python ecosystem decision: [`python-ecosystem.md`](python-ecosystem.md)
- Implementation plan and Impact Handshake: [`implementation-plan.md`](implementation-plan.md)
- Real-project acceptance: [`acceptance.md`](acceptance.md)
- Planned proof: [`verification.md`](verification.md)
