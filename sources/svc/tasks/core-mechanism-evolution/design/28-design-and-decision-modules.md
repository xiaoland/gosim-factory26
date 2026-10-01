# Working Note — Design and Decision Task-Packet Modules

- **State**: accepted task-packet module model; package details remain subject to real-task evidence
- **Sources**: `D-014..D-016`, `D-024..D-026`, `D-034..D-040`;
  `V-062..V-073`; current SVC owner registry and Working Protocol; contrasting
  task-local `design.md`, `proposal.md`, design-resolution, compact decision
  register, detailed decision dossier, and high-volume decision-ledger cases
- **Use**: Give design work and authoritative task-local dispositions stable,
  progressively loaded information owners without turning them into lifecycle
  phases, duplicate Plans, or shadow durable architecture truth

## Two Adjacent Semantic Jobs, Not One File Type

Design and decision often occur in one `DS` Slice, but their information has
different update semantics:

- **Design** constructs and revises a coherent candidate model from intent,
  evidence, constraints, taste, and expected system consequences. Its current
  synthesis is deliberately mutable while the question remains open.
- **Decision** records an explicit disposition by the applicable authority so
  later work does not reopen or reinterpret the same choice accidentally. An
  accepted decision is superseded or reopened explicitly, not silently edited
  into a different historical meaning.

Therefore they should be adjacent modules with different contracts, not one
generic “thinking” dossier and not automatically one file. A Task may activate
either one without the other.

`DS` remains the Plan/Slice return scope. `design.md` and `decisions.md` own
information state; neither owns sequencing.

## Field Pressure

The sampled current packets expose several useful shapes and failure modes:

| Case | Useful pressure | Visible limitation |
| --- | --- | --- |
| v10 Versioned Consumption, 129-line `design.md` | one coherent system model can carry authority, state-machine, SemVer, and proof consequences | confirmed decisions, full design, implementation gate, and later supersession share one surface |
| v10 Agent Observability, 78-line `slice-0-decisions.md` | a 16-row frozen-answer register is cheap to scan and bounds later implementation | most rows omit local rationale, evidence boundary, reversibility, and reopen condition |
| v11 Tag-authoritative Release, 279-line `slice-0-decisions.md` | four decisions preserve substantial rationale, evidence, authority matrix, and migration consequences | cohesive design explanation and decision record accrete into one long file |
| v9.6 Multi-repo, 53-line design resolution | objection-oriented resolution makes the changed model and reasons concise | rejected alternatives, authority, and later invalidation path are mostly implicit |
| Test-topology ROI, 143-line decision ledger | one common rule plus many repeated dispositions supports high-volume review | it is a mechanical disposition register, not a reusable system design narrative |
| this task, 955-line `decisions.md` | stable IDs and explicit reopen triggers preserve long discussion continuity | one semantic register has crossed a physical reading/editing pressure and now earns mechanical sharding |

These cases do not prove outcome improvement, but they show that “design” and
“decision” are already recurring semantic jobs and that file names alone do
not preserve their boundary.

## Progressive Package Shape

### Level 0 — inline

A bounded, reversible choice with one obvious consumer stays in the owning
Plan/`DS` Slice. Do not create a file merely because design reasoning occurred.

### Level 1 — stable entries

Activate the relevant entry when its semantic pressure is credible:

```text
packet.md
design.md       # current design synthesis, when needed
decisions.md    # task-local dispositions, when needed
```

The files are independently optional. Their stable names prevent
`proposal-v2-final.md`, chronological navigation, and repeated rediscovery of
which file is current.

### Level 2 — same-stem depth

When one entry cannot remain a cheap synthesis surface:

```text
design.md
design/
  release-authority.md
  migration-recovery.md

decisions.md
decisions/
  D001-D010.md
  D011-D020.md
```

Design depth follows independently reviewable semantic concerns, vertical
rehearsals, or alternatives that need their own evidence. Decision depth may
use deterministic ID-range sharding solely to lower file operation cost; the
shards remain one semantic module. Neither directory is pre-created.

`decisions.md` remains the stable current map when sharded: it expands the ID
grammar and carries the compact title/state/authority/current-effect view that
routes to full records. It need not repeat every rationale.

## Activation Pressure

Activate `design.md` early when at least one of these pressures is material:

- several real alternatives or interacting trade-offs must remain comparable
- product/technical taste or a consequential Human review is required
- authority, topology, lifecycle cost, compatibility, recovery, or another
  hard-to-reverse boundary is being shaped
- several owners/consumers must receive one coherent candidate model
- delegated design work must return into one Lead synthesis
- implementation depends on assumptions or a vertical system rehearsal that
  would be expensive to reconstruct

Activate `decisions.md` when a disposition must remain addressable across
Slices, Cells, handoff, or task switching; when several decisions interact; or
when authority, supersession, deferral, and reopen state can no longer remain
clear inline.

