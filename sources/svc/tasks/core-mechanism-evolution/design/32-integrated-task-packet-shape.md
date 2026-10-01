# Working Note — Integrated Task-Packet Shape

- **State**: integrated Task Packet synthesis; Inquiry/Diagnosis and distributed
  Verification boundaries accepted through [`D-043`](../decisions.md)
- **Sources**: accepted `D-013..D-042`; corrected `V-082`, `V-083`;
  [`design/24..31`](../design); current Working Protocol and template inventory
- **Use**: Reconcile the Human entry, work topology, information modules,
  progressive file growth, template namespace, and rough durable SVC landing
  before leaving the Task Packet functional cluster

## One Package, Three Different Jobs

A task packet is one volatile filesystem package serving Task completion. Its
contents are not peers:

| Layer | Question answered | Primary consumer |
| --- | --- | --- |
| Human current view | What is this Task, what matters now, and what does the Human need to know or decide? | Human and Lead |
| work topology | Where is work currently controlled, sequenced, blocked, returned, and integrated? | Lead and executors |
| information topology | Which inquiry, design, decision, or verification concern needs a stable current synthesis and depth? | Agents performing/reviewing that concern |

Coordination remains a material relation set over work topology—assignment,
authority, dependency, verifier, return, and integration—not a fourth directory
tree or runtime scheduler.

Only `packet.md` is universal. Every other path is admitted by semantic
pressure and has an explicit owner.

## Universal Human Entry: `packet.md`

The five current responsibilities remain useful:

- **Objective**: intended task outcome, not a process description
- **Guardrails**: authority, invariants, and excluded effects
- **Verification**: terminal claim and required evidence horizon, not a test
  command inventory
- **Current Truth**: compressed accepted state, material uncertainty, active
  mismatch, and consequential module/Plan returns
- **Next Step**: next concrete Agent action or one Human decision/review need

For an activated Task map, `Current Truth` includes one compact Human-language
table/list projection of current Plan owners/Cells:

```text
owner/Cell | barrier state | current return or next | Human attention
```

The body must remain sufficient; links provide optional depth rather than
completeness. A returning Human should not need `task-map.md`, a module dossier,
or the conversation transcript to reconstruct the consequential current state.

### Compression contract

`packet.md` should read like the next useful Human-Agent conversation turn, not
an audit register:

- use the language in which Human and Agent are actually collaborating
- foreground one current issue; retain another only when it changes that issue
- synthesize accepted foundations instead of appending one bullet per decision
- collapse completed/history detail unless it changes reopening, risk, or the
  current choice
- project outcomes and residual unknowns, not work logs, every Slice/Cell, test
  counts, or module indexes
- link the one active dossier when deeper review is useful; do not make the
  link carry the proposition

No fixed line limit is semantically reliable, but root growth itself is a
signal to rewrite and integrate—not a reason to split the Human view into a
second root file.

## Common Work Vocabulary

The accepted management objects have different jobs:

| Object | Management meaning |
| --- | --- |
| Task | objective, authority/guardrails, verification, resume, and terminal return boundary |
| Track | horizontal continuing obligation whose state must remain visible across changing work |
| Phase | scoped vertical semantic barrier; only real shared wait/exit predicates justify it |
| Cell | real participating `Track × Phase` coordinate and default Plan owner |
| Plan | current partial linear route under one owner; may end TBC with a continuation condition |
| Slice | bounded independently useful return/integration unit inside one Plan |
| Step | concrete next action retained only when it improves control or recovery |
| Assignment | bounded execution delegation inside a Slice; parallel Agents do not create Plan topology |

Slice handles use one Plan-local sequence and an optional return-scope tag:

```text
01-IQ -> 02-DS -> 03-IQ -> 04-IM -> 05-VR -> 06-RT
```

`IQ`, `DS`, `IM`, `VR`, and `RT` communicate epistemic, design/decision,
implementation, verification/acceptance, and retrospective return scope. The
tag does not bind internal working posture or grant authority. Simple,
unambiguous one-return Tasks need not display a tag.

`TBC` is a Plan continuation horizon with a condition, not a Slice or scope
tag. A current Plan may retain the immediately relevant completed return, but
it must not become a completed-work ledger; integrate older consequences into
the applicable Cell/module/decision owner and compress the route.

The exact RT SOP, consumer, return, and task-level Plan placement remain open
for the Working Protocol cluster. Its existence as a Task activity is not
conditional on fitting a Cell or becoming a new Task.

## Progressive Work-Topology Shapes

### Shape 0 — compact Task

```text
<task>/
  packet.md               # may contain the small Task Plan inline
```

Use when one Human/Lead can hold one bounded route without independent
information ownership. This remains a real packet even with one file.

### Shape 1 — one deep Task Plan

```text
<task>/
  packet.md
  plan.md                 # only when the one Plan needs stable Agent depth
```

