# Implementation Plan

## Impact Handshake

- **From**: Published SVC 10.0.0 has an adoption-only schema-v1 `svc.json`, no local overlay, no `.gitignore` projection, no worktree/runtime identity, no dev probes or coordinator, no `svc dev` commands, and no editor/package setup adapters.
- **To**: SVC 10.0.1 accepts strict schema-v2 base plus generic sparse local override, keeps local state outside the repository, resolves worktree-safe capability identities, observes and ensures declared dev targets, and plan/applies bounded VS Code Tasks and `package.json` projections.
- **Actual impact**: Behavioral MAJOR. Required/default project layout, accepted config, task/runtime semantics, and CLI behavior change.
- **Version decision**: Ship all remaining v10 work as 10.0.1 through one exact, machine-audited exception. Pending `release_policy.version_exception` becomes immutable `behavioral_impact.version_exception`; its fixed kind is `zero-known-adopted-consumers`, from/to are exactly 10.0.0/10.0.1, `one_time` is true, and a non-empty owner assertion/reason is required. A public 10.0.0 package means this is a human statement about known adoption, not proof of global non-use.
- **Migration**: Not applicable under that owner assertion. Schema v1 is reported and write-blocked; it is neither silently migrated nor erased by `adopt`.
- **Invariant**: No healthy static endpoint is enough to reuse another worktree's application; no external process is taken over; no secret values appear in evidence; no repository runtime state is created; no unrelated Consumer byte is overwritten.
- **Backout**: Before release, remove the unconsumed fragment/exception and revert completed slices in reverse dependency order. During failed runtime attempts, clean up only the current launch group and report uncertainty. Planned file writes use the existing full rollback engine. No commit, tag, publish, or release action occurs without separate user authorization.

## Execution Order

Each slice ends with its targeted tests and `pdm run test`. A failed gate stops the sequence; later slices do not paper over an earlier failure.

### 1. Encode the 10.0.1 Release Exception

Owner surfaces: `tools/release.py`, `tests/test_release.py`, staged `src/manifest.json` policy, and one real-impact Towncrier fragment.

- Keep fragment impact MAJOR and keep `bump_impact()` strict.
- Add a separate verifier that permits only the exact staged 10.0.0 -> 10.0.1 exception, carries it through `prepare`, and rejects missing fields, wrong versions, direct pre-bumps, ordinary PATCH disguise, or later reuse.
- Keep the MAJOR migration policy explicit as `not-applicable` with the zero-known-adopted-consumer reason.
- Gate: targeted release tests; `pdm run release check --json`; `pdm run release plan --json`; full tests. `release prepare` remains release-branch work and is not run during feature implementation.

### 2. Add Dependencies and the Configuration Boundary

Owner surfaces: PDM-managed `pyproject.toml`/`pdm.lock`, new `svc_cli/config.py`, and `tests/test_config.py`.

- Use `pdm add`, never hand-edit dependency resolution.
- Implement strict JSON bytes -> duplicate/non-finite rejection -> Pydantic base model -> local authority scan/merge -> final effective Pydantic model.
- Make schema v2 root/dev/profile/target/probe/provision models deep and discriminated; generate stable declaration digests without writing an effective file.
- Reject symlinks, non-files, invalid UTF-8, unknown fixed fields, forbidden local adoption/schema fields, null tombstones, and invalid selected profiles.
- Gate: config fixture matrix; `pdm lock --check`; Python support through the CI matrix; full tests.

### 3. Integrate Init, Status, and Adoption

Owner surfaces: `svc_cli/project.py`, `svc_cli/integration.py` or a focused ignore helper, `tests/test_project.py`, and ignore fixtures.

- Extend `svc init` planning with the bounded `.gitignore` local-config section while never creating or modifying `svc.local.json`.
- Make `svc status` report base/local/effective/ignore health without values.
- Replace whole-file adoption rendering with a surgical current-schema `svc_version` span update; preserve all dev configuration and unrelated bytes.
- Block v1/future schema writes with an actionable status; do not add a migration command in this release.
- Gate: create/append/no-op/drift/CRLF/stale/rollback fixtures, adopt byte-preservation fixtures, and full tests.

### 4. Resolve Workspace Identity and Interpolation

Owner surfaces: new `svc_cli/dev/identity.py` and `tests/test_dev_identity.py`.

