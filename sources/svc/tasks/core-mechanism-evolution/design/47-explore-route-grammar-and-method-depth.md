# Lead Proposal — Compose Explore Routes Without a Strategy Matrix

- **State**: accepted for design in `D-055`; method detail and outcome evidence
  remain open
- **Consumer**: `WP × P1 / 14-DS`
- **Accepted input**: Route selects a proportionate information-seeking method;
  sufficiency is strategy-relative; the original five contrasts mix epistemic
  jobs and evidence mechanisms
- **Question**: what routing grammar preserves useful distinctions without
  turning Explore into a taxonomy or combinatorial matrix
- **Not decided now**: durable SVC location/wording, exact source filenames,
  Explorer sub-agent SOP, Verification's evidence methods, or tool catalog

## Alternatives

### A — Preserve One Flat Five-Strategy List

`Retrieve / Map / Discriminate / Discover / Probe`

**Benefit**: one recognizable choice after Frame; low apparent vocabulary and
easy examples.

**Failure**: the items are not mutually comparable. A runtime probe can map a
system, discriminate causes, or discover behavior; Map may use static artifacts
or observation; Retrieve is usually much cheaper than the others. Real work
therefore selects several items or changes interpretation mid-route.

### B — Materialize a Full Job × Access Matrix

Select one epistemic job and one evidence-access mechanism from two fixed
catalogs, then prescribe every intersection.

**Benefit**: exposes orthogonality and makes combinations addressable.

**Failure**: creates empty/fake cells, terminology selection cost, and pressure
to fill a taxonomy before any intersection proves a distinct SOP. It repeats
the same matrix-regularity problem rejected for Task Packet Phases and Cells.

### C — One Route, Composed Only When Useful

Keep `Route` as one control point. Describe the next move in plain language,
optionally making two semantic parts explicit:

```text
<epistemic job about target> through <evidence path>,
because <possible result would change or secure the key distinction>.
```

Example:

```text
Distinguish cache invalidation from stale read by inspecting the request trace;
if both remain compatible, use a bounded concurrency probe.
```

The Route is not persisted as a universal field and does not require choosing
catalog labels. The distinction exists to improve method selection and content
ownership when the move is non-obvious.

## Proposed Epistemic Jobs

These are a small method-family index, not an exhaustive ontology:

| Job | Information situation | Characteristic return/sufficiency |
| --- | --- | --- |
| **Lookup** | answer/artifact is expected to exist and target is sufficiently specified | applicable authoritative answer obtained; normally compressed |
| **Model** | relevant structure, behavior, mechanism, boundary, or relations are not understood enough | model preserves the distinctions needed for navigation, explanation, or prediction; not a whole-system map |
| **Generate** | plausible candidates, alternatives, vocabulary, or frames may be missing | materially different families represented; another diverse route has low expected discovery value |
| **Discriminate** | several material explanations, interpretations, or options remain compatible | evidence separates them enough, or leaves only action-equivalent residuals under the loss tolerance |

`Model` replaces the narrower `Map`: a structural code map, behavioral model,
causal explanation, and system-boundary model have a common need to construct
and revise a representation, although their specialized methods may differ.

Jobs can compose or recur. Generate may produce candidates that Discriminate
compares; a Model may expose a new Lookup; a failed Discriminate may force a
new Model. They are strategy families selected inside Route, not stages or new
Working Postures.

## Evidence Paths Stay Mostly Plain-Language

The recurring distinction is whether information already exists in an
accessible source or must be elicited/observed/produced. A minimal working set
for reasoning is:

- inspect, search, or query existing artifacts/data
- observe current behavior/environment
- elicit knowledge, intent, preference, or constraints from a person
- produce a bounded observation through experiment, simulation, prototype, or
  controlled intervention

Do not publish this as a mandatory four-item selection list merely for
symmetry. Evidence paths cross posture and owner boundaries:

- repository search/tool choice and context compression may belong to an
  Explorer sub-agent or specialist skill
- eliciting Human intent/preference belongs to Human collaboration and its
  authority model
