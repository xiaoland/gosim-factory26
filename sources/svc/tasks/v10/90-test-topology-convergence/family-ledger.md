# Test Family Ledger

> Historical family map. The current cost/value decision and static ownership
> are in [`roi-reassessment.md`](roi-reassessment.md) and
> [`static-gate-decision.md`](static-gate-decision.md).

## Authority and Scope

`pdm run test` is the authoritative baseline: 213 passing unittest cases.
The per-file count below was obtained with the PDM environment's
`unittest.TestLoader().discover(...)`; it corrects the earlier 97/115
telemetry estimate to **105 telemetry + 18 harness = 123 cases**.

The ledger groups a family only where its tests share a consumer, failure mode,
and oracle. A group is not a deletion proposal. Its historical “retain” label
only meant that no equivalent lower-cost proof had yet been demonstrated; it
was not a completed cost/value decision.

```text
Codex source / SQLite / rollout file
            │ provider-specific mapping and physical safety
            ▼
canonical trajectory ──► archive publication ──► CLI / navigation / TUI
      │                        │                         │
      └──── analysis core ─────┴──── installed-wheel black-box harness
```

## Repository Families

| Family (cases) | Consumer and layer | Named failure mode / oracle authority | Current disposition |
| --- | --- | --- | --- |
| `test_build_monolith.py` (9) | Source-corpus build contract | Broken local Markdown paths, fragments, and anchor rewrites; builder is the oracle | Retain; distinct deterministic builder failures |
| `test_catalog.py` (4) | Wheel/catalog projection | Canonical corpus not represented exactly once in the distributable package | Retain; packaging boundary |
| `test_config.py` (7) | Configuration core | Invalid/ambiguous config adoption, merge, or filesystem ownership | Retain; pure contract plus filesystem safety |
| `test_project.py` (11) | Consumer-project integration | A plan/apply transaction mutates consumer data incorrectly or fails rollback | Retain; transaction boundary |
| `test_cli.py`, `test_lookup.py`, `test_update.py` (10) | Public non-telemetry CLI | JSON identity, plan binding, corpus integrity, or self-update trust failure | Retain; public-command boundary |
| `test_dev_identity.py`, `test_dev_runtime.py`, `test_dev_setup.py` (16) | Local development runtime | Probe, lock, setup, or worktree identity failure | Retain; independent operational risks |
| `test_framework_contract.py`, `test_release.py`, `test_workflows.py` (33) | Framework/release governance | Durable protocol, release, or workflow declaration drifts from executable policy | Defer audit; these are contract tests, but not part of the telemetry topology's first slices |

## Telemetry and Acceptance Families

| Family (cases) | Consumer and layer | Named failure mode / oracle authority | Overlap decision |
| --- | --- | --- | --- |
| `test_telemetry_trajectory.py` (11) | Pure trajectory contract | Canonical JSONL, IDs/order, bounded collection, strict schema, manifest and schema-v1 rejection; core validator/canonical serialization | Retain as the lower-layer contract oracle. Archive/harness checks add publication or black-box semantics. |
| `test_telemetry_analysis.py` (8) | Pure analysis contract | Q1–Q10 facts, partial/unknown treatment, bounds, determinism, references, and bundle authority; analysis validator | Retain. CLI tests own public input/output and render-neutral import behavior, not the same failure model. |
| `test_telemetry_archive.py` (8) | Archive integration | Deterministic restrictive ZIP, cap accounting, ephemeral/export equivalence, no overwrite/unsafe parent, and no artifact after provider failure | Retain. It reuses trajectory facts only to prove publication semantics. |
| `test_telemetry_codex_rollout.py`: source mapping (5) | Codex adapter | Provider session/response fields map to canonical records, malformed/noise handling, task-reference eligibility, and source limits | **Focused in Slice 2.** It owns native field-path mapping; orphan-result and sink-limit subsets were removed. |
| `test_telemetry_codex_rollout.py`: inventory/state safety (24) | SQLite/filesystem provider integration | Metadata-only projection, source availability, safe ID/path/descriptor/reparse/race behavior, ordering/filtering, and bounded sensitive projection | Retain. Direct helper coverage is justified only where it protects a physical privacy or atomicity boundary; revisit the incidental portions in Slice 3. |
| `test_telemetry_codex_trajectory.py` (12) | Canonical Codex normalizer/stream | Canonical relationship/loss classification, deterministic identities, opaque reasoning, streaming growth, linkage and task-ref caps | **Focused in Slice 2.** It owns canonical order/source refs plus the stronger orphan-result and record-limit proofs. |
| `test_telemetry_cli.py`: export/analyze (7) | Public CLI/service integration | Acknowledgement/redaction, direct-vs-bundle equivalence, option/TTY order, schema-v1 opening discipline, and no Textual import on JSON paths | Retain as a user-visible integration boundary. |
| `test_telemetry_cli.py`: listing (7) | Public CLI/service integration | Safe metadata projection, archive filter, human/JSON warning redaction, and missing/corrupt state behavior | Retain. It is intentionally distinct from provider SQL tests. |
| `test_telemetry_navigation.py`: model (12) | Pure navigation model | Bounded immutable rows, archive filtering, lexical workspace parsing, tree labels/order/escaping, stale generations and selected-thread continuity | Retain. The cap check is a cheap model proof; TUI owns lazy interaction. |
| `test_telemetry_navigation.py`: structure (1 plus assertions within workspace test) | Static module boundary | `navigation` must not import UI/provider/filesystem dependencies, and lexical parsing must not start filesystem traversal | Replace source-substring inspection with a dedicated AST boundary gate in a later, separately approved CI/tooling slice. |
| `test_telemetry_tui.py` (8) | TUI integration / human acceptance proxy | Lazy tree, unavailable selection, keyboard/filter/resize/quit, stale loader rejection, cancellation/redaction, capacity, selection and partial-loss presentation | Retain dynamic interaction. Later move assertions from private widget/status names to visible render/state outcomes where that preserves the exact user contract. |
| Harness input/lifecycle: `test_accept_agent_thread.py` (5) | Installed-wheel harness safety | Argument/report bounds, SHA staging race, wheelhouse validation, no-shell execution | Retain; harness owns this orchestration boundary. |
| Harness individual successful slices (4) | Installed-wheel harness unit seam | Each of inventory, bundle, analysis, and UI starts an isolated accepted run and reports only its public summary | **Slice 1A:** exact repeated wheel/venv/patch/cleanup scaffolding; parameterize while retaining one slice-specific assertion each. |
| Harness `all` ordering (1) | Installed-wheel harness orchestration | The aggregate invocation uses inventory → bundle → analysis → UI command order | Retain separately; this is not an individual-slice success case. |
| Harness adversarial bundle/schema (3) | Installed-wheel black-box safety | Extra member, private stdout, and schema-v1 probe behavior fail closed without leaking details | Retain. Independent golden/adversarial evidence is required before touching deep harness validation. |
| Harness install/venv/case/cleanup failures (5) | Installed-wheel harness safety | Installation whitelist, precondition, case failure, and cleanup exit semantics | Retain; distinct cleanup/error paths. |

