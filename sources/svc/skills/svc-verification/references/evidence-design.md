# Evidence Design

Use Evidence Design when the judgment is clear enough to ask which conditions and observation boundary can distinguish the important possibilities.
Choose what to examine, where to observe it, and what cost the evidence can justify.

## Separate Three Connected Choices

The oracle states what counts as correct, selection determines what the system experiences, and observation determines how the result becomes known.
For an invoice, these may be receipt of the right document by the intended recipient within the required time, a particular account and invoice with a retry history, and inspection of that recipient's mailbox and message contents.
An accurate oracle cannot compensate for conditions that never expose a relevant fault, and a suitable input cannot compensate for observing only an intermediate success signal.
If the final result is difficult to observe, reconsider the observation mechanism or technical boundary before replacing the promise with an easier signal.

## Select Conditions That Matter

Finite execution compresses a large behavior space into a smaller set of observations.
This depends on assumptions about which differences affect behavior and which failures matter for the decision.
Start with the uncertainty that could change the next action, then choose conditions that make the competing explanations predict different results.
Implementation details can reveal risks, but the current code's branches do not define all required behavior.

| Selection method | Why and how to use it | Limit of the evidence |
| --- | --- | --- |
| Representative values and boundaries | When a rule divides inputs into regions, choose a value in each relevant region and values on both sides of the boundary to expose a mistaken comparison or rule assignment. | A region may contain differences that the assumed partition overlooks. |
| State transitions and history | When prior login, expiry, permission changes, or retries alter an action's meaning, construct that history and perform the action from the resulting state. | Reaching a state once does not cover every history leading to it. |
| Interacting conditions | When rules can apply together, choose a reachable overlap that exposes their precedence or interaction, instead of testing only each rule alone. | Pairwise combinations do not establish higher-order interactions; choose combinations for a concrete risk. |
| Properties with generated inputs | When a general rule has a trustworthy oracle, generate varied inputs and retain enough information to reproduce a failure, such as the failing input and relevant seed. | The property can be too weak, and the generator can omit rare but important conditions. |
| Invalid inputs and controlled failures | When rejection, timeout, retry, or recovery behavior matters, construct the invalid input or failure and observe the required resulting state. | Not crashing does not establish correct rejection, recovery, or preservation of state. |
| Known counterexamples and important journeys | Preserve a rare failure condition or a connected path whose meaning a cheaper check would lose. | Fixed examples can be overfit and do not define the whole behavior space. |

For the saved-setting example, use a changed value and a real logout and reauthentication to distinguish persistent behavior from an in-memory success message.
Checking the unchanged default could pass even if saving never occurred.
Add another user, a failed save, or concurrent edits when the requirement or current risk makes those explanations relevant, not to complete a generic catalogue.

General properties and concrete cases complement each other.
Keep a specific case when a broader check would not reliably exercise its valuable conditions.
When reporting coverage, name the space being covered, such as requirements, transitions, journeys, or code branches; a percentage in one space does not establish coverage in another.

## Choose an Observation Boundary

Choose the lowest-cost boundary that preserves the promised meaning.
A local state observation can establish an internal invariant, an API observation can establish an API contract, and a real user path can establish the connected interaction that the requirement promises.
A transfer function's conservation rule does not establish conservation through real transactions and retries.
A browser-specific authentication redirect loses part of its meaning if the browser is removed from the check.

Use real dependencies when they are affordable and controllable, because their actual interaction can expose assumptions that substitutes hide.
A substitute is useful for controlling time, rare failures, or costly external effects.
Make it express the minimum contract the system actually depends on, and identify which assumptions still need a real interaction.
A fake that is configured to return the required persisted value cannot establish that the application persisted it.
Asserting collaborator call counts or order is justified when the protocol requires them; otherwise it can bind the check to a design that could validly change.

