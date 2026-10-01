# Normalized Trajectory Bundle Schema v2

Status: Slice 0 frozen task-local contract. The implementation owns a
schema-v2 SVC bundle carrying `svc.trajectory/v1` records.

## Authority and Layout

```text
provider-local source
        |
        v
provider normalizer
        |
        v
schema-v2 ZIP: manifest.json + trajectory.jsonl
        |
        +------------------+
        v                  v
deterministic analysis   Textual analysis
```

The provider owns source discovery and translation. The trajectory is the
canonical provider-neutral analysis input. The manifest owns policy,
capability, status, loss, and bundle provenance. Analysis is a derived
projection and never edits either.

The normal ZIP contains exactly:

- `manifest.json`
- `trajectory.jsonl`

It contains no native transcript, provider namespace, old structural index,
task file, or derived `analysis.json`. ZIP entry timestamps and permissions are
fixed to the ZIP epoch `1980-01-01T00:00:00` and regular-file mode `0600`;
member order is manifest then trajectory and the exporter uses deflate.
Readers accept only stored or deflated regular members. The output file is
private where the platform supports it. The ZIP remains a portable, atomically
published container, but cross-platform ZIP bytes are not promised to be
identical because compression implementations can differ.

`manifest.json` is one compact, sorted-key, UTF-8 JSON object followed by LF.
Schema-v2 readers reject duplicate names, encrypted members, non-regular member
types, unexpected members, unsafe lexical paths, inconsistent declared sizes,
and container/member bounds before analysis. They never extract a bundle.
They open the selected bundle as one regular non-link descriptor and reject a
changed/displaced input during validation; the manifest's historical
`source_status` remains the evidence status and is never rewritten by reading.

## Canonical Encoding

`trajectory.jsonl` is UTF-8 JSON Lines:

- one JSON object per LF-terminated line
- keys sorted lexically
- compact separators
- Unicode preserved rather than ASCII-escaped
- duplicate object keys, non-finite numbers, decoded lone surrogates/non-scalar
  strings, and non-object records rejected or diagnosed at the provider
  boundary
- record order follows native source ordinal/byte position, never wall-clock
  sorting

The first line is one `meta` record. Every later line is one normalized record.
Missing timestamps remain `null`; v1 does not synthesize time merely to make a
timeline look complete.

Valid timestamps normalize to UTC RFC 3339 with `Z`, mandatory seconds, and
zero to nine fractional digits after trailing-zero removal. Provider adapters
own documented epoch units. Invalid values become `null` with a diagnostic;
precision beyond nanoseconds is truncated toward zero and diagnosed.

`trajectory_sha256` hashes the uncompressed canonical JSONL bytes. The bundle
identity metadata is canonical compact/sorted-key UTF-8 JSON containing:

- normalizer name/version
- source provider, adapter, format, opaque thread ref, and source status
- the full effective policy
- result status, capabilities, counts, lossiness, and bounded diagnostics

`bundle_id` is hexadecimal SHA-256 over:

```text
b"svc-agent-thread-bundle-v2\0"
+ trajectory_jsonl_bytes
+ b"\0"
+ canonical_identity_metadata_json_bytes
```

It excludes ZIP compression, generation time, output path, and SVC package
version. The same normalized evidence, policy, provenance/status, and declared
loss retain the same identity across platforms; a stable versus partial
capture does not alias merely because its retained records happen to match.

## Common Record Fields

Every record has:

| Field | Contract |
| --- | --- |
| `type` | One frozen record type below |
| `record_id` | `r` plus the six-digit zero-padded `record_index`, beginning at `r000000` |
| `record_index` | Zero-based emitted-record order |
| `timestamp` | Provider time normalized to RFC 3339, or `null` |
| `source_ref` | Safe structural reference containing source event index and optional line/byte/component offsets; never a path |

The synthesized leading `meta` record uses
`source_ref={"event_index":null,"component":"meta"}`. Every provider-derived
record has a non-negative source event index; dropped native events create no
gap in `record_index` and remain visible only through counts/diagnostics.
`event_index`, optional `line`, optional `byte_offset`, and optional numeric
`component_index` are zero-based integers. Optional `component` is a frozen
provider-parser structural label, never provider content.

Optional relationship fields are:

- `turn_ref`
- `actor_ref`
- `parent_actor_ref`
- `lane_ref`
- `concurrency_group`

They appear only when the provider supplies explicit linkage. SVC never infers
parallelism from overlapping timestamps.

