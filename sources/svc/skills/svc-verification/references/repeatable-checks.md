# Repeatable Checks

Use this guidance when a judgment needs to be run again, compared across changes, or trusted by another person or process.
Repeatability makes a difference interpretable: without known starting conditions, an observed change could come from the product, its environment, or earlier activity.
It does not establish that the judgment itself represents the requirement; use [check design](check-design.md) for that question.

Connect conditions → action → observation → judgment → reset → retained result.
Each link serves a different purpose: reach the relevant behavior, exercise it, see its consequence, interpret it, prevent carryover, and preserve what actually happened.

## Establish the Conditions

Construct the inputs, state, and history chosen in [evidence design](evidence-design.md).
Record the candidate or artifact, check entry point, relevant setup, and dependency conditions that another execution would need to interpret a difference.
When the requirement promises a fresh or default entry, observe its required initial state before adding data.
Setup may create prerequisites that the product does not promise to supply, but manually creating promised initial data would bypass part of the requirement.
Keep that initial-state obligation separate from any later behavior examined with constructed data.

If a prerequisite fails, retain the first concrete failure and mark dependent behavior as unexamined.
A login failure means a later save was not exercised; it does not establish whether saving works.
Use the concrete failure to decide whether the environment, check, or product needs repair, rather than translating all unfinished steps into product failures or passes.

Before execution, choose a durable result location for the complete command output and actual exit status, with the candidate and relevant conditions.
Use an execution tool's retained record or a separate output file; do not add a reporting system when the existing record suffices.
Retain each execution as a distinct, directly referenceable result, so a repeat cannot overwrite an earlier failure or interruption.

## Exercise and Observe the Promised Consequence

Execute the behavior described by the requirement and apply the judgment rule to its consequence.
Keep the important action and assertion visible in the execution record: a successfully completed runner does not establish that either ran.
For saved settings, a response or success message can precede persistence; observe the later read under the required session transition.

Reuse the execution system's completion signal to learn when the command finishes, and separately wait for any product consequence promised by the requirement.
Where asynchronous delay matters, use a bounded wait for the actual condition rather than a fixed sleep that can be too short or unnecessarily long.
On timeout, retain the expected condition, elapsed bound, and last useful observation, so “timeout” does not erase what was reached.
Choose the bound from the requirement or justified execution conditions; changing it can change what the check establishes.

Capture the status of the command that carries the check before any display filter.
A successful filter or final shell command does not establish the check's exit status.
Preserve concrete error messages, response status and useful response content, and the relevant inputs and state before reducing them to a summary.
If the output or status is missing, report that gap; a later pass supports its own execution but cannot explain the lost failure.
Do not repeat a long check merely to manufacture a record that already exists.

## Reset Without Losing the Explanation

State carried between runs can make a missing action appear successful or create a failure that a clean run would not reproduce.
Reset the sessions, records, files, queues, permissions, or other history on which the judgment depends.
Use controlled cleanup or an independent data scope that preserves the required conditions, rather than assuming a fresh process implies fresh state.
If state cannot be restored, make the changed conditions explicit and limit comparisons accordingly.
A hidden retry or later pass does not erase an earlier unexplained failure.

Keep temporary services attributable to the check that created them, using the job handle or process group that the execution system provides.
Stop only those resources: a separate checkout does not create a separate process space, and cleanup by program name can interrupt another execution.
Retain the failure evidence needed for diagnosis before cleanup removes the relevant state.

## Preserve the Execution in the Handoff

Produce the summary from the retained original result, including the concrete failure and a direct reference when one occurred.
Before handing it off, confirm that the candidate, relevant conditions, actual exit status, and cited output belong to the same execution.
Keep earlier and later results separately attributable; combining an earlier successful status with a later failure log creates an event that never happened.
Describe which later observation resolves an earlier failure, or leave the contradiction visible for [result interpretation](interpreting-results.md).

A missing record is a limitation in evidence, not a reason to invent an outcome.
Decide whether another execution would resolve a live question, and retain its separate identity if it is useful.
This lets another person reuse applicable evidence without mistaking a summary or a retry for the original observation.

## Choose the Right Reuse Level

Use a reusable test when the behavior is stable, the judgment will recur, and maintenance is justified by the feedback it provides.
Use a temporary script when the question matters but the experiment or interface is still changing.
Use a one-off observation when it answers an unstable product question and repetition has no current value.
The form can evolve as the question stabilizes; every form still needs conditions, an observation, and a grounded judgment.

Repeat under changed conditions when the change can separate remaining explanations.
Repeating the same inconclusive execution with the same hidden state adds little evidence.
Record what was run, what was observed, what was judged, and what would require another evaluation in the task's existing material.
