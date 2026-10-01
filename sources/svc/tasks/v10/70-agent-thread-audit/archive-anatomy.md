# Archive Anatomy and Segmentation Questions

## Observed Common Layout

Every retained archive has these three core members:

| Member | Role in the audit | What it does not establish alone |
| --- | --- | --- |
| `manifest.json` | Provenance, exporter/provider identity, source digest/size, capability and warning summaries, and packet-association metadata | A conversational or task boundary |
| `providers/codex/rollout.jsonl` | Native chronological evidence stream | A ready-made human–Agent episode structure |
| `thread/index.json` | One timestamped structural record per native line, with line, bytes, digest, and type | Message role, semantic intent, or causal outcome |

The SVC-v10 archive alone also contains associated task-packet members. That is
useful as a parallel work-artifact layer, but it must not be treated as a
complete account of the conversation or as proof that a packet caused an
outcome.

All eight ZIP CRC checks pass. In each archive, the manifest's record counts,
the native JSONL line count, and the index record count agree; no malformed
JSONL line was observed. ZIP member timestamps are fixed packaging metadata,
not event time, so they must never be used for chronology.

## What the Index Makes Possible

The index has complete timestamp coverage for the captured native stream and
enumerates structural record types. Its timestamps are non-decreasing but can
repeat, so timestamp alone cannot define a segment. Across the corpus, observed
types include message/event records, response items, turn context, session
metadata, world state, compaction, multi-agent metadata, and
execution-completion records.

This supports a first, content-free pass that can locate:

- temporal gaps and bursts;
- context-window compaction boundaries;
- configuration/environment context changes;
- likely turn IDs, event IDs, message roles/status/phases, and user-message
  triggers after bounded rollout review; and
- execution/coordination density around a candidate episode.

It does **not** tell us, without bounded rollout review, whether a record is a
human request, injected runtime context, assistant message, reasoning, tool
payload, or a meaningful task transition.

The native schema also exposes call IDs and, in the newer long-running cases,
multi-agent coordination triggers. These are useful linking signals, but their
runtime meaning must be checked against nearby turns rather than assumed to
mean delegation or completion.

## Multi-Resolution Boundary Model

| Resolution | Candidate boundary | Evidence source | Audit use |
| --- | --- | --- | --- |
| Corpus | The eight selected archives | external inventory | sampling and coverage bias |
| Case | One exact thread archive | manifest and provenance | a bounded collaboration episode candidate |
| Context window | compaction/session boundary | index plus native event schema | avoid falsely treating compacted history as continuous context |
| Turn | user-message trigger and its linked turn ID | rollout plus index | request → response → execution cycle |
| Work episode | a coherent objective, checkpoint, recovery, or handoff | coded turn sequence | unit for cross-case comparison |
| Micro-event | tool/coordination/state record | index and bounded event review | evidence for execution, interference, or recovery |

The audit should begin from top to bottom, then revisit lower-level events only
when a higher-level claim needs evidence. This prevents both transcript-only
reading and misleading event-count analysis.

## Open Segmentation Questions

1. How consistently can `turn_id` link a user trigger, assistant response, and
   tool activity across different Codex rollout variants?
2. Does compaction mark a genuine collaboration discontinuity, merely an
   internal context replacement, or both?
3. Which multi-agent metadata indicates delegation versus only runtime status?
4. Can task-packet references be aligned with a work episode without assuming
   the referenced file was current, read, or followed?
5. What minimum event-derived facts can be recorded privately to support later
   reproducibility without retaining raw message text?
6. Why do seven cases have no resolved packet attachment despite task-like work,
   and how should the audit distinguish absent association from a failed or
   unsupported association?
