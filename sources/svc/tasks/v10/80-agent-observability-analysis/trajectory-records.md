# Trajectory Record Schema v1

Status: Slice 0 frozen task-local machine contract. Runtime executable schemas
and validators will own this shape after implementation.

## Common Shape

Every record contains exactly the required common keys:

```text
type
record_id
record_index
timestamp
source_ref
```

Optional relationship keys are omitted when unavailable:

```text
turn_ref
actor_ref
parent_actor_ref
lane_ref
concurrency_group
```

No key may contain null except required `timestamp`, the synthesized meta
record's `source_ref.event_index`, and the explicit nullable fields described
below. Hashed refs use the kind-prefixed SHA-256 format; record
IDs/indexes/source refs follow `trajectory-schema.md`.

For the synthesized meta record, `source_ref` is exactly
`{"event_index":null,"component":"meta"}`. For every provider-derived record,
`source_ref` contains a required non-negative `event_index` plus optional
`line`, `byte_offset`, `component_index`, and `component`. Integer offsets are
non-negative and zero-based. `component` is a structural provider-parser label
matching lowercase ASCII `[a-z][a-z0-9_-]{0,127}`; each registered adapter owns
and fixture-freezes the labels it emits.

## Bounded Text

Every retained text field with possible truncation has an adjacent metadata
object:

```text
truncated                boolean
observed_code_points     non-negative integer
retained_code_points     non-negative integer
strategy                 none | head | head_tail
```

When not truncated, strategy is `none` and observed equals retained. For
`head_tail`, the retained limit is split with the extra code point assigned to
the head. No marker is inserted into canonical content; renderers add a visual
loss marker from metadata.

Message, system/developer context, reasoning, tool arguments, and tool results
use `head_tail`. Tool names, workspace labels, and scalar context attributes
use `head`. Context attribute metadata is carried by the aligned
`attributes_meta` object below. A task reference over its per-reference bound
is omitted and diagnosed, never truncated into a different path.

## `meta`

Required type-specific keys:

```text
trajectory_schema = svc.trajectory/v1
provider_id
adapter_id
source_format
thread_ref
workspace
content_profile = bounded-normalized-v1
```

`timestamp` is null. `workspace` is the exact object from the workspace
projection contract:

```text
status = present | missing
flavor = posix | windows | unc | null
label = bounded string | null
ref = workspace_<64 lowercase hex> | null
label_truncated = boolean
observed_code_points = non-negative integer
retained_code_points = non-negative integer
```

Missing workspace has null flavor/label/ref and zero counts.

## `message`

Required keys:

```text
role = user | assistant
content = bounded string
content_meta = BoundedText
task_refs = ordered array of normalized relative paths
```

`task_refs` is always present, can be empty, and contains no duplicates within
the record. Optional turn/actor/lane relationships use the common fields.

## `reasoning`

Required keys:

```text
reasoning_kind = full | summary
content = bounded string
content_meta = BoundedText
```

Opaque/absent reasoning emits no `reasoning` record.

## `tool_call`

Required keys:

```text
tool_call_id
name = bounded string
name_meta = BoundedText
name_fingerprint = 64 lowercase hex
arguments_kind = json | text | absent
arguments = bounded string | null
arguments_meta = BoundedText
arguments_fingerprint = 64 lowercase hex | null
```

For `json`, `arguments` is canonical JSON text when untruncated. For `text`, it
is exact decoded provider text before bounding. For `absent`, arguments and
fingerprint are null and metadata counts are zero. A fingerprint always covers
the full observed canonical/text arguments before truncation. The name
fingerprint covers the full observed tool name before truncation.

## `tool_result`

Required keys:

```text
tool_call_id
content = bounded head-tail string
content_meta = BoundedText
status = success | error | unknown
link_status = linked | unresolved
```

The canonical record is never rewritten when later analysis establishes
`late_linked` or `orphan`. Structured JSON results become compact sorted-key
JSON text before bounding; other provider-visible result text is decoded
without semantic rewriting. `status` comes only from an explicit structured
provider outcome/error fact and is otherwise `unknown`; result text is never
scanned to guess success.

## `context`

Required keys:

```text
context_kind = system | developer | tool_config | turn
content = bounded string | null
content_meta = BoundedText
attributes
attributes_meta
fingerprint = 64 lowercase hex
```

System/developer context may carry content. Tool-config/turn content is null and
has zero metadata counts. `attributes` contains only these optional keys:

```text
model
reasoning_effort
approval_mode
sandbox_mode
collaboration_mode
tool_names
```

Scalar values are bounded strings of at most 512 code points.
`attributes_meta` contains exactly the same keys as `attributes`. For each
scalar key its value is the aligned `BoundedText`. For `tool_names`,
`attributes.tool_names` is an array of objects:

```text
name = bounded string
name_meta = BoundedText
name_fingerprint = shared `svc-tool-name-v1` fingerprint over the full observed name
```

The tool-name array is sorted by the full observed name's UTF-8 bytes,
deduplicated before bounding, and retains at most the first 256 names.
`attributes_meta.tool_names` is exactly:

```text
observed_items = non-negative integer
retained_items = integer 0..256
truncated = boolean
```

`truncated` is true exactly when the collection cap discards one or more unique
names; `retained_items` equals the emitted array length. Per-name truncation is
instead recorded by each `name_meta`. Complete tool schemas, defaults, and
descriptions are never retained. The fingerprint canonicalization is frozen in
`analysis-algorithms.md`.

## `event`

Required keys:

```text
event_kind =
  turn_start | turn_complete | turn_abort |
  agent_start | agent_complete | compaction | approval | error
outcome =
  requested | granted | denied | cancelled |
  completed | error | aborted | unknown | null
```

Allowed combinations:

- approval: requested/granted/denied/cancelled/unknown
- turn/agent complete: completed/error/aborted/unknown
- turn abort: aborted
- error: error
- start/compaction: null

No provider payload/details/free-text error is retained on an event. Actor,
turn, parent, lane, and concurrency refs are common optional relationships.

## Validation

Readers reject:

- extra/missing keys or wrong scalar types/enums
- duplicate JSON keys, non-finite numbers, invalid UTF-8, decoded lone
  surrogates/non-scalar strings, or excessive depth
- non-contiguous `record_index`, mismatched `record_id`, or a second/meta-late
  meta record
- meta provider/adapter/format/thread/profile values that do not equal the
  manifest source and policy
- unresolved relationship refs with invalid hash shape
- text metadata inconsistent with actual retained content/bounds
- tool/context fingerprints with invalid form, and context fingerprints that
  do not recompute
- invalid task refs or event-kind/outcome combinations

Provider-boundary malformed records can be dropped/diagnosed into a partial
valid trajectory. A malformed normalized trajectory is never repaired by the
analysis reader.
