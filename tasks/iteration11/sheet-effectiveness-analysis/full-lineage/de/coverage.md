# D/E coverage ledger

## Scope

Source root: `tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4`

Machine inventory: `../inventory/inventory.json`, `../inventory/records.jsonl`. The inventory parser opened every source JSONL line with the source path preserved. It found 565 JSONL files / 38,414 records overall, parse errors 0. The D/E slice below is the complete work-item slice, not a basename-deduplicated sample.

## Complete slice totals

| work item | native files | records/lines | bytes | cwd/identity treatment | semantic status |
|---|---:|---:|---:|---|---|
| `issue:6` | 9 | 818 | 2,314,352 | canonical provider + session headers + continuation, each path distinct | program parse complete; semantic excerpts #220/#221/#227/#289/#294/#302/#304 and D Pi advisor |
| `pr:11` | 20 | 1,576 | 5,717,392 | provider sessions, 3 vision subagent paths, continuations distinct | program parse complete; implementation handoff, first-failure, second-pass, D→E and stability excerpts |
| `issue:7` | 44 | 2,581 | 12,973,282 | provider sessions, vision/advisor artifacts and continuations distinct | program parse complete; #314/#323/#331/#355/#362/#375/#377/#396/#427/#470/#521 excerpts |
| `pr:12` | 9 | 1,129 | 4,596,711 | canonical PR session + later continuation sessions distinct | program parse complete; gate, RT/rowMap, sentinel and final handoff excerpts |
| `pr:13` | 4 | 415 | 1,498,064 | mainline sessions distinct | program parse complete; final candidate/merge excerpts |
| `pr:14` | 3 | 52 | 97,270 | stability PR and continuation distinct | program parse complete; merge and close excerpts |
| **total** | **89** | **6,571** | **27,257,071** | no basename collapse | complete D/E + integration slice |

The 6,571 records above include assistant/user messages, tool calls, tool results and session records. Repeated code snapshots and delayed polling notifications remain present in the raw source and are counted; `report.md` cites the first decision/result and records supersession where relevant.

## Semantic reading batches and omission boundary

The complete scan was a local Python JSONL parse used for counts, source-path identity, physical line numbers and msg ids. It does **not** mean that all 27,257,071 bytes entered model context or received semantic interpretation. The actual semantic batches were:

