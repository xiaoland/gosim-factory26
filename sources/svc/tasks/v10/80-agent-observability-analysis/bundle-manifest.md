# Bundle Manifest Schema v2

Status: Slice 0 frozen task-local machine contract. The implementation must own
an executable schema/validator with this exact vocabulary.

## Root Shape

`manifest.json` contains exactly:

```text
format
schema_version
trajectory
bundle_id
exporter
generated_at
source
policy
result_status
capabilities
counts
lossiness
diagnostics
```

Required scalar values:

```text
format = svc-agent-thread-bundle
schema_version = 2
result_status = ready | partial
generated_at = canonical UTC RFC 3339 timestamp
bundle_id = 64 lowercase hex
```

`trajectory` is:

```text
schema = svc.trajectory/v1
member = trajectory.jsonl
sha256 = 64 lowercase hex
bytes = non-negative integer <= 32 MiB
records = integer 1..50,000
```

`exporter` is:

```text
name = svc
version = installed SVC semantic version
normalizer_name = svc-agent-thread-normalizer
normalizer_version = 1
```

## Source

`source` is:

```text
provider_id                 safe fixed provider component
adapter_id                  safe fixed adapter component
source_format               safe fixed provider format
thread_ref                  thread_<64 lowercase hex>
source_status               stable | grew | changed | displaced
```

The provider/adapter/format components match lowercase ASCII
`[a-z][a-z0-9_-]{0,63}` and must be registered by the executable adapter; a
schema-valid but unregistered tuple is unsupported rather than dynamically
loaded.

`source_status` describes only the descriptor-bound provider rollout read by
the normalizer. Schema-v1 archives are not normalizer inputs.

## Policy

`policy` contains exactly:

```text
profile = bounded-normalized-v1
sensitivity = acknowledged
redaction = none
noise_policy = structural-v1
task_reference_policy = lexical-relative-packet-v1
timestamp_policy = utc-rfc3339-nanosecond-v1
bounds = exact object
```

`bounds` is the exact integer object:

```text
source_bytes = 268435456
native_line_bytes = 4194304
native_json_depth = 64
records = 50000
trajectory_bytes = 33554432
schema_v2_zip_bytes = 67108864
manifest_bytes = 1048576
workspace_label_code_points = 256
message_context_code_points = 16384
reasoning_code_points = 8192
tool_name_code_points = 256
tool_arguments_code_points = 20000
tool_result_code_points = 2500
context_attribute_keys = 6
context_attribute_code_points = 512
tool_config_names = 256
task_reference_code_points = 1024
task_reference_occurrences = 2048
structural_label_ascii = 128
diagnostics = 256
diagnostic_detail_keys = 16
diagnostic_detail_ascii = 128
```

A reader rejects a missing, extra, weaker, or internally inconsistent v1
policy rather than assuming defaults.

## Capabilities

The exact capability keys and values are:

| Key | Values |
| --- | --- |
| `reasoning` | `full`, `summary`, `opaque`, `absent` |
| `tool_linkage` | `explicit`, `mixed`, `synthesized`, `absent` |
| `context` | `full`, `partial`, `absent` |
| `task_references` | `available`, `unavailable` |
| `explicit_concurrency` | `available`, `unavailable` |
| `timestamps` | `full`, `partial`, `absent` |
| `terminal_events` | `available`, `unavailable` |

`mixed` tool linkage means both explicit and synthesized/unresolved IDs were
observed; `synthesized` means tool records exist but no explicit call identity
was usable; `explicit` also applies when the adapter supports exact linkage and
the thread has zero tool records. `context=full` means all four frozen context
kinds are source-format observable, `partial` means a documented subset.
Reasoning describes the strongest provider-obtainable representation:
full text, summary only, opaque/encrypted presence, or no representation.
`timestamps=full` means every provider-derived emitted record has a valid
timestamp, `partial` means a mix, and `absent` means none. The two
`available|unavailable` capability pairs describe source-format observability,
not whether this particular thread had a matching record; counts own presence.

