# Implementation Workflow

Use Implementation to make an intended change real when its scope and useful local feedback are clear enough to act.

## Plan Before Committing to the Route

Use [Planning and Rehearsal](planning.md) to connect the design and acceptance criteria to dependencies, early feedback, and coherent implementation returns.
Resolve consequential unknowns before dependent work, then execute only as far as the available evidence supports.
Keep the current route and continuation conditions in the task's existing plan.

## Implement and Use the Feedback

### Use Test-first When Its Conditions Hold

Use [feedback and evolution](../../svc-verification/references/feedback-and-evolution.md#choose-test-first-for-stable-behavior) for the reasons to choose test-first, its limits during product exploration, and how local feedback connects to complete outcomes.

When the behavior is clear, the check can exercise the real boundary, and its expected failure would identify the missing behavior, write or adapt the check first.
Confirm that the failure is caused by the absent behavior rather than syntax, dependency, fixture, or environment setup.
Then make the smallest coherent implementation, obtain the expected pass, and improve the implementation while preserving the established behavior.

Do not create a ceremonial Red when the behavior already exists, the check boundary is still being designed, or the failure would only prove broken setup.
Resolve the product or technical uncertainty first, then choose the first useful feedback.

Make the smallest coherent change that advances the outcome.
Keep authoritative state and affected consumers consistent within that change.
When a shared contract or the use of an entry point changes, trace its callers and affected behavior, including exceptions that depended on the old use.
Update the decision and affected consumers together; a passing check against the old implementation does not reverse the agreed contract.
Use [project documentation](../../svc-documentation/SKILL.md) to update the shared definition and communicate the relevant revision to its consumers.
Publish a minimal producer-consumer example early enough to expose incompatibility before integration.
Exercise the actual caller through the changed path, including a disallowed outcome when a guard is part of the contract; an isolated helper check cannot establish that the caller reaches the guard.
Start dependent work after its prerequisite execution has successfully finished; partial files or an accepted background job do not establish readiness.
Parallelize independent work, not competing writes to the same dependency tree or a state change and the read intended to observe it.
For an external write that was accepted or whose result is unclear, read back the affected object before retrying; a pending notification is not a failed write.
Keep temporary files, service processes, and browser sessions attributable to their owner, and limit cleanup accordingly.
If an action disrupts another worker, notify that worker with the affected resource and observed consequence.
Use appropriate compiler, type, test, replay, runtime, or visual feedback to guide the local work.
Local feedback helps choose the next change; the verification skill determines which completion claims it supports.

When feedback invalidates the intended behavior or solution, revisit that decision and update the affected plan.
For recurring boundary or timing problems, use engineering judgment before adding another exception.
Return the actual changed artifact, observed feedback, and unresolved work.
Use the implementation delegation guidance when the change is worth delegating.
After local feedback, select broader checks according to the changed behavior and affected boundaries.
Do not treat a local pass as final acceptance when the user path, persistence, integration, or other promised consequence remains unobserved.

## Check the Basis Before Handoff

Compare the candidate and its acceptance evidence with the current decisions at the authoritative locations linked by the task.
When a decision has changed, use [shared-decision adoption](../../svc-documentation/SKILL.md#keep-the-definition-and-its-consumers-current) to reconcile the affected work rather than reporting only against the original handoff message.
Update and rerun checks whose assumptions or expected behavior changed; retain evidence that still applies to the candidate.
Report remaining dependencies and unresolved interpretations with the handoff, so the recipient can distinguish a usable result from a provisional one.