- probes that create effects cross the mutation/effect gate
- claim proof, independence, environment validity, and requalification belong
  to Verification

Explore Route states the information need and fitting path; it does not absorb
the full SOPs of every way evidence can be accessed.

## Which Content Deserves Progressive SOP Depth?

### Keep cheap in the Explore core

- `Lookup`: target/source applicability and direct return are usually obvious;
  no separate substantial method by default.
- Route composition: one short explanation only when the method choice or stop
  condition is consequential.

### Candidate Explore specialist methods

- **Model unfamiliar or partially understood systems**: select focus points,
  expand only material relations, vary representation with the sought answer,
  and compress findings into the smallest useful model.
- **Generate missing candidates/frames**: diversify routes and contrasts rather
  than merely collecting more instances of the current family; keep open-world
  residual explicit.
- **Discriminate competing candidates**: state candidates and a separator,
  prefer observations with different predicted outcomes, and update rather
  than defend the favored explanation.

These methods have different characteristic failures and sufficiency rules, so
they provisionally justify progressive depth. They still need their own
case-based derivation before becoming durable content.

### Candidate cross-posture specialist methods, not Explore-owned

- bounded probe/experiment design
- Human elicitation/decision preparation
- claim verification and independent evidence
- repository/tool-specific exploration and delegated context compression

Their use during Explore is an interface. Co-occurrence does not transfer
ownership.

## Case Rehearsal

| Explore situation | Composed Route | What the flat list obscures |
| --- | --- | --- |
| locate the owner and change surface of unfamiliar product behavior | Model the relevant ownership/consumer relations through existing docs and code; observe runtime only if static relations remain ambiguous | “Map” does not say whether to inspect or observe, while “Probe” is only a later access choice |
| explain a production mismatch with several plausible causes | Discriminate the candidates through an existing request trace; if predicted outcomes are not separable there, produce one bounded concurrency observation | Discriminate and Probe are not alternatives: the probe implements the discrimination |
| explore an architecture or product interaction with possible fixation | Generate materially different model families through contrasting precedents and constraints, then Discriminate them through consequential scenarios or a reversible prototype | Discover and Discriminate recur as a loop; forcing one selected strategy hides the return change |
| find the current definition or version of a known API/contract | Lookup the authoritative applicable source directly | a full strategy selection ceremony costs more than the work |

The cases also pressure the proposed job boundaries:

- `Model` is deliberately broad enough to cover structural, behavioral, and
  causal representations, but its later method may need conditional branches;
  it must never mean “understand the whole system.”
- `Generate` and `Discriminate` often alternate, yet remain distinct because
  their characteristic failures differ: missing materially different
  candidates versus collecting evidence that cannot separate known candidates.
- Evidence access can change without changing the epistemic job; the Route
  should then reroute its path rather than pretend the Task entered a new job.

## Cost and Effect Boundary

The composed model is worthwhile only if it changes actual moves—for example,
stops static searching when behavioral evidence is required, prevents probing
before existing authority is inspected, or distinguishes candidate generation
from collecting confirming examples.

It fails if Agents spend attention naming jobs and paths after the correct move
was obvious, if `Model` becomes an unlimited bucket, or if job/access ownership
forces duplicated SOPs. Cheap work must remain one direct move. Real-task
effect and total cost remain unproven; current design only identifies these
falsifiers rather than designing a benchmark or acceptance ritual.

## Recommendation

Adopt Alternative C as the capability model:

1. one Route control point, not two announced selection stages
2. Lookup / Model / Generate / Discriminate as provisional epistemic job
   families
3. evidence path described only as specifically as the current move needs
4. progressive Explore methods only for Model, Generate, and Discriminate after
   independent case derivation
5. probe, Human elicitation, Verification, and Explorer tool method remain
   interfaces with their own future owners

## Review Disposition

Sir accepted the composed single Route, the four non-exhaustive job families,
and progressive Explore depth only for Model / Generate / Discriminate.
`D-055` records that decision. [`design/48`](48-explore-posture-sop-synthesis.md)
consolidates the resulting Explore topology for confirmation before specialist
method derivation continues.
