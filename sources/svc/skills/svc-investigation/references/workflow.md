# Investigation Workflow

Use Investigation to obtain information that can change a decision or make the next action possible.
If the answer has an obvious authoritative source, query it directly.

## Identify the Missing Answer

State what needs to be understood and how the answer will be used.
Choose the scope, version, environment, and freshness that matter to that use.
Separate observed facts from candidate explanations and assumptions.
When new evidence changes the question, keep findings that still apply.

Choose the smallest query scope and output that can distinguish the live explanations.
Request relevant fields or sections before dumping complete files, directories, or process lists.
Keep a source handle for details that the consumer may need; a short display must not turn a failed query or incomplete search into a negative finding.

For an unfamiliar problem, first inspect enough of the context to form a useful question.
When several explanations or approaches remain plausible, seek an observation on which they differ.
If every candidate assumes the same disputed premise, reconsider that premise before searching deeper within those candidates.
A model, example, existing record, direct observation, or small experiment can supply the distinction; choose by its likely value and cost.

## Example: A Saved Setting Disappears

Suppose a user sees the previous value after logging in again.
Before adding retries, distinguish where the changed value stops following the promised path.

| Candidate explanation | Observation that separates it | Consequence |
| --- | --- | --- |
| The control never sent the changed value. | Inspect the actual save request and response from the failing journey. | Repair the caller or its interpretation of the response. |
| The write did not persist. | Follow that request to the stored value for the same identity. | Investigate the write boundary and its failure handling. |
| The read uses another identity or stale state. | Compare the later read's identity and returned value with the stored value. | Investigate the read path rather than repeating the save. |
| The UI displays something else. | Compare the later response with the rendered control state. | Investigate presentation or client state. |

These are starting hypotheses, not an exhaustive checklist.
Choose the next observation using evidence already available; a failed authentication setup may prevent any of these paths from being exercised.
A second search that yields the same facts does not distinguish them, while one matching request or identity can change the next action.
After diagnosis, [verification](../../svc-verification/SKILL.md) returns to the promised journey; a correct database row alone does not establish the user outcome.

## Return Enough to Enable the Decision

Stop when the supported answer is sufficient for its intended use and further investigation is unlikely to repay its delay and attention cost.
More sources that repeat the same information do not necessarily improve the answer.
Return the finding, its provenance, remaining uncertainty, and the consequence for the next action.
If a needed observation is unavailable, identify that gap rather than presenting absence of evidence as a negative result.
Keep recoverable inquiry state in the task-packet skill's inquiry guidance; do not make the consumer reconstruct it from a search transcript.

## When Work Stops Advancing

Repeated searches, explanations, patches, or reviews deserve reconsideration when they neither improve the artifact nor change what you know. Ruling out an explanation or identifying a necessary external wait is useful progress; elapsed time and tool-call counts alone do not measure it.

Before repeating work, identify what has changed or what a new observation could distinguish.
Revisit the question when the goal is unclear and the evidence path when observations are missing.
Use an available completion notification or wait mechanism for work already in progress.
Do not add repeated sleep-and-status calls that provide no new decision-relevant information.
If no completion signal is available and progress must be checked, make the query bounded and preserve the condition that will justify the next action.
Preserve the current conclusion and next useful action in the task-packet skill.
When continuation is not feasible, return the supported result and the specific unmet condition.
