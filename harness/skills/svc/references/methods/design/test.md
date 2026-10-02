# Test Design

Use Test Design to decide what observation would support or change a product or technical judgment.
Start with the intended outcome, identify the behavior or property that matters, then choose an observation and a rule for judging it.
Keep requirements distinct from design assumptions and incidental implementation choices.
When the intended behavior needs a choice, use [Product Design](product.md) to form a proposal before treating that choice as an acceptance rule.

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
If the oracle needs revision, explain the requirement change or mistaken assumption; do not relax it merely to make an implementation pass.

## Choose Useful, Affordable Observations

Observe the promised consequence.
For example, a saved setting must remain available to a later session; a success message alone does not establish persistence.
A storage or API check can isolate the persistence rule, while a user-path check establishes that the real interface connects to it.
An incidental route, DOM structure, or storage technique should remain changeable unless the requirement constrains it.

Choose the lowest-cost boundary that preserves this meaning.
Include setup, feedback delay, maintenance, diagnosis, false results, and restrictions on implementation in the cost.
Reuse applicable compiler, type, schema, or component guarantees; add evidence where their assumptions or real composition remain uncertain.
Multiple layers earn their cost through complementary evidence, not a required test count or ratio.

Prefer real dependencies when they are affordable and controllable.
A substitute may help control time, failures, or expensive effects, but must not assume the behavior being checked.
Make important conditions reproducible, results observable, and relevant state resettable when repeated experiments need them.
Choose between a reusable test, a temporary script, and a one-off observation according to the need for repetition and reuse.

Record the property, conditions, observation, judgment, and important gaps in the existing task or design material.
[Verification](../../verification/index.md) interprets the actual results and determines what further evidence is needed.
