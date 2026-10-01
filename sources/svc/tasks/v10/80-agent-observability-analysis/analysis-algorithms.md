# Deterministic Analysis Algorithms v1

Status: Slice 0 frozen task-local algorithm contract. These rules define
`deterministic-v1`; an implementation cannot replace them with intuitive
semantic classification while retaining that method name.

## Common Pass

1. Validate the manifest and canonical trajectory before deriving output.
2. Traverse `record_index` order. Timestamps never reorder evidence.
3. Build bounded indexes for record ID, user turns, context, explicit
   actor/lane/parent/group refs, task refs, terminal events, and tools.
4. Emit metric candidates and finding/unknown candidates using the rules below.
5. Use the exact candidate tuple and metric-array orders in
   `analysis-schema.md`. Coalesce identical candidates, retain at most 25
   findings and 25 unknowns per dimension with the frozen limit-unknown
   reservation, apply the global caps, and only then assign `f...`/`u...` IDs
   in final order.
6. Apply metric/cardinality/byte bounds. Any omission marks its dimension and
   overall result partial and is counted in analysis loss.

An absent finding is not proof that the opposite happened. Metrics own complete
bounded counts; findings are navigation landmarks.

## Loss-to-Dimension Propagation

The phrase “relevant loss” means this exact matrix:

| Manifest fact | Affected dimensions |
| --- | --- |
| Any non-zero `partial_reasons`, or dropped `unsupported_record`, `invalid_json`, `oversize_record`, or `excessive_json_depth` | Every dimension with otherwise usable evidence; these facts also make terminal tail completeness unproven, and coverage is partial |
| Dropped `duplicate_tool_result` | `tool_outcomes`, `loop_candidates` |
| Dropped/truncated/unavailable task references | `task_evidence`, `constraint_evidence`, `svc_signals` |
| Truncated context content/attribute/tool-config names or absent/partial context capability | `constraint_evidence`, `context_changes` |
| Truncated tool name | `tool_outcomes`, `loop_candidates`, `svc_signals` |
| Truncated tool arguments | `svc_signals`; loop grouping still uses the full pre-truncation fingerprint |
| Truncated tool result | `tool_outcomes` |
| Absent/mixed/synthesized tool linkage or synthesized call IDs | `tool_outcomes`, `loop_candidates` |
| Unavailable explicit concurrency | `lanes` |
| Unavailable terminal events | `terminal_coverage` |

All other declared noise/content loss—provider envelopes, UI/rate/world/
bookkeeping/opaque metadata, timestamp precision/availability, workspace or
message truncation, reasoning loss, diagnostic truncation, and task-reference
diagnostic detail loss—is reported by `coverage` but does not by itself make
another dimension partial. A relevant loss makes a dimension partial when
useful evidence remains; a projection-specific rule may instead make it
unavailable when its required evidence/capability is wholly absent. This matrix
is authority over intuitive guesses from diagnostic text.

## Shared Fingerprints and Tool Linkage

Valid JSON tool arguments canonicalize as compact sorted-key UTF-8 JSON with
duplicate keys and non-finite numbers rejected. Text arguments use their exact
decoded UTF-8 value. Before content truncation:

```text
arguments_fingerprint =
SHA-256(b"svc-tool-arguments-v1\0" + canonical_argument_bytes)

name_fingerprint =
SHA-256(b"svc-tool-name-v1\0" + full_tool_name_utf8)

retry_signature =
SHA-256(b"svc-tool-retry-v1\0" + name_fingerprint_ascii + b"\0"
       + argument_component)

argument_component =
  arguments_fingerprint_ascii for json/text arguments
  b"absent" for arguments_kind=absent
```

Fingerprints are 64 lowercase hex characters and are not secrecy guarantees.
Calls with absent arguments retain a null arguments fingerprint but have the
explicit `absent` retry component, so genuinely argument-free calls can still
be compared without inventing arguments.

The analysis pass creates one call slot per canonical `tool_call_id`.

- A `linked` result resolves immediately.
- An emitted `unresolved` result becomes `late_linked` only if the complete
  trajectory contains the exact same canonical call ID.
- An unresolved result with no exact call is `orphan`.
- A call with no winning result is `pending`.
- The first structurally valid result for one call wins; later results remain
  duplicate/loss counts and never overwrite the outcome.
- Duplicate native call IDs follow the trajectory suffix rule; an ambiguous
  raw result belongs only to the unsuffixed earliest call.

Trajectory records are immutable; late linkage exists only in analysis metrics
and findings.

## Projection Rules

### 1. `task_evidence`

- `user_turn_refs` contains every user message in source order up to its bound.
- The first user message yields `first-user-turn`.
- Every normalized relative task reference is counted by path and first
  evidence. Retained distinct references yield `task-reference`.
- With no user message the dimension is unavailable and emits
  `user-evidence-unavailable`.
