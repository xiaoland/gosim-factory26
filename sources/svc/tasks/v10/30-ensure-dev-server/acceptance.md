# Real-Project Acceptance

## Purpose and Authority

Fixtures prove protocol branches deterministically; `mvp-HA` proves that the released wheel composes with an actual WSL, pnpm/portless, VS Code, Git worktree, and human/Agent workflow. This gate supplements tests rather than replacing them.

The primary `~/Development/Anana/mvp-HA` checkout remains Consumer-owned and read-only throughout acceptance. Work occurs only in a uniquely named disposable sibling worktree and a dedicated temporary Python environment. No acceptance change is committed or pushed.

## Preconditions

- Local `pdm run test`, `pdm run build-monolith`, `pdm build`, and installed-wheel smoke have passed.
- The exact built wheel and SHA256 are copied to a remote temporary directory; the remote does not install SVC globally.
- SSH connectivity, Git, Python 3.11+, the consumer's declared package manager, and its existing dev prerequisites are healthy.
- Record the primary checkout status, HEAD, existing worktrees, existing dev routes/processes, and target worktree path before mutation. Abort on an existing target path or ambiguous ownership.

Current evidence on 2026-07-15: `wsl.ws-win.localhost` resolves locally but refuses SSH on ports 22, 122, 2022, and 2222. The previously discussed hostname was `wsl.win-ws.localhost`; do not substitute it without user confirmation.

## Isolation Layout

Recommended shape after the remote repository is inspected:

```text
~/Development/Anana/mvp-HA                 primary checkout, read-only
~/Development/Anana/mvp-HA-svc-acceptance detached disposable worktree
~/.cache/svc-acceptance/<attempt>/         wheel, venv, command/evidence logs
```

Create the worktree detached from an explicitly recorded commit so no acceptance branch is left behind. The isolated environment installs only the locally built wheel plus its declared dependencies. Every `svc` invocation records `svc --version` and the executable path.

## Acceptance Sequence

1. **Baseline isolation**: prove the primary checkout bytes/status and existing worktrees are unchanged after creating the detached worktree.
2. **Init boundary**: run explicit init plan/apply in the acceptance worktree; verify the generated Codex skill, navigation, schema-v2 `svc.json`, and bounded `.gitignore` section. Confirm `svc.local.json` was not created.
3. **Local overlay**: create an uncommitted acceptance-only `svc.local.json`; prove it is ignored, generic, sparse, and reflected in `svc status` without value disclosure.
4. **Worktree identity**: compare primary and acceptance identities. Common-repository identity must match; private worktree/instance identity must differ.
5. **Safe negative case**: model the existing static `partner-up.localhost`/API endpoint as worktree-scoped. If it is healthy or occupied, `svc dev ensure` must refuse unverified provenance and must neither spawn nor kill anything.
6. **Positive unique instance**: configure an acceptance-only portless route or exact exec probe containing `${dev.instance}` and the project's real pnpm command. `svc dev ensure` starts it once, reports the access URL/log/evidence, and a second call reuses it.
7. **Concurrency**: run two ensures for the same absent target concurrently. The consumer's launch counter/process evidence must prove exactly one provision attempt; the waiter re-probes and reuses.
8. **Human/Agent bridge**: plan/apply the VS Code Task and root `package.json` script. Execute the package script and direct CLI entry in both orders; both converge on the same target. `launch.json` and unrelated JSON/JSONC bytes remain identical.
9. **Failure preservation**: exercise one bounded readiness failure with an acceptance-owned command. Cleanup may affect only that attempt; any pre-existing consumer route/process survives.
10. **Artifact/status proof**: capture structured outputs, relevant surgical diffs, process/log evidence, worktree list, and primary checkout status.

## Cleanup

Cleanup is explicit and evidence-driven:

- terminate only process groups recorded as created by the acceptance attempt, then prove the route is absent;
- retain logs/evidence outside the repository;
- remove the detached worktree only when its changed/untracked inventory matches the expected acceptance files and process cleanup is complete;
- never use generic `killall`, `portless --force`, or `git worktree remove --force` against an unverified tree;
- re-check that the primary checkout status, HEAD, and existing dev processes match the baseline.

If cleanup ownership is uncertain, stop and leave the isolated worktree for human inspection. Uncertainty is a failed acceptance outcome, not permission to take over state.

## Pass Criteria

Acceptance passes only when the exact packaged wheel demonstrates safe static-endpoint refusal, worktree-specific single startup/reuse, concurrent convergence, bounded Consumer-owned setup, truthful failure cleanup, and zero primary-checkout mutation. Project-specific surprises become either SVC fixes or explicit contract exclusions before release preparation.
