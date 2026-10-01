# Design Workflow

Use Design when the intended outcome or its realization needs a consequential choice.
Form a concrete proposal from the task's intent, current system, constraints, and available resources.

Start with a representative journey or state transition where the choice matters.
Trace the entry point, state owner, dependencies, and failure or recovery path.
Challenge a proposed arrangement with a plausible counterexample or change.
If it fails, reconsider the product assumption or technical boundary that caused the contradiction.

- Product Design shapes what people can do, understand, and value.
- Technical Design shapes how the system delivers and maintains that behavior.
- Verification design determines which observations could support or challenge the solution.

These are views of one solution, not separate mandatory phases or files.
Develop enough detail that implementation can proceed without silently deciding a material requirement.
Leave cheap, reversible local choices open when they do not change the outcome.

Read Product Design or Technical Design directly when only one view is needed.
Bring the views together when a product choice changes ownership, lifecycle, failure handling, or what can be observed.
Define the important behavior and its evidence boundary together; a design that cannot be observed or reset may need a different technical boundary.

Use prose, a diagram, a prototype, or another representation that makes the decision easy to understand and revise.
Preserve the recommendation, reasons, important alternatives, assumptions, and remaining uncertainty in the existing task material.
A proposal's coherence does not establish its actual behavior; use the verification skill for that judgment.

## Independent Judgment

Seek independent judgment before committing to an interpretation that several tasks will rely on, a consequential responsibility or interface boundary, or acceptance criteria whose assumptions remain uncertain.
Revisit the decision when contradictory evidence, repeated failures, or growing complexity challenge its basis.
Routine decisions with clear evidence can proceed directly.

Consultation is part of forming a sound decision, not a work package that must earn back delegation, waiting, and verification costs.
Give the advisor the original goal, constraints, relevant sources, and the decision to resolve.
Ask for a recommendation, alternatives, counterexamples, and missing facts that could change the choice.
A proposed solution is one candidate to examine, rather than a conclusion to endorse.

Use the response to revise the decision, resolve a material uncertainty through a small check, or explain why a recommendation does not apply.
Preserve the chosen rationale and remaining assumptions where affected work can find them.
The decision owner retains responsibility; agreement is a judgment input, while validation of behavior requires observations.