## Exact Adjacent Duplicates Identified

Slice 2 completed the following replacement relationships without a shared
fixture or product change:

| Provider case | Normalizer case | What is duplicated | What remains distinct |
| --- | --- | --- | --- |
| rollout `:80` | codex-trajectory `:22` | One explicit source produces meta/message/tool records | Both remain, narrowed: rollout owns field paths; stream owns order/source identity. |
| rollout `:103` | codex-trajectory `:47` | Result-before-call is unresolved | Rollout subset removed; stream retains unresolved order and deterministic IDs. |
| rollout `:141` | codex-trajectory `:392` | Sink record limit makes the result partial | Rollout subset removed; stream retains exact record-limit diagnostics. |

The harness has a more serious authority duplication: it independently declares
record fields, manifest/loss/count keys, policy bounds, and analysis shape in
[`tools/accept_agent_thread.py`](../../../tools/accept_agent_thread.py), while
the core owns the equivalent trajectory and analysis validators. Its synthetic
fixture repeats that representation again in
[`test_accept_agent_thread.py`](../../../tests/test_accept_agent_thread.py).
The previous `rate_limit_noise` classification drift proves the duplicate can
become stale. Nevertheless, the harness may not simply import the core as its
oracle: it needs a small independent frozen golden and adversarial probes to
remain a real installed-wheel acceptance boundary.

## Static vs Dynamic Responsibility

Static ownership is appropriate for import/layer restrictions and syntactic
filesystem-prohibition claims. It is not evidence for SQLite query privacy,
descriptor identity/races, ZIP permission/publication, error redaction,
installed-wheel isolation, or Textual keyboard/terminal behavior. Those remain
dynamic families even after a static gate exists.

## Selected First Slice: 1A — Harness Success-Path Scaffolding

**Address:** only
[`tests/test_accept_agent_thread.py`](../../../tests/test_accept_agent_thread.py),
the success-path tests currently at lines 675–897.

**From → To:** four copies of temporary wheel creation, fake venv creation,
`_command` patching, and cleanup assertions become one test helper plus a
table-driven/subtest matrix. Inventory retains the wheel digest assertion;
bundle retains bundle/trajectory redaction; analysis retains the installed
Textual and analysis-payload checks; UI retains UI-payload redaction. The
aggregate `all` order test remains a dedicated test and reuses only the same
setup helper.

**Invariant:** do not change the harness, fixtures, schema validator, fake
command semantics, negative cases, product behavior, dependencies, or CI.
The installed-wheel boundary, privacy assertions, cleanup proof, and command
order stay present.

**Verification:** focused harness module, then `pdm run test`; compare the
post-change case count only as a by-product, not a target. A later slice must
build a real wheel and run the unmocked harness.