Provider-native thread, turn, call, actor, lane, and concurrency IDs are
transformed to deterministic opaque references:

```text
native_ref(kind, value) =
  kind + "_" + lowercase_hex(
    SHA-256(provider_id_utf8 + NUL + kind_ascii + NUL +
            b"native" + NUL + value_utf8))

synthetic_call_ref(event_index, component_index) =
  "call_" + lowercase_hex(
    SHA-256(provider_id_utf8 + NUL + b"call" + NUL +
            b"synthetic" + NUL + decimal_ascii(event_index) + NUL +
            decimal_ascii(component_index)))

synthetic_result_ref(event_index, component_index) =
  "call_" + lowercase_hex(
    SHA-256(provider_id_utf8 + NUL + b"call" + NUL +
            b"orphan-result" + NUL + decimal_ascii(event_index) + NUL +
            decimal_ascii(component_index)))
```

Every parser-emitted tool component has a zero-based `component_index`.
A call with no usable native ID uses `synthetic_call_ref` and is diagnosed.
A result with no usable ID reuses the exact canonical ref of a native,
synthetic, or duplicate-suffixed call only when the provider supplies an
explicit structural link to that call; otherwise it uses
`synthetic_result_ref` for its own event/component. The distinct
`orphan-result` domain can never intentionally late-link to any call. Record
IDs are SVC-owned and never reuse Textual node IDs or provider line numbers as
identity.

The v1 kinds/prefixes are exactly `thread`, `turn`, `call`, `actor`, `lane`,
and `concurrency`; workspace uses its separately framed `workspace` contract.
`parent_actor_ref` is an `actor` ref and `concurrency_group` is a
`concurrency` ref. For calls sharing one native base ref, source-order
occurrence 1 is the base ref and occurrence `n >= 2` is exactly
`<base>_d<zero-padded-six-digit n>`; the suffix is not part of the hash
preimage. A result without an explicit provider duplicate-occurrence link maps
to occurrence 1. An explicit one-based occurrence link maps to that exact
suffix even when the result precedes the call; an out-of-range/unrealized link
remains unresolved and ultimately orphan. No other opaque ref has a suffix.

## Record Types

Exact keys, optionality, scalar types, text metadata, and extra-key rejection
are frozen in [`trajectory-records.md`](trajectory-records.md).

| Type | Required semantics |
| --- | --- |
| `meta` | Trajectory schema, provider/adapter/source format/kind, opaque thread ref, bounded workspace projection, and effective content profile |
| `message` | `role` is `user` or `assistant`; includes bounded `content`, optional turn/actor/lane refs, and bounded lexical `task_refs` |
| `reasoning` | Available provider summary/full text with `reasoning_kind` set to `summary` or `full`; opaque/absent reasoning emits no fabricated content |
| `tool_call` | Opaque `tool_call_id`, bounded tool name and arguments, arguments kind/fingerprint, and optional actor/turn refs |
| `tool_result` | `tool_call_id`, bounded content, a `status` of `success`, `error`, or `unknown`, and a `link_status` of `linked` or `unresolved` at streaming emission |
| `context` | `context_kind` is `system`, `developer`, `tool_config`, or `turn`; includes selected bounded content/attributes and a stable fingerprint |
| `event` | `event_kind` is one of the exact event enums; includes an outcome and optional relationship refs |

Known provider envelopes, UI notifications, rate-limit polling noise, world
state snapshots, duplicate bookkeeping, and opaque passthrough metadata are not
records. Their removal is counted as intentional loss.

For `approval`, a provider-supplied outcome is
`requested|granted|denied|cancelled|unknown`. For `turn_complete` and
`agent_complete`, a provider-supplied outcome is
`completed|error|aborted|unknown`. Unknown provider semantic events are dropped
and diagnosed; v1 does not emit an open-ended passthrough event name.

### Context

Improving SVC requires knowing which instructions and capabilities shaped a
thread. V1 therefore keeps:

- bounded system/developer instruction content when provider-visible
- tool names and tool-configuration fingerprints
- selected turn attributes such as model, effort, approval, sandbox, and
  collaboration mode

It does not retain complete tool schemas, UI state, absolute paths, account
metadata, provider credentials, or opaque internal passthrough fields. A
context change unsupported by the provider is `unavailable`, never inferred.

### Workspace Projection

The interactive inventory may hold a bounded full CWD only in process. A
persistent trajectory never stores that absolute path. `meta.workspace` is:

