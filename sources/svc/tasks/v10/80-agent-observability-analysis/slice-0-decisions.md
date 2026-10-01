# Slice 0 Product Decisions

Status: frozen task-local contract on 2026-07-28. Implementation evidence may
return a decision to Slice 0, but an implementation slice must not silently
reinterpret it.

## Decision Register

| ID | Decision | Frozen answer |
| --- | --- | --- |
| `D1` | Public command grammar | Keep `list` and `export`; add the verb `analyze`. `analysis` is the product capability. Add no public `browse` or separate `analysis` command family in v1. |
| `D2` | Interactive entry | `analyze` with no selector/input requires a TTY and opens the local thread navigator before analysis. The explicit command is the sensitive-rendering acknowledgement. |
| `D3` | Safe inventory | Existing plain/JSON `list` envelope and descriptor keys stay schema-v1 and non-sensitive. Add `--archive-state` with `active`, `archived`, or `all`, defaulting to `all`; filtering happens before the safe-result limit. Honest `unknown`/`unavailable` source-state values may replace an old path-based guess as part of the MAJOR change. |
| `D4` | Interactive inventory | The navigator defaults to `active` and can switch to `archived` or `all`. It may render bounded workspace, title, and first-user-message values but never logs, caches, or emits them as diagnostics. |
| `D5` | Artifact | Normal `export` becomes a schema-v2 ZIP containing exactly `manifest.json` and `trajectory.jsonl`. It contains no provider-native transcript, old structural index, task file, or derived analysis member. |
| `D6` | Sensitivity | Normalized content still contains private messages/tool data, so persistent export continues to require `--include-sensitive`. V1 makes no heuristic secret-redaction promise; it relies on explicit acknowledgement, structural noise removal, and declared bounds. |
| `D7` | Raw behavior | V1 exposes no raw/debug export mode. The old raw ZIP is superseded rather than kept as an attractive compatibility path. |
| `D8` | Schema-v1 archive cut-off | Schema-v1 SVC archives are unsupported inputs. V1 adds no legacy reader, converter, re-export selector, or transition path. Once a bounded root manifest identifies that format, `analyze --input` fails `unsupported-agent-thread-bundle-schema` before opening another member; users must recollect from an available provider-local source. |
| `D9` | UI technology | Use Textual `>=8.2.8,<9` without syntax/textual-dev extras as the v1 human UI runtime. Both selector and analysis TUI consume render-neutral models; safe list and JSON paths do not instantiate Textual. |
| `D10` | Workspace grouping | Use provider-reported CWD as sensitive provenance, not ownership. Parse its native path flavor lexically, do not resolve/walk it, and group missing values under an explicit unknown workspace. |
| `D11` | ccxray | ccxray remains a design reference only. This task adds no proxy, external observation source, Node/browser server, account integration, ccxray identifier, or copied implementation/schema. |
| `D12` | Provider scope | Codex is the only production adapter in v1. Provider-neutral contracts and a second synthetic provider shape prove the seam; a second real provider is not a deliverable. |
| `D13` | Source/result status | A successfully published manifest uses one of `stable`, `grew`, `changed`, or `displaced` for `source_status`, and either `ready` or `partial` for `result_status`. Open/authority/containment failures publish nothing. Expected append growth or a changed/displaced descriptor-bound source may publish valid partial evidence with diagnostics. |
| `D14` | Analysis scope | V1 provides deterministic projections, a Textual human surface, and compact Agent-facing JSON for one thread. Results are composable, but automated cross-thread/corpus synthesis and model-generated conclusions are deferred. |
| `D15` | First implementation slice | Slice 1 is the safe inventory core: split lifecycle/availability, add safe archive filtering, and test large inventories without selecting private recognition columns. The bounded sensitive projection stays frozen but is materialized only with its Textual consumer. Slice 1 does not modify archive publication or add Textual. |
| `D16` | Release | Replacing the released default export is an ordinary MAJOR change. The consumed 10.0.1 exception is not reused; the implementation prepares a migration guide and pending MAJOR release policy. |

## Public Grammar

```text
svc telemetry agent-thread list \
  [--archive-state active|archived|all] \
  [--codex-home <path>] [--limit <1-100>] [--json]

svc telemetry agent-thread export \
  (--thread-id <id> | --source <rollout.jsonl>) \
  --output <bundle.zip> --include-sensitive \
  [--repo <path>] [--codex-home <path>] [--json]

svc telemetry agent-thread analyze \
  [--input <schema-v2-bundle.zip> | --thread-id <id> | --source <rollout.jsonl>] \
  [--archive-state active|archived|all] [--codex-home <path>] [--json]
```

Rules:

- `list` defaults to the released `all` behavior and retains its existing
  output shape and its 1–100/default-20 limit. The new filter is additive.
- `analyze` with no input/selector opens the navigator only on a TTY; otherwise
  it fails with a stable actionable error. Its interactive selector defaults to
  `active`.
- `--input`, `--thread-id`, and `--source` are mutually exclusive. Supplying
  none selects the interactive flow.
- `--archive-state` is valid only for the no-selector interactive flow;
  explicit bundle/thread/source analysis rejects it rather than ignoring it.
- `--codex-home` is invalid with `--input`, which is provider-home independent.
- `analyze --json` requires an explicit input or selector and never starts a
  TUI.
- Without `--json`, both interactive selection and explicit-input analysis
  require a TTY and open the Textual analysis surface; a non-TTY fails with
  guidance to use `--json`.
- `analyze --input` accepts only an exact schema-v2 normalized bundle.
- Once a bounded root manifest identifies a schema-v1 archive, validation fails
  `unsupported-agent-thread-bundle-schema`; its native member, index, and task
  files are never opened or interpreted.
- Direct local analysis is ephemeral: it uses the same normalizer and analysis
  engine but publishes no bundle unless the user separately invokes `export`.
- `--repo` remains an explicit output-containment boundary. It no longer causes
  automatic task-packet discovery or copying.

## Explicit Deferrals

- A second production provider.
- Static HTML, hosted/local Web server, or browser dashboard output.
- Automatic cross-thread/cohort synthesis.
- Embedded LLM calls, network analysis, or authoritative quality/causal scores.
- New raw capture and automatic task-directory attachment.
- Dynamic provider/plugin discovery.
