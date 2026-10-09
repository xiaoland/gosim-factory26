---
name: svc-verification
description: "Use before changing shared entry points or behavior, when first forming acceptance checks, changing their criteria, assessing coverage, or judging delivery. Identify affected journeys, compare actual checks with original scenario obligations, and distinguish passing checks from verified requirements."
metadata:
  version: "16.0.0"
---

# Verification and Validation

Use this skill to decide what evidence is needed, how to obtain it, and what to do with the result while designing, building, changing, and evaluating software.
It applies before implementation, during development and refactoring, at delivery, and when observations from actual use challenge earlier assumptions.
The purpose is to improve product and engineering decisions with trustworthy, timely evidence at a justified cost.

Verification asks whether the product meets its stated requirements.
Validation also asks whether our interpretation of those requirements serves the intended goal.
Tests, measurements, prototypes, and observations answer different parts of these questions; passing a check does not by itself answer all of them.

## The Basis for Judgment

Intent, requirements, design, implementation, and checks are different expressions, and each translation can omit or add a constraint.
Automating an interpretation makes it repeatable, not necessarily correct.
Keep the reason that connects a requirement to its observable consequence, so a disagreement can lead to changing the right expression.

Correctness is relative to requirements and conditions.
A local calculation may be correct while the complete user journey is broken.
A good judgment rejects behavior that violates the requirement and accepts different implementations that satisfy it; greater strictness alone is not greater accuracy.
Explicit interface, timing, and interaction requirements remain constraints on that freedom.

Finite observations usually support conditional conclusions.
A general assertion does not imply that every relevant state was reached, and several passing checks may repeat one mistaken assumption.
Choose the judgment, exercised conditions, and observation mechanism together, then limit the claim to what their actual execution supports.

Feedback has a cost and changes the direction of subsequent work.
Weak checks reward incomplete behavior, overly restrictive checks freeze incidental design choices, and slow feedback delays correction.
Consider meaning, new information, feedback delay, diagnosis, and maintenance together, rather than optimizing only execution time or check counts.

## Follow the Current Decision

Requirements ground evidence design; the chosen conditions and observation boundary limit what results can establish.
Interpreting a result determines whether to accept it, investigate, repair the product or check, or reconsider the design.
Feedback brings that decision into the next change, while new counterexamples can revise the requirements or evidence design.
These are connected questions, not mandatory phases or a reading sequence.

| Current question | Read directly |
| --- | --- |
| Which journeys can a shared change affect, and do the first checks preserve their obligations? | [Check design](references/check-design.md), including shared-change impact and independent translation review |
| What counts as correct, and how can an observation represent the requirement? | [Check design](references/check-design.md) |
| Which cases, measurements, and boundaries provide useful evidence at reasonable cost? | [Evidence design](references/evidence-design.md), including the [check pyramid](references/evidence-design.md#a-check-pyramid) |
| How can the conditions, execution, result, and reset be made reproducible? | [Repeatable checks](references/repeatable-checks.md) |
| What do existing results establish, and what needs to change or be examined next? | [Interpreting results](references/interpreting-results.md) |
| How should evidence guide design, implementation, delivery, and continued use? | [Feedback and evolution](references/feedback-and-evolution.md) |

Keep the property, relevant conditions, original evidence, conclusion, and important gaps in existing task or design material.
Use the detail needed for the next decision; a new report format does not itself improve the judgment.
