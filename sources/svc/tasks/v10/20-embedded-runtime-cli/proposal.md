# Proposed Design

## Product Boundary

SVC is a versioned knowledge corpus and a local development-collaboration tool, delivered in one CLI distribution. It does not install or own a consumer's documentation. A Coding Agent receives a small skill and navigation anchors that tell it to query the current packaged corpus when it needs SVC guidance.

```text
                     read-only, versioned
canonical SVC source ----------------------> installed svc CLI
       |                                          |
       | build catalog                             | lookup by name / keyword / semantic capability
       v                                          v
  source review                              Coding Agent
                                                   |
                                                   | consumer-owned changes
                                                   v
project AGENTS.md / docs/index.md <--- svc init --- svc.json
```

The crucial separation is:

- `svc self-update` changes the installed tool.
- project adoption changes `svc.json` after the agent applies the release's migration guide to consumer-owned material.
- neither action gives SVC write authority over the consumer's actual knowledge documents.

## Repository Topology

```text
src/                              canonical SVC core only
  index.md
  sections/
  assets/
  migrations/                     release guidance, when introduced

svc_cli/                          Python runtime package
  cli.py
  catalog.py
  lookup.py
  project.py
  plans.py
  integration.py
  update.py
  data/                           wheel-only release projection

tools/                            repository-only build and verification code
  build_monolith.py
  build_catalog.py

tests/
pdm_build.py                      thin PDM hook delegating to tools/
```

`src/` is not a Python source-layout directory after this pivot. Its recursive, normalized content paths are the SVC corpus namespace. A packaged lookup resource such as `svc_cli/data/corpus/sections/working-protocol.md` is a build projection of `src/sections/working-protocol.md`, whose public lookup name is simply `sections/working-protocol.md`.

The catalog builder traverses the allowed canonical content types in `src/` deterministically, rejects hidden/unsafe paths, and emits a source-relative catalog. This avoids a second hand-maintained inventory: if a canonical Markdown document belongs in `src/`, it belongs in the lookup corpus. Runtime code and tooling cannot enter the corpus because they no longer live below `src/`.

## Minimal Project Metadata

Use the project root's `svc.json`:

```json
{
  "schema_version": 1,
  "svc_version": "10.0.0"
}
```

`svc_version` is the baseline the project says it has adopted, not an assertion that its consumer-owned documents are mechanically identical to SVC. `schema_version` is only the file-format compatibility marker; it is not project configuration.

## Corpus and Lookup

At package build time, canonical SVC Markdown becomes a catalog of stable entries. An entry contains its normalized source-relative path, title, corpus version, and digest. Its body exists once, as a matching read-only file in the packaged corpus; the catalog deliberately does not duplicate it. Canonical source remains the sole authoring owner. Runtime keyword ranking reads the local corpus deterministically, which is simpler and smaller than a premature serialized full-text index for this corpus size.

Initial interface:

```text
svc lookup --name 'assets/templates/AGENTS\.local\.template\.md'
svc lookup --name 'sections/(working-protocol|implementation-taste)\.md' --all
svc lookup --keyword "task packet mutation gate"
```

`--name` accepts a regular expression matched with full-path semantics over normalized, catalog-relative document paths. It returns a single document body by default and reports ambiguity; `--all` permits multiple matches. A literal path is expressed by an anchored/escaped pattern. `--keyword` is deterministic local text search with transparent ranking and returns concise result metadata/excerpts; callers resolve a selected result through `--name` to receive the authoritative body.

The first release deliberately does not expose `--semantic`: an unavailable public flag would be a stable surface with no user value. Internally, lookup uses one query/result model and isolated ranking implementations so a later semantic backend can be added without changing path-regex or keyword consumers. [`semantic-research.md`](semantic-research.md) records the future candidate and its constraints.

## Bootstrap Contract

`svc init [repo]` remains plan-first. The plan can perform only the following declared operations:

1. create `svc.json` when absent;
2. install the Codex skill at `.agents/skills/svc/SKILL.md`, an operational guide to use `svc lookup` and the rest of the CLI;
3. create root `AGENTS.md` when absent, or add/refresh its bounded SVC navigation block when present; and create `docs/index.md` when absent, or add/refresh its bounded marked block when present.

