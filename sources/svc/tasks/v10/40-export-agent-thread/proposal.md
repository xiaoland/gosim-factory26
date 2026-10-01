# Proposed Export Protocol

## Boundary

`svc telemetry agent-thread export` is an evidence exporter, not a Codex client replacement.
The first adapter is deliberately small: it reads one selected, validated Codex
rollout JSONL snapshot and writes one portable ZIP. It does not launch `codex`,
connect to a running App or VS Code, scrape Electron/VS Code caches, or use the
network. This is the path that works when a front end exists but `codex` is not on
`PATH`.

```text
exact selector + sensitive-export acknowledgement
        |
        v
read-only state lookup or explicit source --> selected rollout JSONL
        |                                           |
        +-- metadata diagnostics/provenance <-------+
        |
        v
streamed byte-for-byte ZIP entry + parsed metadata --> lexical task collector
        |                                                |
        v                                                v
archive manifest + content index ----------------> validated task-packet copies
        |
        v
atomic ZIP at an absent explicit destination
```

The crucial separation is between source-specific recovery and portable archival.
The archive must name the selected source, its stable hash, what record classes it
observed, and what was not obtainable. It may truthfully say “complete local
snapshot”; it must not label provider-redacted or unavailable hidden reasoning as
recovered content.

## Candidate Command Shape

The recommended surface separates discovery from the sensitive write:

```text
svc telemetry agent-thread list [--codex-home <path>] [--json]
svc telemetry agent-thread export --thread-id <uuid> --output /safe/export-dir/evidence.zip --include-sensitive
svc telemetry agent-thread export --source <rollout.jsonl> --output /safe/export-dir/evidence.zip --include-sensitive
```

`list` uses the read-only `state_5.sqlite` thread metadata when its known table
signature exists; it does not print message bodies, tool values, reasoning, or
full local paths by default. `export --thread-id` maps that exact ID to its stored
rollout path. `--source` is both the deterministic escape hatch and the fixture
input. No command guesses “latest.” The destination must be absent and physically
outside `--repo`, so neither a final archive nor its temporary staging file can
become packet evidence.

The initial adapter accepts a `rollout-v1` stream whose outer records are JSONL
envelopes with `timestamp`, `type`, and `payload`, validated by a `session_meta`
signature and streamed with unknown records intact. It indexes observed message,
reasoning, function/custom-tool, and lifecycle records without interpreting or
decrypting opaque payload fields. `app-server thread/read` is promising for a
future active-thread adapter, but is deliberately deferred: launching/discovering
a runtime has a different authority and compatibility boundary. The resulting
`CapturedThread` is provider-neutral: it carries an opaque provider/thread identity,
raw artifacts, observable capability states, text occurrences, and diagnostics.

## Proposed ZIP Shape

```text
manifest.json                         # provider-neutral schema, provenance, hashes, warnings
providers/codex/rollout.jsonl         # byte-for-byte selected Codex source
thread/index.json                     # record order/types/line hashes, no duplicated values
task-packets/tasks/<packet-root>/...  # validated copies beneath repository tasks/
```

`manifest.json` records archive schema, exporter version, provider ID, adapter and
source-format version, selected thread identity, content hash/size, collection time,
observed record-class counts, field-availability declarations, and every retained
task-reference occurrence. It never duplicates raw tool output or reasoning values.
The index preserves line-number provenance and line hashes without duplicating raw
values. A future provider stores its native source beneath
`providers/<provider-id>/` while using the same manifest and task-packet evidence
model.

The writer streams the source through bounded spools while it parses it, then writes
the resulting ZIP. It detects a mutable source before finalizing and re-verifies the
raw digest and packet snapshots after ZIP fsync at the atomic-commit boundary. A
change after that commit cannot alter the already hash-bound archive. Packet copies
have no external symlink traversal; publication accepts only an absent target. On
Unix it creates the destination private to the user; Windows uses its normal
creating-user ACL semantics.

## Error Model

- `thread-source-not-found`: no validated rollout source is available.
- `thread-source-incompatible`: a candidate does not meet the rollout-v1 signature.
- `thread-not-found`: the selected source does not contain the requested thread.
- `thread-source-mutated`: the source changed or ended in an incomplete record
  before the atomic commit; no output archive remains.
- `sensitive-export-not-acknowledged`: the caller did not deliberately authorize
  copying raw conversation/tool/reasoning payloads.
- `task_packet_*`: a lexical reference cannot be safely associated with a local
  packet; it is a manifest warning, not an evidence-loss failure.
- `output-exists` / `output-write-failed`: the sole mutation boundary did not
  safely converge.
- `archive-output-mutated`: the requested destination changed during publication;
  SVC does not delete the untrusted replacement.

Malformed non-final lines are retained in `providers/codex/rollout.jsonl` and declared as
parse warnings; a malformed final line or a source that changes during capture is
refused because it cannot provide one coherent local snapshot.
