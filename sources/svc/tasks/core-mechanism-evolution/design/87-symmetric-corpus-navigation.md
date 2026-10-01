# Symmetric Corpus Navigation Grammar

- **State**: navigation grammar accepted through `D-091`; exact landing and
  realization entry refined by [`design/88`](88-p2-review-and-realization-outline.md)
- **Corrects**: the mixed file/directory grammar in
  [`design/85`](85-browse-first-layout-and-task-cli.md) and
  [`design/86`](86-progressive-source-depth.md)
- **Retains**: their semantic owners, browse-first categories, admitted source
  depth, Corpus-local authoring owner, Task CLI seam, and migration boundary
- **Boundary**: no durable source, template, CLI, or release mutation is
  authorized

## Correction

The previous proposal made progressive depth conditional on current content:
some concepts were `<owner>.md`, while others were `<owner>.md + <owner>/`.
That avoids empty structure, but it makes the filesystem grammar itself carry
an unstable and unnecessary distinction. A reader must remember which concepts
have already grown, and a concept's canonical address changes when it first
needs depth.

For a browsable Corpus, structural symmetry is part of the interface. The
minimum grammar is therefore:

```text
<concept>/
  index.md              # stable entry and compact route
  <depth>.md            # optional, pressure-created depth
  <subconcept>/index.md # optional nested concept using the same grammar
```

Every navigable semantic concept uses this shape from its first landing. A
directory with only `index.md` is not a placeholder: the directory is the
stable concept address and `index.md` is its current sufficient interface.
Adding depth never moves the entry.

Symmetry applies to **node shape**, not to the amount of content. Requiring
every sibling to have the same children would manufacture false semantics.
`verification/index.md` may remain sufficient while `methods/design/` has
three independently useful projections; both still obey the same navigation
grammar.

## Selected Browse Tree

```text
src/
├── AGENTS.md                         # local authoring contract; not Corpus
├── index.md                          # Corpus root entry and owner map
├── version.json                      # machine metadata, not a concept node
├── working-protocol/
│   └── index.md                      # compact universal kernel/router
├── task-packet/
│   ├── index.md                      # compact model and routes
│   ├── planning.md
│   ├── information.md
│   └── growth.md
├── sub-agents/
│   ├── index.md                      # placement, authority, result routing
│   ├── explorer.md
│   └── executor.md
├── verification/
│   └── index.md                      # cohesive qualification contract today
├── methods/
│   ├── index.md                      # method-family entry and selection route
│   ├── explore/
│   │   ├── index.md
│   │   └── agent-task-analysis.md
│   ├── design/
│   │   ├── index.md
│   │   ├── product.md
│   │   ├── technical.md
│   │   └── test.md
│   └── implementation/
│       └── index.md
├── project/
│   ├── index.md                      # durable project-truth owner map
│   ├── prd/
│   │   ├── index.md
│   │   ├── corpus.md
│   │   ├── development.md
│   │   ├── agent-analysis.md
│   │   ├── run.md
│   │   └── double.md
│   ├── product-tdd/
│   │   ├── index.md
│   │   ├── execution.md
│   │   ├── agent-analysis.md
│   │   └── double.md
│   ├── unit-tdd/
│   │   └── index.md
│   └── deployment/
│       ├── index.md
│       ├── execution.md
│       ├── agent-analysis.md
│       └── double.md
├── taste/
│   ├── index.md                      # taste authority and discovery route
│   └── implementation/
│       └── index.md
├── extensions/
│   ├── index.md                      # optional-extension route
│   ├── alignment/
│   │   └── index.md
│   └── multi-repo/
│       └── index.md
├── templates/
│   ├── index.md                      # template catalog and use boundary
│   ├── task-packet/
│   │   ├── index.md                  # Task Packet template-family route
│   │   ├── packet.template.md
│   │   ├── plan.template.md
│   │   ├── task-map.template.md
│   │   ├── cell.template.md
│   │   ├── inquiry.template.md
│   │   ├── diagnostic-matrix.template.md
│   │   ├── design.template.md
│   │   ├── decisions.template.md
│   │   └── verification.template.md
│   └── <other atomic *.template.md artifacts>
└── migrations/
    ├── index.md                      # migration selection and reading route
    └── <versioned or capability migration documents>
```

`methods/`, `project/`, `taste/`, `extensions/`, `templates/`, and
`migrations/` are not silent grouping folders: each has an `index.md` that
states what belongs there, how a consumer chooses the next entry, and what the
category does not own. This makes navigation compositional at every level.

Atomic template and migration documents are terminal artifacts rather than
expandable semantic nodes, so their complete identity may remain a file. If an
artifact becomes a family with its own route and depth, it must first become a
directory with `index.md`; it does not use the mixed `<name>.md + <name>/`
shape.

## Monofile Consequence

The monofile admission test from `design/86` remains useful, but it no longer
controls whether a concept receives a directory. It controls only whether
content stays in `index.md` or moves into a sibling depth entry.

Move content out of `index.md` when it has a distinct recurring retrieval
trigger, consumer, authority/provenance boundary, or change cadence. Keep it in
`index.md` while the compact contract is cheaper to understand as a whole.
Line count alone remains insufficient.

This yields a stable growth operation:

```text
before: verification/index.md
after:  verification/index.md + verification/<proven-depth>.md
```

No public entry path changes, no sibling requires a matching empty file, and a
reader never has to guess whether a concept is represented by a file or a
directory.

## Navigation and Writing Consequences

- Root `src/index.md` routes only to first-level concept directories and does
  not duplicate their contracts.
- Every directory `index.md` is a compact semantic interface, not a link dump:
  it states purpose, ownership/boundary, minimum guidance, and progressive
  routes.
- Parent and child entries do not restate normative claims. The parent explains
  selection; the child owns the selected depth.
- Corpus links use canonical `.../index.md` addresses. No directory shorthand
  or permanent alias behavior is required from the CLI.
- `src/AGENTS.md` and `version.json` are explicit non-Corpus/non-concept
  exceptions; the catalog exclusion remains exact rather than pattern-based.

## Task CLI and Migration Consequence

The `task init/grow` product boundary from `design/85` is unchanged, but its
canonical routes become:

- Task Packet guidance: `task-packet/index.md`;
- growth guidance: `task-packet/growth.md`; and
- packet template: `templates/task-packet/packet.template.md`.

The public-path move remains one Behavioral SemVer major transition. The path
map now targets directory entries, for example:

```text
sections/working-protocol.md -> working-protocol/index.md
sections/prd.md              -> project/prd/index.md
sections/implementation-taste.md -> taste/implementation/index.md
sections/extensions/alignment.md -> extensions/alignment/index.md
```

Machine-exposed references, catalog tests, installed-wheel lookup tests,
monolith links, templates, CLI constants, and migration documentation move in
the same change.

## Falsifiers

Reopen this grammar if real filesystem/lookup use shows that repeated
`index.md` addresses cause more ambiguity than the mixed grammar, or if a
concept cannot be assigned a stable directory name without creating a false
category. Do not reject it merely because some directories initially contain
one file; that is the deliberate cost of a stable, symmetric navigation
interface.