Trajectory consistency is mechanical:

- `reasoning=summary` forbids full-reasoning records; opaque/absent forbids all
  reasoning records, while full/summary capabilities may validly observe zero
- `tool_linkage=absent` requires zero tool records; explicit requires zero
  synthesized-ID loss; mixed/synthesized must agree with non-zero synthesized
  or unavailable linkage facts
- `context=absent` forbids context records; full/partial may observe zero
- `task_references=unavailable` requires every message `task_refs` array empty
- `explicit_concurrency=unavailable` forbids lane, parent-actor, and
  concurrency-group refs, but does not forbid a standalone actor ref
- timestamp full/partial/absent agrees exactly with all/some/none of the
  provider-derived records carrying non-null time
- `terminal_events=unavailable` forbids turn/agent start, completion, abort,
  and error events; available may observe zero

A mismatch rejects the bundle instead of letting analysis choose which source
to trust.

## Counts

`counts` contains every key, including zeros:

```text
source_bytes_read
source_events_seen
records_emitted
trajectory_bytes
records_by_type {
  meta, message, reasoning, tool_call, tool_result, context, event
}
messages_by_role { user, assistant }
tool_calls
tool_results
task_references
diagnostics_emitted
diagnostics_suppressed
```

All values are non-negative integers. Root totals must equal their nested sums
where applicable and must agree with the canonical trajectory. A mismatch
invalidates the bundle.

## Lossiness

`lossiness.mode` is `bounded_normalized`. Every following map is present and
contains every frozen class with a non-negative integer:

```text
dropped {
  provider_envelope
  ui_event
  rate_limit_noise
  world_state
  duplicate_bookkeeping
  opaque_metadata
  unsupported_record
  invalid_json
  oversize_record
  excessive_json_depth
  duplicate_tool_result
  absolute_task_reference
  invalid_task_reference
  oversize_task_reference
}

truncated {
  timestamp_precision
  workspace_label
  message
  context_content
  context_attribute
  reasoning
  tool_name
  tool_config_names
  tool_arguments
  tool_result
  task_references
  diagnostics
}

unavailable {
  reasoning
  tool_linkage
  context
  task_references
  explicit_concurrency
  timestamps
  terminal_events
}

synthesized {
  tool_call_id
}

partial_reasons {
  source_grew
  source_changed
  source_displaced
  source_read_interrupted
  input_limit
  record_limit
  trajectory_limit
}
```

Intentional structural drops and bounded content truncation alone may remain
`ready`. Any non-zero `partial_reasons` value requires `partial`.
`unsupported_record`, `invalid_json`, `oversize_record`,
`excessive_json_depth`, or `duplicate_tool_result` also requires `partial`
because evidence semantics are missing/ambiguous. Provider/UI/rate/world/
bookkeeping/opaque noise, bounded task-ref drops, synthesized IDs, diagnostic
coalescing/caps, and declared content truncation alone remain `ready`.

## Diagnostics

A diagnostic contains exactly:

```text
code
severity = info | warning | error
action = drop | truncate | normalize | synthesize | unavailable | partial
count = positive integer
record_ref = record ID or null
source_ref = structural source ref or null
details = structural detail object
```

Repeated identical code/details coalesce into `count` and retain the earliest
record/source ref. Regular groups sort by source event index, line, byte offset,
and component index (a missing coordinate sorts last at its position), then
code ASCII bytes and canonical compact/sorted details bytes. At most 256
entries are emitted. With at most 256 regular groups, all are retained. With
more, retain the first 255 and append `diagnostic-limit-reached` unconditionally
as the final slot, with null refs, `count=1`, and details
`observed_count=<regular group count>, limit_count=256`.
`diagnostics_suppressed` and `truncated.diagnostics` equal the sum of occurrence
counts in suppressed regular groups, not merely the number of groups.