- User-array/task-reference bounds make it partial.

No task summary or semantic task label is generated.

### 2. `interaction_transitions`

Every user message after the first is one observed `user-turn-boundary`.
Its preceding action is the latest assistant message, tool call, approval event,
or agent-start event strictly after the prior user message and before the
current user message. Its following action is the first such record strictly
after the current user message and before the next user message, or before end
of trajectory for the final boundary. Missing sides are null.

Every structured approval event contributes once to
`structured_approval_count` and yields one `structured-approval` finding.
Approvals strictly between the prior and current user messages are also
attached to that current boundary in record order. Approvals before the first
user message or after the last remain findings/counts but belong to no boundary.
Text is never classified as authorization, correction, or scope change. The
dimension is:

- available when at least one user boundary or structured approval is present
- unavailable with `transition-semantics-unavailable` when the question could
  only be answered from free-text interpretation
- partial when user/action records intersect relevant loss or array bounds

### 3. `constraint_evidence`

Evidence is limited to:

- system/developer/tool-config/turn context records
- normalized task references
- structured approval events

All retained source records appear in the dimension's ordered `evidence_refs`;
this dimension does not duplicate the context-change findings owned by
`context_changes`. No user/assistant sentence is labeled a constraint. If none
of the structured sources exists, emit `constraint-evidence-unavailable`.

### 4. `tool_outcomes`

Use only the shared linkage result and structured tool-result status:

- `success` → `tool-success`
- `error` → `tool-error`
- absent/unrecognized status → `tool-unknown`
- call without a result → `tool-pending`
- result without a call → `tool-orphan`
- result linked only after the full pass → `tool-late-linked`

Counts include all records even when finding caps suppress landmarks. Missing
tool-linkage capability makes the dimension unavailable; mixed/synthesized
linkage or relevant truncation/loss makes it partial.

### 5. `loop_candidates`

Calls group by exact retry signature within the same explicit `turn_ref` and
`lane_ref` (null lane is one value):

- two or more calls → `retry-group`
- three or more calls → `loop-candidate`
- three or more calls whose final observed outcome is error, unknown, or
  pending and has no later success → `stall-candidate`
- two or more calls with an error followed later by success →
  `recovery-candidate`

No elapsed-time threshold is used. With zero calls the dimension is available
with zero groups. With calls but no explicit `turn_ref`, it is unavailable with
`turn-linkage-unavailable`; it does not group the whole thread heuristically.
When only some calls lack `turn_ref`, the linked subset is analyzed, the
dimension is partial, and one `turn-linkage-unavailable` unknown references the
earliest affected calls. Every candidate kind is heuristic with medium
confidence, except a two-call retry group which is deterministic/high as a
repetition fact.

Every `LoopSummary.call_count` is the number of calls in that candidate group;
the matching finding's `retry_count` is `call_count - 1`.

### 6. `lanes`

Count and expose only explicit canonical actor, parent, lane, and concurrency
refs. Emit one `explicit-lane` finding at the first record for each distinct
lane ref and one `explicit-parent-link` finding at the first record for each
distinct `(actor_ref, parent_actor_ref)` pair. Timestamps never imply
concurrency. `actors` is the sorted union of actor and parent-actor refs;
`actor_count`, `lane_count`, and `concurrency_group_count` count distinct refs,
while `parent_link_count` counts distinct pairs. An available
explicit-concurrency capability with no refs is an available zero result; an
unavailable capability yields `concurrency-unavailable`.

### 7. `terminal_coverage`

Terminal candidates are `turn_complete`, `turn_abort`, `agent_complete`, and
`error`. The last candidate in record order wins; later explicit evidence is
authority over earlier evidence.

If manifest `terminal_events=unavailable`, the dimension is unavailable with
status `unknown` and `terminal-evidence-unavailable(cause=capability,
capability=terminal_events)`. No terminal/start finding is emitted. A bundle
that nevertheless carries a terminal/start event is inconsistent and rejected.
`tail_loss` is still computed from the exact loss predicate below; the
remaining winner rules apply only when the capability is available.

Mapping:

- complete event with completed outcome → `completed`
- complete/error event with error outcome → `error`
- abort event or aborted outcome → `aborted`
- a `turn_start` or `agent_start` after the last terminal candidate, or any
  start when no terminal candidate exists, with a stable/ready captured tail →
  `open`
- a candidate with no mapping above, or no candidate/start → `unknown`

