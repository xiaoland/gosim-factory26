# Working Note — Work-Decomposition Dimensions

- **State**: supporting semantic derivation; names and primitive set are not
  accepted; current model is in
  [`20-task-axes-and-linear-plans.md`](20-task-axes-and-linear-plans.md)
- **Sources**: `D-016`, `D-017`, `D-019`, `D-021`; `V-039`, `V-042`,
  `V-044`, `V-045`, `V-047`; earlier candidate in
  [`17`](17-planning-common-ground-candidates.md)
- **Use**: Derive planning building blocks from distinct decomposition jobs
  before selecting a vocabulary or hierarchy

## Why Reopen the Candidate

The `Task / Plan / Slice / Step` proposal correctly separated work objects from
views, gates, feedback patterns, and outcome markers. It may still place too
many obligations on `Slice`: a persistent concern stream, a bounded return, a
time horizon, a delegation package, and a recursively refined work item can all
be mistaken for one kind of slice.

The remedy should not be to insert another approximate size between `Slice`
and `Step`. First identify which decomposition operations change completion,
integration, ordering, authority, or Human steering semantics. Only those
distinctions deserve stable SVC building blocks.

## “Horizontal” and “Vertical” Are Not Yet Safe Terms

Both words are overloaded:

- horizontal may mean sibling work at the same abstraction level, persistent
  product/system concerns, or parallel execution
- vertical may mean deeper refinement of one item, but “vertical slice” usually
  means an end-to-end result that crosses architectural layers

Use semantic operation names during the derivation. Human-facing shorthand can
be selected after the underlying contracts are stable.

## Decomposition Jobs

### 1. Obligation split — breadth

Divide a parent obligation into peer obligations whose results jointly satisfy
it. Peers need not run concurrently. This operation answers “which separately
meaningful results must exist?”

Candidate carrier: result-bounded **Slice**.

### 2. Refinement — depth

Replace one coarse work description with a more detailed work topology while
preserving its outcome contract. Refinement may produce smaller slices, steps,
or relations; it is an operation, not necessarily a new noun.

Candidate carriers: recursively refined **Slice**, then local **Step** when no
independent return/integration boundary remains.

### 3. Concern continuity — persistent breadth

Group obligations that share a durable product area, technical boundary,
discipline, risk class, or owner across several results and time horizons. It
answers “which direction must remain coherent?” rather than “what is the next
deliverable?”

Candidate carrier: **Track**. A track may produce several slices and may cross
several phases. It has a continuing obligation, not one integration event.

### 4. Temporal and control staging

Create an ordered horizon because later work should not become active until an
exit condition, evidence threshold, migration state, or Human review has been
reached. This improves long-migration readability even when the underlying
work graph is non-linear.

Candidate carrier: **Phase**, defined as an optional coordination horizon with
an entry/exit condition—not a mandatory lifecycle stage or approximate size.

### 5. Integration cut

Select work across one or more concerns/layers so it returns one observable,
integratable result. This is the common software meaning of an end-to-end or
vertical slice.

Candidate carrier: **Slice**. The integration boundary, not layer count or
duration, gives it meaning.

### 6. Authority/context split

Separate work because it needs its own Human steering, objective, context,
mutation authority, or acceptance boundary. This is not ordinary refinement.

Candidate carrier: child **Task** when the Human-steerable boundary is real;
otherwise an **Assignment** relation over a slice or step.

### 7. Uncertainty and feedback isolation

Perform bounded work to reduce uncertainty, compare alternatives, or obtain
feedback before choosing subsequent work. The return may be evidence or a
decision rather than a system mutation.

Candidate representation: a scope-qualified slice plus an **Iteration** or
`reopens` relation. `Probe`, `spike`, or `experiment` may be return-contract
qualifiers rather than new plan levels.

## A Typed Coordinate Model

One promising model has three kinds of planning building block:

| Kind | Candidate | Stable job |
| --- | --- | --- |
| authority/outcome boundary | `Task` | independently Human-steerable objective and acceptance boundary |
| work/result boundary | `Slice`, `Step` | bounded return/integration; executable local action |
| projection/coordination axis | `Track`, `Phase` | persistent concern continuity; ordered horizon with exit condition |

This produces a matrix when useful, not a mandatory tree:

```text
                    Track A          Track B
Phase 1          └──── Slice 1 crosses both ────┘
Phase 2             Slice 2          Slice 3
                         └─ local Steps ─┘
```

A slice may belong to multiple tracks, and a phase may activate slices from
multiple tracks. Dependencies and reopening may cross phase boundaries. The
matrix is only one projection of the actual work relations.

## Progressive Activation

| Pressure | Smallest representation |
| --- | --- |
| one obvious action | `Next Step` only |
| several independently meaningful returns | named slices and material relations |
| one concern must remain coherent across returns | add a track |
| a long migration/review campaign needs a visible ordering horizon | add a phase with entry/exit conditions |
| an item has local executable detail | add steps inside its owning slice/plan |
| outcome or authority becomes independently Human-steerable | create a child task, not a deeper generic level |

No task creates empty tracks, phases, slices, or steps merely because the terms
exist.

## Competing Interpretations

### One recursive result unit plus relations

Keep only `Slice` and `Step`; model concern and time entirely through labels and
relations. This is minimal but risks making Humans repeatedly reconstruct
long-lived workstreams and migration horizons.

### Fixed Track / Phase / Slice / Step hierarchy

Give each task the same tree. This is legible for a narrow class of plans but
fails when one slice crosses tracks or a feedback loop reopens an earlier
phase.

### Typed, optional axes — current Lead preference

Standardize `Track`, `Phase`, `Slice`, and `Step` by distinct jobs, allow only
semantically meaningful relations among them, and activate each by pressure.
This adds two concepts but removes pressure for local synonyms and prevents
`Slice` from owning every grouping function.

## Risks and Falsifiers

- `Track` may duplicate durable product/unit ownership or task-packet modules.
- `Phase` may regress into a linear lifecycle label without explicit exit
  conditions.
- A matrix can become coordination ceremony or suggest false independence.
- A slice that crosses many tracks can still become too large.
- Human readers may find a small tree easier than typed relations despite its
  theoretical inaccuracy.

Reject a primitive when removing it does not make completion, integration,
ordering, authority, or Human steering materially harder to express. Reopen the
model when real plans require repeated local explanations, or when two Agents
map the same work to different primitives despite the contracts.

## Current Inquiry

Before selecting names, test whether these are genuinely distinct semantic
jobs:

1. `Track` — continuing concern/obligation across several returns
2. `Phase` — optional ordered horizon with entry/exit conditions
3. `Slice` — bounded return with an integration/disposition target
4. `Step` — local executable action without independent integration

If they are distinct, the likely common ground is not a deeper hierarchy but a
small typed composition language.
