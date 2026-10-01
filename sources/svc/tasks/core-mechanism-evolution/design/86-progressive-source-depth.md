# Progressive Source Depth and Monofile Pressure

> **Historical/non-normative as layout**: retain only the monofile pressure and
> admitted-depth evidence. Do not implement the mixed file/directory examples;
> use [`design/87`](87-symmetric-corpus-navigation.md) and
> [`design/88`](88-p2-review-and-realization-outline.md).

- **State**: superseded as a filesystem grammar by [`design/87`](87-symmetric-corpus-navigation.md); retained for monofile pressure and admitted depth evidence
- **Refines**: [`design/85`](85-browse-first-layout-and-task-cli.md)
- **Question**: which selected source entries are compact owners, and which
  already contain enough distinct retrieval pressure to require depth at the
  first landing
- **Boundary**: no durable source or CLI mutation is authorized

## Monofile Is a Semantic Failure, Not a Line-count Failure

> **Correction**: the conditional `<owner>.md + <owner>/` grammar below is no
> longer the target layout. `design/87` keeps the semantic depth conclusions
> but gives every navigable concept the symmetric `<concept>/index.md` shape.

A long file is not automatically wrong. A monofile becomes costly when one
entry must be loaded or edited for concerns with different triggers, consumers,
authority, provenance, or change cadence. Conversely, splitting one cohesive
contract into symmetrical fragments increases navigation and reconciliation
cost.

The selected source grammar is the same stable-entry rule accepted for Task
Packet modules:

```text
<owner>.md
  -> compact contract and progressive routes

<owner>.md + <owner>/<depth>.md
  -> depth exists only for an already distinct consumer or trigger
```

The root entry is therefore not a promise that all future content remains in
one file. It is a stable address and the cheapest sufficient interface.

## Depth Required in the First Landing

### Task Packet

`task-packet.md` owns the compact purpose, universal Human entry, common
vocabulary, routing questions, and return-to-root invariant. Existing accepted
content already has three independently loaded depths:

```text
task-packet.md
task-packet/
  planning.md             # Plan vocabulary and Shapes 0–3
  information.md          # Inquiry/Design/Decision/Verification modules
  growth.md               # admission, transition, retirement, and CLI seam
```

This prevents the complete 394-line design model from becoming a new durable
monofile while preserving one discoverable Task Packet owner.

### Explore

The Explore core—Frame, adaptive Route, embedded Model/Generate/Discriminate,
sufficiency, and bounded-incomplete return—remains cohesive in
`methods/explore.md`. Agent Task Analysis has a narrower trigger, machine-
exposed method reference, and separate evidence interface, so it receives
depth immediately:

```text
methods/explore.md
methods/explore/
  agent-task-analysis.md
```

Model, Generate, and Discriminate do not become files merely because they have
names; they remain embedded logic without independent management returns.

### Design

`methods/design.md` owns the primitive method, typed forces, coupled solution,
consequence challenge, horizon adequacy, and projection routing. Product,
Technical, and Test Design are already accepted as independently useful,
claim-linked solution projections with different questions and review carriers:

```text
methods/design.md
methods/design/
  product.md
  technical.md
  test.md
```

These are not phases or three required documents for every task. They are
progressive guidance loaded only when the applicable projection is material.

### Sub-agents

`sub-agents.md` owns placement economics, Primary/Child authority, context,
Assignment sizing, result routing, and admission/non-goals. Explorer and
Executor have different consumers and result paths, so embedding both would
make every delegation load irrelevant guidance:

```text
sub-agents.md
sub-agents/
  explorer.md
  executor.md
```

This is not a role catalog. These remain the only two admitted profiles; a new
file requires a separately proven recurring boundary.

### Existing project-truth owners

The current `prd.md`, `product-tdd.md`, and `deployment.md` mix their stable
owner contract with several already-independent SVC capability projections.
Moving those files unchanged into `project/` would preserve current monofiles.

Retain the generic owner/admission/expansion contract in each entry and move
the existing capability sections behind same-stem depth:

```text
project/
  prd.md
  prd/
    corpus.md
    development.md
    agent-analysis.md
    run.md
    double.md
  product-tdd.md
  product-tdd/
    execution.md
    agent-analysis.md
    double.md
  unit-tdd.md
  deployment.md
  deployment/
    execution.md
    agent-analysis.md
    double.md
```

The repeated capability names across Product, cross-unit Technical, and
Deployment owners are projections, not duplicated authority. Each file must
link vertically only where the consumer needs the adjacent claim/contract/
runtime consequence; it must not restate the other owner's content.

`index.md` loses its detailed copies of these CLI capabilities and remains the
short product entry and owner/navigation map. CLI grammar remains in command
help.

## Entries That Should Stay Single Initially

- `working-protocol.md`: one compact universal kernel and router; specialist
  depth is linked, not retained here.
- `methods/implementation.md`: one realization-feedback method with a single
  return boundary.
- `verification.md`: the accepted claim→surface/oracle→evidence/TCB/residual→
  disposition chain and mechanism economy currently form one compact
  qualification contract. Split only when a mechanism/composition concern has
  an independent recurring consumer.
- `taste/implementation.md`: current implementation judgment is approximately
  one compact foothold. A same-stem directory appears only after real use-case
  guidance becomes independently retrievable.
- `project/unit-tdd.md`: its current unit-owner and local-instruction contract
  is small and cohesive.

No empty directory, index-only file, or mirrored hierarchy is created for
these entries.

## Resulting Browse Shape

```text
src/
├── AGENTS.md
├── index.md
├── working-protocol.md
├── task-packet.md + task-packet/
├── sub-agents.md + sub-agents/
├── verification.md
├── methods/
│   ├── explore.md + explore/
│   ├── design.md + design/
│   └── implementation.md
├── project/                     # stable entries plus justified depth
├── taste/implementation.md
├── extensions/
├── templates/
└── migrations/
```

The tree now uses directories for one of two reasons only: a coherent family
of same-kind entries (`methods/`, `project/`, `taste/`, `templates/`,
`extensions/`, `migrations/`) or pressure-proven same-owner depth.

## Falsifiers

Reopen a split when a depth file cannot state a distinct load condition and
return, repeatedly requires its entire sibling set to be understood, or causes
more cross-file reconciliation than selective loading saves. Reopen an unsplit
entry when unrelated consumers repeatedly load or edit it, or when one change
cadence forces unnecessary review of the rest.

Line count alone is neither admission nor retirement evidence.
