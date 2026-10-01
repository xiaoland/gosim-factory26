# Collection Plan

## Impact Handshake

| Lens | Decision |
| --- | --- |
| Address and object | Read local Codex rollout snapshots on macOS, WSL, and Windows; create selected ZIPs in host-local evidence directories and copy remote ZIPs to one local evidence root outside `/Volumes/WorkSSD/Development/svc`. |
| State diff | `read-only rollout state` → `one immutable, private ZIP per selected exact thread` plus a non-sensitive central inventory and digest record. |
| Blast radius | The three user-scoped hosts and their local Codex evidence. Source repositories are read-only except for no writes at all; the SVC source tree receives only this method packet. |
| Invariants | No broad export, no source mutation/deletion, no raw evidence in terminals/task files/Git, no guessed task-packet association, no network egress other than encrypted SSH transfer between the scoped hosts. |
| Verification | Successful CLI JSON result, archive existence and collision-free name, SHA-256/size inventory, and matching source-selection record for every archive. |

## Collection Sequence

1. On each host, identify the installed `svc`, its version, and whether
   `telemetry agent-thread list` is available. Do not install or export during
   this probe.
2. Run bounded JSON list discovery. Store only the returned safe metadata in
   the local evidence root; do not copy it into this repository.
3. Apply [the selection policy](selection-policy.md) across all hosts before
   opening the export gate. Resolve `--repo` only from an evidenced workspace
   association; otherwise omit it.
4. For each selected thread, run the exact `svc telemetry agent-thread export`
   command with an absent ZIP destination, `--include-sensitive`, and JSON
   output. Use host and opaque-ID-prefixed filenames to prevent collisions.
5. Copy remote archives over SSH into the local mode-0700 evidence root,
   preserve their remote originals, and record SHA-256 plus file size locally.
6. Do not unzip the evidence during collection. Report only inventory-level
   coverage, successes, failures, and deliberate omissions.

## Availability Fallback

If a host has no usable telemetry command, first confirm whether its active
Python can install user-level packages. Only then install the precise released
package `sustainable-vibe-coding==10.0.1`, rerun the non-sensitive probe, and
record the before/after version in the external inventory. A blocked or unsafe
installer is a collection result, not a reason to substitute raw Codex files.

## Evidence Root Layout

The primary collector creates a local, mode-0700 root outside the repository:

```text
/Volumes/WorkSSD/Development/svc-evidence/field-study-2026-07-20/
  inventory/              # safe metadata, rationales, and checksums only
  macos/
  wsl/
  windows/
```

Remote hosts use private host-local staging locations outside their repositories
until transfer succeeds. The concrete paths are discovered per host and recorded
in the external inventory, not in Git.
