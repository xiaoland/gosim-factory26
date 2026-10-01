# P2 Review and Realization Outline

- **State**: implementation-ready design proposal; concise Human review pending
- **Owns**: the unique implementation entry for the accepted P2 capability landing
- **Uses**: [`design/84`](84-source-content-migration-and-review.md) only for
  semantic content evidence, [`design/85`](85-browse-first-layout-and-task-cli.md)
  for the Task CLI boundary, [`design/86`](86-progressive-source-depth.md) for
  depth pressure, and [`design/87`](87-symmetric-corpus-navigation.md) for the
  accepted navigation grammar
- **Boundary**: this is Task Packet design/Plan material; source mutation still
  requires Sir's explicit `start`

## Review Result

The capability model and symmetric `<concept>/index.md` grammar have no
conceptual blocker. The implementation is still small in code terms, but it is
not merely prose editing: Corpus paths are packaged public addresses, the
catalog and wheel project every canonical document, and the dirty Task CLI
already carries the superseded paths and behavior.

The review retains the proposed capability content while correcting five
implementation gaps:

1. one canonical path/content map replaces competing historical layouts;
2. the authoring-only `src/AGENTS.md` exclusion is exact and tested across
   every projection;
3. the Task Packet family includes opt-in templates for every admitted building
   block, without automatic scaffolding;
4. `task init/grow` receives one bounded behavior contract before code changes;
5. the path change closes as one Behavioral SemVer major migration.

## Canonical Source and Content Map

[`design/87`](87-symmetric-corpus-navigation.md) is the only canonical tree.
The following table owns the current-to-target content move; older path tables
are historical evidence, not implementation instructions.

| Current source | Target owner | Disposition |
| --- | --- | --- |
| `src/index.md` — Core Contract and compact packaged-consumption bootstrap | `index.md` | retain and compress into the root purpose/navigation entry |
| `src/index.md` — Project Adoption | `project/prd/corpus.md` | move the observable adoption and Corpus-evolution product contract; CLI grammar stays in help |
| `src/index.md` — Task Packets | `task-packet/index.md` | integrate with the accepted packet model; remove duplicate root detail |
| `src/index.md` — Development, Run, Agent-thread Analysis | `project/prd/{development,run,agent-analysis}.md` | move product claims; technical/runtime projections remain below |
| `src/index.md` — Migration/SemVer | `migrations/index.md` | move release/migration selection logic; root keeps one route |
| `src/index.md` — Knowledge Owners | `project/index.md` | move the detailed durable-owner map; root keeps a compact owner route |
| `src/index.md` — Optional Extensions | `extensions/index.md` | move admission/navigation; root keeps one route |
| `src/sections/working-protocol.md` | `working-protocol/index.md` plus `methods/*` and `task-packet/*` | keep only universal obligation/return, authority/effect, feedback/integration, Human/close, and progressive-navigation laws; move method/packet/VF detail |
| `src/sections/prd.md` — generic owner contract | `project/prd/index.md` | retain purpose, derivation, boundary, admission, and expansion |
| `src/sections/prd.md` — Corpus, Development, Analysis, Run, External Boundary | `project/prd/{corpus,development,agent-analysis,run,double}.md` | move each independently consumed product projection without restating technical/runtime claims |
| `src/sections/product-tdd.md` — generic owner contract | `project/product-tdd/index.md` | retain admission and ownership boundary |
| `src/sections/product-tdd.md` — Execution, Double, Evidence Query | `project/product-tdd/{execution,double,agent-analysis}.md` | move cross-unit technical contracts |
| `src/sections/unit-tdd.md` | `project/unit-tdd/index.md` | move intact and repair links |
| `src/sections/deployment.md` — generic owner contract | `project/deployment/index.md` | retain runtime-owner admission and boundary |
| `src/sections/deployment.md` — Execution, Double, Evidence Runtime | `project/deployment/{execution,double,agent-analysis}.md` | move operational projections |
| `src/sections/implementation-taste.md` | `taste/implementation/index.md` | preserve claims, reorganize by recurring pressure, add causal reason/counter-pressure where it changes choice |
| `src/sections/extensions/{alignment,multi-repo}.md` | `extensions/{alignment,multi-repo}/index.md` | move intact, then remove duplicated owner prose |
| `src/assets/templates/*.template.md` | `templates/` and `templates/task-packet/` | move atomic Consumer shapes; Task Packet family is expanded below |
| existing `src/migrations/*.md` | same paths | retain; add the new layout migration and `migrations/index.md` |
| uncommitted `src/sections/task-packet-growth.md` | `task-packet/growth.md` | rewrite against the accepted grammar rather than preserve the old static tree |

