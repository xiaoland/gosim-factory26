# Codex Agent-Thread Export

- **Objective**: Add the first local-observability capability, `svc telemetry agent-thread export`. It exports a selected Codex thread as a self-describing ZIP containing the complete provider-obtainable thread record—conversation items, reasoning items, tool calls/results, and provider metadata—plus associated SVC task-packet material discovered from auditable `tasks/...` references in that record.
- **Status**: Implementation and cross-platform fixture verification complete; user-authorized release hardening is in progress after Linux CI exposed an inode-reuse gap in destination verification. The product owner confirmed the Impact Handshake and explicitly authorized this sub-task on 2026-07-16.
- **Scope**:
  - Codex is the first provider, not a permanent public-protocol constraint. `agent-thread` selection, archive manifests, task-packet association, diagnostics, and ZIP writing are provider-neutral; `codex-rollout-v1` is the only source adapter implemented in this slice. It must work when the user is using Codex App or the Codex VS Code extension and has not installed `codex` CLI.
  - The supported hosts are macOS, Windows, and Linux. The first adapter reads a validated local Codex rollout snapshot from `$CODEX_HOME` (default `~/.codex`) or an explicit source path. It must not require a PATH-installed `codex`, a running App/extension, or a network connection.
  - The archive contains the original rollout JSONL byte stream, a generated content/provenance index, an export manifest with integrity hashes, and task-packet copies selected under the current repository's `tasks/` root.
  - It must never execute, upload, or rewrite thread data. An explicit output path creates one ZIP atomically, refuses an existing destination, and must resolve outside the selected repository so a temporary or final archive cannot become task-packet material.
- **Non-goals**:
  - No dynamic plugin loading, provider marketplace, provider-specific CLI roots, or promise of feature parity among future agents. The first slice uses a static in-process provider registry with one Codex adapter.
  - No semantic/LLM inference to decide task-packet ownership, no transcript redaction, replay, import, cloud synchronization, or UI.
  - No promise that unavailable or provider-redacted data (especially hidden reasoning) can be reconstructed or decrypted.
- **Guardrails**:
  - “Complete local snapshot” means the selected rollout file is copied byte-for-byte while parsed streamingly; every intact source record—including unknown records and opaque encrypted-reasoning fields—is retained. It never means fabricating fields, decrypting opaque reasoning, or recovering content absent from the selected local source.
  - Thread selection is deterministic and explicit. `state_5.sqlite` may map an exact thread ID to a rollout path in read-only mode; an explicit `--source` may select one rollout file. The command never chooses the most-recent thread, recursively exports a home, or treats VS Code's generic workspace cache as canonical data.
  - An active source must be detected as mutable (growth, replacement, or malformed final record) before atomic commit, and the temporary archive discarded rather than silently exporting an incoherent snapshot. The archive core re-verifies the raw source digest and task-packet snapshot after ZIP fsync immediately before publication. A change after the atomic commit cannot alter the already hash-bound ZIP. A future app-server adapter may improve active-thread capture, but it cannot change the raw snapshot promise without a new protocol review.
  - `telemetry` here means an explicit, local evidence capture: it never implies automatic collection, network egress, upload, or anonymous metrics. The archive is privacy-sensitive. Full raw export requires a deliberate acknowledgement flag, retains raw tool arguments/results and reasoning fields where the source makes them available, keeps their values out of terminal diagnostics, and creates a private output file where the platform supports it.
  - Task-packet discovery is lexical and provenance-preserving: examine only user/assistant message-like record content, retain bounded candidate paths rather than transcript bodies, normalize each as a repository-relative path, reject traversal/symlink escapes, and include every validated packet root beneath the current repository's `tasks/` root. Invalid, missing, or resource-bounded references become manifest warnings, never guessed inclusions. Packet files are copied through descriptor-bound, streaming reads and digest-verified in the manifest.
  - The ZIP layout, manifest schema, selection rules, collision behavior, and failure modes are protocol surfaces. They need fixtures and Behavioral SemVer review before release.
