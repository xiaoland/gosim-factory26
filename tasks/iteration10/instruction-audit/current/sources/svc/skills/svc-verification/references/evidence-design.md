# Evidence Design

Use Evidence Design when the judgment is clear enough to ask which conditions and observation boundary can distinguish the important possibilities.
Choose what to examine, where to observe it, and what cost the evidence can justify.

## Select Conditions That Matter

Separate the property being judged from the inputs, state, history, concurrency, and failures used to expose it.
Choose a condition because it can distinguish a consequential uncertainty, not because the condition appears in a familiar test catalogue.
Include a changed value, boundary state, transition, invalid input, or competing actor when that condition changes the prediction that matters.

General properties and concrete cases complement each other.
A general property states the allowed behavior over a meaningful range; a concrete case preserves a known failure or a small reproducible journey.
The general statement does not guarantee that a generator or broad suite will reach a rare boundary, and the concrete case does not establish behavior outside its conditions.

For the saved-setting example, the later read after a real logout and reauthentication is the condition that distinguishes persistence from an in-memory success message.
Add another user, a failed save, or concurrent edits only when the requirement or current risk makes those explanations live.

## Choose an Observation Boundary

Choose the lowest-cost boundary that preserves the promised meaning.
A local state observation can support an internal invariant; an API observation can support an API contract; a real user path is needed when the requirement includes the connected interaction.
Do not expand a local result into a product conclusion merely because the same implementation appears at both boundaries.

Real dependencies are useful when they are affordable and controllable.
A substitute can control time, failure, or expensive effects, but it must not assume the behavior being checked.
Several layers earn their cost through complementary observations, not through a required count or ratio.

Account for setup, feedback delay, maintenance, diagnosis, false results, and restrictions on implementation.
If a cheaper boundary loses a required state transition or hides the failure mode, its apparent speed is not a real saving.
If a broader boundary adds no information for the current decision, stop at the smaller one.

## Measure With a Defined Question

For a measurement, define the observation object, load or stimulus, start and end points, units, samples, statistic, comparison, and threshold.
State uncertainty when noise can change the judgment.
A single number that cannot distinguish the alternatives is not a stable conclusion; improve the measurement or narrow the claim.

Record the property, selected conditions, observation boundary, cost, and important blind spots in the existing task or design material.
Use Repeatable Checks to turn this selection into a reproducible procedure, and use Interpreting Results after execution to limit the conclusion to the observed conditions.
