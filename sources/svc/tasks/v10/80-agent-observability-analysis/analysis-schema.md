# Agent Analysis JSON Schema v1

Status: Slice 0 frozen task-local machine contract. The implementation must
realize it as executable validation plus tests; this prose is not the eventual
runtime validator.

## Top-Level Object

`analyze --json` writes one compact, sorted-key, UTF-8 JSON object followed by
LF with exactly these keys:

| Key | Type and value |
| --- | --- |
| `format` | Literal `svc-agent-thread-analysis` |
| `schema_version` | Integer `1` |
| `bundle_id` | The 64-lowercase-hex schema-v2 semantic evidence identity, including for ephemeral normalization |
| `analyzer` | Exact object below |
| `result_status` | `ready` or `partial` |
| `dimensions` | Exact ten-key map below |
| `metrics` | Exact ten-key map below |
| `findings` | Ordered array of `Finding`, maximum 256 |
| `unknowns` | Ordered array of `Unknown`, maximum 256 |
| `lossiness` | Exact bundle/analysis loss object below |

There is no generation timestamp, provider path, native ID, message excerpt,
reasoning, tool argument/result, or arbitrary provider field.

Overall `result_status` is `partial` when the bundle is partial or any
analysis-local cap/loss affects output; otherwise it is `ready`. An honestly
`unavailable` dimension caused solely by an absent provider capability does not
make an otherwise ready analysis partial.

`analyzer` is:

```text
name = svc-agent-thread-analyzer
version = 1
method = deterministic-v1
```

## Dimensions

`dimensions` contains exactly:

```text
task_evidence
interaction_transitions
constraint_evidence
tool_outcomes
loop_candidates
lanes
terminal_coverage
svc_signals
context_changes
coverage
```

Each value is:

```text
status = available | partial | unavailable
finding_ids = [analysis-local finding ID ...]
unknown_ids = [analysis-local unknown ID ...]
```

`available` means the required provider capability/evidence was observable and
no relevant loss or analysis cap intersects the projection; zero findings can
still be available. `partial` means useful output exists but relevant source,
normalization, or analysis loss intersects it. `unavailable` means the required
capability/evidence does not exist or is contradictory enough that the
projection would be a guess.

IDs in each dimension appear in global result order and must resolve exactly
once. No dimension-specific ad hoc key is allowed.

## Findings and Unknowns

A `Finding` has exactly:

```text
id                 f000001-style ID
dimension          one dimension name
code               one finding code
kind               observed | deterministic | heuristic
confidence         high | medium
evidence_refs      1..32 EvidenceRef objects
details            bounded structural Detail object
```

An `Unknown` has exactly:

```text
id                 u000001-style ID
dimension          one dimension name
code               one unknown code
cause              capability | missing | loss | ambiguity | conflict | analysis_limit
evidence_refs      0..32 EvidenceRef objects
details            bounded structural Detail object
```

An `EvidenceRef` has exactly `bundle_id`, `record_id`, and `record_index`.
`bundle_id` must equal the analysis root `bundle_id`; `record_id` and index must
resolve to the same validated trajectory record. Cross-bundle evidence is
invalid in this single-bundle schema.

Finding codes are:

```text
first-user-turn
task-reference
user-turn-boundary
structured-approval
context-established
context-changed
tool-success
tool-error
tool-unknown
tool-pending
tool-orphan
tool-late-linked
retry-group
loop-candidate
stall-candidate
recovery-candidate
explicit-lane
explicit-parent-link
terminal-status
svc-task-reference
svc-cli-call
svc-test-call
svc-build-call
loss-observed
```

Unknown codes are:

```text
user-evidence-unavailable
transition-semantics-unavailable
constraint-evidence-unavailable
tool-linkage-unavailable
turn-linkage-unavailable
concurrency-unavailable
terminal-evidence-unavailable
svc-signal-unavailable
context-evidence-unavailable
coverage-partial
evidence-conflict
analysis-limit-reached
```

Code-to-dimension assignment is exact:

