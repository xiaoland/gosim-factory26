# Verification Plan

Status: the frozen proof matrix and every automatic gate passed on 2026-07-28.
The only open evidence is hands-on terminal experience; these claims cannot be
weakened without returning to the decision register.

## Inventory Contract

| ID | Claim | Objective proof |
| --- | --- | --- |
| `INV-01` | Safe list shape survives | With no filter, plain and JSON output retain schema-v1 envelope/descriptor keys, default to `all`, and contain no recognition values |
| `INV-02` | Lifecycle filtering precedes limits | Mixed active/archived/unknown fixtures prove `active`, `archived`, and `all`; archived-only results are not starved by newer active rows |
| `INV-03` | Lifecycle and availability are independent | Every row in the frozen Codex inspection table covers active/archived crossed with available/missing/unavailable plus unknown lifecycle, without path-based inference |
| `INV-04` | Safe queries never materialize recognition content | A recording SQLite fixture proves the safe projection does not select CWD, title, first message, preview, reasoning, or tool/message content |
| `INV-05` | Unsafe rows remain isolated | Invalid/oversized IDs and escaping/oversized paths, in-home final/parent symlinks, and Windows reparse paths do not consume a safe result slot and produce only the aggregate redacted warning |
| `INV-06` | Identity, ordering, and compatibility projection are deterministic | SQL bound-plus-one projections, integer sec/ms, invalid/null/ties, Unicode IDs, same/cross-lifecycle duplicate IDs omitted in every filter, and the exact internal-facts-to-`source_state` table are frozen |
| `INV-07` | Sensitive values are bounded at their source | Provider fixtures later prove 4,096/160/512-code-point bounds and truncation flags without retaining discarded suffixes |
| `INV-08` | Large trees remain navigable | A render-neutral 5,000-row model and Textual Pilot fixture prove lazy expansion, stable selection, filtering, and an explicit truncation state |
| `INV-09` | Recognition data is useful only after explicit entry | Duplicate/similar titles are distinguished by bounded workspace/title/first-message values in the TUI, while logs, diagnostics, JSON list, and clipboard remain clean |

Lifecycle-column absence or invalid values must yield `unknown`; no test may
restore archive inference from `rollout_path`. Unknown lifecycle participates
only in `all`. A missing rollout remains eligible for its true lifecycle filter
even though the schema-v1 `source_state` projection is `missing`.

## Trajectory and Bundle Contract

| ID | Claim | Objective proof |
| --- | --- | --- |
| `TRJ-01` | Bundle layout is exact | ZIP inspection finds exactly `manifest.json` and `trajectory.jsonl`, fixed entry metadata, and no native transcript/index/task/analysis member |
| `TRJ-02` | Normalization is provider-neutral | Codex plus a synthetic second provider shape map to the same seven record types without native fields becoming core authority |
| `TRJ-03` | Encoding and evidence identity are deterministic | Repeated runs freeze JSONL bytes, record IDs/order, trajectory hash, semantic manifest projection, thread/status-sensitive bundle ID, native/synthetic/duplicate-call ref framing, and tool linkage |
| `TRJ-04` | Intended loss is observable | Envelope/UI/rate-limit/duplicate-noise fixtures are absent from records and present in bounded class/count diagnostics; over-256 diagnostic groups freeze first-255 plus final-limit ordering and suppressed occurrence counts |
| `TRJ-05` | Bounds are exact | Boundary-minus-one/exact/plus-one or proportional streaming cases cover every input/container/depth/record/content/cardinality/diagnostic bound and POSIX/drive/UNC/URI task-reference rejection rule in the schema |
| `TRJ-06` | Tool evidence remains honest | In-order, result-before-call, duplicate ID/result/explicit occurrence link, missing-ID synthesis, missing-result-ID linked to native/synthetic calls, invalid arguments, pending, orphan, error, and truncated-result cases freeze exact IDs/linkage/outcomes |
| `TRJ-07` | Capability/loss absence is not fabricated | Every exact capability value and fixed loss/count map validates and drives `unavailable` rather than invented records |
| `TRJ-08` | Source races are explicit | Stable, grew, changed, displaced, interrupted, and safely unopenable sources produce the frozen status or no-artifact behavior |
| `TRJ-09` | Diagnostics do not leak discarded values | Credentials, absolute paths, native IDs, messages, tool values, and oversized suffix sentinels are absent from errors/manifests |
| `TRJ-10` | Schema-v1 archives fail closed | When a bounded root manifest identifies schema v1, `analyze --input` fails `unsupported-agent-thread-bundle-schema` before opening any native, index, or task member; no reader, converter, or re-export path exists |

