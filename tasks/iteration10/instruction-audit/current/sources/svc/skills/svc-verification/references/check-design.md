# Check Design

Use Check Design to decide what observation would support or change a product or technical judgment.
Start with the intended outcome, identify the behavior or property that matters, then turn the requirement into an observable result and a rule for judging it.
Keep requirements distinct from design assumptions and incidental implementation choices.
When the intended behavior needs a choice, use the design skill's Product Design guidance to form a proposal before treating that choice as an acceptance rule.

The conversion is deliberate: requirement → observable outcome → judgment rule → check implementation.
The first three items describe the meaning of the check.
The last item is only one way to obtain the observation.
Preserve any stated scenario preconditions and initial data through this conversion; a check that supplies them itself may prove a narrower behavior than the requirement.
Carry the conditions that make the judgment meaningful into evidence design, and carry setup, execution, waiting, and reset into repeatable checks.

## Decide What the Evidence Must Distinguish

Ask whether the proposed solution meets the stated requirements and whether the interpretation of those requirements serves the original goal.
Passing checks for the first question does not settle the second.
For an open design choice, a prototype, observed use, or a reasoned comparison may be more informative than a pass/fail test.
State the criteria and limits of that judgment without presenting a preference as an objective oracle.

For a check, distinguish **what counts as correct** from **which inputs, states, histories, concurrency, and failures to examine**.
Choose conditions that expose a consequential uncertainty; naming a general property does not cover every situation.
Keep a concrete regression case when it exposes a failure that broader checks would not reliably catch.

Challenge the oracle in both directions: would broken behavior fail, and would a different implementation that still meets the requirement pass?
Use a deliberate defect or an equivalent valid implementation when it can expose a weak check at reasonable cost.
Never let the implementation determine the acceptance criteria.
If the oracle needs revision, justify it from the requirement or a corrected requirement interpretation, not from what the current implementation happens to do.

## Check the Translation, Not Only the Code

Before implementing a check, compare its judgment rule with the original requirement and scenario, including the initial state and any named interaction contract.
Check each distinct object or behavior promised by a combined requirement; one working member of a set does not establish the rest.
For a rule with explicit exceptions or non-inclusive categories, choose a nearby allowed and disallowed case that distinguishes the actual rule from a plausible simplification.
Observe the promised boundary: a visible label does not establish a required interactive control, and a successful response does not establish a required state change.
Use these distinctions when the requirement makes them relevant, not as additional requirements for every task.

If a check creates data or changes initial state to reach a later behavior, record what that setup bypassed.
Keep a separate observation of the promised initial state when the product must provide it.
When contradictory requirements require an assumption, keep the unresolved branch visible; a pass under the chosen assumption does not validate the discarded interpretation.

## A Requirement-to-Judgment Example

Suppose the requirement is: “After a user saves a setting, the same user can see that setting after the next login.”
The requirement promises a state that survives a session boundary.
A “saved successfully” message is an observation, but it does not establish that the later read returns the saved value.

Use the real save path with a value different from the initial value, end the old session, authenticate again as the same user, and compare the later read with the expected value.
A storage record can help diagnose persistence, but it cannot by itself establish that the user path saved and read the value.
The judgment rule is therefore the later user-visible value, under the stated session transition, not the presence of a message or an internal record.

Challenge the check in both directions.
If the implementation only changes memory or only displays success, the check should fail.
If the implementation changes its route or storage mechanism while preserving the requirement, the check should still pass.
Do not add service restart, another user, or concurrency as mandatory conditions unless the requirement or current risk requires them.

This example is a method, not a universal persistence checklist.
Choose additional conditions when they distinguish a live uncertainty; do not turn the example's details into requirements that were never stated.

## Choose Useful, Affordable Observations

Choose the observation boundary and execution form in [Evidence Design](evidence-design.md) and [Repeatable Checks](repeatable-checks.md).

Record the property, conditions, observation, judgment, and important gaps in the existing task or design material.
The interpreting-results guidance determines what the actual result supports and what further evidence is needed.