```text
status = present | missing
flavor = posix | windows | unc | null
label = final lexical path component (or root label), max 256 code points, or null
ref = workspace_<SHA-256(provider_id + NUL + "workspace" + NUL +
                        flavor + NUL + exact CWD UTF-8)>, or null
label_truncated = boolean
observed_code_points = non-negative integer
retained_code_points = non-negative integer
```

POSIX `/` uses `/`; a Windows drive root uses its drive label; a UNC share root
uses the share component. An invalid/unparseable CWD becomes `missing` rather
than persisting opaque path text. The label is sensitive normalized content and
is rendered only in explicitly sensitive human analysis. Agent JSON carries
neither the label nor full path; an Agent that needs the opaque equality ref
reads the acknowledged normalized trajectory.

### Tool Linkage

- Calls and results link through canonical opaque `tool_call_id`.
- A result seen before its call is emitted as `unresolved`. The analysis pass
  may resolve it only from the same explicit canonical call ID; otherwise its
  final outcome is orphan.
- An unfinished call remains pending in analysis; it is not dropped.
- Duplicate call IDs receive deterministic source-order suffixes and a
  diagnostic (`_d000002` for the second occurrence, and so on). Ambiguous
  results map only to the earliest call with the native ID; a suffixed
  duplicate remains pending unless the provider supplies the explicit
  duplicate-occurrence link defined above.
- For duplicate results, first structurally valid result wins and later results
  remain counted/diagnosed rather than overwriting evidence.
- Valid JSON tool arguments become canonical compact/sorted-key JSON text with
  `arguments_kind=json`; invalid JSON remains bounded text with
  `arguments_kind=text`. Truncated canonical JSON is explicitly non-parseable
  preview text; the full pre-truncation fingerprint remains structural evidence.
- The exact full-argument and retry fingerprints are defined in
  [`analysis-algorithms.md`](analysis-algorithms.md); they are not integrity or
  secrecy guarantees.

### Reasoning

Manifest capability is one of:

- `full`
- `summary`
- `opaque`
- `absent`

Opaque or absent reasoning is not an error and produces no invented reasoning
record. The frozen v1 dimensions report the capability/loss honestly and do not
fabricate reasoning-dependent claims.

## Frozen Bounds and Loss Policy

| Resource | V1 bound |
| --- | ---: |
| Source bytes read | 256 MiB |
| One native JSONL line | 4 MiB |
| Native JSON nesting | 64 levels |
| Emitted records | 50,000 |
| Uncompressed trajectory | 32 MiB |
| Schema-v2 ZIP file | 64 MiB |
| Manifest JSON | 1 MiB |
| Workspace label | 256 Unicode code points |
| Message/system/developer content | 16,384 Unicode code points |
| Reasoning content | 8,192 Unicode code points |
| Tool name | 256 Unicode code points |
| Tool arguments | 20,000 Unicode code points |
| Tool result | 2,500 Unicode code points, head-tail |
| Context attributes | 6 fixed keys; scalar string 512 code points |
| Tool names per tool-config context | 256 |
| One task reference | 1,024 Unicode code points |
| Task-reference occurrences | 2,048 |
| Structural label | 128 ASCII characters |
| Manifest diagnostics | 256 entries |
| Diagnostic details | 16 keys; scalar string 128 ASCII characters |

All MiB values are binary multiples. Source bytes include every raw byte read,
including discarded records and line terminators. The native-line bound
includes its LF when present; a final unterminated line uses its actual bytes.
JSON depth counts the root object as level 1. The 50,000-record cap includes the
required meta record. Trajectory and manifest byte bounds include their final
LF; the ZIP bound is the complete container size. Code-point bounds count
decoded Unicode scalar values before UTF-8 encoding.

Head-tail truncation retains up to 1,250 leading and 1,250 trailing code points;
the truncation marker and original/retained counts live in record metadata
rather than replacing retained content. No discarded suffix is persisted.

Known noise removal and bounded content truncation are normal
`bounded_normalized` behavior: they leave `result_status=ready` while manifest
loss counters make them visible. Unknown/invalid records, source change, read
interruption, or source/record/artifact limit exhaustion produce
`result_status=partial` when a structurally valid trajectory exists.

V1 does not claim heuristic credential/secret redaction. Persistent export
requires `--include-sensitive`; provider-known credential envelopes are
dropped structurally, while retained content remains sensitive. The manifest
must not imply that `redacted=0` means secret-free.