`plan.md` owns the partial linear Task Plan; `packet.md` projects its
consequential current return/next. Do not create `plans/` for one Plan.

### Shape 2 — one-axis topology

```text
<task>/
  packet.md
  task-map.md
  track-<semantic-name>.md ...

# or, when Phase is the only axis
  phase-<semantic-name>.md ...
```

At Track/Phase admission, shape preflight creates every real Plan-owner entry
before detailed work accumulates, even when its Plan currently ends TBC.
`task-map.md` owns declarations, current fronts, barriers, relations, and
integration; each owner entry owns its Plan. No default `tracks/`, `phases/`,
or `plans/` directory exists.

### Shape 3 — two-axis topology

```text
<task>/
  packet.md
  task-map.md
  cells/
    <track>-<phase>.md
    <track>-<phase>/       # only after pressure creates supporting depth
      <slice-or-artifact>.md
```

Create one Cell entry for every real participating coordinate and no future,
out-of-scope, `N/A`, or symmetry-only Cell. The entry owns Track obligation,
Phase contribution, current satisfaction/evidence state, partial Plan,
relations, and expected barrier return.

The same-stem Cell directory appears only for a substantial Slice artifact,
immutable receipt, or the bounded multi-Plan exception. A Cell does not become
a nested Task, and a directory does not own state independently of its entry.

### Nested Task

A nested `packet.md` is admitted only when the work has its own objective,
authority/guardrails, verification, resume point, and terminal integration
return. A Phase, Cell, Slice, finding, Agent instance, RT scope, or file volume
does not establish that boundary.

No universal nested-task collection path is selected yet; semantic ownership
and the parent return should determine its local name.

## Progressive Information Topology

Every semantic module follows:

```text
inline in owner/packet
  -> <module>.md
  -> <module>.md + <module>/<semantic artifacts>
```

The stable entry owns current integrated state and return. It is not an index,
history, or miniature `packet.md`. Same-stem depth appears only with the first
independently useful artifact. Mechanical ledger sharding remains one module.

### Refined module catalog

| Concern | Stable entry | Activation pressure | Important exclusions |
| --- | --- | --- | --- |
| Inquiry | `inquiry.md` | multi-source/case, method/sampling, provenance, cross-consumer, delegated research, freshness risk, or an observed mismatch needing causal discrimination | raw search transcript, repair Plan, implementation progress, verification acceptance |
| Design | `design.md` | alternatives/trade-offs, cross-owner model, hard-to-reverse boundary, delegated design, Human taste review | accepted-decision register, durable design truth |
| Decision | `decisions.md` | disposition must survive Slice/Cell/handoff and retain authority, rationale, consequence, reopen/supersession | mutable design exploration, project truth |
| Verification | `verification.md` | cross-return claims/horizons, several proof owners, certificates, partial results, expensive external/Human evidence, requalification | work sequence, raw logs, product requirements, acceptance authority |

Diagnosis is an Inquiry kind/method, not a peer module or alternative stable
entry: a bug Task can title `inquiry.md` as a diagnosis and grow semantic probe
artifacts under `inquiry/`. Design and Decision are adjacent, independently
activated modules. Verification may mix planned obligations and observed
results because they share one claim/evidence lifecycle, but distributed
verification work remains owned by applicable Plans/Slices/Cells/barriers.
`verification.md` exists only for shared task-level synthesis and does not imply
a final verification stage.

### Explicit module-negative boundaries

Do not standardize these peer modules:

- `implementation.md`, `implementation-plan.md`, or `delivery-plan.md`:
  implementation is an `IM` Slice mutation/return contract; persistent
  migration/release/rollout/adoption is specifically named Task topology
- `acceptance.md`: acceptance is an authority-bearing disposition at the
  consuming integration/barrier/Human/external effect gate
- `retrospective.md`: current evidence supports a task-level close-screen and
  later protocol-directed activity, not an independent information lifecycle
- generic `coordination.md`: coordination is the smallest material relation
  projection over current work owners and Assignments

This does not prohibit a supporting artifact with one of those words in its
semantic name, such as an immutable release-attempt certificate. Artifact
ownership remains explicit.

## Module Entry and Root Return

A module entry lets its Agent consumer recover, in locally natural language:

1. owned concern and exclusions
2. current integrated synthesis/disposition
3. authority, evidence, baseline, and freshness boundary
4. current question/return or relevant status
5. only the depth needed to continue or audit
6. consequential return path to Plan, `packet.md`, another module, or durable
   owner

Update flows outward from authority:

```text
artifact/observation
  -> module or Plan owner integrates
  -> task-map integrates affected front/barrier
  -> packet.md projects Human consequence
```

Do not synchronize the same detailed state across all layers. Contradictions
are repaired from the deepest authority outward.

## Activation, Growth, and Retirement

### At Task opening

1. Create `packet.md` in the Human collaboration language.
2. Identify the smallest credible current Plan owner and whether Track/Phase
   topology is already semantically obvious.
