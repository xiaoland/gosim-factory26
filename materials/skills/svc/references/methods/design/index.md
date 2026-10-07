# Design

Use Design when the intended outcome or its realization needs a consequential choice.
Form a concrete proposal from the task's intent, current system, constraints, and available resources.

Start with a representative journey or state transition where the choice matters.
Trace the entry point, state owner, dependencies, and failure or recovery path.
Challenge a proposed arrangement with a plausible counterexample or change.
If it fails, reconsider the product assumption or technical boundary that caused the contradiction.

- [Product Design](product.md) shapes what people can do, understand, and value.
- [Technical Design](technical.md) shapes how the system delivers and maintains that behavior.
- [Test Design](test.md) determines which observations could support or challenge the solution.

These are views of one solution, not separate mandatory phases or files.
Develop enough detail that implementation can proceed without silently deciding a material requirement.
Leave cheap, reversible local choices open when they do not change the outcome.

Use prose, a diagram, a prototype, or another representation that makes the decision easy to understand and revise.
Preserve the recommendation, reasons, important alternatives, assumptions, and remaining uncertainty in the existing task material.
A proposal's coherence does not establish its actual behavior; use [Verification](../../verification/index.md) for that judgment.