`AGENTS.md` and `docs/index.md` are Consumer-owned from their creation. Their initial bodies are only a minimal heading plus the marked SVC navigation block; all unmarked text is consumer-owned. The installed skill and every generated block have a stable marker and digest. A clean, earlier generated integration surface may be explicitly refreshed through the exact plan; if it has user edits, initialization blocks and reports drift rather than replacing it. Unmarked user content is never inferred to be SVC-owned. Re-running an unchanged plan is a verified no-op.

The first provider is Codex only. The installed skill is deliberately richer than a navigation stub: it introduces SVC's purpose and operating model, explains each SVC CLI command's when-to-use and know-how, provides safe command examples, explains lookup escalation, and points the Coding Agent to project-local consumer truth. It must not copy the mutable/canonical SVC guidance that lookup serves. `svc init --agent codex` refuses every other provider until a provider-specific discovery and path contract is proven.

## Busybox Command Spine

The CLI should grow as one binary with deep, narrow commands—not as a plugin framework or an unbounded collection of scripts.

| Command | Owner and trigger | Minimal contract | Initial scope |
| --- | --- | --- | --- |
| `lookup` | Packaged SVC catalog; agent/human needs guidance | Read-only path-regex and keyword query; internal extension boundary | Foundation |
| `init`, `status` | Project bootstrap/adoption | Plan/apply `svc.json`, skill, and marked anchors; report baseline vs installed tool | Foundation |
| `self-update` | Installed package manager | Check/update through explicitly selected or uniquely detected installer; never silently change project adoption | Foundation |
| `thread export` | User-owned local agent transcript | Normalize an explicit source into a versioned local evidence record; redact by default; never upload | Second slice |
| `task` | Consumer task packet | Create, inspect, hand off, and machine-read the existing five-field packet contract without becoming a second task tracker | Second slice |
| `dev ensure` | Explicit caller command and health contract | Reuse a healthy local process or start exactly the provided argv; record transient runtime evidence outside `svc.json` | Third slice |

`dev ensure` deliberately takes explicit argv/port/health inputs in its first form. With only version metadata in `svc.json`, inferring `npm run dev`, ports, or readiness endpoints would create an opaque authority boundary.

## Upgrade and Migration

The old `svc migrate` command is removed from the consumer-file model. A release may package a migration guide as lookup content. A Coding Agent reads that guide, evaluates actual consumer-owned facts, makes consumer-owned changes under the project's mutation gate, and then updates `svc.json` through an explicit adoption action.

`svc self-update` plans only one initial adapter: the current interpreter's non-editable pip installation. Its exact-plan apply runs `sys.executable -m pip install --upgrade sustainable-vibe-coding`, reports the command and provenance before mutation, verifies the resulting installed version in a fresh interpreter, and never changes `svc.json`. Editable installs and unsupported installer provenance block without mutation. `svc adopt <version>` validates that the requested installed corpus is available and records project adoption only after the user/Coding Agent has handled the release guide.

`src/manifest.json` remains release metadata rather than a consumer-file inventory. It records corpus version, Behavioral SemVer impact, and for future major releases either a packaged lookup migration-guide path or an explicit, reviewable non-applicability reason. The release planner validates this declaration; it no longer resolves or applies a consumer-file migration graph.

The first unreleased v10 pivot can replace the prior v10 schema and release manifest because no external v10 consumer exists. After the first published release, all future changes obey Behavioral SemVer and must provide compatible lookup/migration guidance.

## Recommended Delivery Order

1. Replace the managed-file manifest/state/migration model with the packaged catalog, `svc.json`, extensible path-regex/keyword lookup, Codex skill, navigation anchors, init/status, self-update, adopt, and migration-guide lookup.
2. Add normalized local thread export and minimal task-packet helpers.
3. Add explicit dev-server assurance after a concrete process/health contract is reviewed.
4. Revisit the static semantic-search pack only after a measured prototype selects its local artifact contract.
