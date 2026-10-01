# Working Note — Task-Packet Organization Patterns

- **State**: superseded whole-packet archetype proposal; local evidence and
  counterexamples retained; replaced by [`14`](14-composable-task-packet-modules.md)
- **Sources**: `D-013`, `V-013`, `V-030..V-032`, current Working Protocol and
  task-packet template, [`05`](05-shared-task-control-surface.md), and selected
  task packets in this repository
- **Use**: Preserve the local topology evidence and the rejected mutually
  primary packet-type proposal beneath the composable-module model

## Corrected Problem

The current SVC contract defines a five-field `packet.md` and says to split
supporting material when the file becomes hard to scan. That preserves a
minimum interface but does not teach the Agent how to organize a **packet**.

The resulting failure is predictable:

```text
new information arrives
-> no recognized destination or packet pattern exists
-> append it to Current Truth or another packet.md section
-> derivation, history, decisions, evidence, slices, and current control mix
-> packet.md becomes both entry point and entire workspace
-> Human collaboration and Agent recovery degrade together
```

The missing capability is not a larger entry-file schema. It is organization
routing: recognize the task's dominant pressure, choose a familiar package
shape, and keep `packet.md` as the Human collaboration core while other files
serve distinct work.

## Local Evidence, Not a Universal Sample

Current repository packets already show different useful shapes:

| Example | Shape | Observation |
| --- | --- | --- |
| `tasks/v9.8-task-packet-workspace/` | 58-line `packet.md` only | A bounded task can remain compact |
| `tasks/svc-cli-local-acceptance/` | 97-line entry plus baseline, decisions, design map, and design dossiers | Design discussion benefits from a compact Human view plus one active dossier |
| `tasks/v10/50-agent-thread-field-study/` | 46-line entry plus collection, selection, review, diagnostics, and observations | Evidence work needs method and provenance outside the Human view |
| `tasks/v10/70-agent-thread-audit/` | Entry plus method, coverage, synthesis, and case cards | Repeated evidence units benefit from a task-shaped collection |
| `tasks/agent-evidence-telemetry-test-simplification/` | 262-line `packet.md` only | A complex multi-direction, multi-slice task can continue growing as a monolith when no delivery pattern is selected |

These examples support the existence of organization pressure. They do not yet
prove a complete or portable catalog.

## Fixed Interface, Variable Interior

Every pattern preserves the same external contract:

- `packet.md` is the default Human and Agent resume entry
- its body gives the consequential current picture without requiring link
  traversal
- it foregrounds one Human issue, decision, or expected return
- it summarizes supporting work after integration rather than copying its
  derivation or chronology
- the Lead maintains it; sub-agents and specialist work do not independently
  rewrite the shared Human view

The package interior changes because task-local materials have different
consumers and change cadence. A decision argument, evidence case, implementation
slice, and delegation return should not be forced into the same prose merely
because all belong to one task.

## Selection Dimensions

Three dimensions provide routing evidence rather than a Cartesian taxonomy:

| Dimension | Questions that change organization |
| --- | --- |
| Task scale | Is there one bounded front or several interleaved fronts? Will the task survive interruption, handoff, or many material transitions? |
| Task nature | Is the dominant pressure inquiry/diagnosis, design/decision, or approved delivery/acceptance? Which derivation or proof must remain challengeable? |
| Collaboration shape | Is one Lead operating autonomously, is Sir reviewing frequent consequential decisions, or are several Agents producing independently integrated returns? |

Working postures remain orthogonal. `Explore`, `Solidify`, `Execute`, and
`Diagnose` can recur inside any sufficiently complex packet; they are not
directory names or packet lifecycle states.

## Candidate Primary Patterns

### A. Compact packet

**Use when**: one bounded issue, one main owner, little independent derivation,
low handoff pressure, and a short path to relevant proof.

```text
packet.md
```

One supporting note may be added before selecting a larger pattern. Do not
create empty directories for hypothetical growth. A long file is not
automatically wrong, but it fails this pattern when a returning Human cannot
recover the current picture without reading history or derivation.

### B. Inquiry/evidence packet

**Use when**: the result depends on diagnosis, research, cases, competing
causes, provenance, sampling boundaries, or independently reviewable evidence.

```text
packet.md
method.md             # only when evidence handling is non-trivial
evidence/             # cases, matrices, bounded observations, or pointers
synthesis.md          # supported findings, counterexamples, and unknowns
```