Any non-zero manifest `partial_reasons`, or dropped `unsupported_record`,
`invalid_json`, `oversize_record`, or `excessive_json_depth`, means the
captured tail cannot be proven complete: `tail_loss=true` conservatively, even
when a diagnostic's known position is earlier. No other declared loss sets
this flag. It is a completeness flag, not a claim that loss was localized at
the tail, and it makes a resolved provisional status partial. `unknown` yields
`terminal-evidence-unavailable`, referencing the winning unmapped candidate
when one exists. Its cause is `loss` when no candidate/start survives and
`tail_loss=true`, `missing` when no candidate/start exists without tail loss,
and `ambiguity` for an unmapped candidate. Contradictory terminal events at the
same structural `source_ref` position yield unknown plus both
`evidence-conflict` and `terminal-evidence-unavailable(cause=ambiguity)`; this
rule wins over record order. A resolved provisional status with tail loss is a
partial dimension; every `unknown` case is unavailable. Every non-conflicting
resolved status, including `unknown`, yields one `terminal-status` finding at
its winning candidate/start when an evidence record exists. No
implemented/verified/blocked/superseded semantic status is inferred.

`terminal_evidence_refs` contains every `turn_start`, `agent_start`, and
terminal-candidate ref in record order. It uses the common first-16/last-16
EvidenceRef rule above 32, so winning tail evidence remains retained while an
omission makes this dimension partial.

### 8. `svc_signals`

Observed signals:

- normalized task references → `svc-task-reference`

Tool arguments are scanned without execution. For JSON arguments, traverse
string leaves in canonical key/index order; for text arguments, use the bounded
text. Tokenize each string as maximal case-sensitive ASCII
`[A-Za-z0-9_.-]+` runs. Scan contiguous token subsequences left to right,
preferring the longest pattern at a position and consuming a match so patterns
do not overlap. For every command `C` in the frozen command set, match:

```text
[svc, C]
[svc.exe, C]
[pdm, run, svc, C]
[pdm, run, svc.exe, C]
```

where:

```text
C = lookup | status | init | adopt | self-update | dev | telemetry
```

Also match these exact token sequences:

```text
pdm run test
pdm run build-monolith
pdm build
```

Matches yield `svc-cli-call`, `svc-test-call`, or `svc-build-call`. Within one
tool call, matches of the same signal kind coalesce into one finding/count;
the metric `signals` array then aggregates those counts by signal kind across
calls. Only signal kind/tool name/count/evidence ref survives, never the
command. Message, reasoning, and tool-result text are not scanned. The
dimension is available with zero signals when task-reference extraction is
available or at least one tool call has JSON/text arguments. If neither source
is available it emits `svc-signal-unavailable(cause=capability,
capability=task_references)`; argument truncation or unsupported tool arguments
makes it partial. Provider approval events remain interaction/constraint
evidence and are never mislabeled as an SVC mutation gate.

Truncated canonical JSON arguments are not parsed/scanned because their preview
is intentionally invalid JSON. Truncated text arguments scan only retained text
and make the dimension partial.

### 9. `context_changes`

For each already bounded context record, remove common record fields and its
stored `fingerprint`. Canonicalize exactly this required post-normalization
object as compact sorted-key UTF-8 JSON:

```text
{
  "context_kind": <enum>,
  "content": <retained bounded string or null>,
  "content_meta": <exact BoundedText>,
  "attributes": <exact retained attribute object>,
  "attributes_meta": <exact aligned metadata object>
}
```

Empty `attributes` and `attributes_meta` are present as empty objects; optional
attribute keys are omitted from both, never represented as null. Truncation
metadata and retained content participate in the fingerprint; discarded
content does not. Then:

```text
context_fingerprint =
SHA-256(b"svc-context-v1\0" + canonical_context_bytes)
```

The first fingerprint per `(context_kind, actor_ref-or-null)` establishes a
baseline and yields `context-established`. A later different fingerprint
yields `context-changed` with the immediately prior record for that key and the
changed record; returning to an earlier fingerprint is another change.
Analysis verifies the stored fingerprint against this canonicalization;
mismatch invalidates the bundle. Context capability absent makes the dimension
unavailable; an available capability with zero context records is an available
zero result; partial context capability or relevant loss makes it partial.

### 10. `coverage`

Copy fixed manifest statuses, capabilities, record counts, and loss maps;
compute record/role/timestamp counts from the trajectory and require them to
agree with the manifest. A mismatch rejects analysis as an invalid bundle.

Any bundle partial status produces `coverage-partial` and partial dimension
status. A valid ready/loss-declared bundle can have intentional drops and still
have available coverage because the loss itself is fully observed. Each
non-zero fixed loss class is an observed `loss-observed` landmark, bounded by
the per-dimension finding cap while exact counts remain in metrics.

## Kind and Confidence

Direct record/manifest facts are `observed/high`. Exact indexing, linkage, and
aggregation are `deterministic/high`. Frozen command scanning and
loop/stall/recovery interpretation are `heuristic/medium`; missing outcomes
produce the frozen status/unknown rules rather than lowering confidence ad hoc.
Unknowns have no finding/confidence object.

These labels describe evidence strength, not product quality or causality.
