# What v9.7 Changes

## Release-Level Delta

v9.7 should change the alignment story in five ways:

1. Rename `Alignment Pack` to `Alignment Substrate`.
2. Define alignment as a coordination grammar rather than a static document bundle.
3. Make the seven coordination primitives explicit.
4. Introduce a pre-execution impact handshake for non-local or durable mutations.
5. Keep MVT as the default task frame while allowing substrate-driven expansion when drift pressure rises.

## Core Model

### Seven Coordination Primitives

The substrate becomes actionable only when the following primitives are explicit enough to constrain action:

1. Object
2. Address
3. Operation
4. Boundary / Invariants
5. State / Context
6. Evidence
7. Protocol

These can be explained in three coordination clusters:

- Reference: Object, Address
- Mutation Contract: Operation, Boundary / Invariants
- Grounding and Synchronization: State / Context, Evidence, Protocol

### Owner Split For The Seven Primitives

The substrate should own the fields and grammar, but not all underlying truth.

| Primitive | What alignment owns | Where the underlying truth usually lives |
| --- | --- | --- |
| Object | coordination object type and naming conventions | PRD, TDD, code, or local `AGENTS.md` |
| Address | addressing formats and stable-anchor conventions | code symbols, files, routes, UI anchors |
| Operation | controlled verbs and their verification implications | task intent plus owning truth layer |
| Boundary / Invariants | the need to declare them before mutation | PRD, Product TDD, Unit TDD, local `AGENTS.md` |
| State / Context | the need to state when a request is valid | PRD, TDD, tasks, runtime context |
| Evidence | the need to cite objective proof | tasks, tests, logs, deployment docs |
| Protocol | the need to synchronize before risky mutation | Meta Engine and mode SOPs |

This owner split is the main guardrail that keeps v9.7 maintainable.

## Relationship To Existing SVC Mechanisms

### MVT Stays

MVT remains the default for non-trivial tasks:

- Objective & Hypothesis
- Guardrails Touched
- Verification

The substrate should be framed as a structured expansion of that baseline when the task suffers from referential ambiguity, risky mutation, or unclear blast radius.

### Typed Ownership Stays

The substrate does not change the front-door classifier:

- Intent
- Constraint
- Reality
- Artifact

It only makes risky coordination more deterministic after the route is already known.

### Evidence-First Reality Work Stays

v9.7 must not let alignment become an excuse for speculative fixes. If evidence is missing, the task must route back to diagnosis instead of pretending the substrate is complete.

## Scope Boundaries

### In Scope For v9.7

- naming and narrative consistency around `Alignment Substrate`
- explicit coordination primitives and their guardrails
- `From -> To` state-diff framing
- operation words as verification contracts
- pre-execution impact handshake
- template support for substrate requests
- migration notes from v9.6 to v9.7

### Out Of Scope For v9.7

- making substrate fields mandatory for every task
- introducing a new top-level route taxonomy
- redefining PRD, Product TDD, Unit TDD, Deployment, or Tasks ownership
- requiring every project to add stable anchors everywhere
- replacing code/tests with documentation

## Expected User-Facing Outcome

After v9.7, a human should still be allowed to speak directionally and naturally, but the agent should have a stronger framework-backed obligation:

- deserialize intent into substrate fields when risk demands it
- state the expected blast radius before crossing durable boundaries
- bind claimed operations to verification
- pause for an impact handshake before non-local durable mutation

## Acceptance Criteria

The source update should be considered complete only when:

- source-facing naming is consistent on `Alignment Substrate`
- the alignment section explains the seven primitives and the three engineering rules
- meta-engine defines when the impact handshake is required
- the request template can express substrate-heavy work without bloating routine tasks
- migration guidance explains the v9.6 to v9.7 delta in one scan
- the generated monolith reflects the same ownership model as the source files
