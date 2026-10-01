# Working Note — Telemetry Task-Packet Field Cases

- **State**: supporting field evidence for the task-packet cluster; current
  counterfactual synthesis is in
  [`19-track-slice-counterfactual.md`](19-track-slice-counterfactual.md); cases
  are not exemplars and make no task-outcome claim
- **Sources**: `D-017..D-019`, `V-042..V-044`; local SVC CLI telemetry and
  schema-v3 analysis; current task-packet files in InKCre `core-py`,
  `sfp7-camera`, and `workbench`
- **Use**: Expose real organization pressure and vocabulary drift before
  selecting common planning primitives or module shapes

## Method and Evidence Boundary

The Lead used the local CLI rather than treating remembered threads as cases:

1. read `svc telemetry agent-thread` and `svc analysis` help
2. read the packaged Working Protocol `Agent Task Analysis` method
3. list bounded local thread selection metadata
4. export exact selected threads to temporary schema-v3 evidence ZIPs
5. inspect structural overview, match exact packet paths, and read contiguous
   native context around packet creation or use
6. inspect the corresponding current task directories read-only

Selection used task shape plus native record/message/tool-call scale only to
find large candidates. Those counts are not quality, outcome, cost, or
completion evidence. All three projections are partial: reasoning is summary,
context is partial, and explicit concurrency is unavailable. Current packet
files may also be newer than the thread region that first created them.

The cases therefore support structural observations only: addresses, file
topology, line counts, explicit headings, vocabulary, and directly visible
duplication. They cannot establish that a packet organization caused a better
or worse terminal result.

## Case Selection

| Case | Thread evidence | Why selected | Current packet surface |
| --- | --- | --- | --- |
| InKCre knowledge lifecycle | `019fad3c-57eb-7160-ae35-b04cf79f6dcd`; 20,061 native records, 1,104 messages, 2,452 tool calls | Large multi-capability program mixing product discussion, technical design, implementation, verification, and several implementable units | `tasks/knowledge-lifecycle-capabilities/`: 29 Markdown files, 8,478 lines; root `packet.md` 133 lines |
| Surface Pro 7 camera loop | `019fb156-6627-7a33-bc79-b6591d61da14`; 69,872 native records, 2,873 messages, 12,647 tool calls | Large hardware/software lifecycle with remote machine mutation, gates, evidence, recovery, and extensive sub-agent execution | `tasks/development-loop/`: 865 Markdown files, 93,603 lines; root `packet.md` 1,956 lines; 156 instance directories |
| Workbench Coding Surface | `019f884b-7e40-7512-9056-0965f20dbc43`; 67,279 native records, 2,540 messages, 12,027 tool calls | Large long-lived product/system feature spanning product, UX, architecture, protocol, implementation, acceptance, and Human iterations | `tasks/0020-coding-surface/`: 260 Markdown files, 23,368 lines; root `README.md` 356 lines; 12 sub-task and 8 iteration directories |

The telemetry capture connected the exact threads to the named packet paths.
The filesystem counts describe their current local state, not an immutable
historical snapshot.

## Case A — Program, Track, and Implementable Unit

The InKCre packet has a recognizable composition:

```text
packet.md
capability-map.md
decisions.md
pressure-ledger.md
documentation-promotion.md
tracks/{collection,organization,application}.md
units/<unit>/
  packet.md
  design / evidence / acceptance / implementation-plan / preflight ...
```

Useful properties:

- the root packet identifies one active implementable unit
- track maps preserve capability scope while unit directories support bounded
  implementation and verification work
- evidence, design, acceptance, and implementation plans have recognizable
  addresses instead of remaining in one entry
- decision IDs establish precise Human-Agent references across files

Observed pressure and failure risk:

- root `Current Truth` still carries long histories of completed units and
  decisions, including a dense `D-050..D-075` chain
- `decisions.md` has grown to 2,308 lines, while unit packets range from 101 to
  301 lines and one technical design reaches 1,280 lines
- a unit becomes another packet with its own gates and execution evidence;
  recursion provides isolation but lacks a visible common rule for when a
  module becomes a nested packet or how it returns and retires
- `program`, `track`, `unit`, `gate`, `B0..B8`, and `I-01..I-08` form a useful
  local language but do not map to an SVC-wide planning vocabulary

This case supports composable information modules, but also shows that splitting
files does not by itself keep the Human entry or decision authority compact.

## Case B — Coordination and Execution State Dominates

The Surface camera packet has several sensible top-level owners:

```text
packet.md
acceptance.md
collaboration-protocol.md
development-loop.md
environment-plan.md
repository-topology.md
roles/
instances/<many bounded Agent work instances>/
```

