# Working Note — Task-Packet Module Grammar

- **State**: four-object and progressive-entry grammar accepted through
  `D-034`; mechanical-sharding distinction accepted through `D-035`; corrected
  work-topology projection continues in [`25`](25-task-map-and-cell-files.md)
- **Sources**: `D-013..D-033`; `V-033`, `V-038`, `V-043`, `V-044`,
  `V-050..V-061`; current SVC template/protocol; current InKCre, Workbench,
  Surface Camera, and this design packet
- **Use**: Define how a task packet grows from one Human entry into useful
  modules without equating a file split, Agent instance, posture, or directory
  with a semantic owner

## Why a Module Grammar Comes First

Naming `design/`, `verification/`, `tracks/`, or `instances/` before defining
their owners would reproduce the current problem at directory scale. A module
is useful because it lowers control/recovery/integration cost for a distinct
task-local concern; a directory is only one possible storage projection.

The required common ground is therefore not one mandatory tree. It is a small
grammar for:

1. what counts as a packet, module, supporting artifact, or nested Task
2. when each receives a stable address
3. how it grows without breaking the Human entry or creating empty structure
4. what its entry must tell the next Agent
5. how work topology and information topology avoid duplicating one another

Specific inquiry, design, implementation, verification, and retrospective
package contracts can then specialize this grammar.

## Field Pressure

### InKCre

The knowledge-lifecycle packet usefully separates three Track files and three
implementable-unit directories. The Track files are compact continuing-
obligation caches; implementable units have their own objective, guardrails,
verification, design, evidence, and implementation plan.

Pressure appears elsewhere:

- the root packet still carries a large current-understanding history
- 170 decisions are divided into deterministic ten-ID shards plus an index;
  this has real bounded-read/edit value even though each shard is not a
  separate semantic module
- one unit packet has grown into a long cross-concern monolith despite having
  supporting files

The useful distinction is not “directory good, file bad.” Track and independent
unit ownership are useful; deterministic ledger sharding can be useful physical
management; repeated integrated state remains costly. Storage partition and
semantic modularization are different decisions.

### Workbench

The Coding Surface root contains many 175–415-line product, architecture,
experience, contract, implementation, and acceptance files plus deep Sub-task
and Iteration trees. Iterations have meaningful Human feedback/acceptance
identity, while ordered correction `phases/` and per-finding `README.md` files
sometimes represent local work/evidence rather than independent Tasks.

The root `README.md` has consequently become a progress store, authority
history, module map, and Human entry at once. File richness did not prevent
entry-surface accretion because no return-to-root contract constrained it.

### Surface Camera

The development loop has 156 instance directories and 853 instance Markdown
files. The V4 aggregate audit and two child auditors needed exact bounded
authority, frozen inputs, handoffs, and independent evidence. That is a real
high-assurance return contract.

However, representing every Agent Assignment recursively as `packet.md +
role.md + handoff.md`, while repeating frozen paths and digests through parent
and child packets, causes substantial synchronization and verification cost.
The delegation semantics may justify a certificate package; Agent identity by
itself does not justify a nested Task packet.

### This Design Task

The 100-line `packet.md` now works as a Human current view, while a design map,
decision register, verification ledger, and 24 design notes support Agent
recovery. The pressure has moved inward:

- numeric `00..23` design filenames preserve creation order better than
  semantic navigation
- the former `design-map.md` existed partly to compensate for those filenames;
  the rehearsal now uses the accepted stable `design.md` entry
- `decisions.md` has reached more than 750 lines and is a plausible candidate
  for deterministic internal sharding without changing its semantic owner

This is evidence that keeping the Human entry short is necessary but not
sufficient; modules also need stable entry and growth semantics.

## Four Different Things

### Task Packet

One Task-owned directory rooted by `packet.md`. Its `packet.md` remains the
short, Human-language, self-contained current view accepted by `D-018` and
`D-020`. The packet may contain no other file.

### Module

A task-local semantic owner activated by distinct content plus a consumer,
change cadence, provenance boundary, or integration role. It has one stable
entry and returns consequential state to `packet.md`.

A module is not activated merely because:

- a working posture was used
- a second Agent/tool executed work
- content passed a line threshold
- a possible future concern has a conventional filename
- another project had the directory

### Supporting Artifact

Evidence, a design alternative, a receipt, a case, a plan return, or another
bounded object consumed by a module. It does not need its own current-state
surface when its parent module can integrate it unambiguously.

### Nested Task Packet

An independent Task boundary with its own objective, guardrails/authority,
verification, Lead resume point, and terminal integration return. It may be
delegated or independently scheduled, but neither property is sufficient.

A Phase, Cell, Slice, Finding, Agent instance, or document topic does not
automatically become a nested Task. Ordinary sub-agent work later attaches to
Assignment and returns a result/certificate to its Plan owner.

## Progressive Module Shape

The default growth path is:

```text
packet.md
  -> concern remains inline

<module>.md
  -> one stable module entry contains all useful depth

<module>.md + <module>/
  -> entry remains stable; semantic artifacts move behind it
```

Example:

```text
packet.md
design.md
design/
  capability-boundary.md
  storage-authority.md
```

This sibling file/directory shape is preferred over the two main alternatives:

| Shape | Benefit | Cost |
| --- | --- | --- |
| `<module>/README.md` | one namespace | either pre-creates structure or moves/breaks the original entry when the module expands |
| `<module>-map.md + <module>/` | explicit map role | invents role-specific filenames and makes the stable entry harder to predict |
| `<module>.md + <module>/` | stable direct entry and progressive depth | file and directory share a stem, which must be explained once |

No empty module directory or placeholder files are created. A directory appears
only with the first artifact that the entry should no longer contain.

## Module Entry Contract

The entry is a current control/resume surface for its Agent consumers—not an
index of links and not a miniature `packet.md`. In locally natural headings and
language, it must let the next Agent recover:

1. **ownership** — what concern/result this module owns and excludes
2. **current integrated state** — the conclusion, disposition, or active
   topology now, distinguished from history and raw evidence
3. **authority and evidence boundary** — which inputs/baseline are trusted,
   disputed, stale, or only candidate evidence
4. **active return** — the current question, Plan front, expected result, or
   integration condition
5. **depth map** — only the artifacts needed to continue or audit that return
6. **return path** — what consequential change goes back to `packet.md`,
   another module, or a durable owner

These are semantic obligations, not six mandatory headings. Omit what is
obvious; never omit it when the omission makes authority, state, or continuation
ambiguous.

Historical detail moves behind the entry or is removed when it no longer
supports a current decision, proof, or expensive recovery. The entry integrates
artifact results; it does not copy their full contents.

## Semantic Split, Mechanical Sharding, and Retirement

Two kinds of split must remain distinct.

A **semantic split** creates a supporting artifact when at least one pressure
is material:

- independent consumer or review/acceptance authority
- different update cadence or lifecycle
- provenance/immutability boundary such as a receipt
- independent return that may be accepted, rejected, parked, or superseded
- content whose inclusion obscures the module's current state or active return

Choose a semantic split by subject or return. Numeric prefixes are used only
when the order itself has management meaning, such as a Phase, accepted
Iteration, or Plan sequence. Creation chronology is not a semantic filename.

A **mechanical shard** keeps one semantic owner while partitioning a large,
regular collection for bounded reading, editing, diffing, or concurrent writes.
Stable key ranges such as `D001-D010` can have management value when:

- every item maps to exactly one shard by a deterministic rule
- the module entry/index remains the routing and current-state owner
- shards do not acquire independent lifecycle, authority, or roll-up state
- the partition avoids repeated whole-ledger reads or high-conflict edits
- changing the shard size/rule does not change the meaning of an item

This exception fits ledgers, registers, receipts, or similarly regular
collections. Equal-size splitting of a narrative or design argument usually
destroys semantic locality and remains unsupported.

Retire an artifact/module when its distinct consumer or integration role ends.
First integrate its consequential result into the remaining task surface or
durable owner; then remove or stop maintaining scaffolding that no longer helps
complete the Task. Task closure still deletes the whole packet under the
repository's retention rule.

## Work-Topology Projection — Corrected Edge

Work topology should use the same progressive rule instead of becoming another
mandatory module taxonomy.

