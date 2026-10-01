# Working Note — Role-Based Sub-Agent Orchestration

- **State**: provisional-note
- **Sources**: Sir's orchestration gleanings, the current
  [`oil-oil/codex-team-mode`](https://github.com/oil-oil/codex-team-mode), and
  bounded Lead synthesis
- **Use**: Preserve useful raw thoughts and emerging distinctions without
  accepting a role catalog, pipeline, or SVC protocol

## What the Reference Establishes

`codex-team-mode` is primarily a textual routing policy plus Codex Agent
profiles, not an independent scheduler. Its current design uses Explorer,
Executor, and Reviewer profiles and asks the main thread to:

- use the smallest team whose benefit exceeds briefing, waiting, inspection,
  integration, and rework cost
- keep unresolved product, architecture, safety, scope, and acceptance
  decisions in the main thread
- give a child a bounded dispatch contract, use one writer per mutable target,
  and parallelize only independent slices
- reuse an Agent when its focused context remains valuable, but use fresh
  context for independent review
- inspect real sources, artifacts, diffs, and checks before accepting a return

The repository does not implement a queue, merge engine, lock manager, policy
enforcer, or orchestration state machine. Model names, `agent_type`, TOML
profiles, `fork_turns`, trace fields, and nesting settings are current Codex
delivery details rather than stable SVC semantics. The project also recently
collapsed four working roles into three, evidence that role count and model
tiering are design variables rather than a durable interface.

## Emerging Distinctions

Do not collapse these concepts:

- **working posture**: what kind of move is appropriate now—Explore, Solidify,
  Execute, or Diagnose
- **role**: a reusable work contract with a distinctive method, authority
  boundary, and return shape
- **skill**: specialized know-how a role or Agent can apply
- **tool**: an evidence or effect channel
- **assignment**: one task-specific objective, context projection, scope, and
  stop condition
- **validator or acceptor**: the mechanism or Human that judges the returned
  claim, artifact, or effect

A role may move through several postures. A posture does not by itself justify
a new Agent. Therefore “per SVC working mode per Agent” is promising if every
assignment declares its current posture and uses a matching method; it is
probably too rigid if it means one permanent Agent role for each posture.

## Role as a Deep Work Module

A useful role resembles a deep software module:

- its dispatch and return interface is small enough to preserve context
  isolation
- it performs substantial internally coherent work behind that interface
- its dependencies and authority are narrow enough to avoid continuous Lead
  synchronization
- its output has a credible local acceptance or escalation path
- its specialized method improves results beyond a generic prompt

This suggests that the best delegation boundary is not merely a small task. It
is a low-coupling cut where the internal work is large relative to the context
that must cross the boundary. Delegation value rises with useful internal work,
context noise avoided, and independent evidence; it falls with boundary
bandwidth, unstable dependencies, weak oracles, integration burden, and effect
risk.

Keep three context layers separate when useful:

1. stable role method and invariants
2. task-specific objective, authority, snapshot, and return contract
3. source handles loaded progressively when the work encounters a concrete
   need

This is a candidate way to reduce the context paradox without pretending that
context selection is free or complete.

## Reading the Proposed Roles

### Current-rule resolver

The proposed “what rules should be applied now” Agent is better understood as
a context or constraint resolver. It could reduce Lead context load before
high-risk, high-unknown, or high-complexity reasoning. Its central risk is a
false omission: the Lead may not notice that a relevant rule was filtered out.

A safer shape combines mechanically discoverable candidate sources with
semantic relevance judgment. The return should preserve source references,
why a rule applies, detected conflict or precedence, and material uncertainty;
it should not claim to replace the canonical instructions or make the pending
decision. Whether this deserves a permanent role rather than a reusable
capability remains open.

### Explorer

Explorer's specialization is not read-only access. It is adaptive evidence
acquisition: select tools and search modes, plan multi-step retrieval, filter
noise, follow causal or ownership paths, test a counterexample, and stop when
the decision has enough evidence.

Its valuable return is a compact answer and evidence map with resolvable
handles, gaps, conflicts, and the remaining search frontier—not a transcript or
large evidence dump. Reproducible source paths and bounded claims are its main
verification surface.

### Durable-document integrator

The proposed doc writer is not primarily a prose producer. It integrates a
change into the durable truth topology:

1. determine what the change means at the relevant product or technical layer
2. find nearby, analogous, contradictory, or superseded claims
3. resolve whether the claim belongs in durable documentation and identify its
   canonical owner
4. edit only after the meaning and destination are stable

It must stop when product meaning, technical authority, or a material trade-off
is unresolved. Its acceptance concerns canonical placement, consistency,
non-duplication, navigation, and language quality as well as prose correctness.

This semantic integration role should not be generalized into a writer Agent
for repetitive multi-file edits. File count is not a delegation boundary. When
the intended relation among edits can be expressed as one transformation rule,
a compiler-assisted rename, codemod, structural rewrite, formatter, generator,
or other deterministic mechanism is normally a lower-cost executor than an LLM
writer. Agent judgment may still help design the rule, identify exceptions, and
choose verification, but it should not repeatedly regenerate what the rule can
apply consistently.

### Executor

Executor should not mean “Agent that edits several files.” The stronger model
is bounded ownership of a minimal-development loop around one observable seam:

```text
real input or replay
  -> observe current behavior
  -> form a local hypothesis
  -> make the smallest useful change
  -> replay or probe
  -> compare evidence
  -> continue, stop, or request Human judgment
```

Some loops have mechanical checks. Others, such as handwriting input to canvas
glyphs, use a bounded Human taste oracle. In the latter case the Executor can
own replay, candidate production, and evidence preparation, while the Human
retains experience acceptance. Reusing the same Agent across iterations may be
more valuable than fresh context because focused local state is an asset.

An Executor may use a deterministic transformation internally. The distinction
is not tool versus Agent: deterministic machinery handles expressible scale;
the Executor owns the remaining local uncertainty, feedback, exceptions, and
evidence. If an LLM is used to infer or author a codemod, enclose that work in a
small loop of examples, candidate rule, bounded application, inspection, and
verification rather than delegating an unstructured pile of edits.

### Reviewer

Independent review is a verification strategy before it is a permanent role.
It is valuable when a specific residual risk needs a fresh evidence path. A
generic second opinion or ritual review of already-proven checks can reproduce
the trust paradox rather than resolve it.

## Orchestration as a Dynamic Control Loop

The Lead Agent is not merely a dispatcher. It retains the coupled objective,
Human interface, unresolved decisions, task topology, integration judgment,
and residual-risk budget. It repeatedly chooses among:

- work locally or delegate
- keep an existing focused Agent or start fresh
- sequence coupled work or parallelize independent cuts
- mechanically validate, seek independent review, ask for Human taste, or
  contain the remaining effect
- integrate a return, request a bounded follow-up, reject it, or reopen an
  upstream assumption

The work graph is often discovered during execution, so this should not become
a fixed Explorer-to-Executor-to-Reviewer pipeline. Only ready frontier slices
whose objective, authority, inputs, and judgment path are stable enough should
leave the Lead context.

Human attention is part of this topology. Where acceptance depends on product
or technical taste, Agents should reduce the decision surface through real
replays, contrasted candidates, and concise evidence rather than simulate
Human acceptance or transfer raw exploration burden to Sir.

Do not collapse four different topologies:

- the **Agent runtime tree** says which thread spawned which Agent
- the **work graph** says which findings, decisions, and changes depend on one
  another and which frontier slices are ready
- the **authority graph** says who may decide, mutate, accept, or cause an
  external effect
- the **evidence graph** says which observation or validator supports which
  claim or artifact

A runtime restriction such as shallow child nesting does not make the work
graph shallow, prove authority, or validate a result. SVC should preserve these
meanings even when one current tool projects all of them through a parent-child
thread UI.

## Role Admission and Evolution

A possible progressive path is:

```text
one-off delegation contract
  -> recurring specialized working method
  -> reusable role/profile
  -> mechanical support where repeated evidence justifies it
```

Promote a role only when a recurring task shape has a distinctive method,
bounded authority, compact context interface, and credible return check. Let a
role merge, split, or disappear when those properties change. SVC may need to
own the admission and orchestration grammar while Consumer projects own much of
the domain-specific role library.

This remains raw synthesis. It is intentionally not a required core role set,
dispatch schema, lifecycle, or implementation proposal.
