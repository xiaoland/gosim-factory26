---
name: svc-sub-agents
description: Decide when and how to delegate work so its result advances the task without requiring the parent to repeat it. Shape useful assignments, match capability and feedback, and judge returns using observations or arguments whose scope and limits are understood.
metadata:
  version: "16.0.0"
---

# Delegation and Result Use

Delegation must solve two problems: getting useful work done and having enough basis to adopt its result.
The caller cannot do everything, but a child's confidence does not make its answer correct.
Repeating the entire task can consume the gain, while asking another similar Agent to approve it can transfer the same trust problem and preserve correlated mistakes.
Useful delegation shapes work whose result can inform a decision or be integrated at lower total cost than doing and judging it directly.
It retains uncertainty that cannot be removed cheaply.

## Compare the Total Work

The gain may come from parallel work, a capability or reasoning route the caller lacks, isolation of extensive raw material, or the child's independent use of local feedback.
Include background transfer, waiting, correction, understanding the return, integration, and the consequences of accepting an error.
Also include unnecessary rejection and repeated checking: they can discard valid work and create another task with no new information.
This is a qualitative choice, not a mandatory cost score or a restriction to easy tasks.

Compare with direct work and an available deterministic tool.
If the schema, query, and interpretation are already clear, running the query is usually cheaper than assigning it.
If the relationship is uncertain, sources are noisy, or several rounds of feedback are needed, a child can resolve that work and return a smaller object the caller can understand.
Open design questions can also be delegated; a lack of a complete objective oracle changes the kind of return and judgment, not whether independent work has value.

## Shape Work Around Its Use

Begin with the decision or effect the caller needs, the return that could advance it, and the observations or arguments that would be enough to adopt that return.
Then choose the work boundary and integration point.
An independent result may be a supported explanation, a candidate change with relevant observations, a useful query, or a comparison that exposes a consequential assumption.
Do not prescribe an answer to an open question merely to make its return easy to check.

Supply enough background to identify the problem, purpose, useful return, and necessary effect limits, with entries to relevant materials and known ongoing work.
Pass context that changes the intended outcome or its conditions, rather than the full parent history or an already completed investigation.
Carry known scenario preconditions and important dependencies to the child; the caller need not first discover every local state, enumerate exact files, or design the execution steps.
Requiring that preparation can consume the work delegation was meant to save.

The child fills in local investigation, design, implementation details, and coordination using the available material and feedback.
It establishes the actual source identity, initial state, and affected consumers needed for its conclusions and actions rather than assuming the caller supplied a complete picture.
It handles recoverable gaps and concrete failures within the authorized boundary.
Escalate a gap that cannot be resolved there, or a choice that changes the overall goal, permission, or consequential tradeoff, with the smallest decision and its effect on the result.
Do not return routine local choices merely because the initial assignment did not specify them.

Match the judgment, tools, context capacity, feedback, and consequences of error to the work.
Bounded scope does not imply low difficulty, and a role name does not establish capability.
Use task-relevant evidence about available Agents; a different approach can help when it challenges an assumption, but another model's agreement alone is not independent evidence.
The caller retains the overall decision and integration responsibility.

## Choose an Affordable Basis for Judgment

Generation and judgment can have different costs.
A child may search many sources or explore several explanations, then return a short query or relationship that compresses the relevant facts.
The caller understands that smaller check, its inputs, and what the actual result supports rather than repeating the search or reading every record.
More evidence links alone do not produce this gain if the caller must reconstruct the whole argument from them.

Different claims permit different mechanisms:

| Claim and conditions | Useful judgment and its limit |
| --- | --- |
| A fact can be precisely queried or constrained. | A short SQL or structural query, schema, type constraint, or existing check can compress many facts. Understand the query meaning, input coverage, version, and actual result. An empty result can mean the query missed the case; structure or compilation does not establish business correctness. |
| There is no complete oracle, but a meaningful relationship can be checked. | Use an invariant, difference, round trip, conservation, or compatibility relation. Check its conditions and comparison reference. A necessary relationship is not sufficient for all requirements, and both sides may share a defect. |
| Full observation is too expensive. | Select samples or add evidence progressively around the uncertainty that could change the decision. Explain coverage and inference assumptions. Sample success does not prove the full population or provide an error probability without a justified model. |
| The result is a design, explanation, or preference with open judgment. | Use assumptions, causal reasons, alternatives, counterexamples, and observed use. Retain what remains unresolved and keep further commitments proportionate to their consequences and reversibility. A precise score or Agent vote cannot create an objective oracle. |

Choose the mechanism for the claim, not from a fixed ranking of tool names.
A hash can establish artifact identity but not quality; a deployment state can establish that a process runs but not that the user journey works.
A large checker with nearly the same reasoning burden as the original task can destroy the intended saving.
Its value depends on a clear relationship between the requirement, observation, and judgment.

## Example: Resolve Missing Parent Records

Suppose failures may arise because invoices refer to accounts that no longer exist, but the relationship and relevant data scope are uncertain.
Give the child the schema, failing identifiers, snapshot entry, and read-only scope.
It investigates the relationship and whether null references, archived records, or deleted accounts are legitimate.
It can return an illustrative query of this form, adapted to the actual relationship:

```sql
SELECT i.id, i.account_id
FROM invoices AS i
LEFT JOIN accounts AS a ON a.id = i.account_id
WHERE i.account_id IS NOT NULL AND a.id IS NULL;
```

The useful return includes the actual result for the relevant snapshot and its interpretation, rather than “there are orphans.”
The caller checks that the join and null handling represent the intended relationship, that the selected records include the failing cases, and that the result was actually obtained from the stated input.
This can replace reading all invoices or repeating the child's search for the relationship.
It supports a repair direction if those cases match; it does not establish every business rule or authorize deleting records.
If the domain excludes archived records or treats a missing parent as valid history, the query and conclusion must reflect that condition.
If the relationship and query were obvious from the beginning, direct execution would have been enough.

## Example: Compare an Interaction Choice

Suppose users repeatedly lose an unsaved filter when switching views, and the desired interaction is still open.
A child can compare preserving the filter, resetting it visibly, and asking before discarding it, using the user goal and relevant constraints.
It returns the reasons each option serves or harms that goal, a counterexample such as a hidden filter making a new view appear empty, and observations from a prototype or actual use when available.
The caller need not recreate every candidate or review the entire exploration history to see the decisive tradeoff.

Observed users completing one path can support that path's usability under those conditions; it cannot settle every preference or unobserved view.
Without observed use, the return remains a reasoned proposal.
The caller may adopt a reversible candidate, request a specific missing observation, or retain the choice as unresolved.
A second Agent preferring the same option is another opinion, not a user observation.

## Consume, Correct, and Recover

Distinguish a child's report that it executed a check from the corresponding observation for the actual candidate, input, and environment.
Obtain the relevant result at its source when needed and understand the small check or argument that connects it to the claim.
A launch receipt, role identity, self-assessment, or another Agent's approval is insufficient by itself.
Reuse results that remain applicable; investigate specific contradictions and gaps instead of mechanically repeating all work.
When the candidate or a premise changes, determine which conclusions still apply before using old observations to support it.

Decide whether to adopt the result, return it for repair, or keep a material claim unknown.
For repair, give the concrete counterexample and actionable reason so the child can continue locally within its boundary.
Do not relay every operation through the caller when local feedback can guide correction.
Retain unsupported claims and residual risk explicitly when the available evidence does not settle them.

Before adding another writer, inspect current ownership, work in progress, and overlapping effects.
Separate working directories do not make shared services, mutable data, or external resources independent.
Coordinate the mutable targets and integration boundary using the actual execution environment.
After interruption, inspect the original work and saved artifacts before reassigning the same effects; missing status does not establish that the child stopped.
