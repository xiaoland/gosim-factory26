# Browse-first Corpus Layout and Task CLI

- **State**: Task CLI, authoring-owner, and browse-category proposal; exact
  symmetric layout corrected by [`design/87`](87-symmetric-corpus-navigation.md)
  and implementation contract finalized for review in
  [`design/88`](88-p2-review-and-realization-outline.md)
- **Corrects**: the `sections/` layout and `CONTRIBUTING.md` authoring owner in
  [`design/83`](83-source-landing-layout-and-writing.md) and
  [`design/84`](84-source-content-migration-and-review.md)
- **Consumer**: all five `P2` Cells and the later source/CLI Impact Handshake
- **Boundary**: Task Packet design only; no `src/`, CLI, template, release, or
  generated-output mutation is authorized

## Why the Previous Landing Is Insufficient

`sections/` classifies files by their implementation role in the repository.
It contributes no information to a reader asking where to start, how to work,
how to organize project truth, or where a specific kind of judgment lives.
Retaining it would preserve the current browsing defect beneath a larger set of
documents.

`CONTRIBUTING.md` owns contribution behavior for the whole repository. Corpus
authoring has a narrower scope, vocabulary, representation contract, and
progressive-disclosure discipline. Putting those rules in a repository-wide
document would make both owners less precise.

The current uncommitted `svc task init/grow` implementation also projects an
older Task Packet model: `init` creates one flat file and `grow` returns the
same generic guide regardless of the existing package. Source landing must
design the Corpus model and these commands as one product seam.

## Navigation Model

Optimize the tree for the first question a Human or Agent asks, not for the
internal SVC capability taxonomy:

```text
What am I trying to find?
├── the universal operating contract   -> working-protocol/index.md
├── a reusable problem-solving method  -> methods/
├── how bounded work is delegated      -> sub-agents/index.md
├── how a claim is qualified           -> verification/index.md
├── how an active task is organized    -> task-packet/index.md
├── how durable project truth is owned -> project/
├── how design judgment is sharpened   -> taste/
├── which optional topology applies    -> extensions/
├── which reusable shape to instantiate-> templates/
└── what changed between releases      -> migrations/
```

`index.md` is the short landing page and owner map. It is not a second copy of
every CLI product contract. CLI grammar remains in layered command help;
product, cross-unit, unit, and runtime claims remain in their durable project
owners.

## Selected Source Tree

This tree records the accepted browse categories but its mixed file/directory
shape is superseded. The canonical tree and progressive-depth grammar are in
[`design/87`](87-symmetric-corpus-navigation.md); monofile pressure evidence is
retained in [`design/86`](86-progressive-source-depth.md).

```text
src/
├── AGENTS.md                         # local authoring contract; not Corpus
├── index.md                          # short entry, owner map, navigation
├── working-protocol.md               # universal operational kernel/router
├── task-packet.md                    # Task Packet model and growth guidance
├── sub-agents.md                     # delegation placement/contracts
├── verification.md                   # claim qualification capability
├── methods/
│   ├── explore.md                    # foundational Working Method
│   ├── design.md                     # foundational Working Method
│   └── implementation.md             # foundational Working Method
├── project/
│   ├── prd.md
│   ├── product-tdd.md
│   ├── unit-tdd.md
│   └── deployment.md
├── taste/
│   └── implementation.md
├── extensions/
│   ├── alignment.md
│   └── multi-repo.md
├── templates/
│   ├── task-packet/
│   │   └── packet.template.md
│   └── <the other existing Consumer templates>
├── migrations/
└── version.json
```

### Why this tree is smaller than the former proposals

- `working-protocol.md`, `sub-agents.md`, and `verification.md` stay directly
  visible because they are different semantic kinds with different consumers
  and triggers. A generic `work/` parent would be another umbrella rather than
  an owner.
- Only the three genuinely homogeneous foundational Working Methods share
  `methods/`. There is no extra `working-methods.md`; the small stateless,
  composable, bounded-incomplete bootstrap belongs in `working-protocol.md`.
- `project/` groups the already-existing durable truth owners. It does not add
  a new knowledge layer or change their authority.
- `taste/` is a discoverable progressive-depth foothold. Only implementation
  judgment exists initially; UI/UX or architecture files require later real
  content and retrieval pressure.
- `templates/` removes the implementation-flavored `assets/` wrapper. Existing
  template basenames can remain stable inside the new directory except for the
  already accepted Task Packet family boundary.

The target root listing is therefore made of meaningful concepts rather than
`assets/`, `sections/`, and an oversized `index.md`.