Allowed detail keys are:

```text
record_type
content_kind
observed_bytes
limit_bytes
observed_code_points
retained_code_points
observed_digits
retained_digits
observed_depth
limit_depth
observed_count
limit_count
occurrence
capability
arguments_kind
source_status
```

Values are frozen enums or non-negative integers. Details never contain free
text, paths, provider/native IDs, fingerprints, task refs, messages, reasoning,
tool values, or discarded content.

`record_type` is limited to:

```text
envelope | ui | rate_limit | world_state | duplicate | opaque | unknown
```

`content_kind` is limited to:

```text
system | developer | model | reasoning_effort | approval_mode |
sandbox_mode | collaboration_mode | tool_call_name | tool_config_name
```

Other enum detail values must come from the capability/status/arguments
vocabularies already frozen in this schema.

The code/action/severity/detail families are:

| Code | Action | Severity | Required details |
| --- | --- | --- | --- |
| `noise-record-dropped` | drop | info | `record_type` |
| `unsupported-record-dropped` | drop | warning | `record_type` |
| `invalid-json-line` | drop | warning | none; `source_ref` required |
| `record-oversize-dropped` | drop | warning | `observed_bytes`, `limit_bytes` |
| `json-depth-exceeded` | drop | warning | `observed_depth`, `limit_depth` |
| `timestamp-invalid` | unavailable | warning | none; `source_ref` required |
| `timestamp-precision-truncated` | truncate | info | `observed_digits`, `retained_digits` |
| `workspace-label-truncated` | truncate | info | `observed_code_points`, `retained_code_points` |
| `message-truncated` | truncate | info | `observed_code_points`, `retained_code_points` |
| `context-content-truncated` | truncate | info | `content_kind`, `observed_code_points`, `retained_code_points` |
| `context-attribute-truncated` | truncate | info | `content_kind`, `observed_code_points`, `retained_code_points` |
| `reasoning-truncated` | truncate | info | `observed_code_points`, `retained_code_points` |
| `reasoning-unavailable` | unavailable | info | `capability` |
| `tool-name-truncated` | truncate | info | `content_kind`, `observed_code_points`, `retained_code_points` |
| `tool-config-name-limit-reached` | truncate | warning | `observed_count`, `limit_count` |
| `tool-arguments-text` | normalize | info | `arguments_kind` |
| `tool-arguments-truncated` | truncate | info | `observed_code_points`, `retained_code_points` |
| `tool-result-truncated` | truncate | info | `observed_code_points`, `retained_code_points` |
| `tool-call-id-synthesized` | synthesize | warning | `occurrence` |
| `duplicate-tool-call-id` | synthesize | warning | `occurrence` |
| `duplicate-tool-result` | drop | warning | `occurrence` |
| `orphan-tool-result` | unavailable | warning | none; `record_ref` required |
| `absolute-task-reference-dropped` | drop | info | none; `source_ref` required |
| `invalid-task-reference-dropped` | drop | info | none; `source_ref` required |
| `task-reference-oversize-dropped` | drop | warning | `observed_code_points`, `retained_code_points` |
| `source-grew-during-collection` | partial | warning | `source_status` |
| `source-changed-during-collection` | partial | warning | `source_status` |
| `source-displaced-during-collection` | partial | warning | `source_status` |
| `source-read-interrupted` | partial | error | none; `source_ref` required when known |
| `input-limit-reached` | partial | warning | `observed_bytes`, `limit_bytes` |
| `record-limit-reached` | partial | warning | `observed_count`, `limit_count` |
| `trajectory-limit-reached` | partial | warning | `observed_bytes`, `limit_bytes` |
| `task-reference-limit-reached` | truncate | warning | `observed_count`, `limit_count` |
| `diagnostic-limit-reached` | truncate | warning | `observed_count`, `limit_count` |

No extra detail key is allowed for a code. The common whitelist makes
omitted/private values mechanically unrepresentable.
