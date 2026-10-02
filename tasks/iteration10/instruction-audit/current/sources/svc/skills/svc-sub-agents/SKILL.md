---
name: svc-sub-agents
description: Delegate execution or investigation with useful boundaries and consume the result. For independent advice on consequential decisions, use svc-design.
metadata:
  version: "16.0.0"
---

# Delegation

Independent consultation on consequential decisions follows [Design: Independent Judgment](../svc-design/references/workflow.md#independent-judgment), outside the delegation economics below.
Its purpose is to challenge a decision before it becomes a commitment; it need not repay the cost of transferring or verifying a work package.
The guidance below on supplying context and consuming a return still applies.

For delegated execution or investigation, use a child Agent when its independent work can repay context transfer, waiting, correction, verification, and integration.
Compare delegation with direct work and an available deterministic tool.
The gain may come from parallel work, a different method, or reducing the raw material the Primary must process.
A known lookup is usually cheaper to perform directly; noisy retrieval can benefit from a child that returns a supported answer instead of the search transcript.

## Shape Useful Work

Shape an assignment around a result with an independent use, enough source context, local feedback, permitted effects, and a clear integration boundary.
An open question can be delegated without prescribing its answer.
Let the child resolve bounded information and design gaps; keep decisions beyond that boundary with the consumer.

Before assigning work, check the current owner, work already in progress, and relevant shared conditions.
Coordinate overlapping effects before adding another writer; prefer one writer per mutable target unless a clear merge boundary exists.
On interruption or recovery, inspect the original work and existing artifacts before reassigning the same change.
Missing status does not establish that the original work stopped.

## Match Capability to the Work

Consider the judgment, tools, context, feedback, and consequences of an error that the work involves.
Bounded scope does not imply low difficulty, and a role name does not establish capability.
Choose among available agents using task-relevant evidence, not a fixed ranking.
A reusable role earns its place through a recurring class of problems, methods suited to them, and returns that a consumer can use.
A one-time assignment need not become a role, and a stage name does not require a separate Agent.

## Supply the Assignment

Name the intended result and its consumer, relevant sources, effect limits, required initial state, available feedback, and conditions for returning unresolved work.
Pass the context needed for that return rather than the full parent history.
When splitting a requirement, carry its observable scenario preconditions and initial state to the owner that must provide them, and name consumers of that state.
The child handles local reasoning and recoverable failures; the Primary owns the overall decision and integration.
These roles concern children of the current Agent, not coordination among independent task owners.

## Consume the Result

Decide what claim the return must support and how it can be judged at lower cost than repeating the work.
For a checkable claim, a small query or constraint with its actual result and input scope may be more useful than a large evidence dump.
For an open judgment, use reasons, alternatives, counterexamples, and remaining uncertainty to inform the next decision.
Neither form makes unsupported conclusions acceptable, and another Agent's agreement alone does not add independent evidence.

For example, a relationship query can check for orphan records without the Primary reading every record.
The consumer still checks whether the query expresses the intended relationship, handles relevant null values, and examines the intended data.
It does not establish every business rule about those records.
An interaction design may instead need a comparison, a counterexample, or observed use; do not invent a boolean oracle for a preference.

Consume the actual return against the current decision and artifact.
A launch receipt is not a result.
Reuse applicable observations, investigate material contradictions, and retain uncertainty where evidence is missing.
Do not require the Primary to repeat the whole task merely to use it.
Account for unnecessary rejection and repeated checking as well as the consequences of accepting an error.

Use [verification](../svc-verification/SKILL.md) to judge the evidence and its limits.
Use the [Explorer guidance](../svc-investigation/references/delegating-investigation.md) for a bounded information question and the [Executor guidance](../svc-implementation/references/delegating-implementation.md) for a bounded change with local feedback.
Use [task state](../svc-task-packet/SKILL.md) when ownership, ongoing work, or results need a durable recovery entry.
These are routes for the current need, not a required sequence.
