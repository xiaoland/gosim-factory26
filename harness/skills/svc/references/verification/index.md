# Verification and Validation

Use this guidance to judge what observed results establish and what work remains.
[Evidence design](../methods/design/test.md) chooses the properties, conditions, and judgment criteria.
Use the existing criteria and evidence before adding more checks.

## Read the Result in Context

Run the applicable check under known conditions and retain the observation, relevant inputs, environment, and original failure information.
Link the result to the artifact actually examined; stale or different artifacts cannot establish the current claim.
Distinguish the observed behavior from your explanation of it.

Acceptance evidence addresses the promised outcome; diagnostic evidence helps explain how it occurred or failed.
For an invoice email, SMTP handoff helps diagnose delivery, while receipt by the intended recipient with the right invoice addresses the promised outcome.
An internal state can itself be an acceptance result when the requirement concerns that state.

Check whether the result disagrees with the product requirement, the check misrepresents the requirement, the environment prevented execution, or the necessary observation is missing.
An interrupted check is not a demonstrated product failure, and a successful tool call is not automatically a successful product outcome.
Passing selected cases supports only the behavior and conditions they examine.

## Establish Confidence Through Evidence

Look for assumptions shared by the requirement interpretation, implementation, oracle, and observation mechanism.
Several checks can agree because they repeat the same mistaken assumption.
Use an applicable independent mechanism or external observation when that would resolve a consequential doubt.
Another Agent's agreement alone does not add independent evidence.

Do not delegate generic code reading to hunt for defects.
Read relevant code to explain a concrete discrepancy; establish the defect and its repair through observable behavior, a reliable static check, or other evidence suited to the property.
A compiler, schema, or constraint may already establish a property that another manual review would merely repeat.

## Let the Result Determine the Next Action

Repair a demonstrated local defect and obtain feedback at the boundary that exposes it.
If the result contradicts a design assumption or the intended outcome, return to [Design](../methods/design/index.md) rather than accumulating local exceptions.
If the evidence is insufficient, state the missing observation and how it could change the conclusion.
Repeating the same inconclusive check without changed conditions does not fill that gap.

Use broader acceptance when interactions or the complete product outcome remain unexamined.
Once the evidence adequately supports the current decision, stop expanding checks unless a change, failure, or unresolved concern justifies more.
Report what holds, what remains uncertain, and what would require another evaluation in the existing task record.