Resource tests use synthetic sparse/streaming fixtures where possible; they do
not allocate the full bound in every unit test. At least one proportional
integration test observes peak memory and verifies that parsing is streaming.

## Analysis Contract

| ID | Claim | Objective proof |
| --- | --- | --- |
| `ANL-01` | Analysis is independent | A schema-v2 bundle analyzes after provider home/native transcript removal and with network/model calls disabled |
| `ANL-02` | Every projection answers a frozen question | The `AN-Q1` through `AN-Q10` fixture families assert exact `analysis-schema.md` values and `analysis-algorithms.md` outputs, including thresholds/conflicts |
| `ANL-03` | Derived claims remain traceable | Every non-availability finding references an existing same-bundle record/index triple; result-before-call late-link refs remain in record order and all candidate/metric tie orders are stable |
| `ANL-04` | Agent JSON stays compact and non-duplicative | Executable-schema validation plus every per-class/2-MiB boundary and content sentinels prove metrics/findings do not copy messages, reasoning, arguments/results, workspace labels, or absolute paths |
| `ANL-05` | Loss propagates | Every relevant manifest loss/capability, nested/top-level analysis cap, late tool link, conflict, normal ready loss, and tail-destructive loss case produces the exact retained head/tail arrays and dimension/result status |
| `ANL-06` | Human UI is analysis, not transcript styling | Headless scenarios exercise overview, chronology levels, tool pairing, lanes, context changes, task/SVC signals, terminal state, and loss markers |
| `ANL-07` | JSON never starts Textual | Import instrumentation proves every `--json` path remains non-interactive and render-neutral |

## Private Aggregate Study

Use the existing eight private cases only outside Git. Record aggregate results:

- source events and emitted records by structural class
- dropped, truncated, unavailable, synthesized, and unsupported counts
- tool linkage, pending, orphan, duplicate, and outcome counts
- `AN-Q1` through `AN-Q10` dimension availability
- source/result status, artifact bytes, duration, and peak memory
- cases where the normalized evidence cannot support a promised projection

Do not commit provider archives, transcript fragments, titles, paths, thread
IDs, prompts, tool values, or case-identifying free text. The study can reject
an implementation or force a contract review; it cannot silently redefine the
product.

### 2026-07-28 Aggregate Result

The study driver remained outside the product: it extracted each private
schema-v1 archive's native source into an ephemeral directory and supplied that
file through the current explicit `--source` boundary. SVC itself gained no
legacy reader, converter, or archive transition path. Only these aggregates
were retained:

- 8/8 sources were `stable`; 8/8 normalizations were `ready`; analysis was
  `ready` once and `partial` seven times. No case failed, no partial source
  reason occurred, and `unsupported_record` was zero after all observed Codex
  structural shapes were deliberately mapped or deliberately dropped.
- 50,156 source events emitted 28,545 records: 8 meta, 2,947 message
  (261 user and 2,686 assistant), 8,413 reasoning, 8,081 tool call, 8,139 tool
  result, 493 context, and 464 event records.
- Deliberate drops were 50,156 provider envelopes, 12,394 UI events, 8,206
  rate-limit events, 120 world-state events, 46 absolute task references, and
  57 invalid task references. Truncation affected 8 context bodies, 11
  messages, 23 tool arguments, 2,730 tool results, and 1,352 suppressed
  diagnostic occurrences. Full reasoning was unavailable 9,181 times; no
  synthetic tool ID was required.
- Tool analysis observed 8,081 calls and 8,139 results: 521 success, 16 error,
  7,543 explicit-status-unknown, 59 orphan results, one pending call, 200 retry
  groups, and 2,730 truncated results. Unknown remains an honest absence of
  provider outcome rather than result-text inference.

