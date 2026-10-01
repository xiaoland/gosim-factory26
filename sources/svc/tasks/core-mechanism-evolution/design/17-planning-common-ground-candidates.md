# Working Note — Planning Common-Ground Candidates

- **State**: supporting earlier candidate; `D-021` reopens whether `Slice` and
  `Step` are sufficient, with active inquiry moved to
  [`18-work-decomposition-dimensions.md`](18-work-decomposition-dimensions.md)
- **Sources**: `D-016`, `D-017`, `D-019`, `V-039`, `V-040`, `V-042`, `V-044`;
  telemetry field cases in [`16`](16-telemetry-task-packet-field-cases.md)
- **Use**: Compare small planning vocabularies that make Agent intent legible to
  Sir without imposing a linear lifecycle or a universal directory tree

## Problem

SVC currently gives Agents postures and a `Next Step`, but not a stable planning
language. Large packets consequently use `phase`, `slice`, `step`, `sub-task`,
`segment`, `unit`, `iteration`, `batch`, `milestone`, and `gate` with overlapping
or implicit meanings.

The problem is not merely inconsistent names. These words belong to different
semantic categories:

- a bounded piece of work
- a grouping or ordering horizon
- one executable action
- a feedback/repetition pattern
- a current-attention pointer
- an admission predicate
- an achieved outcome marker
- a separately governed task

Calling all of them planning “levels” makes the Agent's intended topology and
completion semantics hard for a Human to infer.

## Required Properties

A useful common ground must:

1. define each term by purpose and completion/return semantics, not approximate
   size
2. keep plan scope independent from organization
3. express dependency, concurrency, feedback, reopening, assignment, and
   integration without requiring one tree
4. let a simple task use only one next action
5. let a large task progressively externalize bounded work without inventing
   local synonyms
6. distinguish a work object from a view, predicate, relation, or outcome marker
7. remain understandable from `packet.md` without an external framework
   codebook

## Alternative A — Fixed Phase / Slice / Step Hierarchy

```text
Plan
└── Phase
    └── Slice
        └── Step
```

Benefit: familiar and easy to render.

Failure: it makes optional grouping look mandatory, implies linear phase
progression, and cannot faithfully represent a design slice that reopens
exploration or an implementation probe inside diagnosis. The field cases would
still need separate meanings for iterations, gates, and child tasks.

Disposition: reject as the universal model; a task may locally render this
shape when its real relations happen to fit.

## Alternative B — One Generic Recursive Work Item

```text
WorkItem { type?, scope?, children?, relations? }
```

Benefit: structurally minimal and can represent almost anything.

Failure: it moves the ambiguity into `type` and local prose. Human readers still
cannot know whether an item returns a decision, a state mutation, a checkpoint,
or merely the next command. It resembles a Task IR and creates schema pressure
before stable semantics exist.

Disposition: retain the insight that work can decompose recursively, but reject
an untyped universal item as Human common ground.

## Alternative C — Small Semantic Vocabulary

The current recommendation separates core work concepts from control terms.

### Core concepts

| Term | Meaning | Completion/return |
| --- | --- | --- |
| **Task** | Human-steerable outcome and authority boundary served by one task packet | Objective is satisfied at the declared verification/acceptance horizon, or honestly closed with another explicit disposition |
| **Plan** | Current projection of intended work for one declared scope; not necessarily a file or tree | Replaced as evidence changes; its items return into task or module state |
| **Slice** | Bounded work with an independently meaningful result and explicit integration target | Result is integrated, accepted, rejected, parked, or returned honestly blocked |
| **Step** | Concrete executable action whose result is consumed locally and does not need independent integration | Action is performed and its observation updates the containing plan/slice |

`Task` and scope are not planning levels. A plan may have task-wide or local
scope. `Slice` and `Step` are the only candidate work-decomposition primitives.
A simple task may expose one direct step and no slice. A complex plan may relate
several slices, and a slice may be refined into smaller slices or steps when the
return boundary justifies it.

Scope qualifies a slice without changing its base meaning:

- exploration slice → evidence and synthesis
- design slice → decision/model and consequences
- implementation slice → bounded mutation, proof, and recovery
- verification slice → changed-claim evidence and acceptance horizon
- mixed slice → one terminal result spanning several postures/scopes