Names are illustrative; the stable roles are method, evidence units, and
synthesis. Sensitive or bulky raw evidence may remain outside the repository.
`packet.md` exposes the current claim frontier and evidence boundary, not the
whole corpus.

### C. Design/decision dossier

**Use when**: semantic uncertainty, real alternatives, cross-concern coupling,
or repeated Human rulings dominate the task.

```text
packet.md
design-map.md         # resume route and one active discussion front
decisions.md          # accepted, rejected, deferred, and superseded rulings
design/               # pressure-created dossiers
verification.md       # only when material hypotheses need a ledger
```

`packet.md` states the current synthesis and decision Sir can judge. The map
routes Agent depth; it cannot replace the Human current view. A new dossier is
created for a distinct question or consumer, not for every conversation turn.

### D. Sliced delivery packet

**Use when**: the intended change is sufficiently solidified but execution
crosses owners, components, migrations, environments, or acceptance horizons.

```text
packet.md
plan.md or slices/    # bounded change units, dependencies, and handoffs
verification.md       # cross-slice claim and proof status when needed
acceptance.md         # only for substantial Human/external acceptance
```

`packet.md` keeps the approved boundary, current slice, integrated system
state, next handoff, and residual risk. Completed slice derivation and detailed
proof leave the entry file. External-effect or recovery pressure may add an
Impact Handshake, migration, recovery, or runbook artifact; it does not require
a separate universal packet schema.

## Collaboration Overlay — Multi-Front or Delegated Work

Parallel or delegated work can occur inside inquiry, design, or delivery. It is
therefore an overlay rather than a fifth mutually exclusive base packet:

```text
packet.md
work-map.md           # active fronts, dependencies, owners, integration state
fronts/               # work-unit briefs and integrated returns
```

The exact brief/return shape belongs to the later sub-agent discussion. The
task-packet invariant is already visible: organize by bounded work or claim,
not by Agent identity or heartbeat. Only the Lead integrates a return into
`packet.md`; raw sub-agent output is not Human current truth.

High Human-decision pressure may add or activate `decisions.md` in any primary
pattern. It does not justify copying every option analysis into `packet.md`.

## Avoiding Combination Explosion

Use one primary pattern for the dominant current pressure. Add one supporting
artifact or the collaboration overlay only when another pressure has a real
consumer. A hybrid task may transition or compose patterns, but SVC should not
enumerate every `scale x nature x collaboration` combination.

Selection is qualitative:

```text
Can packet.md still provide the current Human picture cleanly?
  yes -> remain compact
  no  -> identify what has a distinct consumer or cadence
          evidence/provenance -> inquiry pattern
          alternatives/rulings -> design pattern
          slices/handoffs      -> delivery pattern
          parallel integration -> collaboration overlay
```

Do not use a line-count threshold. Upgrade when scan loss, semantic
uncertainty, evidence provenance, coordination handoff, or integration pressure
has become material. Transition without ceremony: create the smallest useful
supporting owner, move derivation rather than current meaning, and update
`packet.md` with the resulting current picture and resume route.

## Rough SVC Landing Shape

- Working Protocol should keep the universal minimum: what the task packet is,
  the `packet.md` Human contract, start-compact routing, split/transition
  pressure, and progressive loading.
- The pattern catalog now has concrete content, a distinct non-trivial-task
  trigger, and an Agent consumer. A pressure-loaded
  `src/sections/task-packet.md` is therefore a credible candidate rather than a
  hypothetical file, but it is not yet approved.
- The existing task-packet template should remain the common entry-file shape.
  Pattern examples or additional templates are justified only if prose routing
  repeatedly fails; one template per pattern would create premature surface.
- Consumer `tasks/<task-id>/` directories remain task-owned and disposable.
  SVC teaches recognizable roles and examples, not an exhaustive allowed tree.
- CLI has no semantic role. It may distribute the admitted source later.

## Superseded Questions

1. Is “four primary patterns plus a multi-front/delegation overlay” a useful
   compression, or should collaboration topology be a primary pattern itself?
2. Are inquiry, design, and delivery the right dominant task natures, or is a
   common recurring shape missing?
3. Should the catalog show illustrative filenames as above, or define only
   artifact roles and let every task choose names?
4. Does the pattern catalog now justify a separate pressure-loaded SVC section,
   or can a compact version remain legible inside Working Protocol?

These questions and the former recommendation are retained only as the
superseded alternative. `D-014` replaces whole-packet primary patterns with
progressively composable modules and separates task coordination from
delegation and implementation slicing.
