# Check Design

Use Check Design to decide what observation would support or change a product or technical judgment.
Start with the intended outcome, identify the behavior or property that matters, then turn the requirement into an observable result and a rule for judging it.
Keep requirements distinct from design assumptions and incidental implementation choices.
When the intended behavior needs a choice, form a proposal from the product goal, constraints, alternatives, and relevant feedback before treating that choice as an acceptance rule.

The conversion is deliberate: requirement → observable outcome → judgment rule → check implementation.
A requirement link identifies the source; the reason for each conversion explains why this observation can establish the promised behavior.
A complete list of links cannot substitute for that reasoning.
The first three items describe the meaning of the check.
The last item is only one way to obtain the observation.
Preserve any stated scenario preconditions and initial data through this conversion; a check that supplies them itself may prove a narrower behavior than the requirement.
Carry the conditions that make the judgment meaningful into evidence design, and carry setup, execution, waiting, and reset into repeatable checks.

## Express the Behavior Before Choosing the Check

Product intent describes the value sought; a requirement describes what must hold; a design proposes how to achieve it.
For example, preventing duplicate charges is a behavioral constraint, while using a particular queue is usually a design choice.
Treating the queue as the acceptance criterion could reject a valid alternative while overlooking duplicate charges.
Treat a design choice as a product acceptance constraint only when the requirement actually specifies it; evaluate technical design constraints against their own stated reasons and obligations.

Choose an expression that preserves the relevant meaning:

| Behavior being constrained | What the judgment must retain |
| --- | --- |
| State, such as visibility of private data | The actor, ownership, and permitted visible result. |
| Transition, such as a transfer | The prior state, action, resulting state, and required behavior on failure. |
| Journey or time relationship, such as payment followed by confirmation | The connected outcome and any required ordering or deadline. |
| Invariant, such as conservation of funds | The operations, retries, and concurrent conditions over which it must hold. |
| Quantitative behavior, such as search latency | The workload, measured interval, statistic, and grounded threshold. |

These perspectives can overlap; they are aids to understanding, not categories that every feature must fill.
A property expresses a rule across conditions, while a concrete case states an expected result for particular conditions.
A property can be incomplete, and even an adequate property needs conditions that expose the relevant violations.
A general statement is not exhaustive execution.
Use [evidence design](evidence-design.md#select-conditions-that-matter) to choose those conditions and [feedback and evolution](feedback-and-evolution.md#learn-from-counterexamples) to decide what to retain from a discovered failure.

## Decide What the Evidence Must Distinguish

Ask whether the proposed solution meets the stated requirements and whether the interpretation of those requirements serves the original goal.
Passing checks for the first question does not settle the second.
For an open design choice, a prototype, observed use, or a reasoned comparison may be more informative than a pass/fail test.
State the criteria and limits of that judgment without presenting a preference as an objective oracle.

For a check, distinguish **what counts as correct** from **which inputs, states, histories, concurrency, and failures to examine**.
Choose conditions that expose a consequential uncertainty; naming a general property does not cover every situation.
Keep a concrete regression case when it exposes a failure that broader checks would not reliably catch.

The oracle is the rule that determines whether an observation satisfies the requirement.
It defines an acceptance range, which can be too broad or too narrow.
Challenge the oracle in both directions: would broken behavior fail, and would a different implementation that still meets the requirement pass?
First reason through a concrete violation and a valid alternative.
Use a deliberate defect or an equivalent valid implementation when an important doubt remains and execution can expose a weak check at reasonable cost.
If a deliberate violation still passes, distinguish failure to reach the condition, failure to observe its consequence, and an overly permissive judgment.
Do not turn this technique into a mandatory second test system.
Ground expected results in requirements, justified invariants, explicit protocols, or a suitable comparison reference.
A reference implementation can support a comparison, but its applicability and possible shared defects still matter.
Pages, files, databases, and mailboxes provide observations; their current contents do not define what ought to be there.
Never let the implementation determine the acceptance criteria.
If the oracle needs revision, justify it from the requirement or a corrected requirement interpretation, not from what the current implementation happens to do.

A route, role, exact name, protocol order, or visible control is part of the contract when the requirement specifies it.
Otherwise, asserting an incidental URL or markup structure can reject a valid product change without detecting a user-visible defect.
Changing a locator while preserving the promised result may repair observation; accepting a different result changes the judgment and needs a requirement-based reason.

## Check the Translation, Not Only the Code

Before implementing a check, compare its judgment rule with the original requirement and scenario, including the initial state and any named interaction contract.
Check each distinct object or behavior promised by a combined requirement; one working member of a set does not establish the rest.
For a rule with explicit exceptions or non-inclusive categories, choose a nearby allowed and disallowed case that distinguishes the actual rule from a plausible simplification.
When several rules can apply to the same state, include a reachable overlap or transition that distinguishes their precedence or interaction; agreement on isolated examples does not establish agreement there.
For an outcome spanning components, follow the original journey across their actual handoff and observe the resulting state, rather than treating each component's local pass as proof of the connection.
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
