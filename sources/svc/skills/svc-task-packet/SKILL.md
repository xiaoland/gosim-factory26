---
name: svc-task-packet
description: Use for multi-step work to keep current reasoning, decisions, evidence, and work in progress usable outside the conversation, during investigation, implementation, coordination, and recovery.
metadata:
  version: "16.0.0"
---

# Task Packet

Conversation accumulates in time order, while the current decision depends on a smaller set of still-applicable facts, explanations, and unanswered questions.
Appending every return makes that basis harder to recover and can revive an old conclusion after its assumptions changed.
Keeping only the final answer loses the material needed to reconsider it.
A task packet provides working memory outside the conversation: a current synthesis and route, with addressable sources and work that can be read when needed.
It helps reasoning and action during the task, rather than merely documenting progress afterward.

## Start With the Existing Material

For work with more than one obvious action, create or resume `tasks/<task-id>/packet.md`.
First inspect an existing task entry and work in progress; do not start a competing packet or repeat work merely because the conversation changed.
A short entry can begin with the following content, without requiring these as fixed headings:

- The outcome and boundaries, with the original requirement entry.
- The current explanation or decision and the evidence that supports it.
- Material questions or assumptions that remain unresolved.
- The next useful action, why it follows, and what observation or return can change it.
- Existing owners and ongoing work, with entries to their materials and results when coordination matters.

Link the original observation, source, or detailed work rather than copying every transcript into the entry.
The entry must still explain the current basis; a list of links leaves the next owner to reconstruct the answer.
Keep it short enough to recover the problem and route before reading depth.
Use the task's communication language and concrete component names rather than organization vocabulary that the reader must decode.

## Use the Packet While Reasoning

Acquire relevant material, form the current explanation, obtain an observation that distinguishes live alternatives, use the result, and revise the explanation and next action.
Keep facts, inferences, decisions, and uncertainty distinct through that loop.
Intended behavior comes from requirements and accepted decisions; observations establish what happened under their actual conditions.
Stored evidence is available for judgment, but has not been adopted merely because it appears in a file.

For example, an editor and importer share a configuration format, and reopening an imported file produces an unexpected preference.
The packet links the shared definition and failing file, records the observed result, and keeps two explanations live: the importer changed the value, or the editor applied a different precedence rule.
The next action observes the stored value and the editor's later interpretation for the same file revision.
The result selects one explanation or exposes a missing condition; update the current answer and route accordingly.
Do not leave the rejected explanation beside the new one as an equally current instruction.

If the finding changes the shared rule, update its project definition and coordinate the editor and importer consumers.
The packet records the accepted interpretation, adoption state, remaining dependency, and each owner's current work entry.
New feedback can reopen the question or change the implementation route without requiring a new packet.
Messages communicate the question, decision, and material entry; the task files preserve the usable work state.

## Revise What Changed

Update the packet when a result changes the explanation, decision, next action, completion judgment, or owner of work.
When a shared decision changes, update that definition first and then the affected task state.
An unrelated change does not require synchronizing every remote value or rewriting a progress report.
Preserve the condition and source that explain why a conclusion changed, while retiring it from the current action basis.
Do not falsify history by replacing the original failed output with a later successful result.

At handoff or recovery, leave enough current synthesis and ongoing-work entries to avoid repeating retrieval or overlapping existing effects.
At completion, state the actual result and remaining uncertainty with their evidence.
Implemented source, raw observations, and durable project knowledge retain their own locations; the packet does not become another project specification.

## Read Deeper Only When Needed

Keep small plans and explanations in the entry while that makes them easier to use.
Add a file when distinct retrieval, ownership, update pressure, or dependency control makes the extra address useful.
The following guidance supports that need without imposing a first-use shape check or mandatory hierarchy:

| Need | Read |
| --- | --- |
| Keep evidence, current explanations, designs, decisions, and result judgments usable | [Information and result use](references/information.md). |
| Plan a route or coordinate owners, dependencies, and real shared barriers | [Planning and dependencies](references/planning.md). |
| Decide what work another Agent can usefully own and how to consume it | [Delegation](../svc-sub-agents/SKILL.md). |
| Preserve accepted reusable product, technical, or operating knowledge | [Project documentation](../svc-documentation/SKILL.md). |

Use [templates](assets/templates/index.md) only when their shape helps; they are optional starting material, not a fixed packet layout.