3. If topology is admitted, create `task-map.md` and every real stable Plan
   owner atomically; do not wait for length or a cleanup reminder.
4. Keep information concerns inline until their distinct owner/consumer,
   evidence, review, cadence, or integration pressure is real.

### During work

Activate a module/artifact only when useful content exists now and its bounded
retrieval, review, provenance, conflict, or integration return repays creation
and synchronization. Posture, line count, Agent count, and imagined future
growth are not sufficient triggers.

When evidence changes topology, revise the semantic owners and paths in one
coherent shape transition, then update Task-map and Human projections. A growth
reminder/sub-agent may audit drift later but cannot replace this admission rule.

### At concern or Task closure

Integrate consequential state into the remaining Plan/root/durable owner, then
retire supporting scaffolding whose consumer/cadence ended. Known durable
deltas are implemented through normal Plan work rather than postponed to
packet deletion. The whole packet remains volatile and follows repository
retention directly.

Project-truth consolidation and Agent work-system adaptation remain separate
closing SOPs. The latter's detailed close-screen and future-consumer semantics
are intentionally deferred.

## Reusable Template Namespace

The current flat `task-packet.template.md` visually teaches “task packet equals
one file.” The accepted namespace direction is:

```text
src/assets/templates/task-packet/
  packet.template.md
  # pressure-proven optional templates only
```

The directory names the **template family**, not a directory that Consumers
must copy wholesale. CLI/catalog lookup exposes each source file on demand;
ordinary task creation still starts only from `packet.template.md`.

Candidate optional templates, admitted separately after prose/examples prove
insufficient, are:

```text
plan.template.md
task-map.template.md
cell.template.md
inquiry.template.md
design.template.md
decisions.template.md
verification.template.md
```

No implementation, delivery, acceptance, retrospective, `tracks/`, `phases/`,
or generic slice template is currently justified. A template's existence must
not cause automatic file creation. The current diagnostics-matrix template is
reviewed by its own consumer/compatibility contract rather than moved merely
for visual symmetry.

Moving the existing catalog path is a Consumer-visible packaged-resource
change. Exact compatibility and Behavioral SemVer treatment belong to the later
landing plan; the Task Packet cluster accepts the target namespace, not an
unreviewed deletion of the old address.

## Rough Durable SVC Landing

No source mutation is authorized yet. The smallest coherent later ownership is:

```text
src/sections/working-protocol.md
  universal packet minimum, Human projection, Plan/protocol entry,
  mutation/verification/closing routing

src/sections/extensions/task-packet.md
  progressive packet grammar, activation/retirement, root integration

src/sections/extensions/task-packet/
  planning.md
  inquiry.md
  design-decisions.md
  implementation.md       # IM Slice contract, not a packet module
  verification.md

src/assets/templates/task-packet/
  packet.template.md
  <only templates separately admitted above>
```

The exact source split remains conditional on final content size and navigation
rehearsal. `working-protocol.md` must stay a compact universal router; the
pressure-loaded entry must be directly discoverable through packaged lookup.
RT/adaptation guidance is not added to this tree until its SOP is discussed.
CLI remains a deterministic catalog/template carrier, not a semantic packet
selector, task graph, status engine, or automatic module grower.

## Dogfood Findings from This Packet

The current design Task validates the need for concern modules and also exposes
two cleanup pressures:

- `packet.md` has grown by appending one accepted-contract bullet at a time;
  it remains complete but is no longer an economical Human current view and
  should be semantically recompressed after this cluster is accepted
- `decisions.md` exceeds one thousand lines; the accepted deterministic ID-range
  sharding can reduce read/edit/conflict cost while one entry retains routing
- the rename to `design.md + design/` rehearses the stable sibling-entry shape
  and removes a role-specific entry suffix

These are task-packet maintenance candidates, not proof that every Consumer
needs the same depth. Applying the accepted shape here after Human review is a
useful vertical rehearsal before durable SVC landing.

## Review Proposition

Accept the integrated direction if all of these remain faithful:

1. `packet.md` is the only universal file and remains a complete compact Human
   current view.
2. Work topology grows from inline Task Plan to stable Plan owners at semantic
   topology admission, with `task-map.md` plus Cell files only when applicable.
3. Information topology admits Inquiry, Design, Decision, and Verification
   modules independently under pressure; diagnosis remains an Inquiry method,
   while verification activity remains distributed beneath optional task-level
   synthesis.
4. Implementation, Delivery, Acceptance, Retrospective, and Coordination stay
   with their accepted Slice/disposition/activity/relation owners rather than
   becoming default modules.
5. Template namespace expresses a packet family without causing scaffold
   creation; only the Human entry template is initially universal.
6. Working Protocol remains the universal router; detailed task-packet guidance
   is progressively loaded; CLI does not become the semantic orchestrator.
7. RT remains a legitimate original-Task activity whose SOP, return, consumer,
   and Plan placement are discussed next rather than guessed here.
