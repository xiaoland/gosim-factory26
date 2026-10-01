# Interpreting Results

Use this guidance to judge what observed results establish and what work remains.
The check-design guidance chooses the properties, conditions, and judgment criteria.
Use the existing criteria and evidence before adding more checks.
The purpose is a supported next decision, not the largest possible collection of passing results.

## Read the Result in Context

Separate the observation, its explanation, and the completion claim.
“Request returned 200” is an observation; “the business operation succeeded” is an interpretation; “the feature is complete” is a broader claim that needs evidence for its obligations.
A static check can establish the constraints it actually enforces, and a measurement can establish behavior under its workload, without either establishing an unobserved user journey.

Run the applicable check under known conditions and retain the observation, relevant inputs, environment, and original failure information.
Link the result to the artifact actually examined; evidence for a different candidate supports the current claim only when its applicability has been established.
Distinguish the observed behavior from your explanation of it.

Acceptance evidence addresses the promised outcome; diagnostic evidence helps explain how it occurred or failed.
For an invoice email, SMTP handoff helps diagnose delivery, while receipt by the intended recipient with the right invoice addresses the promised outcome.
An internal state can itself be an acceptance result when the requirement concerns that state.

When dismissing a contradictory observation as a capture or measurement error, explain which part is unreliable and what evidence resolves the same disputed property.
A pass at another boundary can support a separate claim without explaining the contradiction.
If a saved observation does not show the state it is meant to demonstrate, obtain the missing observation or narrow the claim; its filename, caption, or a different passing suite cannot supply that evidence.

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
Inspect shared expected values, reference implementations, substitutes, generators, and observation mechanisms when they could explain the agreement.
A passing local rule and integration check followed by a failing user journey can focus investigation on the connection, but does not prove the fault is in the interface; different conditions or a shared wrong expectation can also explain that pattern.

A requirement-to-check mapping locates evidence; a reference or a passing check does not establish that its judgment covers the original scenario.
When accepting existing checks for an integrated coverage claim, compare what they actually judge with the original objects, actors, initial conditions, actions, and promised results, especially at excluded boundaries or revised interpretations.
Ask whether the evidence could still pass if a promised behavior were absent.
This comparison is needed even if another contributor already performed the translation; it does not itself require rerunning valid checks.

For example, a requirement may promise that both an editor and an importer update the same setting and preserve it after reopening.
Passing editor checks support that path but cannot establish the importer path simply because both requirement IDs appear in a mapping.
Retain the editor evidence and name the unsupported importer behavior, then obtain the missing observation or narrow the completion claim.
This targets a semantic gap without turning it into an unnecessary full rerun.

Do not delegate generic code reading to hunt for defects.
Read relevant code to explain a concrete discrepancy; establish the defect and its repair through observable behavior, a reliable static check, or other evidence suited to the property.
A compiler, schema, or constraint may already establish a property that another manual review would merely repeat.

## Let the Result Determine the Next Action

Repair a demonstrated local defect and obtain feedback at the boundary that exposes it.
If the result contradicts a design assumption or the intended outcome, revisit that assumption or requirement interpretation rather than accumulating local exceptions.
If the evidence is insufficient, state the missing observation and how it could change the conclusion.
Repeating the same inconclusive check without changed conditions does not fill that gap.

When a result is surprising, identify what must change before changing the product:

1. Did the check reach and observe the intended object under the required conditions?
   If a locator matches several objects, setup fails, or the observation is missing, repair that part of the check or environment and retain the unexamined status.
2. Does the judgment rule follow from the requirement?
   If it adds an incidental restriction, correct the rule.
   Return genuinely unclear product choices to design and preserve the uncertainty.
3. Does the observed behavior violate that grounded rule?
   Repair the product at the responsible boundary and rerun the path that exposed the violation.

These questions can reveal more than one defect; resolving a measurement problem does not establish that the product works.
A guess about an unavailable evaluator is not a product requirement.
Choose unspecified product behavior for its intended use and constraints, not to make that guess pass.

For example, two folders may legitimately contain documents with the same name.
A check that selects by name alone cannot identify the document the requirement asks to update.
Scope the check to the intended folder and document, perform the update, and reopen that document to observe the required saved result.
Deleting or renaming the other valid document would make the ambiguous selector pass without repairing the check.
If the correctly targeted update still fails to persist, that observation now supports a product repair.
Use [check design](check-design.md) to keep the judgment grounded in the requirement while changing its observation mechanism.

Before calling a result PASS, confirm that the intended artifact, inputs, conditions, action, observation, and assertion actually ran.
Before calling it FAIL, confirm that the observed mismatch is against the requirement and not only against an incidental implementation detail.

## Reuse Evidence and Stop at a Supported Decision

Before accepting a handoff or repeating a completed check, compare the examined artifact with the current candidate and record the applicability decision in the existing task record:

- Identify the requirement supported and the original result, including the artifact and conditions actually examined.
- Inspect the candidate diff and changes to check code, build artifacts, inputs, persistent data, dependencies and relevant environment conditions.
  State which conclusions those changes can invalidate.
- Reuse applicable results and recheck the affected behavior.
  Obtain broader evidence when an interaction or the complete promised outcome remains unexamined; name that gap before starting the additional check.

Determine applicability from the relevant changes and the conditions actually examined.
Include materials consumed by the build, runtime or check; filenames alone do not establish their effect.
Record the new candidate and the reason for reuse without relabeling the original run as having examined it.
Use the [retained execution and handoff](repeatable-checks.md#preserve-the-execution-in-the-handoff) to keep the cited output, conditions, and actual status attributable to the same original execution; a summary cannot resolve a mismatch between them.
Equal trees alone do not prove equal runtime conditions, and a change of responsible person is not by itself a new verification condition.
Once applicable evidence satisfies the current acceptance obligations and no unresolved contradiction remains, hand off the result and stop.
Another acknowledgement or identical passing run adds no evidence for that decision.
Report what holds, what remains uncertain, and what change would require another evaluation.

Use [feedback and evolution](feedback-and-evolution.md) to carry the resulting decision into implementation, delivery, and observations from actual use.
