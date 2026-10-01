# Working Note — Implementation Slice and Delivery Boundary

- **State**: accepted task-packet design input (`D-041`)
- **Sources**: `D-015..D-017`, `D-025..D-040`; `V-008`, `V-034`,
  `V-039`, `V-053..V-059`, `V-072..V-075`; current Working Protocol mutation
  gate; real implementation-plan, implementation-rehearsal, delivery-plan,
  migration-plan, and per-Slice Impact Handshake packets
- **Use**: Place implementation control where it lowers mutation, recovery,
  delegation, and integration cost without creating a duplicate Plan, source
  shadow, or generic delivery bureaucracy

## The Existing File Names Hide Several Different Jobs

Historical packets named `implementation-plan.md` or `delivery-plan.md`
commonly combine:

1. Plan sequencing and status
2. pre-implementation design/topology rehearsal
3. mutation scope and Human authority
4. per-Slice implementation detail and Agent assignment
5. verification/acceptance evidence
6. migration, rollout, release, or external recovery state

These jobs do not share one owner or lifecycle. Standardizing the historical
file name as a semantic module would preserve the overlap rather than solve it.

## Field Pressure

| Case | Useful content | Boundary failure exposed |
| --- | --- | --- |
| Ensure-dev-server, 100-line `implementation-plan.md` | exact owner surfaces, dependency order, gates, backout, and parallel boundary | largely duplicates the Task Plan while combining one Task-wide handshake with eight implementation units |
| Agent Observability, 445-line `delivery-plan.md` | dependency graph, Slice exits, exact per-Slice mutation contracts, completion state | one file owns plan, repeated handshakes, status, and automatic acceptance; it becomes a second oversized control surface |
| Agent Observability, 190-line `implementation-rehearsal.md` | current fractures, target topology, failure simulation, resource model, review triggers | despite its name it is design/preflight evidence for `DS`, not implementation state |
| Tag-authoritative Release, 214-line `migration-plan.md` | hard-cut topology, external sequencing, rollback boundaries, real execution result | migration/release is a continuing domain obligation spanning design, implementation, external mutation, and acceptance, not a generic implementation module |
| same task, 226-line `impact-handshake.md` | exact address, state diff, blast radius, and proof per Slice | correctly Slice-relative, but separated from the Plan owner and repeats shared/current state at growing scale |
| CLI local acceptance, 626-line “implementation plan and preflight” | file-level change map, batches, sequence simulations, verification matrix, measured preflight | this is primarily a deep design dossier plus mutation proposal; naming it a Plan obscures its information owner |

The examples show real need for implementation control, but not an independent
cross-Slice `implementation.md` semantic owner.

## Owner Decomposition

| Information | Owner |
| --- | --- |
| current route, ordering, TBC, Slice state | Task/Track/Phase/Cell Plan |
| accepted system model and realization constraints | `design.md` / `decisions.md`, then normal durable owner |
| bounded system-state transition and its return | one `IM` Slice |
| exact mutation scope, authority, invariants, recovery, and proof horizon | the same `IM` Slice's implementation contract |
| detailed impact map, preflight simulation, temporary transformation rule, or delegated work order | Slice-owned supporting artifact when pressure requires |
| observed proof or acceptance disposition | later Verification/Acceptance module contract |
| long-running migration, rollout, release, or adoption obligation | a semantic Track/Phase/Cell topology, named for that obligation |
| realized behavior and structure | code, schema, configuration, tests, durable docs, or external system owner |

Implementation is therefore primarily a **Slice return and mutation contract**,
not a peer semantic module. “Delivery” is too ambiguous to be a default module:
it may mean source integration, consumer migration, rollout, release, or Human
acceptance, each with different owners and proof horizons.

## The `IM` Slice Contract

The Plan entry keeps the compact management view. Expand only the fields whose
risk or complexity is material:

- **return**: exact changed system claim/state plus required integration result
- **baseline/preconditions**: source, configuration, environment, or external
  state on which the change is valid
- **address and state diff**: owner surfaces and objective `From -> To`
- **invariants and exclusions**: behavior, authority, compatibility, and
  unrelated state that must remain unchanged
- **realization route**: deterministic transformation, direct Lead work, or
  bounded Executor/Assignments
- **feedback and proof horizon**: observation that discriminates progress and
  the verifier/certificate needed for integration
- **recovery/stop/escalation**: reversible boundary, failure containment, and
  evidence that returns work to `IQ` or `DS`
- **effect authority**: requested/approved mutation scope and any later
  external or irreversible gate that remains separate

For a small local mutation, this may be one Plan row plus a few Steps. Do not
force an eight-field form. The existing Impact Handshake is the risk-expanded
projection of this contract, not a separate Plan and not implementation
authorization by itself.

## Small, Stable Development Loop

An `IM` Slice should be shaped around the smallest independently integratable
state transition with a useful feedback surface:

```text
accepted specification/model S + current baseline X
                    ↓
bounded executor/transformation produces candidate Y + evidence W
                    ↓
independent check or Human product observation V(S, X, Y, W)
                    ↓
adjust locally / return to IQ or DS / accept candidate
                    ↓
effect gate and Lead integration
```

The loop is stable when:

- the candidate can be assessed before its effects spread farther
- feedback discriminates a real product or technical expectation
- failure has a bounded recovery or honest escalation path
- one Agent/Assignment can own the candidate without also owning acceptance
- the Slice can return a coherent changed state rather than a pile of edited
  files

This accommodates the handwriting example: replay real pen data, render the
glyph, let Human judge the product observation, and repeatedly adjust the
input-to-glyph function. The Slice is not “edit these files”; it owns the
bounded behavioral transition and feedback loop.

## Deterministic Transformation Before LLM Editing

Edit volume does not justify an Executor or implementation module. When the
change is expressible as a structural rule with a deterministic match/edit and
verification surface, use a codemod, AST rule, Grit-like transformation,
formatter, schema migration, or script.

The rule/script and dry-run result may be temporary Slice artifacts. If the
same prevention or transformation is expected again, its useful destination
is durable tooling, a linter, or another normal owner—not a permanent packet
procedure.

LLM execution earns its cost where semantic judgment, local adaptation, or
feedback-driven development remains after deterministic work is extracted.
It should still receive a bounded contract and return a candidate plus proof,
not an unreviewed multi-file activity log.

## Progressive File Shape

### Inline by default

```text
Cell or Task Plan
  03-IM · migrate owner boundary
    return / effect / state
    Steps or Assignments
```

### Slice-owned supporting depth under pressure

For a two-axis Cell:

```text
cells/<track>-<phase>.md
cells/<track>-<phase>/
  03-IM.md              # expanded contract/work order when needed
  03-IM-transform.md    # temporary deterministic rule/rehearsal if useful
```

The exact artifact suffix is semantic; no universal `implementation/`
directory is created. A one-axis Plan uses the same ownership relation at its
stable Plan entry.

An expanded Slice artifact is warranted for cross-owner impact, several
coherent batches, delegated execution, non-trivial recovery, external effects,
or a detailed preflight that would swamp the Plan. It is not a module, does
not own independent current status, and returns to the Plan.

## Delivery Is Topology or Domain State, Not a Generic Module

Use the actual continuing obligation:

- `Migration` Track for compatibility/data transition across Phases
- `Release` Track for qualification, publication, and recovery
- `Rollout` Track for progressive runtime exposure and observation
- `Adoption` Track for consumer transition

Only admit such a Track when the obligation persists across several Slices or
barriers and has positive management value. A single local code change does
not acquire a Delivery Track.

External execution state may require a task-local semantic artifact or module,
but it should be named for the real owner—release attempt, migration cohort,
rollout state—not generic `delivery.md`. Exact run IDs, published artifacts,
irreversibility, and recovery evidence later meet the Verification/Acceptance
contract rather than living as prose completion claims in an implementation
file.

## Human Projection

During an active `IM` Slice, `packet.md` needs only the consequential current
view:

- what state transition is active
- whether durable/external mutation is authorized
- current proof/feedback or material mismatch
- next effect gate or decision needing Human attention

It does not list every file, completed Step, or test. A changed state diff,
blast radius, or irreversible boundary returns to Human before mutation; an
ordinary local adjustment inside the approved contract does not.

## Failure Modes and Falsifiers

- `implementation.md` becomes a second Plan or a manual change log.
- file checklists replace semantic changed-state returns.
- source/config truth is copied into the packet and becomes stale during edits.
- an Impact Handshake is treated as mutation permission or repeated unchanged
  for every trivial Step.
- a long “delivery plan” hides distinct migration, release, and acceptance
  authority boundaries.
- every tool output and patch attempt is retained as execution history.
- deterministic refactors are delegated as many correlated LLM edits.
- implementation failures silently broaden the design rather than return to
  `IQ`/`DS`.

Reopen the module-negative conclusion if real Tasks repeatedly need one
cross-Slice realization state consumed by several Plan owners and neither
Design, Cell Plan, Slice artifacts, nor a real domain Track can own it without
costly duplication. Such evidence may justify a specifically named
`realization.md` module; it would not automatically justify generic
Implementation or Delivery modules.

## Lead Recommendation

1. Do not standardize `implementation.md`, `implementation-plan.md`, or
   `delivery-plan.md` as task-packet semantic modules.
2. Make the `IM` Slice own the bounded implementation/mutation contract and
   the Plan own sequence/state.
3. Expand implementation detail into Slice-owned supporting artifacts only
   under impact, delegation, preflight, or recovery pressure.
4. Route expressible repetition through deterministic transformations; use an
   Executor for the remaining bounded semantic/feedback loop.
5. Represent persistent delivery obligations as specifically named
   Track/Phase/Cell topology and keep acceptance evidence with its later
   verification owner.