- **Verification**:
  - Fixture-backed adapter tests prove byte-for-byte source retention; messages, reasoning envelopes, tool invocations/results, unknown provider fields, event ordering, opaque fields, malformed-tail handling, and large-file streaming.
  - Discovery tests cover exact state-DB resolution, active/archived paths, explicit source selection, absent/unreadable/incompatible sources, CLI-absent home resolution, and host-specific path behavior without requiring a live Codex installation.
  - Archive tests prove atomic write, no silent overwrite, ZIP-slip-safe paths, source-change refusal, restrictive output policy, corrupt-input refusal, and deterministic hashes/indexes.
  - Task-packet fixtures prove lexical detection from message-like fields only, provenance, exact packet-directory inclusion, multiple valid roots, missing/invalid references, traversal/symlink refusal, streamed copy integrity, and zero mutation of the repository.
  - Acceptance runs exercise the installed wheel on macOS locally, Windows through `ssh win-ws.localhost`, and Linux through `ssh wsl.win-ws.localhost`; each uses a safe fixture source as the portable baseline and a real provider source only when present and consented.
- **Impact Handshake (confirmed)**:
  - Owner: `svc_cli.telemetry.agent_threads` owns the provider-neutral capture contract, archive schema, ZIP writer, task-reference collector, diagnostics, and static provider registry. `svc_cli.telemetry.providers.codex_rollout` owns Codex-home discovery and rollout-v1 capture. Consumers own local agent state, the selected thread, output destination, acknowledgement of sensitive export, and repository task packets.
  - Trigger: an explicit export command with an exact thread selector or exact rollout source, an explicit archive destination, and a sensitive-export acknowledgement.
  - Consumer: a human or coding agent needing a durable, inspectable evidence bundle for later analysis and SVC improvement.
  - Mutation boundary: source/repository reads are read-only; archive creation is the sole write. It is an explicit artifact write, not a plan/apply projection, but it must be atomic and collision-safe.
  - Behavioral SemVer: adding the capability is MINOR in ordinary release terms; under the v10 one-time exception it remains assigned to 10.0.1 while preserving its actual impact declaration.

## Current Implementation Truth

- The public surface is `svc telemetry agent-thread list|export`; `telemetry` is the CLI term, while `o11y` remains an internal taxonomy only.
- The static provider registry contains only provider `codex`, implemented by adapter `codex-rollout-v1`; no installed `codex` executable is required for either explicit-source export or state-database selection.
- `list` validates the state-table and rollout-path safety without reading transcript bodies; exact export validates the rollout-v1 signature before capture.
- The ZIP layout is `providers/<provider>/…`, `thread/index.json`, `task-packets/tasks/…`, and `manifest.json`. It has no dynamic-provider or cloud boundary.
- Full-source export is gated by `--include-sensitive`; it preserves native JSONL byte-for-byte and keeps provider-unavailable reasoning opaque.
- Source and task-packet snapshots are rechecked after ZIP fsync at the pre-publication commit gate. A destination that changes during publication is rejected as `archive-output-mutated` without deleting the untrusted replacement; its cross-platform file identity is device, inode, file type, size, and mtime, deliberately excluding Windows-read-sensitive ctime.
- Cross-platform identities intentionally use device/inode/size/mtime rather than `ctime_ns`: Windows may change `ctime_ns` during read-only inspection. Raw source hashes and descriptor-bound reads remain the content proof.
- Release hardening: `pdm run test` passed 131 tests; `pdm run build-monolith`, `pdm run release check-ci --json`, and `pdm build` passed. The existing fresh-wheel fixture passed on macOS (Python 3.12.10), Windows (3.14.0), and Linux (3.13.5); a new replacement-during-publication regression also passed from a freshly installed wheel on Windows and Linux. Details are in [`acceptance.md`](acceptance.md).

## Supporting Material

- Proposed source and archive contract: [`proposal.md`](proposal.md)
- Cross-platform discovery matrix: [`discovery.md`](discovery.md)
- Task-packet association rules: [`task-packet-association.md`](task-packet-association.md)
- Acceptance and fixture plan: [`acceptance.md`](acceptance.md)
- Observability taxonomy: [`taxonomy.md`](taxonomy.md)
- Provider extension contract: [`extensibility.md`](extensibility.md)