## Source and Result Status

A published bundle has:

```text
source_status = stable | grew | changed | displaced
result_status = ready | partial
```

Collection opens one regular non-link source descriptor and records its initial
identity/size. It reads a bounded prefix without chasing later appends.

- `stable`: descriptor and path identity/size remain stable.
- `grew`: the same source grew after the initial boundary.
- `changed`: the same source changed or shrank while being collected.
- `displaced`: the opened descriptor remained readable but its path disappeared
  or resolved to another object before publication.

`grew`, `changed`, and `displaced` publish only a valid partial result with a
diagnostic. They do not restore a byte-audit contract.

The classifier uses the initial/final descriptor and lexical path snapshots
`(device, inode, regular-file type, size, mtime_ns)` and ignores ctime, which
read-only access can change on Windows filesystems. Final unsafe/missing path or
path identity mismatch has first precedence as `displaced`; otherwise a
smaller size or equal size with changed mtime is `changed`, a larger size is
`grew`, and equal size/mtime is `stable`. `grew` reports observed size growth,
not proof of append-only bytes. An unclassifiable final safety/identity check
publishes nothing rather than guessing a status.

No artifact is published when the source cannot be safely opened, is a
symlink/reparse point, violates containment/selection authority, has no
compatible thread identity/meta record, or cannot produce a structurally valid
prefix. Output containment, no-overwrite, and atomic-publication violations
also fail without publication.

## Manifest and Diagnostics

The exact root shape, policy, capability/count/loss maps, diagnostic vocabulary,
and detail whitelist are frozen in
[`bundle-manifest.md`](bundle-manifest.md). The manifest never contains an
absolute source/workspace path, native thread ID, native-source hash/size
receipt, discarded content, or copied task file. `source_bytes_read` is a
resource observation, not native completeness proof.

## Task References

Only lexical relative `tasks/.../packet.md` references observed in normalized
user or assistant messages are eligible. Each eligible message may carry a
`task_refs` array of normalized relative path strings in first-occurrence
order. Duplicates within one message collapse; the bundle-wide 2,048-reference
cap counts retained occurrences across messages. Extraction may inspect the
full provider-visible message before content truncation, but only the bounded
message content, normalized references, counts, and structural diagnostics
survive. V1 never scans, infers, or copies a task directory or packet file.
Absolute task paths are omitted/diagnosed.

Before relative scanning, the scanner consumes maximal path-like tokens that
start with a POSIX root, Windows drive root, UNC root, or URI scheme. If such a
token contains a `tasks` component and ends in `packet.md`, POSIX
(`/repo/tasks/...`), drive (`C:\repo\tasks\...` or `C:/repo/tasks/...`), and
UNC (`\\server\share\tasks\...` or `//server/share/tasks/...`) forms use
`absolute-task-reference-dropped`; URI forms use
`invalid-task-reference-dropped`. Their embedded `tasks/` suffix is never
rescanned as a relative candidate. A backslash-bearing unrooted path-like token
is invalid and likewise not rescanned.

The relative scanner then begins only at a token boundary before literal
`tasks/`, stops at Unicode whitespace/control, angle brackets, quotes,
backtick, square/curly brackets, parentheses, or backslash, and removes only
terminal sentence punctuation `.,;:!?。！？；：、`. The resulting Pure POSIX
path must be at most 1,024 code points, begin with component `tasks`, end with
component `packet.md`, contain at least one intervening non-empty component,
contain no `.`/`..` component or backslash, and already equal its normalized
slash form. Root/URI detection precedes the per-reference size check;
otherwise oversize precedes generic invalid. No URL/percent decoding,
filesystem lookup, case folding, or Unicode normalization occurs.

An over-bound candidate is omitted with
`task-reference-oversize-dropped`; a leading-root candidate uses
`absolute-task-reference-dropped`; any other invalid lexical candidate uses
`invalid-task-reference-dropped`. No diagnostic retains the candidate.

## Schema-v1 Archive Cut-off

The normalizer accepts provider-local sources only. `analyze --input` accepts
only the exact two-member schema-v2 bundle defined here.

When the bounded root `manifest.json` identifies the released schema-v1 SVC
archive format, validation fails with
`unsupported-agent-thread-bundle-schema` before any native provider member,
old index, or copied task file is opened. Other foreign/malformed ZIPs use the
normal invalid-bundle errors. V1 contains no schema-v1 reader, converter,
re-export selector, or hidden raw compatibility path.