```text
task_evidence             first-user-turn, task-reference
interaction_transitions   user-turn-boundary, structured-approval
constraint_evidence       no finding code; metrics carry the structured refs
tool_outcomes             tool-success, tool-error, tool-unknown, tool-pending,
                          tool-orphan, tool-late-linked
loop_candidates           retry-group, loop-candidate, stall-candidate,
                          recovery-candidate
lanes                     explicit-lane, explicit-parent-link
terminal_coverage         terminal-status
svc_signals               svc-task-reference, svc-cli-call, svc-test-call,
                          svc-build-call
context_changes           context-established, context-changed
coverage                  loss-observed
```

Unknown codes map in the same order: user evidence to `task_evidence`,
transition semantics to `interaction_transitions`, constraint evidence to
`constraint_evidence`, tool linkage to `tool_outcomes`, turn linkage to
`loop_candidates`, concurrency to `lanes`, terminal evidence and evidence
conflict to `terminal_coverage`, SVC signal to `svc_signals`, context evidence
to `context_changes`, and coverage partial to `coverage`.
`analysis-limit-reached` belongs to whichever dimension lost candidates; one
unknown is emitted per affected dimension.

The following tables freeze output fields beyond the code. `evidence` names
the exact records placed into `evidence_refs`, always deduplicated and ordered
by `record_index`. `{}` means the details object is present and empty.

| Finding code | Kind / confidence | Evidence | Exact details |
| --- | --- | --- | --- |
| `first-user-turn` | observed / high | first user message | `{}` |
| `task-reference` | observed / high | first message carrying that reference | `task_ref`, total `count` |
| `user-turn-boundary` | deterministic / high | current user message | `{}` |
| `structured-approval` | observed / high | approval event | `outcome` |
| `context-established` | deterministic / high | first context record for the key | `context_kind` |
| `context-changed` | deterministic / high | prior context record for the key, then changed record | `context_kind` |
| `tool-success` | deterministic / high | call and winning result in record order | `tool_name`, `status=success` |
| `tool-error` | deterministic / high | call and winning result in record order | `tool_name`, `status=error` |
| `tool-unknown` | deterministic / high | call and winning result in record order | `tool_name`, `status=unknown` |
| `tool-pending` | deterministic / high | call | `tool_name`, `status=pending` |
| `tool-orphan` | deterministic / high | unresolved result | result `status`; no invented tool name |
| `tool-late-linked` | deterministic / high | call and result in record order | `tool_name`, result `status`, `late_linked=true` |
| `retry-group` | deterministic / high | first and last call in group | `tool_name`, `retry_count` |
| `loop-candidate` | heuristic / medium | first and last call in group | `tool_name`, `retry_count` |
| `stall-candidate` | heuristic / medium | first and last call in group | `tool_name`, `retry_count` |
| `recovery-candidate` | heuristic / medium | first and last call in group | `tool_name`, `retry_count` |
| `explicit-lane` | observed / high | first record carrying the distinct lane ref | `{}` |
| `explicit-parent-link` | observed / high | first record carrying the distinct actor/parent pair | `{}` |
| `terminal-status` | deterministic / high | winning terminal/start record | `status`, nullable event `outcome` |
| `svc-task-reference` | observed / high | first message carrying that reference | `task_ref`, total `count`, `signal_kind=task_reference` |
| `svc-cli-call` | heuristic / medium | matching tool call | `signal_kind=svc_cli`, `tool_name`, match `count` in that call |
| `svc-test-call` | heuristic / medium | matching tool call | `signal_kind=test`, `tool_name`, match `count` in that call |
| `svc-build-call` | heuristic / medium | matching tool call | `signal_kind=build`, `tool_name`, match `count` in that call |
| `loss-observed` | observed / high | meta record | dotted `loss_class`, non-zero `count` |

One `tool-late-linked` finding is emitted in addition to the winning
status finding. One signal finding is emitted per `(tool call, signal kind)`
with matches coalesced into its `count`. One loss finding is emitted per
non-zero fixed manifest loss class; the meta record is its bundle-scoped
evidence anchor rather than a claim that the loss occurred at record zero.

