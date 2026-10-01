# Planning and Rehearsal

Use this method to turn an agreed design and its acceptance criteria into a route that can be executed and adjusted with useful feedback.
A plan connects changes to outcomes; a list of files to edit or commands to run is not enough when dependencies and uncertainty affect the route.
A small, obvious change may need only the next action and its feedback, not a separate planning document.

## Establish the Starting Point

Read the intended behavior, technical decisions, acceptance criteria, and current implementation relevant to the change.
Identify work already in progress and reusable results before assigning or repeating it.
Keep unresolved product choices visible and return consequential ones to design; planning should not silently settle them.
Before handing work to an implementer, distinguish a reversible local assumption from an unresolved choice that changes shared data, interfaces, or acceptance criteria.
For the latter, identify the decision owner and the dependent portion of the work instead of describing the whole design as settled.
Proceed with independent portions; if proceeding provisionally is worthwhile, make the assumption and potential rework explicit to its consumer.
Use [check design](../../svc-verification/references/check-design.md) when the acceptance criteria do not yet distinguish the intended behavior from a plausible failure.

## Resolve Unknowns That Could Change the Route

Before committing to a route, identify unknowns that could overturn the design or cause substantial rework, such as protocol behavior, compatibility, or resource lifetime.
Check the relevant version's documentation, interface definitions, existing callers, and available observations.
When these do not resolve a consequential uncertainty, use the smallest real spike that can distinguish the possibilities and explain how its result changes the plan.
Prefer real execution when it costs less than constructing a faithful simulation.
A mechanical change with no such uncertainty can proceed directly.

Rehearse the proposed route against actual boundaries: what does each change consume, what must already exist, who can change it, and what observation will make its return usable?
Check shared interfaces, required data, environment assumptions, and integration points where a wrong assumption would force later work to be redone.
Rehearsal may be a short walkthrough using verified interfaces or a real operation where behavior remains uncertain; it does not require a second implementation or a simulation suite.
Resolve the uncertainties worth resolving now rather than trying to predict every local detail.

## Build an Executable Route

Work backward from the promised outcome to identify necessary dependencies, then order coherent changes forward from the current state.
For each meaningful return, identify its owner, prerequisites, changed behavior, feedback, and consumer or integration point.
Choose changes that produce useful evidence without leaving a critical invariant broken for a later step to repair.
Do not make all implementation finish before any feedback becomes available.
Use [the check pyramid](../../svc-verification/references/evidence-design.md#a-check-pyramid) to choose early feedback and the broader evidence still needed.

Publish shared decisions before consumers implement incompatible assumptions.
Parallelize work whose effects and feedback can remain independent; separate worktrees do not isolate shared services or mutable data.
A dependency delays its consumers, not every activity of the same owner.
Make integration work explicit instead of assuming independently completed parts will connect themselves.

Plan a linear route only as far as the evidence supports.
Name the observation or decision needed to plan beyond that point rather than inventing distant steps.
An uncertain dependency can have a short conditional next action without expanding into a tree of speculative plans.
Preserve the route and recovery state using [task packets](../../svc-task-packet/SKILL.md); the packet's topology organizes the plan but does not choose the solution.

## Example: Change a Shared Configuration Format

Suppose an editor and an importer must accept an agreed new configuration format while preserving the existing supported format.
Product design has specified the compatibility behavior; acceptance must observe an imported configuration being edited and saved without losing its meaning.

| Return | Preparation and dependency | Useful feedback |
| --- | --- | --- |
| Establish the shared format and transition | Locate the current readers and writers; check whether their parser supports the chosen format, using a small real input if the API documentation leaves doubt. | Resolve the compatibility uncertainty before both consumers depend on it. |
| Implement the shared boundary | Publish the agreed representation and conversion behavior in its authoritative location. | Exercise relevant old/new inputs and invalid cases against the requirement. |
| Adapt editor and importer | Each consumes the agreed revision; work can proceed in parallel if mutable targets and feedback are independent. | Observe each actual caller through the shared boundary. |
| Integrate and qualify the result | Combine the returns in the candidate to be delivered. | Import, edit, save, and reopen using the required initial conditions; observe the promised compatibility and preserved meaning. |

If the parser cannot support the agreed transition, reconsider the technical design before writing two consumer-specific workarounds.
If both consumers must change the same mutable target, revise ownership or sequencing instead of treating the diagram's parallelism as mandatory.
The example illustrates dependencies and feedback, not a required file layout, component architecture, or fixed number of phases.

## Update the Route From Evidence

After a return, compare the observation with the criterion and identify which next work it enables or invalidates.
Repair a local defect within the current route when the design remains sound.
Replan when evidence changes a dependency, responsibility, acceptance assumption, or the intended solution.
Keep the original product obligation unless an explicit design decision changes it; an inconvenient result is not a reason to weaken the criteria.
Preserve still-applicable work and evidence, update the current plan, and communicate changed dependencies to their consumers.
Completion means the agreed outcome has supporting evidence, not merely that every listed step was performed.
