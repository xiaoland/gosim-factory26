# v10 Executable Change Protocol

- **Objective**: Evolve SVC from a documented methodology into an executable, migratable, and measurable change protocol for sustainable long-cycle software development under Vibe Coding. The first delivery slice establishes a versioned, on-demand upstream corpus and reliable project-local adoption without copying framework documents into consumer repositories.
- **Guardrails**:
  - Keep SVC small, source-first, and mechanically verifiable; every new surface needs an owner, trigger, consumer, and verification path.
  - Preserve explicit authority across the canonical SVC corpus, Consumer-owned project material, and bounded Generated integration artifacts; never infer authority from a path alone.
  - No downstream SVC-managed framework document exists. The CLI serves immutable release content; consumer knowledge documents remain Consumer-owned.
  - Require a non-mutating exact plan only for high-risk writes to non-SVC-owned project content or installer state. Keep read-only commands and direct, explicitly requested runtime convergence free of digest ceremony. Every planned repository write remains idempotent, preconditioned, postconditioned, rollback-safe, and fixture-tested.
  - `svc self-update` is an explicit installer operation, separate from adoption. It must not change `svc.json`; it does not promise to reverse a package-manager transaction.
  - Treat task state as disposable. Move verified durable truth to its canonical owner during implementation and delete this packet when v10 closes.
  - Do not mutate a new implementation or release-automation slice until its high-level protocol and Impact Handshake are confirmed by the user.
- **Verification**:
  - A clean wheel contains a generated catalog plus one read-only corpus projection; an sdist contains canonical source and the builder needed to reproduce that wheel payload.
  - CLI fixtures prove dry-run byte stability, exact-plan application, repeated-apply no-op behavior, conflict refusal, Consumer-owned preservation, generated-anchor/skill drift detection, pre/postcondition failure, and full rollback after injected local write failure.
  - Contract tests prove catalog integrity, deterministic machine output, lookup-query/result boundary stability, and allowed Behavioral SemVer declarations.
  - A clean consumer can initialize, inspect, query the installed corpus, explicitly adopt the installed baseline, and verify the resulting project state without framework-document copying.
  - `pdm run test` and `pdm run build-monolith` pass for every implementation slice.
- **Current Truth**:
  - v9 has no observable installation state. Its consumer path is four result files plus manual copy/customization instructions, and its migrations are prose in `CHANGELOG.md`.
  - Commit `986ef6a` implemented an unreleased, copy-and-migrate v10 contract with SVC-managed documents, `.svc/state.json`, and a migration graph. It is mechanically sound but superseded by the embedded-runtime product boundary.
  - v10 therefore requires a deliberate replacement of that consumption contract, not a revival or extension of the old copy-based installer.
  - The first sub-task has its own now-superseded design record at [`10-versioned-consumption/packet.md`](10-versioned-consumption/packet.md); its release topology and Towncrier work remain useful, but its consumer-copy engine does not describe the current product.
  - The embedded-runtime foundation in [`20-embedded-runtime-cli/packet.md`](20-embedded-runtime-cli/packet.md) is implemented and released as SVC 10.0.0: pure canonical `src/`, root-level `svc_cli/` runtime and `tools/` tooling, deterministic catalog/corpus lookup, minimal `svc.json`, Codex-only operational skill, non-destructive anchors with default `docs/index.md`, separate self-update and adoption, and no automatic consumer-file migration engine.
  - Its release planner now distinguishes a predeclared MAJOR's migration declaration from a pending MAJOR's staging policy, so an old non-applicability rationale cannot silently carry into a later release.
  - Semantic lookup and task helpers remain deliberately deferred until each has a separate protocol and Impact Handshake. Dev-server assurance is implemented in [`30-ensure-dev-server/packet.md`](30-ensure-dev-server/packet.md). The Codex thread-export contract is implemented in [`40-export-agent-thread/packet.md`](40-export-agent-thread/packet.md), with fresh-wheel fixture acceptance on macOS, Windows, and Linux; it works from direct local rollout data without requiring Codex CLI.
  - The field-study packet in [`50-agent-thread-field-study/packet.md`](50-agent-thread-field-study/packet.md) has collected a deliberately small, three-host corpus for product-owner analysis. It records collection method and sampling bias only; sensitive archives remain outside the repository.
  - [`70-agent-thread-audit/packet.md`](70-agent-thread-audit/packet.md) now
    governs the evidence-led audit of that corpus. It begins with archive
    anatomy, segmentation validation, and multi-scale coding design; no
    collaboration pattern or SVC gap is yet asserted.
  - A Windows Codex metadata-list isolation defect found during that study is corrected by the release-pending PATCH fragment `v10-windows-thread-list-isolation`: unsafe state rows are redacted from the inventory while containment and export's independent validation remain intact.
  - SVC 10.0.0 is published on PyPI and GitHub Releases. The Release PR workflow uses a built-in, short-lived `GITHUB_TOKEN` with job-scoped Contents and Pull requests write permissions; the repository Actions setting must allow token-created PRs, and a maintainer explicitly approves their CI runs. Protected publication and recovery remain documented in `CONTRIBUTING.md`.
  - Release preparation changes the source catalog, project metadata, and lockfile together. Its candidate job must re-sync PDM after `release prepare` before testing, so editable distribution metadata represents the prepared version rather than a stale prior release. Project integration fixtures bind their expected adoption version to the plan's target, not a historical release number.
  - Candidate staging is deletion-aware and allowlisted: it stages Towncrier's removed fragments along with the prepared release outputs, then refuses any unexpected path. `release/svc` reuses only an open candidate PR; a merged historical PR on the same branch is not a mutable candidate. An isolated 10.0.1 rehearsal confirmed the resynced installed/catalog versions, all 131 tests, build, six expected staged paths, and no open candidate despite historical PR #2.
  - The one-time 10.0.1 exception is consumed. Follow-on fixes declare their ordinary Behavioral SemVer impact; the Windows list-isolation correction is planned as 10.0.2 PATCH.
  - Sub-agents are available again for bounded parallel research and review; the primary agent retains packet and implementation authority.
- **Next Step**: Push the verified PATCH correction to `main`, then review and publish its Release PR through the protected environment.

## Supporting Material

- First sub-task: [`10-versioned-consumption/packet.md`](10-versioned-consumption/packet.md)
- Third sub-task: [`30-ensure-dev-server/packet.md`](30-ensure-dev-server/packet.md)
- Fourth sub-task: [`40-export-agent-thread/packet.md`](40-export-agent-thread/packet.md)
- Fifth sub-task: [`50-agent-thread-field-study/packet.md`](50-agent-thread-field-study/packet.md)
- Sixth sub-task: [`70-agent-thread-audit/packet.md`](70-agent-thread-audit/packet.md)