| Unknown code | Cause | Evidence | Exact details |
| --- | --- | --- | --- |
| `user-evidence-unavailable` | missing | none | `{}` |
| `transition-semantics-unavailable` | missing | none | `{}` |
| `constraint-evidence-unavailable` | missing | none | `{}` |
| `tool-linkage-unavailable` | capability | none | `capability=tool_linkage` |
| `turn-linkage-unavailable` | missing | affected calls, up to 32 | `{}` |
| `concurrency-unavailable` | capability | none | `capability=explicit_concurrency` |
| `terminal-evidence-unavailable` | capability, missing, loss, or ambiguity as selected by the terminal algorithm | conflict/unmapped records selected by that algorithm, otherwise none | `capability=terminal_events` only for capability cause; otherwise `{}` |
| `svc-signal-unavailable` | capability | none | `capability=task_references` |
| `context-evidence-unavailable` | capability | none | `capability=context` |
| `coverage-partial` | loss | meta record | manifest `source_status`, manifest `result_status` |
| `evidence-conflict` | conflict | conflicting records in record order | `{}` |
| `analysis-limit-reached` | analysis_limit | earliest retained evidence for the affected dimension when present | `count`, `truncated=true` |

`details` is not free text. Keys are limited to:

```text
status
outcome
signal_kind
context_kind
tool_name
count
truncated
late_linked
retry_count
task_ref
source_status
result_status
capability
loss_class
```

Values are null, booleans, non-negative integers, frozen enums, opaque refs, a
bounded tool name, or a normalized relative task reference. No discarded or
semantic content may be placed in details.

For details, `capability` is limited to the exact manifest capability keys,
`signal_kind` to `task_reference`, `svc_cli`, `test`, or `build`, and
`loss_class` to `<loss-map>.<fixed-key>` from the manifest. A code rejects
details other than the exact fields in the tables above.

## Metrics

`metrics` has the same ten exact keys as `dimensions`.

### `task_evidence`

```text
user_turn_count
user_turn_refs[]            ordered EvidenceRef, max 2,048
task_references[]           TaskReferenceSummary, max 2,048
```

`TaskReferenceSummary` is `{path, occurrences, first_evidence_ref}`. Paths are
normalized relative `tasks/.../packet.md` values, not filesystem reads.

### `interaction_transitions`

```text
boundary_count
boundaries[]                TransitionSummary, max 2,048
structured_approval_count
```

`TransitionSummary` is
`{user_ref, preceding_action_ref, following_action_ref, approval_refs}`.
Nullable action refs are explicit; approval refs are ordered and capped at 32
per boundary.

### `constraint_evidence`

```text
context_record_count
task_reference_count
structured_approval_count
evidence_refs[]             ordered, max 2,048
```

### `tool_outcomes`

```text
calls
results
success
error
unknown
pending
orphan
late_linked
truncated_results
retry_groups
tools[]                     ToolSummary, max 512
```

`ToolSummary` has
`{name,name_fingerprint,calls,results,success,error,unknown,pending,late_linked,
truncated_results,retry_groups,first_evidence_ref}`.
Its result/status counts include only results linked or late-linked to calls
with that exact name fingerprint. Orphan results have no authoritative tool
name, so they appear only in the root `orphan`/`results` totals and findings.

### `loop_candidates`

```text
retry_group_count
loop_candidate_count
stall_candidate_count
recovery_candidate_count
groups[]                    LoopSummary, max 512
```

`LoopSummary` has
`{kind,tool_name,name_fingerprint,call_count,first_evidence_ref,last_evidence_ref,
outcomes}`.
`kind` is `retry|loop|stall|recovery`; `outcomes` is an ordered bounded array
of at most 32 `success|error|unknown|pending` values.
For the corresponding finding, `retry_count` is exactly `call_count - 1`.

### `lanes`

```text
actor_count
lane_count
concurrency_group_count
parent_link_count
actors[]                    opaque actor refs, max 512
lanes[]                     opaque lane refs, max 512
concurrency_groups[]        opaque group refs, max 512
```

### `terminal_coverage`

```text
status                      completed | error | aborted | open | unknown
terminal_evidence_refs[]    ordered, max 32
tail_loss                   boolean
```

### `svc_signals`

```text
task_references
svc_cli_calls
test_calls
build_calls
signals[]                   SignalSummary, max 512
```

`SignalSummary` is `{kind,count,first_evidence_ref}` where kind is
`task_reference|svc_cli|test|build`.

### `context_changes`

```text
context_records
changes
by_kind                     exact system/developer/tool_config/turn counts
change_refs[]               ordered EvidenceRef, max 512
```

### `coverage`

```text
records_total
records_by_type             exact seven record-type counts
messages_by_role            exact user/assistant counts
timestamped_records
untimestamped_records
first_timestamp             RFC 3339 or null
last_timestamp              RFC 3339 or null
source_status
bundle_result_status
capabilities                exact manifest capability object
```

