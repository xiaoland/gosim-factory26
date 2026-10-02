# Implementation Workflow

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

### Use Test-first When Its Conditions Hold

When the behavior is clear, the check can exercise the real boundary, and its expected failure would identify the missing behavior, write or adapt the check first.
Confirm that the failure is caused by the absent behavior rather than syntax, dependency, fixture, or environment setup.
Then make the smallest coherent implementation, obtain the expected pass, and improve the implementation while preserving the established behavior.

Do not create a ceremonial Red when the behavior already exists, the check boundary is still being designed, or the failure would only prove broken setup.
Resolve the product or technical uncertainty first, then choose the first useful feedback.

Make the smallest coherent change that advances the outcome.
Keep authoritative state and affected consumers consistent within that change.
When a shared contract changes, implement against the agreed contract and update its consumers; a passing check against the old implementation does not reverse the decision. Publish a minimal producer-consumer example early enough to expose incompatibility before integration.
Use appropriate compiler, type, test, replay, runtime, or visual feedback to guide the local work.
Local feedback helps choose the next change; the verification skill determines which completion claims it supports.

When feedback invalidates the intended behavior or solution, revisit that decision and update the affected plan.
For recurring boundary or timing problems, use engineering judgment before adding another exception.
Return the actual changed artifact, observed feedback, and unresolved work.
Use the implementation delegation guidance when the change is worth delegating.
After local feedback, select broader checks according to the changed behavior and affected boundaries.
Do not treat a local pass as final acceptance when the user path, persistence, integration, or other promised consequence remains unobserved.