New Working Method, Task Packet, Sub-agent, Verification, and Taste content uses
the semantic contracts already reviewed in `design/84`; only their paths and
progressive split follow `design/87`.

### Complete released-path disposition

The `13.0.0` migration owns this complete disposition for currently released
Corpus Markdown addresses. Unlisted target documents are additive new entries.

| Current `12.0.0` path | `13.0.0` path/disposition |
| --- | --- |
| `index.md` | retained and rewritten as the compact root entry |
| `sections/working-protocol.md` | `working-protocol/index.md` |
| `sections/prd.md` | `project/prd/index.md` |
| `sections/product-tdd.md` | `project/product-tdd/index.md` |
| `sections/unit-tdd.md` | `project/unit-tdd/index.md` |
| `sections/deployment.md` | `project/deployment/index.md` |
| `sections/implementation-taste.md` | `taste/implementation/index.md` |
| `sections/extensions/alignment.md` | `extensions/alignment/index.md` |
| `sections/extensions/multi-repo.md` | `extensions/multi-repo/index.md` |
| `assets/templates/AGENTS.local.template.md` | `templates/AGENTS.local.template.md` |
| `assets/templates/AGENTS.root.template.md` | `templates/AGENTS.root.template.md` |
| `assets/templates/alignment-change-request.template.md` | `templates/alignment-change-request.template.md` |
| `assets/templates/deployment-runbook.template.md` | `templates/deployment-runbook.template.md` |
| `assets/templates/edit-shared-docs.template.md` | `templates/edit-shared-docs.template.md` |
| `assets/templates/product-tdd.template.md` | `templates/product-tdd.template.md` |
| `assets/templates/product-truth.template.md` | `templates/product-truth.template.md` |
| `assets/templates/task-packet.template.md` | `templates/task-packet/packet.template.md` |
| `assets/templates/task-diagnostics-matrix.template.md` | `templates/task-packet/diagnostic-matrix.template.md`; semantics narrow from whole Task to Inquiry artifact |
| `migrations/11.0.0.md` | retained |
| `migrations/agent-analysis-query-read.md` | retained |
| `migrations/agent-task-performance-analysis.md` | retained |
| `migrations/local-trust-boundary.md` | retained |

The machine-exposed Agent Task Analysis reference moves from the Working
Protocol document/fragment to `methods/explore/agent-task-analysis.md`; its
stable method identifier changes only if the rewritten method meaning changes.
The uncommitted `sections/task-packet-growth.md` is corrected directly to
`task-packet/growth.md` and is not described as a released compatibility path.

## Compact Corpus Entry Contract

Every directory `index.md` is a semantic interface, not a link list. In natural
headings and without required front matter, it must communicate:

1. **purpose and use condition** — what problem this entry solves and when to load it;
2. **owner and boundary** — what it owns, consumes, and explicitly does not own;
3. **minimum usable guidance or truth** — enough to act without loading every child;
4. **logic** — the causal reason for a non-obvious rule and its material counter-pressure;
5. **progressive route** — which deeper entry to load for which question.

A depth document starts with its narrower trigger, consumer/return, and parent
relation. Explain rationale near the rule it supports; do not preserve design
history or repeat the parent contract as “context.” Templates use short comments
or placeholders to explain what belongs in each slot and when the file should
not be created.

This lands the writing standard in [`design/36`](36-corpus-writing-standard-draft.md):
precise and consistent wording, semantic compression, structural symmetry,
progressive disclosure, explicit logic, and useful meta-description.

## Task Packet Template Family

Templates are opt-in building blocks, not one automatically copied packet
tree. `svc task init` creates only `packet.md`; an Agent selects another
template after the applicable topology or information owner is admitted.

```text
templates/task-packet/
├── index.md
├── packet.template.md
├── plan.template.md
├── task-map.template.md
├── cell.template.md
├── inquiry.template.md
├── diagnostic-matrix.template.md
├── design.template.md
├── decisions.template.md
└── verification.template.md
```

- `packet` is universal and uses Human collaboration language.
- `plan`, `task-map`, and `cell` cover the accepted work-topology shapes.
- `inquiry`, `design`, `decisions`, and `verification` cover the four admitted
  information modules; each retains its independent activation condition.
- `diagnostic-matrix` preserves the useful part of the existing diagnostics
  template as an optional Inquiry artifact. It is no longer an alternative
  whole-Task packet type.
- There is no implementation, delivery, acceptance, retrospective, Track,
  Phase, Slice, Agent, or generic module template.

`templates/task-packet/index.md` explains the selection logic and links every
template. Template existence never proves that a Consumer Task needs the file.

Each template is short and carries only its owner's recovery contract:

| Template | Minimum skeleton |
| --- | --- |
| `packet` | Objective; Guardrails; terminal Verification; Current Truth; Next Step; optional Human-language Task-map projection |
| `plan` | owner and expected return; current partial route; ordered Slices; TBC continuation condition; material relations |
| `task-map` | admitted Tracks/Phases; current barrier; participating Plan owners/Cells; current fronts; material relations |
| `cell` | Track obligation; Phase contribution; satisfaction/state; partial Plan; integration return |
| `inquiry` | question/decision served; boundary and freshness; evidence versus inference; current synthesis; residual and return |
| `diagnostic-matrix` | candidate cause; supporting/missing evidence; discriminator; current disposition; likely semantic owner |
| `design` | forces and constraints; proposed coherent solution; alternatives only when live; representative consequences; residual/return |
| `decisions` | ID/subject/state; authority/date; decision; rationale; consequences; reopen/supersession condition |
| `verification` | owned claim; observation/oracle; evidence and trusted-base scope; residual/horizon; consumer disposition/requalification |

Placeholders explain why a slot exists and whether it is optional. A Consumer
may rename headings to its collaboration language, but it must not merge owners
or turn the template into a completed-work log.

## Task CLI Contract

### `svc task init`

- Accept one normalized Task ID and repository root.
- Create only an absent `tasks/<id>/packet.md`; never merge or overwrite.
- Preserve the current path-containment and real-directory checks.
- Report the created path, canonical `task-packet/index.md` guidance, the
  immediate shape-preflight obligation, and the `task grow` continuation.

### `svc task grow`

- Require an existing regular `packet.md` and remain read-only.
- Return one deterministic plain-text growth brief containing the packet path,
  a sorted relative inventory bounded to two directory levels and 100 entries,
  recognized packet entries, unrecognized entries, the work/information-topology
  questions, and exact guidance/template paths. State truncation explicitly.
- Recognize only the stable root entries, `track-*.md`, `phase-*.md`, `cells/`
  entries, and same-stem supporting depth described by Task Packet guidance.
  Report but never follow symlinks; an unknown name is information, not failure.
- State explicitly that the command made no semantic decision and changed no file.
- Do not infer a Track, Phase, Cell, module, or scale from filenames, length, or
  Agent count. The Agent performs the coherent semantic edit.
- Do not add JSON/schema output until a real machine consumer exists.

The current uncommitted Task CLI files are inputs to this work, not disposable
experiments. Implementation updates them in place and adds focused success,
error, no-overwrite, containment, read-only, ordering, unknown-entry, and
installed-wheel path tests.

## Projection, Migration, and Release Contract

The source collector excludes exactly the root `src/AGENTS.md`, while still
rejecting a symlink or non-regular file at that address. Catalog, wheel,
lookup, monolith reachability, and corpus-wide document checks must agree that
it is authoring instruction rather than Consumer Corpus. Tests prove the exact
exception and that another Markdown file cannot disappear through a broad pattern.

This is one `13.0.0` Behavioral SemVer major transition from current Corpus
`12.0.0`. Add one migration guide owning the complete old→new path table,
Task Packet template semantic change, Agent Task Analysis reference move, and
Consumer lookup updates. Update `src/version.json`, a separate major Changie
fragment, root/repository Agent instructions, README, templates, CLI constants,
tests, and generated release projections together. Existing unrelated dirty
fragments and edits are preserved.

## Approximate Realization Plan

The later mutation can stay one coherent change with four reviewable returns:

| Slice | Return | Main verification |
| --- | --- | --- |
| `01-IM` | create the symmetric source tree; move current headings to their sole owners; write compact WP, Working Methods, Task Packet, SA, VF, and Taste entries under the entry contract | document/link validation plus owner/duplication review |
| `02-IM` | add the opt-in Task Packet template family and adapt the dirty `task init/grow` implementation to the frozen behavior | focused CLI/template tests and filesystem-effect inspection |
| `03-IM` | update catalog exclusion, all code/document/template references, Agent Task Analysis carrier, migration/version/Changie data, README/root AGENTS, wheel and monolith projections | catalog, monolith, migration-chain, installed lookup tests |
| `04-VR` | run complete source/build/test/wheel acceptance and review representative simple, mixed, delegated, and cross-owner routes | `check-documents`, monolith, focused tests, full tests, wheel build/install/read/task smoke checks |

The exact file list and Impact Handshake are resolved immediately before
`01-IM` because the worktree is dirty. No commit, release, or external effect
is implied.

## Concise Review Proposition

Accept this landing if the symmetric tree in `design/87`, the exact move table,
the nine opt-in Task Packet templates, the read-only growth brief, the compact
entry contract, and one major migration together provide enough implementation
precision without adding another schema, linter, Agent surface, or automatic
packet orchestrator.