First/last timestamp mean first/last non-null value in record order, not a
wall-clock sort or inferred duration.

## Deterministic Array Order

Canonical object keys are sorted by the JSON encoder; arrays use these orders:

- evidence-ref arrays and user/constraint/context/terminal refs: ascending
  `record_index`, then `record_id`
- task references: first-evidence index, then path UTF-8 bytes
- transition boundaries: current user-record index
- tools: first-evidence index, then `name_fingerprint`
- loop groups: first-evidence index, last-evidence index, fixed kind order
  retry/recovery/loop/stall, then `name_fingerprint`
- actor, lane, and concurrency-group refs: exact ASCII byte order
- SVC signal summaries: task-reference, SVC CLI, test, then build
- findings and unknowns: earliest evidence index (no-evidence unknowns last),
  dimension order, code UTF-8 bytes, canonical compact/sorted details bytes,
  then the evidence `(record_index,record_id)` tuple

An exactly identical candidate tuple coalesces before caps. Per-dimension and
global retention keep the front of these orders. When a dimension loses any
candidate/metric/ref, its 25th unknown slot is reserved for the single
`analysis-limit-reached` unknown, so at most 24 other unknowns survive there.
Finding and unknown IDs are assigned only after final retention; a
map/dictionary insertion order is never observable authority.

Every EvidenceRef array with a 32-element cap retains the first 16 and last 16
refs in record order; larger EvidenceRef arrays retain their first declared
cap. `TransitionSummary.approval_refs` follows the 16/16 rule.
`LoopSummary.outcomes` likewise retains the first 16 and last 16 outcomes.
Omitted refs increment `evidence_refs_omitted` and use
`limits_reached=evidence_ref`; omitted outcomes or any other nested non-ref
metric element increment `metric_entries_omitted` and use
`limits_reached=metric_entry`. The affected dimension and overall result become
partial and receive the reserved limit unknown. Parent scalar totals always
describe the complete bounded trajectory rather than the retained nested
preview.

Removing a whole finding, unknown, or metric entry counts only that parent
class, not its now-unreachable child refs. Removing children from a retained
parent counts the child class. Each dimension's
`analysis-limit-reached.details.count` is the sum of its parent and child
omissions across all analysis-local caps; the four root omission counters are
the corresponding cross-dimension totals.

## Lossiness and Bounds

`lossiness.bundle` contains exactly `mode`, `source_status`, `result_status`,
`dropped`, `truncated`, `unavailable`, `synthesized`, and `partial_reasons`,
copying the manifest's fixed values/maps without diagnostic detail text.
`lossiness.analysis` has:

```text
limits_reached[]            finding|unknown|evidence_ref|metric_entry|byte
findings_omitted
unknowns_omitted
evidence_refs_omitted
metric_entries_omitted
```

All counts are non-negative integers and every key is always present. An
analysis-local omission makes the result and affected dimension `partial`.
`limits_reached` is a unique array in the fixed order shown above.
Every removal from a metrics array, whether it is a transition, task
reference, tool, loop, signal, context change, actor, lane, or group, uses
`metric_entry`; the aggregate count is `metric_entries_omitted`.

Hard bounds:

- canonical output: 2 MiB including LF
- findings: 256 total and at most 25 per dimension
- unknowns: 256 total and at most 25 per dimension
- evidence refs: 32 per finding/unknown
- user/constraint/transition/task-ref arrays: 2,048 each
- tool, loop, signal, context-change, actor/lane/group arrays: 512 each
- tool name: 256 Unicode code points
- relative task reference: 1,024 Unicode code points
- code/enum/opaque-ref scalar: 128 ASCII characters

Candidate retention is source-evidence order then stable code/key order. If the
cardinality-bounded object still exceeds 2 MiB, whole trailing metric entries,
findings, unknowns, and non-required evidence refs are removed in the reverse
array orders above, updating loss counts and one `analysis-limit-reached`
unknown per affected dimension after every pass. The canonical object is
re-serialized until it fits; required finding evidence, scalar metrics,
dimension maps, and limit unknowns are never removed. If that fixed core cannot
fit, analysis fails without partial JSON rather than emitting an invalid shape.
