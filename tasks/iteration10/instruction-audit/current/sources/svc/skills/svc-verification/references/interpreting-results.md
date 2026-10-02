# Interpreting Results

Use this guidance to judge what observed results establish and what work remains.
The check-design guidance chooses the properties, conditions, and judgment criteria.
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
These explanations are candidates, not mutually exclusive final labels.
A login setup failure can expose both an environment problem and an application defect; preserve the concrete failure and choose the next observation that separates them.

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
If the result contradicts a design assumption or the intended outcome, return to the design skill rather than accumulating local exceptions.
If the evidence is insufficient, state the missing observation and how it could change the conclusion.
Repeating the same inconclusive check without changed conditions does not fill that gap.

When a result is surprising, ask which object needs revision:

- If the promised behavior is absent under valid conditions, repair the product at the responsible boundary and rerun the original path.
- If the check did not observe the promised behavior, revise the check or its observation boundary before claiming a product failure.
- If the environment prevented the behavior from being exercised, repair or replace the environment condition and retain the unexamined status.
- If the requirement or its interpretation is unclear, return to design and record the unresolved choice instead of weakening the judgment to obtain a pass.

Before calling a result PASS, confirm that the intended artifact, inputs, conditions, action, observation, and assertion actually ran.
Before calling it FAIL, confirm that the observed mismatch is against the requirement and not only against an incidental implementation detail.

When the candidate or a relevant precondition changes, identify which previous conclusions may no longer hold and recheck the affected behavior.
Reuse evidence whose artifact, conditions, and claim remain applicable.
Compare the application content, check implementation, inputs and persistent data, and relevant dependency/environment conditions before repeating a completed check.
A new merge commit can contain the same examined tree; that alone does not require another full run, and equal trees alone do not prove equal runtime conditions.
For a changed precondition, identify the conclusions it can invalidate and repeat the affected checks; add broader checks when an interaction or promised outcome remains unexamined.
A change of responsible person is not by itself a new verification condition.
Use broader acceptance when interactions or the complete promised outcome remain unexamined; reducing feedback cost is not a reason to omit it.
Once the evidence adequately supports the current decision, stop expanding checks unless a change, failure, or unresolved concern justifies more.
Report what holds, what remains uncertain, and what would require another evaluation in the existing task record.