- Resolve Git common/private worktree identities through exact Git CLI calls, plus explicit non-Git fallback and execution namespace identity.
- Derive scope, instance, endpoint, runtime-directory, and lock keys without branch/HEAD/path-as-authority shortcuts.
- Interpolate only documented `${dev.*}` tokens inside existing scalar/argv elements; never invoke a shell or expand arbitrary environment variables.
- Enforce worktree instance proof at the resolved probe boundary; repository/host sharing remains explicit.
- Gate: real main/linked worktree fixtures, move stability, clone/namespace isolation, non-Git/bare cases, and full tests.

### 5. Build Probe and Provision Primitives

Owner surfaces: new `svc_cli/dev/runtime.py` primitives plus focused probe/provision tests.

- Stdlib HTTP probe: pin the actual connection to the policy-validated resolved address through a narrow `http.client` adapter, preserve original Host/SNI, use explicit timeout and TLS context, follow no redirect, read no ambient proxy settings, and support only status intervals (no response-expression language). The coordinator supplies the smaller of the probe timeout and remaining wall-clock deadline.
- Stdlib TCP/exec probes: bounded connect/subprocess, exact argv, output cap, no shell.
- Provisioners: `exec/run`, `exec/activate`, and `manual`; exact cwd/env/interpolation; no framework or package-manager inference.
- Keep clocks, transports, runners, and process adapters injectable so fixtures do not rely on external services.
- Gate: HTTP/TCP/exec policy fixtures, argv and redaction fixtures, provision mode fixtures, and full tests.

### 6. Implement the Coordinator and CLI

Owner surfaces: `svc_cli/dev/runtime.py`, `svc_cli/cli.py`, `tests/test_dev_runtime.py`, and `tests/test_dev_cli.py`.

- Use platformdirs for runtime/state/log roots and filelock for the second-probe -> provision -> readiness critical section.
- Implement healthy reuse, absent launch, concurrent waiter re-probe, occupied-unhealthy preservation, manual action, timeout/early-exit cleanup, and stable outcomes.
- Supervise only this attempt with stdlib platform process groups; never use stale evidence to kill. Report cleanup as completed/partial/unknown.
- Add `dev status`, `dev identity`, and direct idempotent `dev ensure`; stable JSON leads, human output remains actionable. No digest applies to these read/runtime commands.
- Gate: exact single-spawn concurrency, wrong-instance, no-repository-write, cleanup, exit-code/output fixtures; `pdm run svc --help`; full tests.

### 7. Add Surgical Setup Plan/Apply

Owner surfaces: new `svc_cli/dev/setup.py`, a private lexical JSON/JSONC editor, any minimal context extension to `svc_cli/plans.py`, and setup tests.

- Add `dev setup vscode|npm --plan|--apply <digest>` only; omission remains plan-only and modes are exclusive.
- Preserve comments, trailing commas, key order, indentation, line endings, mode, and all unrelated bytes. Reject malformed/duplicate/ambiguous structures and reserved-entry conflicts.
- Never read or modify `launch.json`, infer a package manager, create missing package metadata, or remove orphan entries.
- Bind config declarations and destination bytes into the digest; reuse existing pre/postcondition, atomic write, rollback, and intervening-edit behavior.
- Gate: JSONC/JSON byte fixtures, conflict/idempotence/stale/rollback fixtures, unchanged `launch.json`, and full tests.

### 8. Promote Durable Guidance and Prove the Artifact

Owner surfaces: the appropriate canonical `src/` owners, `README.md`, `CONTRIBUTING.md`, generated Codex skill source in `svc_cli/integration.py`, contract tests, and release metadata.

- Document only implemented behavior: config authority, worktree safety, status/ensure/setup when-to and failure recovery. Do not copy task-packet prose into every owner.
- Teach the Codex skill the complete CLI when-to/know-how while keeping canonical SVC content in lookup.
- Use PDM for `test`, `build-monolith`, CLI smoke, build, release check, and Towncrier draft. Verify source and installed-wheel behavior on the supported Python matrix.
- On successful release preparation, verify the staged exception is consumed into immutable behavioral-impact metadata and cannot affect the next release.
- Gate: all tests, monolith build, wheel/sdist build, installed artifact smoke, release verification. Commit/push/release still require explicit user commands.

The final pre-release gate also runs [`acceptance.md`](acceptance.md) against a disposable real `mvp-HA` worktree on the WSL host. A remote failure is evidence to fix or explicitly explain, never a reason to weaken fixture assertions or mutate the primary consumer checkout.

## Parallel Work Boundary

After the configuration model is stable, identity fixtures and probe/provision primitives can be developed in parallel in disjoint files. The coordinator waits for both. Setup can proceed after the target/CLI contract freezes. The primary agent owns shared files (`cli.py`, `project.py`, `plans.py`, release metadata) and final integration; sub-agents may own isolated modules or read-only review and must not revert concurrent work.