### Control and observation terms

These terms may be standardized, but they are not additional decomposition
levels:

| Term | Type | Meaning |
| --- | --- | --- |
| **Front** | pointer/view | The one issue, decision, slice, or return currently foregrounded for attention |
| **Iteration** | feedback pattern | One pass through work → observation → disposition; it may repeat or revise slices/steps |
| **Gate** | predicate/authority boundary | Evidence or approval required before a named mutation, transition, or acceptance claim |
| **Milestone** | achieved-state marker | A consequential accepted result; it is not work to perform |
| **Assignment** | relation | An actor executes a slice or step under bounded context, authority, expected return, and escalation conditions |

### Terms to remove or translate

- **sub-task**: if it has an independently Human-steerable objective, authority,
  packet, and acceptance boundary, call it a child **Task**; otherwise call it a
  **Slice**
- **segment**: no SVC planning meaning; use slice, step, or a domain-specific
  term that does not control task state
- **unit**: reserved for semantic product/system ownership or locally defined
  task scope; not a generic plan level
- **batch**: execution scheduling of compatible steps/slices; not a work type
- **phase**: not currently needed as a core primitive. When a task needs a
  review/ordering horizon, express the relevant slice relations and gate; a
  local visual grouping may still be labelled phase but gains no universal
  authority from the word

## Relations Carry Topology

The vocabulary stays small because relations express shape:

- `refines` / `decomposes-into`
- `depends-on` / `enables`
- `assigned-to` / `authorized-by`
- `expects-return` / `integrates-into`
- `blocks` / `reopens`
- `verified-by`
- `conflicts-with` / `exclusive-write`

Sequence and parallelism are projections of these relations and resource
compatibility; they are not additional item types.

## Mapping the Field Cases

| Existing case term | Candidate common-ground interpretation |
| --- | --- |
| InKCre implementable unit | Slice when it returns into the program task; child Task only when it truly has independent Human steering and acceptance |
| InKCre `B0..B8` / `I-01..I-08` | Slices when independently integratable; otherwise steps; the letter sequence alone carries no common meaning |
| Surface camera Agent instance | Assignment/execution record for a slice, not a nested task by default |
| Surface camera capability gate | Gate plus evidence; not a plan item |
| Workbench sub-task | Slice unless it satisfies the child-Task boundary |
| Workbench iteration | Iteration feedback pattern over named slices/steps |
| Workbench phase inside an iteration | Slice, step group, or local display grouping according to its actual return; not automatically a framework level |
| Vertical or milestone | A slice when work remains; milestone after the accepted result exists |

## Progressive Representation

```text
simple task
  packet.md: Next Step

several bounded results
  packet.md: current Front + consequential roll-up
  module-local plan: slices and their material relations

deep execution
  slice-local steps only while they improve recovery or delegation
  assignment/proof material in the owning module
```

No empty plan, slice file, iteration directory, graph, or status table is
created from vocabulary availability alone.

## Costs and Falsifiers

The candidate may be too reductive:

- `Slice` may accumulate too many scope-specific contracts and become another
  generic `WorkItem`
- removing `Phase` may make long ordered migrations or Human review campaigns
  harder to communicate
- recursively refining slices may obscure the boundary between a child Task and
  a large slice
- `Iteration` may belong to Working Protocol rather than task-packet planning
- common terms may conflict with established domain language

Reopen or expand the core if real plans cannot be expressed without repeated
local explanations, Human readers still mispredict the Agent's intended
sequence/return, or a removed term has a stable semantic job not representable
as a relation, predicate, view, or qualifier.

## Current Recommendation

Use `Task`, `Plan`, `Slice`, and `Step` as the candidate core; use `Front`,
`Iteration`, `Gate`, `Milestone`, and `Assignment` as standardized orthogonal
terms. Retire ambiguous `sub-task` and `segment`; do not admit `Phase` as a core
primitive unless counterexamples show that ordered relations plus gates are
insufficient.

The smallest Human review is whether these semantic categories and the strict
`sub-task -> Task or Slice` disambiguation match Sir's intuition. Exact field
shapes, templates, and module directories remain out of scope.