Compare the total cost: setup, resource use, feedback delay, maintenance, diagnosis, false results, and restrictions on valid implementation choices.
A fast but brittle substitute may cost more over the product's life than a real integration.
A broad journey that adds no information for the current decision may cost more than a local check with the same useful meaning.
Several layers earn their cost through complementary observations and better diagnosis, not a required count or ratio.

## A Check Pyramid

Use cheaper, more local feedback to find and explain defects early, then use broader boundaries to establish connected behavior and the promised product outcome.

```text
                    End-to-end
             Real user journey and outcome
                  Integration
          Real component handoffs and state
                Local behavior
         Rules, transitions, and components
               Static checks
      Syntax, types, build, and static constraints
```

This is a model of feedback scope and cost, not fixed test counts, mandatory ratios, or an execution gate.
A layer earns its place by exposing a relevant failure; actual costs depend on the system.
Start an important end-to-end check early when it reveals a route-changing uncertainty.
A build may execute generators or other code; it still does not establish the user journey.

Use the [saved-setting example](check-design.md#a-requirement-to-judgment-example) to connect the layers:

| Boundary | Useful observation | What it does not establish |
| --- | --- | --- |
| Static | The chosen setting representation and callers satisfy declared types or schemas. | The correct value is saved or restored. |
| Local | Valid changes and relevant invalid inputs produce the intended transition. | Authentication, storage, and the UI are connected correctly. |
| Integration | The actual save/read path persists the changed value for the authenticated user. | The user-facing control invokes that path and displays its result. |
| End-to-end | Change the setting through the UI, log out, log in, and observe the promised value. | Every local rule or unrelated journey works. |

Use several layers when their observations are complementary, not to repeat every case through every boundary.
After a local repair, rerun the path that originally exposed the defect and the broader outcomes affected by it.
Even a fully green pyramid can share a wrong interpretation: [check design](check-design.md) grounds the oracle in requirements, and [result interpretation](interpreting-results.md) limits each conclusion to its evidence.

## Measure With a Defined Question

A measurement needs a defined object and comparison before a number can answer a useful question.
For search performance, decide whether the requirement concerns API response time or the time until the user can use the results.
Define the units and choose the start and end events accordingly; stopping at response receipt would omit rendering if the requirement concerns usable results.
Specify the relevant data volume, query distribution, offered load, hardware and network conditions, and cold or warm state.
These conditions change the work being measured, so they can change the conclusion without any implementation improvement.

For example, comparing a cold baseline against a warmed candidate can attribute cache effects to the code change.
Compare like conditions, or report cold and warm behavior separately when both matter to use.
A mean can hide a slow tail, while a tail statistic from very few observations can be unstable.
Choose samples and a statistic that address the requirement, retain the underlying observations needed to explain variation, and distinguish a stated acceptance threshold from a target proposed during exploration.
Do not invent a universal time limit.

If noise is large enough to reverse the decision, obtain comparable additional observations, improve control of the relevant conditions, or narrow the claim.
Repeated samples help only when they address that uncertainty; a precise result under an irrelevant workload remains irrelevant.
For an optimization, check that a faster response still produces the required result rather than doing less required work.

## Make the Question Practical to Examine

Technical design and evidence design constrain each other.
If an expiry check requires waiting a day, identify the time-dependent decision and consider controlling time at that boundary.
If a request is accepted but its effect is invisible, find or provide an observation of the promised result, with diagnostic signals to explain delays.
If one run changes permissions or data needed by the next, provide a way to restore the relevant initial state or use an independent data scope.

First check that the observation boundary is appropriate; difficulty alone does not justify replacing a real interaction with a substitute.
Then consider a concrete design improvement, such as explicit state or separation of a decision from its side effect, when it removes the observed obstacle.
Do not introduce a general testing architecture without such a need.

Record the selected conditions, observation boundary, comparison, cost, and important blind spots in the existing task or design material.
Use [repeatable checks](repeatable-checks.md) for the execution procedure and [interpreting results](interpreting-results.md) to limit the conclusion to what actually ran.