Multiple alternatives by themselves do not require a decision register until
an authority actually disposes of something. Multiple decisions do not require
a design module when a common rule and bounded repeated classifications are
sufficient, as in the ROI ledger.

## `design.md` Entry Contract

The entry should make the current model reviewable without replaying the
reasoning history:

1. design question and return horizon
2. current recommended model and the problem it solves
3. governing intent, constraints, taste, and evidence references
4. materially distinct alternatives and why they differ
5. product, technical, lifecycle, reversibility, and change-cost consequences
6. vertical rehearsal across affected owners/consumers where cross-boundary
   behavior matters
7. assumptions, unresolved tensions, falsifiers, and next discriminating
   question
8. exact decision needed from Human or other authority, if any

It does not own a duplicate Plan, raw brainstorm, query transcript, generic
chronology, implementation progress, or copied durable documents. Supporting
files provide depth; the entry preserves the integrated current model.

## Human Decision Surface

The Agent should not transfer synthesis work to Human. When a ruling is
needed, `packet.md` projects one current decision in the language of the
conversation:

- the exact question and why it matters now
- the Agent's recommendation
- the few materially distinct alternatives
- consequences that differentiate them, including reversibility and future
  change cost
- decisive evidence, assumptions, and residual unknowns
- the smallest authority being requested and what happens after the ruling

The full design may remain in `design.md`; `packet.md` is not an index and must
contain enough of the actual case for Human judgment. Low-level option
generation and mechanical comparison remain Agent work.

## `decisions.md` Record Contract

A material record preserves only what later work needs to respect or reassess:

- stable ID expanded in local language, state, authority, and date
- exact disposition and affected scope
- causal rationale and decisive evidence/assumptions by reference
- important rejected/deferred alternatives when their recurrence is likely
- consequences for current Plan/consumers
- supersedes/superseded-by relation and a concrete reopen condition

The register does not copy the complete design. A compact repeated
classification can use a table under one stated decision rule; a consequential
system choice earns an individual record. Mechanical “ten records per shard”
organization changes storage, not semantic admission.

## Return and State Transitions

```text
IQ return / current durable truth
              ↓
       design synthesis
              ↓
   Agent recommendation + Human/owner ruling
              ↓
 task-local decision disposition
              ↓
 Lead integrates DS return into the owning Plan
              ↓
 IQ / IM / VR / TBC as the new route requires
```

- A `DS` Slice may update design and decisions, but it completes only when its
  declared return is integrated or explicitly parked.
- A Human message is not automatically a durable project decision; Lead must
  integrate its exact scope and consequences into task state.
- Implementation friction that only changes tactics remains inside `IM`.
  Evidence that invalidates the accepted model opens `IQ` or a new `DS`
  boundary; accepted history is not silently rewritten.
- Design and decision validity inherit material baselines and invalidation
  conditions from their evidence and owners. A stale premise cannot support an
  unqualified current recommendation.

## Boundary with Durable Truth

Task-local accepted design and decisions coordinate the current Task; they are
not durable architecture or product owners. Once an accepted change is
implemented, the applicable Plan updates code, schema, configuration, PRD,
Product TDD, Unit TDD, Deployment, ADR, or another semantic owner according to
the claim.

An ADR is admitted only for a durable technical decision with real alternatives
and long-lived consequences. A task decision can instead disappear with the
packet when code or another normal owner makes its meaning cheap to recover.
Consistent with `D-025`, design/decision entries do not maintain speculative
promotion-target paths; a later Plan item is created only after a real semantic
delta exists.

## Failure Modes and Falsifiers

- `design.md` becomes a second PRD/TDD or a chronological journal.
- `decisions.md` records every Agent micro-choice and becomes bureaucracy.
- Human receives a document link or option dump instead of a decision-ready
  brief and recommendation.
- A decision ID or “accepted” label hides who had authority or what scope was
  accepted.
- Supporting design files each present a local recommendation without one Lead
  synthesis.
- Implementation silently changes an accepted design rather than returning
  evidence to `IQ`/`DS`.
- Stable entries and sharding cost more than rediscovery, review, and drift they
  prevent in ordinary tasks.

Reopen the two-module boundary if real Tasks rarely need one without the other,
or if one stable `design.md` with embedded dispositions provides the same
Human/Agent management value at materially lower synchronization cost.

## Lead Recommendation

1. Treat Design and Decision as adjacent but independently activated semantic
   modules; `DS` Slice remains their work/return owner.
2. Standardize stable `design.md` and `decisions.md` entries, with same-stem
   depth admitted only by semantic or physical pressure.
3. Make `design.md` a mutable current synthesis and `decisions.md` an explicit
   disposition register with authority and reopen semantics.
4. Project one decision-ready brief into `packet.md`; do not make Human read
   the design dossier to learn the actual choice.
5. Keep both modules task-local and route accepted system truth through later
   Plan work to its normal durable owner.
