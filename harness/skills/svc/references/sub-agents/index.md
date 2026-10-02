# Sub-agents

Use a child Agent when its bounded work saves enough time or attention to repay context transfer, waiting, correction, verification, and integration.
Compare delegation with direct work and an available deterministic tool.
A known lookup is usually cheaper to perform directly; noisy retrieval can benefit from a child that returns a supported answer instead of the search transcript.
If the Primary must repeat the work to use its result, reconsider the assignment or the chosen Agent.

## Match Capability to the Work

Consider whether the answer can be objectively checked, how much open judgment it requires, what context it needs, and the consequences of an error.
Bounded scope does not imply low difficulty, and a role name does not establish capability.
Work with a clear goal and reliable feedback can suit a specialist; forming the problem or choosing among open possibilities requires the corresponding judgment.
Choose among available agents or models using task-relevant evidence, not a fixed model ranking.

## Make the Return Usable

Name the question or intended change, its consumer, relevant source handles, effect limits, sufficient result, and conditions for returning an unresolved issue.
Pass the needed context rather than the whole parent history.
Prefer one writer per mutable target unless a clear merge boundary exists.
The child handles local reasoning and recoverable failures within the assignment; the Primary owns the overall decision and integration.
Verify consequential results using the [evidence appropriate to the claim](../verification/index.md#establish-confidence-through-evidence).

Use [Explorer](explorer.md) for a bounded read-only information question and [Executor](executor.md) for a bounded change with local feedback.
These roles concern children of the current Agent, not coordination among independent task owners.