Its risk boundary is unusually demanding: remote hardware, kernels, Secure
Boot, recovery, sealed evidence, multiple capability gates, and independent
audits. Explicit proof and authority are therefore justified more often than in
an ordinary software task.

The resulting structure is nevertheless an important counterexample:

- root `Current Truth` spans from line 57 to line 1,733 before Delegations and
  Next Step
- 156 instance directories contain checkpoints, subtasks, drafts, models,
  reviews, fixtures, and local roles
- 865 Markdown files total about 93,603 lines
- runtime execution identity, coordination, recovery, proof, and historical
  repair attempts have become a task-local control system

File count alone does not prove waste, and high-risk kernel work needs more
evidence than ordinary tasks. But this organization makes the costs named by
the sub-agent paradox concrete: briefing, state synchronization, integration,
stale instances, recursive packets, and verifying the coordination system
itself. It is strong evidence against making an instance tree, checkpoint
protocol, or coordination graph the default task-packet shape.

## Case C — Theme Modules, Sub-Tasks, and Iterations

The Workbench Coding Surface packet is organized around substantive concerns:

```text
README.md
product-scope.md
architecture.md
experience.md
remote-contract.md
security-reliability.md
acceptance-strategy.md
implementation-plan.md
decision-register.md
subtasks/<12 bounded deliveries>/
iterations/<8 Human report-analysis-correction loops>/
```

Useful properties:

- product, UX, architecture, protocol, reliability, implementation, and
  acceptance have separate semantic owners
- the root contains a Packet Map and explicit dependency topology
- sub-task and iteration directories reflect two real kinds of work pressure:
  bounded delivery and feedback-driven correction

Observed pressure and failure risk:

- the 356-line root repeats status, current phase, guardrails, verification,
  authority, product boundary, topology, packet map, and sub-task index
- the packet uses `phase`, `sub-task`, `slice`, `vertical`, `iteration`,
  `batch`, `milestone`, and `gate`; several mean a bounded piece of work but
  carry different and partly implicit completion semantics
- nested sub-task and iteration README files improve locality but expand the
  total task to 260 Markdown files and 23,368 lines
- the entry filename is `README.md`, illustrating that even the common packet
  address has drifted across SVC generations

This is the clearest vocabulary-pressure case: the task needed several real
organization constructs, but SVC supplied no stable building blocks, so local
terms accumulated around different moments of the lifecycle.

## Cross-Case Findings

### One Human surface, many Agent surfaces

Sir's corrected audience boundary fits all three cases. Root `packet.md` should
carry the short consequential Human view. Maps, evidence, registers, designs,
plans, child work, and proofs may optimize Agent recovery and reasoning. They
need a clear return to the entry, but not independent Human polish.

The cases currently violate this boundary in different ways: dense root
history, a 1,956-line execution/coordination surface, and a 356-line map plus
status/index surface.

### Common primitives are more urgent than a universal directory

The repeated need is not one fixed tree. It is stable answers to:

- what is the current bounded work object?
- is it a semantic scope, a deliverable, a feedback cycle, an execution action,
  or merely a grouping horizon?
- what can run concurrently or reopen another concern?
- what does completion return, and where is that return integrated?
- which term is visible to Sir when steering the Agent?

`phase`, `slice`, `step`, `sub-task`, `segment`, `unit`, and `iteration` should
not remain approximately sized synonyms. The final primitive set must be small
and relation-based, while allowing scope qualifiers such as exploration,
design, implementation, and verification.

### Modular files do not guarantee progressive disclosure

All three cases split material, yet their root entries or registers still grow.
Progressive disclosure also requires:

- a compression/roll-up rule for consequential returns
- retirement or historical-state behavior
- one current front rather than accumulated chronology
- a rule for when a module gains its own local entry
- no duplication of state between root, map, child packet, and execution
  instance

### Thread scale is a selector, not a trigger

Native records, turns, compactions, tool calls, and Agent count help find cases.
They cannot automatically activate a module, infer a task type, select an
active front, or establish task quality. The Lead and packet remain semantic
authorities.

## Consequences for the Next Discussion

The next planning-vocabulary discussion should derive candidate primitives from
the distinct jobs visible here, not choose names first:

1. current attention/decision focus
2. optional ordering or review horizon
3. bounded result and integration unit
4. immediately executable action
5. feedback/repetition cycle

Some jobs may collapse into relations or local state rather than become
separate primitives. Each admitted primitive needs a purpose, scope relation,
composition rules, completion/return meaning, Human-visible representation,
and a simple task that does not activate it.

No case supports a universal directory, nested packet, coordination runtime,
or fixed `phase -> slice -> step` hierarchy. They do support `D-017`: stable
planning common ground is necessary before task-packet module templates can be
designed coherently.