1. DB read-only schema/count/association/activity queries: work-item status, eight association rows, creation/assignment/link/merge/close ordinals, and current comment lifecycle counts.
2. Derived collaboration navigation: D/E/PR11–14 comment ranges and selected root comments (#220/#221/#227/#289/#294/#302/#304, #314/#323/#331/#355/#362/#375/#377/#396/#427/#470/#521/#523/#558/#564/#567/#570/#571/#572/#574/#576/#582/#583/#588/#589). These were used for visible decisions and state transitions; the derived exports remain navigation, not the native source.
3. Native semantic excerpts: the anchor provider lines listed below for D design/implementation, E design/implementation, PR13/14 close, plus E continuation lines 53–69 for the failed multi-ID unresolve and subsequent per-ID recovery.
4. Pi subagent artifacts: D state/paste advisor, D vision transcripts, E pivot/filter advisor and vision, E sentinel advisor, E display-value advisor. The model read their decision-bearing text, not image binary or every tool transcript.

Omitted from model semantic reading: duplicate canonical/session snapshots; delayed polling notifications already marked superseded; full source-code dumps and long test/evidence logs; image binary payloads; unrelated A/B/C files outside the D/E integration slice. Their presence and source locations are still counted/indexed here. Any conclusion about a message not cited in the semantic batches is therefore a program-parse/navigation fact, not a claim of full human/model reading.

## Key raw source locations

The following are relative paths under the source root. Line numbers are JSONL physical lines.

| evidence | source location | use |
|---|---|---|
| D Issue owner advisor | `work/native-homes/pi-glm-fast-01a0ec7d-7062-7913-82da-2f5f9fa60d71/subagent-artifacts/b06382e6-058c-41d4-b47b-792e9c028955_advisor_transcript.jsonl` | state restore already covered; paste transaction and D scope |
| D Issue owner final close | `work/native-homes/pi-glm-fast-01a0ecbb-18b9-79c3-bb99-723f5c502853/sessions/.../2026-09-29T10-34-41-750Z_...jsonl:21` | Issue #6 closed; residuals transferred to E |
| D PR implementation | `work/native-homes/pi-deepseek-fast-01a0ec8e-37ae-7b63-9278-6357cf71c4a9/2026-09-29T09-45-39-523Z_...jsonl:218` | PR #11 scope/base/final handoff |
| D PR implementation | same line has native msg id `48f96560` | exact msg identity for the handoff |
| D second implementation pass | `work/native-homes/pi-deepseek-fast-01a0ecaa-199b-7701-b736-37d7c5869b5a/2026-09-29T10-16-10-675Z_...jsonl:177` (msg `ae84b3da`) | #247 §1 e2e gap and candidate 5b3a514 |
| D→E impact follow-up | `work/native-homes/pi-deepseek-fast-01a0ecbb-dfc2-7291-a3a2-7276441b0b13/2026-09-29T10-35-31-459Z_...jsonl:53,73,88,95` | sentinel, B preview, contract #375, E-D8 receipt |
| E Issue design/close | `work/native-homes/pi-deepseek-fast-01a0ecbb-ccb6-77e1-b369-df370111d350/2026-09-29T10-35-26-785Z_...jsonl:139` | #331 design and handoff |
| E pivot/sentinel advisor | `work/native-homes/pi-deepseek-fast-01a0ecca-0119-7532-a2c3-6b0a196170ed/subagent-artifacts/744ec1d7-fe82-4f37-b1f9-9a9ad33da3da_advisor_transcript.jsonl` | raw-range plan rejected; sentinel selected |
| E display seam advisor | `work/native-homes/pi-deepseek-fast-01a0ecca-0119-7532-a2c3-6b0a196170ed/subagent-artifacts/9ba8b682-0440-4c52-8d35-e4781a35e855_advisor_transcript.jsonl` | display value and `valueFor` implications |
| E context-state correction | `work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_...jsonl:53–69` (msgs `bd1f3d9d`, `1a02d6be`, `01f7b9ae`) | multi-ID `unresolve` failure, per-ID recovery, #470 correction |
| E PR implementation | `work/native-homes/pi-deepseek-fast-01a0ecc7-f2f1-7dc3-a204-8742c8e202ac/2026-09-29T10-48-42-721Z_...jsonl:697,711` | candidates 42f9c5b/422f718 and final handoff |
| E PR implementation msg ids | line 697 `4c8007db`; line 711 is the later same-session final handoff | source identity retained separately from comment ids |
| PR #14 stability | `work/native-homes/pi-glm-fast-01a0ee33-33cc-71c3-930e-8fcabdb592ec/2026-09-29T17-25-54-187Z_...jsonl:26,30` | 18cfeab evidence and merge 2dc4b9f |
| PR #13 final | `work/native-homes/pi-deepseek-fast-01a0efff-7173-7ff0-967a-9e619f01d259/2026-09-30T01-48-34-507Z_...jsonl:156,164` | final 5926059, main 10cba2a |
| PR #13 / #14 native msg ids | PR #13 line 156 `dd4d479c`; PR #14 line 26 `4e5e13ac` | native ids are not substituted by derived comment numbers |

## Collaboration and lifecycle anchors

These are physical lines in the derived comment export, retained as navigation only; the comment bodies were traced back to native records where available.

| event | anchor |
|---|---|
| D handoff PR #11 / D-D1…D-D4 | `evidence/comments.md:4783` comment #220; #221 immediately after |
| D copy-bounds and move corrections | `evidence/comments.md:4795` #221; #227; root contract #232/#242 |
| D first candidate and final 46-pass handoff | `evidence/comments.md` #289/#294/#302/#304; native `pr:11` second pass above |
| D→E paste gate/state/pivot seam | `evidence/comments.md:6975` comment #314; #323 at 7169 |
| E design, empty-range conflict and reconsideration | `evidence/comments.md:7359` #331; #355 at 7905; #362 at 8080 |
| E sentinel and display-value/RT rulings | #377, #396, #427; E handoff #516/#521 |
| C rowMap negative mapping correction | PR #12 #455/#473/#486; Issue #7 #451/#459/#480 |
| PR #12 merge and B regression receipt | #521/#523/#527/#558/#564/#567 |
| D shortcut timing root cause and PR #14 | PR #11 #553/#570/#576; PR #14 #571/#572/#574 |
| PR #13 final candidate/main merge/root close | #582/#583/#586/#588/#589 |

## Explicit gaps and non-claims

- Two early exclusive paths have a final-source/index-versus-local-increment coverage discrepancy. The original files remain in the local increment and the older full-read ledger covers them; they are not whole-corpus-missing and their contents were not inferred from absence.
- The DB has no description-history or relation-history table and stores only current comment lifecycle. Resolve/hide evolution is therefore sourced from native JSONL plus `local_activity`; the current export alone is insufficient.
- Tool outputs containing large code or duplicate snapshots were not copied into this artifact. They remain addressable by source path and physical line in inventory records; only semantically new assistant decisions, commands and results are summarized.
- No claim here uses the 59-point score, hidden evaluation behavior, or application bug as causal evidence for D/E.
