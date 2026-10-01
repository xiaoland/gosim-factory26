# Cross-Host Agent-Thread Field Study

- **Objective**: Collect a deliberately small, high-value corpus of complete Codex agent-thread evidence from this macOS host, `wsl.win-ws.localhost`, and `win-ws.localhost`, so the product owner can analyse durable human–Agent collaboration patterns and diagnose SVC gaps from real work.
- **Guardrails**:
  - Treat every exported ZIP as sensitive: it may contain raw conversation, reasoning envelopes, and tool arguments/results. Metadata-first discovery is followed by the product owner's explicitly authorized, bounded review of *user-role message text only* to decide collection value. The review never reads assistant/system/developer messages, reasoning, tool payloads/results, or attachments, and never copies message text into Git, task packets, the external inventory, commentary, or the final handoff.
  - Preserve source rollouts exactly. Exports are explicit, exact-thread, append-free artifact writes with `--include-sensitive`; no thread, Codex state, project file, or remote configuration is modified or removed.
  - Select for analytical coverage, not volume: retain at most eight threads total, normally no more than three per host. A host with no clearly valuable reviewed candidate contributes no forced sample.
  - Use a `--repo` task-packet association only when the selected thread's repository is evidenced by safe metadata. Never guess a repository or attach unrelated packets.
  - Store collected archives outside the SVC repository in a local mode-0700 evidence root. Remote-to-local transfer stays on SSH; retain the original remote archive unless the product owner later requests a cleanup policy.
  - Check each host's installed `svc` before mutation. If the telemetry surface is absent, use only the released `sustainable-vibe-coding==10.0.1` package required to perform the requested export, and record that repair as non-sensitive collection evidence.
- **Verification**:
  - Each host has a bounded, non-sensitive inventory result or a recorded availability failure.
  - Every selected archive reports successful export, exists as a distinct `.zip` outside its source repository, and has a recorded size and SHA-256 after encrypted transfer to the local evidence root.
  - The central inventory records host, source identifier, timestamp/selection metadata, selection rationale, archive filename, and digest—never transcript, reasoning, tool payload, or ZIP member content.
  - The final handoff states corpus coverage and remaining sampling bias without
    making behavioral claims beyond the bounded user-message selection review.
- **Current Truth**:
  - SVC 10.0.1 is installed in this repository and exposes `svc telemetry agent-thread list` plus exact-thread `export`. The latter deliberately requires `--include-sensitive` and can operate from Codex App or VS Code rollout data without Codex CLI.
  - macOS returned 100 safe descriptors, confirming the deliberate list boundary: only opaque ID, timestamps, and source state are exposed—no title, workspace, or transcript content.
  - WSL2 has a private, pinned 10.0.1 venv because Debian's PEP 668 policy correctly rejected system/user pip mutation; its telemetry list then returned 100 safe descriptors. Windows has a pinned user-level 10.0.1 installation and an existing Codex state DB.
  - Windows `svc telemetry agent-thread list` fails closed with `thread-source-unsafe`. A read-only aggregate diagnostic established that 1,568 of 1,570 nonblank `rollout_path` values are inside `CODEX_HOME`; two outside rows make the entire bounded list fail. This is an SVC list-isolation gap, not a reason to weaken path containment. The narrowly defined safe-metadata workaround is recorded in [`diagnostics.md`](diagnostics.md).
  - The product owner's authorized bounded user-message review selected exactly
    eight threads: three macOS, two WSL/Linux, and three Windows. It excluded
    unavailable sources and lower-contrast one-shot candidates without storing
    excerpts or detailed summaries.
  - All eight exact-thread exports passed SVC's source-consistency checks.
    Remote archives were retained on their source hosts; their copies in the
    central evidence root are mode `0600`, and every remote transfer has a
    matching local SHA-256 and byte size in the external inventory.
  - The macOS SVC-v10 episode alone carries an evidenced task-packet
    association. All other retained threads deliberately omit repository
    association rather than infer it from reviewed content.
  - The present `export --json` receipt includes task-packet association and warning details beyond the minimum integrity receipt needed by a collector. Treat that receipt as sensitive operational output; the external inventory records only selected metadata, archive hash, and size. A future CLI slice could offer an explicitly minimal machine-readable receipt.
  - This packet deliberately holds method, verification, and non-sensitive collection observations only. The sensitive evidence corpus and its inventory live outside the source repository.
- **Next Step**: Continue analysis in the separate
  [`70-agent-thread-audit`](../70-agent-thread-audit/packet.md) packet. Record
  any proposed human–Agent pattern with cross-case evidence; do not treat
  selection tags as behavioral findings.

## Supporting Material

- [Selection policy](selection-policy.md)
- [Bounded user-message review protocol](review-protocol.md)
- [Collection plan and Impact Handshake](collection-plan.md)
- [Windows list-isolation diagnostic](diagnostics.md)
- [Observation template](observations.md)