### Simple Task

```text
packet.md                 # Task Plan may remain inline
plan.md                   # only if one linear Task Plan has useful depth
```

`plan.md` is still one Task Plan. It is not required merely because the Task is
non-trivial.

The former `plans/ + tracks/ + phases/` proposal was incorrect. Track and Phase
are Task-level axes, not automatic storage owners, and when both axes are active
the Cell owns its current Plan. Separating that Plan into a peer `plans/`
directory loses the accepted semantic ownership.

The corrected topology keeps Track/Phase declarations and compact caches in
`task-map.md`. Cell coordinates and short Plans may also remain inline. Only a
Cell whose state/Plan has independent recovery or integration depth earns a
file under a Cell-oriented projection. Root `cell-<track>-<phase>` and `cells/`
alternatives, one-axis Plan ownership, and multi-Plan Cell depth are derived in
[`25-task-map-and-cell-files.md`](25-task-map-and-cell-files.md).

No Track, Phase, Plan, or complete matrix directory is accepted by this note.

## Information-Topology Specialization

Inquiry/diagnosis, design/decisions, implementation/delivery,
verification/acceptance, and retrospective/adaptation remain candidate semantic
module families. Each will be derived separately because their artifacts and
authority differ:

- inquiry needs fact/inference/cause and evidence-boundary discipline
- design needs alternatives, decisions, consequences, and supersession
- implementation needs authorized state transition, invariants, migration,
  recovery, and integration
- verification needs changed claims, discriminating observations, proof
  horizon, residual unknowns, and acceptance authority
- retrospective needs an avoidable trajectory loss, counterfactual
  intervention, normal semantic owner, and future keep/revise/retire evidence

They all use the same entry-plus-depth grammar. None receives a mandatory file
or directory until useful content activates it. Plan scope may reference one of
these concerns, but the posture or scope label does not decide file ownership.

## Root Integration Contract

`packet.md` never becomes a module index. It contains the consequential current
picture in Human language and links only the supporting material needed for the
present review or Agent resume route.

A module update reaches the root only when it changes at least one of:

- the Task outcome/guardrail or accepted decision
- current integrated truth or a material unknown
- authority, risk, proof horizon, or Phase/Cell disposition
- the foreground Human issue or next coordination action

Raw observations, every Plan step, all Agent assignments, and complete decision
history remain behind their owners.

## Failure Modes and Falsifiers

- A standard filename list can become a mandatory empty packet by imitation.
- A generic `task-map.md` can become the same monolith under a new name.
- The sibling file/directory convention may be less intuitive than one
  directory entry for some consumers.
- Over-reserving nested Task packets can make genuinely independent units hard
  to resume or delegate.
- Under-reserving them recreates recursive Agent-instance packet explosions.
- “Semantic split” can be applied subjectively; concrete module-family examples
  must make the distinction learnable.

Reopen the stable sibling-entry convention if real modules repeatedly require
moving or aliasing their entry anyway. Reopen the nested-Task boundary if
independent recovery/authority cannot be represented without full packets, or
if Assignment certificates repeatedly duplicate more context than a nested
packet would.

## Lead Recommendation

1. Define Task packet, module, supporting artifact, and nested Task as separate
   semantic objects.
2. Adopt inline -> `<module>.md` -> `<module>.md + <module>/` as the default
   progressive module grammar.
3. Make the module entry a current integrated control/resume surface with one
   explicit return path, not an index or history store.
4. Use `plan.md` only for one deep linear Task Plan; when Track/Phase activates,
   retire it in favor of `task-map.md` and Cell-owned Plan projection, never
   peer `plans/`, `tracks/`, `phases/`, or a complete matrix by default.
5. Treat deterministic ledger sharding as a physical-management decision
   inside one module, not evidence of more semantic modules.
6. Reserve nested `packet.md` for independently completable Task boundaries,
   not postures, coordinates, findings, or Agent instances.
7. Derive Cell files and the five concern-module families next under this grammar before
   deciding reusable templates or durable SVC paths.

This gives SVC uniform “bricks” without forcing a uniform building. The common
part is semantic ownership and progressive growth; the task-specific part is
which modules reality makes worth their cost.