## Corpus-local Authoring Owner

Create `src/AGENTS.md` as the exact owner of the Corpus writing standard. It
applies automatically to changes under `src/`, is visible to maintainers, and
does not claim repository-wide contribution policy.

It must not be a packaged Consumer document. The catalog projection therefore
excludes exactly the root `src/AGENTS.md` while continuing to fail on accidental
or unsupported Markdown elsewhere. Focused tests must prove that the file is
available as local authoring instruction but absent from catalog, wheel, lookup,
and monolith output.

The standard keeps the accepted rules from [`design/36`](36-corpus-writing-standard-draft.md):
semantic owner first, direct stable language, semantic compression, concept
budget, progressive disclosure, typed authority/uncertainty, representation by
relation, and restrained diagrams. It does not impose front matter, a heading
schema, ASD-STE100 compliance, a linter, or a controlled dictionary.

## Task CLI Product Seam

The Agent owns semantic shape selection and Task Packet content. The CLI owns
only safe addressing, absent-file creation, bounded observation, and exact
Corpus/template routing.

### `svc task init`

Keep one low-risk effect: create an absent `tasks/<task-id>/packet.md` from the
canonical template and never overwrite or merge. Improve the return and
template so the next action is explicit:

1. identify the created packet;
2. name the canonical `task-packet/index.md` guidance address;
3. require an immediate smallest-credible-shape preflight before work
   accumulates; and
4. point to `svc task grow <task-id>` when the current shape needs examination.

Do not ask the CLI to infer task scale, nature, Tracks, Phases, Cells, or
information modules. Those are semantic decisions. Do not pre-create a template
family merely because a future task might grow.

### `svc task grow`

Replace the static guide dump with a bounded, packet-specific **growth brief**.
The command is read-only in the first landing. It reports:

- the exact packet address and a bounded relative tree;
- mechanically recognizable entries such as `task-map.md`, `cells/`, and the
  stable Inquiry/Design/Decision/Verification module names;
- unrecognized or ambiguous paths without treating them as errors;
- the work-topology versus information-topology questions that the Agent must
  answer now;
- the canonical Task Packet guidance and applicable template addresses; and
- an explicit statement that no semantic growth or acceptance occurred.

Presence, filename, file length, or Agent count cannot prove that a module,
Track, Phase, or Cell is warranted. The brief therefore does not recommend a
verdict from mechanical heuristics and does not edit `packet.md`, `task-map.md`,
or any module. The Agent consumes the brief and performs one coherent semantic
transition with ordinary file editing.

This is deliberately less magical than an automatic scaffolder. Updating an
existing packet requires moving current meaning, integrating owner returns, and
repairing projections; a CLI that only creates placeholders would leave a
plausible-looking but inconsistent package. A future no-overwrite projection is
admissible only after a repeated deterministic transition has a stable input,
output, and validator.

## Public-path and Migration Consequence

The browse-first move changes most released Corpus addresses, not only the Task
Packet template. It is one declared Behavioral SemVer major transition:

- `sections/working-protocol.md` -> `working-protocol/index.md`;
- the three Working Methods -> concept directories under `methods/`;
- Sub-agents and Verification -> `sub-agents/index.md` and
  `verification/index.md`;
- `sections/{prd,product-tdd,unit-tdd,deployment}.md` -> corresponding
  `project/<owner>/index.md` entries;
- `sections/implementation-taste.md` -> `taste/implementation/index.md`;
- `sections/extensions/` -> symmetric concept directories under `extensions/`;
- `assets/templates/` -> `templates/`;
- Task Packet guidance -> `task-packet/index.md`; and
- the packet template -> `templates/task-packet/packet.template.md`.

The migration guide gives the explicit address map. Permanent alias documents
would preserve the confusing browsing topology and duplicate normative content,
so none are proposed. Machine-exposed references such as Agent Task Analysis
and Task Packet resource constants move atomically with focused installed-wheel
tests.

## Review and Falsifiers

Accept this correction if a reader can predict the first expansion from the
top-level names, `methods/` contains one coherent kind rather than every form of
Agent work, and local authoring rules no longer leak into either repository-wide
policy or the Consumer Corpus.

Reopen it if real lookup sessions show that `methods/`, `project/`, or `taste/`
hide more than they reveal; if the three root capability entries make the root
harder to scan than a more specific grouping; if the root authoring-file
exclusion creates an unsafe implicit catalog rule; or if the read-only growth
brief costs as much context as directly reading `task-packet/index.md` without
improving packet-shape decisions.
