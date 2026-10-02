# Implementation

Use Implementation to make an intended change real when its scope and useful local feedback are clear enough to act.

## Resolve Unknowns That Could Change the Route

Before committing to a route, identify unknowns that could overturn the design or cause substantial rework, such as protocol behavior, compatibility, or resource lifetime.
Check the relevant version's documentation, interface definitions, existing callers, and available observations.
When these do not resolve a consequential uncertainty, use the smallest real spike that can distinguish the possibilities and explain how its result changes the plan.
Prefer real execution when it costs less than constructing a faithful simulation.
A mechanical change with no such uncertainty can proceed directly.

Plan a linear route only as far as the evidence supports.
Each coherent change should produce useful feedback without leaving a critical invariant broken for a later step to repair.
State what new information would permit planning the next part; preparation need not anticipate every possible failure.

## Implement and Use the Feedback

Make the smallest coherent change that advances the outcome.
Keep authoritative state and affected consumers consistent within that change.
Use appropriate compiler, type, test, replay, runtime, or visual feedback to guide the local work.
Local feedback helps choose the next change; [Verification](../../verification/index.md) determines which completion claims it supports.

When feedback invalidates the intended behavior or solution, revisit that decision and update the affected plan.
For recurring boundary or timing problems, use [Engineering Judgment](../design/engineering-judgment.md#reconsider-growing-complexity) before adding another exception.
Return the actual changed artifact, observed feedback, and unresolved work.
Use an [Executor](../../sub-agents/executor.md) when the change is worth delegating under the [Sub-agent guidance](../../sub-agents/index.md).
