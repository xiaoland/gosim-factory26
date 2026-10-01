# Feedback and Evolution

Use this guidance to connect evidence with the next design, implementation, delivery, or operational decision.
Feedback is useful because it changes what to do next, not because a check ran or a report grew.
Choose its form and timing around the uncertainty: stable behavior calls for repeatable constraints, while an unresolved product choice may need a prototype, comparison, or observation of use.

## Choose Test-first for Stable Behavior

When the intended behavior is clearer than its implementation and a check can exercise the meaningful boundary at reasonable cost, expressing that behavior first can guide the search for an implementation.
It makes the desired result available before implementation details bias the oracle and provides quick evidence when a change violates it.

The initial expected failure matters because it can show that the check distinguishes the missing behavior.
Syntax errors, unavailable dependencies, or broken setup do not provide that evidence.
A pass provides evidence only for the exercised behavior and conditions; it does not establish completeness.
If the behavior already exists, do not damage it to manufacture an initial failure.
Use the [two-direction challenge](check-design.md#decide-what-the-evidence-must-distinguish) when there is a concrete remaining doubt about the check's discrimination.

What is expressed first also influences the design search.
A constraint on the saved value leaves alternative storage designs available; an unjustified sequence of collaborator calls can freeze a guessed architecture.
An explicit protocol can legitimately require an interaction order, so the distinction rests on the requirement rather than on whether a mock is used.

If the uncertainty is what the product should do, a precise assertion can prematurely stabilize a poor choice.
For example, an onboarding prototype and observed use can help choose an understandable flow before tests preserve its sequence.
Resolve that choice from the product goal, alternatives, and relevant feedback, then express the parts that have become stable.
Test-first supports implementation search; it does not replace discovery of the intended behavior.

## Combine Fast Feedback With Complete Outcomes

A fast loop uses small coherent changes and prompt feedback to localize errors and choose the next implementation step.
A broader loop examines real combinations, user journeys, and conditions that local checks omit.
The distinction is purpose and cost: a local performance measurement can be fast feedback, and an early end-to-end check can resolve an uncertainty that would otherwise send the whole design down the wrong route.
Do not postpone the first meaningful product observation until all implementation is complete.

Choose the next coherent change with the relevant product constraints, shared contracts, and invariants in view.
A small diff that updates one authoritative value while leaving its consumers inconsistent is not coherent merely because it is small.
Local success helps guide the work, but cannot establish a connected outcome that it did not observe.
Use the [check pyramid](evidence-design.md#a-check-pyramid) to obtain complementary feedback, not to run every case at every layer.

During refactoring, applicable behavioral checks constrain what must remain stable while internal structure changes.
During optimization, the performance comparison must remain comparable and the functional result must still satisfy its requirements.
After a local repair, examine the path that exposed the fault and the affected broader obligations, reusing other evidence that remains applicable.

Technical and verification design should evolve together.
If required state cannot be constructed, observed, or reset, that cost can justify changing a technical boundary.
First ensure the selected observation boundary preserves the requirement; otherwise architectural changes may solve a testing difficulty while losing the actual question.
When evidence contradicts a design assumption, revisit that assumption instead of treating a series of local exceptions as proof that the design is sound.
A green end-to-end journey can establish its outcome without proving that the architecture is easy to understand or change.

## Learn From Counterexamples

A failure can improve the behavior model as well as motivate a patch.
Preserve enough conditions to reproduce the discrepancy, then ask whether it reveals an implementation error, a missing property, an omitted condition, or an inaccurate observation.
Do not assume every failure calls for a new rule or a permanent one-case test.

For sorting, `[2, 2, 1]` becoming `[1, 2]` can pass a check that output is ordered.
The counterexample reveals a second requirement: sorting must preserve the input multiset.
Checking that property on varied inputs can reject more defects than preserving only this one expected output.
An access failure after a permission change may instead reveal a missing history in condition selection, while the permission rule itself was already correct.

Generalization does not automatically make the concrete case redundant.
Keep it when it preserves a rare combination, an important journey, or a failure a generator would not reliably reach.
Replace or consolidate it only when the replacement retains that evidence value.
Regression describes the purpose of preventing established behavior from degrading; property-based checks can serve that purpose as well as fixed examples.

Update the relevant behavior definition or condition selection and obtain evidence for the correction.
When a check changes, retain the reason: an agreed requirement changed, the observation mechanism needed adaptation, or the previous check encoded an identifiable mistake.
Making the current implementation pass is not by itself a reason to loosen the judgment.
The aim is a more accurate allowed-behavior boundary, which can require tightening an overly weak rule or relaxing an unjustified restriction.

## Carry Evidence Through Delivery and Actual Use

During design, identify the required outcomes and useful observations.
During implementation, use timely feedback to guide coherent changes.
At delivery, evaluate the integrated candidate against the promised outcomes using [applicable evidence](interpreting-results.md#reuse-evidence-and-stop-at-a-supported-decision).
In actual use, observe whether real workloads, long-lived state, and user behavior challenge assumptions that earlier checks could not fully reproduce.
These activities need not introduce new phases, roles, or documents.

When actual use produces a counterexample, preserve the relevant conditions and bring the uncertainty back into development.
A slow request under a previously unseen data distribution may require a new workload model rather than simply a larger timeout.
If users can complete a flow but it does not serve the intended goal, revisit validation and product design rather than adding assertions for the existing flow.

Real-use evidence contains conditions that controlled environments may miss, but observing a fault there can mean that users have already been affected.
Choose the scope of an automated operational response according to evidence reliability, uncertainty, and the consequences of being wrong.
Stopping new work, reverting code, and compensating effects address different problems; reverting code cannot unsend an email or undo a completed payment.

Automate judgments that recur, have trustworthy machine-observable criteria, and affect a real decision.
For subjective or unsettled questions, state the observation and judgment limits instead of inventing a threshold to make them automatable.
Retain the decisions and useful evidence in existing task and design material, and improve the method when actual use reveals its costs or blind spots.