| Dimension | Aggregate status across eight cases |
| --- | --- |
| coverage | 8 available |
| task evidence | 3 available, 5 partial |
| interaction transitions | 4 available, 4 partial |
| constraint evidence | 8 partial |
| tool outcomes | 8 partial |
| loop candidates | 1 available, 4 partial, 3 unavailable |
| lanes | 8 unavailable |
| terminal coverage | 4 available, 4 partial |
| SVC signals | 3 available, 5 partial |
| context changes | 8 partial |

The lane result is evidence, not a mapping failure: the 24,005 observed
passthrough metadata objects exposed only a turn ID and no actor, recipient,
parent, lane, or concurrency authority. The eight native sources totaled
108,176,912 bytes (569,569 minimum; 34,117,693 maximum). Aggregate execution
took 42,870 ms (14,747 ms maximum per case), and maximum observed traced memory
was 76,702,854 bytes. No case-identifying value or transcript fragment was
printed or committed.

## Cross-Platform Acceptance

The authoritative environment preconditions and host facts live in
[`acceptance-environments.md`](acceptance-environments.md). Final installed
wheel acceptance is:

| Environment | Required proof |
| --- | --- |
| Current macOS source tree | Targeted tests, full tests, build, CLI smoke, headless Textual, artifact inspection, and private aggregate study |
| `wsl.win-ws.localhost` | Fresh temporary Python 3 venv installs the wheel; safe list/filter, normalized bundle/schema-v1 rejection, Agent JSON, and headless Textual fixtures pass |
| `win-ws.localhost` | Fresh temporary Python venv installs the same wheel; equivalent safe/list/bundle/JSON/headless cases pass, followed by a manual Windows Terminal TUI check |

The two remote names reach one Windows machine, and their `F:`/`/mnt/f`
repository is the same stale worktree. Acceptance must not run against that
checkout or run mutable shared-drive cases concurrently. Build once from the
current branch, assert the same wheel SHA-256 on each host, use host-local
temporary directories through the bounded harness, prove cleanup, and run WSL
then Windows serially.

Final result: all four installed-wheel cases passed on macOS/Python 3.12.10,
WSL/Python 3.13.5, and Windows/Python 3.14.0 with wheel SHA-256
`f57fbe6a212a37ae49a8736f648667f0e42b6e56375c346546cebeae828af507`.
Each harness reported `cleanup=passed`; caller staging-prefix counts were zero
afterward. WSL then Windows ran serially, and neither used or mutated the stale
shared worktree.

## Repository and Package Gates

Each slice runs its targeted tests and `pdm run test`. Final completion also
requires:

```text
pdm run build-monolith
pdm build
pdm run svc --help
pdm run svc telemetry agent-thread list --help
pdm run svc telemetry agent-thread export --help
pdm run svc telemetry agent-thread analyze --help
pdm run python -m zipfile -l <wheel-or-bundle>
pdm run python tools/accept_agent_thread.py \
  --wheel <wheel> --expected-sha256 <sha256> \
  --wheelhouse <binary-wheelhouse> --slice <slice>
```

Package inspection must prove the migration guide and Textual dependency are
present, task packets/private fixtures are absent, and a fresh wheel has no
undeclared runtime dependency. Inspection also reads the wheel's
`METADATA`/`RECORD` through the standard library and asserts exact packaged
paths/dependency specifiers; listing alone is not sufficient. No release is
committed, staged, pushed, or published without Sir's separate explicit
command.

Final result: 224 pytest items plus Ruff, mypy, Import Linter, zizmor, release
check, monolith, sdist/wheel build, all CLI help smokes, `zipfile` listing, and
final review passed. The wheel contains 51 members, has zero `RECORD` errors,
catalogs and packages `migrations/11.0.0.md`, declares
`textual<9,>=8.2.8`, and contains zero task/test members, native JSONL files,
or `svc_cli/telemetry/task_packets.py`. Quality and test dependencies remain
development-only and are absent from wheel metadata.
