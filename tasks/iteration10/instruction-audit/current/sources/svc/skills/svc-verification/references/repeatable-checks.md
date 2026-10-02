# Repeatable Checks

Use Repeatable Checks when a judgment needs to be run again, compared across changes, or trusted by another person or process.
Make the conditions, action, observation, and failure record explicit enough that a second run can tell what actually happened.

## Construct and Run the Check

Construct the relevant inputs and state.
If the requirement promises behavior from a fresh or default entry, start there and observe its required state before adding test data; setup may create only prerequisites the requirement does not promise to provide.
Record the artifact or candidate version, required setup, selected history, and any dependency conditions that affect the result.
Execute the behavior that the requirement describes, then observe the promised consequence and apply the judgment rule.
Keep the assertion or observation visible; a runner returning successfully does not prove that a key action or assertion ran.
Save the completion result and actual exit status of the command that carries the check during its first execution, alongside the candidate, check entry point, inputs, and relevant setup.
Use the execution tool’s existing job result or durable output record; do not infer an exit status from a passing summary or rerun a long check solely to manufacture a record that already exists.
If that record is missing, state the evidence gap and decide whether the existing observations support the claim or a repeat is necessary.
A successful display filter or final shell command does not replace that status.
Keep output concise while preserving the concrete failure and a path to the original result.
Reuse the execution system's completion signal; separately wait for any product consequence the requirement promises.

Wait for the actual condition being judged.
A returned request, a displayed message, or a completed command may occur before persistence, asynchronous processing, or the user-visible consequence.
Use a bounded condition-based wait where delay matters, and record a timeout as a specific failure with the last useful observation.

## Preserve Failure Meaning

If setup or a prerequisite fails, retain the first concrete failure and mark dependent behavior as unexamined.
Do not report skipped dependent steps as a product pass or product failure.
Keep the inputs, artifact, environment, observation, and original failure information needed to distinguish an application defect, a weak check, an unavailable environment, or an unclear requirement.

Keep ownership of temporary services explicit: retain the job handle or process group created for the check, and stop only those resources.
A separate checkout does not imply a separate process space; program-name cleanup can interrupt another member’s check.

Reset state that could carry a result into the next run.
Recreate relevant sessions, records, files, queues, or other history when the judgment depends on them.
A later pass after stale state or a hidden retry does not erase an earlier unexplained failure.

## Choose the Right Reuse Level

Use a reusable test when the behavior is stable, the judgment will recur, and the maintenance cost is justified.
Use a temporary script when the behavior is important but the experiment or interface is still changing.
Use a one-off observation when it answers an unstable product question and repetition has no current value.
The form can change as the decision stabilizes; the evidence still needs a stated property, condition, observation, and judgment.

Repeat under changed conditions only when the change can distinguish the remaining explanation.
Do not repeat an inconclusive run with identical hidden state and call the unchanged result stronger.
Record what was run, what was observed, what was judged, and what would require another evaluation.
