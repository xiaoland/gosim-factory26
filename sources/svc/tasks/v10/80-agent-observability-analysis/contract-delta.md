# Agent Observability Contract Delta

Status: Slice 0 frozen task-local product decision. It does not supersede
durable product truth until each authorized implementation slice updates the
canonical owner before realizing its corresponding behavior; the release slice
performs the final ownership audit.

## Governing Correction

SVC agent observability exists to help maintainers improve SVC from real
human-Agent collaboration. It is not an audit archive product.

That purpose changes the desired default:

```text
provider-local thread
        |
        v
collect and normalize intentionally useful evidence
        |
        v
human and Agent analysis
        |
        v
supported changes to SVC
```

Preserving provider bytes has value only when it improves this loop. It is not
an end in itself.

## Observable Contract Delta

| Concern | Released/current contract | Target contract | Compatibility consequence |
| --- | --- | --- | --- |
| Product purpose | Export a complete provider-obtainable local source for inspection | Produce bounded evidence for analysis that improves SVC | Durable product truth must change before implementation |
| Default export | Byte-preserved provider member inside a ZIP | Provider-neutral normalized trajectory plus explicit manifest | Existing archive consumers cannot assume the same member layout |
| Completeness | Source hash/size and byte identity are central proof | Useful record coverage and declared loss are central proof | “Complete” must not describe the new default |
| Provider envelope and UI events | Retained when present in native source | Dropped when they do not improve analysis | Loss is intentional and counted |
| Tool arguments and results | Copied with the raw source after sensitive acknowledgement | Useful content retained under exact bounds; oversized/noisy content truncated or dropped and counted | Exact replay is not promised; v1 claims no heuristic secret redaction |
| Raw provider transcript | Normal archive member | Absent from normal export, with no new raw/debug command | Native-source consumers must migrate |
| Existing schema-v1 archive | Released raw ZIP can be manually inspected or consumed by external tooling | Unsupported input with no converter or compatibility reader | Direct cut-off; recollect from a provider-local source when still available |
| Source mutation while reading | Hard failure protects byte fidelity | Safety violations still fail; data-quality change may yield an explicitly partial result | Consumers use the new source/result status contract |
| Task packet | Complete selected subtree may be copied | Only bounded lexical relative references may be recorded | Task files are never scanned or copied |
| Analysis | User manually inspects an archive | Human- and Agent-readable analysis is a first-class capability | Public command and result contracts are new |

## Invariants That Do Not Depend on Audit Fidelity

The redesign must preserve:

- local, explicit thread selection
- no automatic collection or network egress
- no source or selected-repository mutation
- absent output destination and no overwrite
- path and symlink containment
- private output permissions
- bounded memory, record size, and artifact size
- safe non-interactive inventory by default
- provider-neutral core semantics
- diagnostics that do not repeat dropped sensitive values

## Cut-off Policy

- The new ZIP is schema v2 and carries its own trajectory and normalizer
  versions. Its only members are `manifest.json` and `trajectory.jsonl`.
- V1 exposes no legacy reader, archive converter, re-export selector, raw/debug
  command, or hidden compatibility path.
- `analyze --input` accepts only an exact schema-v2 bundle. Once a bounded root
  manifest identifies a schema-v1 archive, validation fails
  `unsupported-agent-thread-bundle-schema` before any provider member, old
  index, or copied task file is opened.
- The cut-off is intentional: an old archive can be replaced only by collecting
  again from an available provider-local source.
- The safe `list` JSON envelope and descriptor keys remain schema v1. Its
  internal truth stops inferring archive state from paths; therefore
  `source_state=unknown` can appear where an old implementation guessed. This
  semantic correction is part of the MAJOR migration, not a silent claim of
  byte-for-byte list compatibility.
- Publish a packaged migration guide with the behavioral release. It must cover
  the command grammar, ZIP members, loss/completeness semantics, list lifecycle
  semantics, task-packet removal, the schema-v1 cut-off, recollection guidance,
  and the absence of a raw replacement.

Replacing the released default raw archive and completeness promise changes a
stable CLI/archive contract and default behavior. Under ordinary SVC Behavioral
SemVer, the classification is **MAJOR**. The consumed 10.0.1 exception cannot
be reused. This task packet deliberately does not assign the numeric release
while other release-pending work exists.

## Ownership Impact

| Truth | Durable owner after implementation | Admission rule |
| --- | --- | --- |
| SVC purpose, public behavior, safety, and command examples | `src/index.md`, projected for package users in `README.md` | Update canonical truth first in each behavior-changing slice and keep the projection synchronized |
| Inventory, bundle, and analysis schemas | Runtime models/validators under `svc_cli/telemetry/` plus contract tests | Prefer executable schemas and tests over a new technical document |
| Codex field and rollout mappings | `svc_cli/telemetry/providers/codex_rollout.py` plus provider fixtures | Provider-local authority stays out of product prose |
| Textual runtime dependency | `pyproject.toml` and `pdm.lock` | Add only when the Textual slice supplies a public consumer and headless proof |
| Migration and behavioral release | A packaged `src/migrations/*.md` guide, `src/manifest.json`, and the release fragment | Required by the ordinary MAJOR policy |
| Non-trivial operational recovery, if implementation proves it exists | `src/sections/deployment.md` | Do not add content merely because the feature is called observability |

No Product TDD, Unit TDD, ADR, template, plugin surface, or provider registry
expansion is admitted by Slice 0. Code, schemas, and tests remain the preferred
technical owners unless implementation makes an expensive cross-unit contract
impossible to recover.

This repository's `src/index.md` is explicitly the SVC framework-purpose and
public-CLI owner and already owns `agent-thread`; `README.md` is its public
projection. `src/sections/prd.md`, `product-tdd.md`, and `deployment.md` are
framework guidance about consumer knowledge owners, not buckets for SVC runtime
feature detail. Cross-unit bundle/analysis contracts will be executable
schemas/validators plus tests under `svc_cli/telemetry/`; a new durable
technical document is admitted only if those mechanical owners prove
insufficient. This routing is deliberate, not an unresolved owner.
