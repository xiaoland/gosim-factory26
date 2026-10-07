---
name: svc-documentation
description: >-
  Build and maintain durable project understanding: product purpose and behavior, technical responsibilities and contracts, internal design, and operation. Use throughout development to locate the current basis, decide where new knowledge belongs, and keep changed decisions usable by their consumers.
metadata:
  version: "16.0.0"
---

# Project Documentation

Code and configuration express the implementation, but may not preserve why it exists, the behavior it promises, how components cooperate, or how to recover from failure.
Reconstructing that meaning from a conversation or a temporary task record costs attention and can revive a conclusion whose conditions no longer hold.
Project documentation keeps useful meaning and reasons available to people and Agents who must understand, operate, or change the project.
It connects original requirements, current decisions, implementation, and observations without treating them as interchangeable sources of truth.

This need exists during first implementation as well as later maintenance.
Start with enough product understanding to guide the work, then retain knowledge as decisions form and consumers depend on it.
Reuse existing documentation and source locations before adding files.
Prefer code, configuration, types, schemas, or automation for facts they can maintain directly; prose should preserve meaning that those mechanisms cannot cheaply express or recover.

## Choose the Knowledge Owner

Use the responsibility of the knowledge, its consumers, and its change conditions to choose its location.
The following names describe responsibilities; they are not a required directory structure or a document ladder.
An existing README, design document, interface definition, or code comment can already own the subject.

| Current question | Responsibility and deeper guidance |
| --- | --- |
| Who is this for, what should it do, and why? | [Product purpose, promises, rules, and scope](references/product.md), often called PRD. |
| How must independent components cooperate? | [Cross-unit technical design](references/technical-design.md), often called Product TDD: authority, topology, interfaces, lifecycle, ordering, compatibility, and failures. |
| Which internal choices must survive a refactor, or which local hazards need guidance? | [Internal design (Unit TDD) and development instructions](references/internal-and-local.md). |
| How is it packaged, operated, changed, and recovered? | [Deployment and operation](references/operations.md). |
| Why do contributors repeatedly disagree about the object or effect of a request? | [Alignment](references/alignment.md), only when normal identifiers and clearer requests are insufficient. |

A separate document is useful when it has stable content, a real consumer, and enough rediscovery or maintenance cost to justify its own address.
Split for distinct readers or independent change, not merely because a file becomes long.
Keep tentative explanations, active plans, raw evidence, and work in progress with the task; move accepted reusable knowledge to its project owner as it becomes useful.
[Optional templates](assets/templates/index.md) can provide a starting shape after that need is clear.

## Find the Right Source

Maintain a short project entry that maps questions to authoritative locations: intended behavior, technical design and shared contracts, operating instructions, and active tasks.
Describe what each location answers rather than listing every file.
At the start of work, locate the original requirement, the current decisions relevant to it, and the implementation or observations that establish present behavior.
Check their identity and applicability; a path alone does not establish that two branches contain the same definition.
Put local implementation rationale near the relevant code; link to it instead of copying it into a second specification.

Requirements establish the intended behavior; design documents record how the project interprets and realizes it.
A derived document does not silently replace an original requirement.
When sources conflict, identify the conflicting statements and obtain a decision from the responsible contributor before dependent work assumes an answer.
Resolve the meaning from the original goal, constraints, alternatives, and applicable evidence, then update the location that consumers use.
A document's authority identifies where the current decision belongs; it does not make a contradiction with requirements or reality disappear.

As a decision forms, preserve the assumptions and reasons that would change it.
When it becomes the current basis, replace provisional wording and link its implementation or observation when useful.
During a change, update only the owners whose claims changed, then the affected task state.
At completion or handoff, check for reusable knowledge still stranded in temporary notes; preserve the original evidence at its own entry.
Do this throughout the work rather than postponing all understanding until a final report.

## Publish Shared Decisions Before They Become Dependencies

Keep one current definition for each shared rule and give it a stable, discoverable location.
For a contract, state its purpose, inputs, observable results, relevant conditions, and the components that consume it.
When rules can overlap, define their precedence, exceptions, and behavior when no rule applies.
Explain intentional differences between consumers; identical names or data shapes do not establish identical semantics.
Use a small overlapping example when it makes the decision unambiguous, but keep expected behavior grounded in requirements.
Record the rationale and unresolved assumptions that would change implementation choices.

Link dependent work to this definition rather than maintaining separate copies of the same rule in each task or discussion.
Prefer one shared implementation where appropriate; documentation should not justify unnecessary duplicate logic.
Where implementations must remain separate, use [verification design](../svc-verification/references/check-design.md) to obtain evidence that they agree under the relevant conditions.
A published agreement is not evidence that its consumers implement it correctly.

## Keep the Definition and Its Consumers Current

Distinguish proposed behavior from the currently agreed contract and from behavior actually implemented and observed.
When a shared decision changes, update its authoritative location and identify the affected consumers.
Tell their responsible contributors which earlier decision is replaced, what behavior changes, and what action is needed; a link to a long discussion alone leaves them to reconstruct the difference.
An affected contributor checks the change against their current design, plan, implementation, and acceptance criteria, then records the necessary adjustment or why their work is unaffected.
Resolve conflicting interpretations before continuing work that depends on them; unrelated work can continue.
A sent notification does not establish adoption, and a passing check against the previous decision does not establish the new behavior.
Keep agreed project rules with the versioned project materials, so another contributor can obtain the definition together with the code it describes.
Update an existing README, design document, or interface definition when it already owns the rule; a new document or separate change request is not required.
In parallel branches, identify the commit carrying that change so a reference to the same path does not imply the same contents.
Contact the contributors implementing and checking the affected behavior, including work already handed off; notifying only the original task owner can leave the active consumer on the old basis.
Use comments or discussions to reach decisions and coordinate adoption; move the resulting current definition into its stable location and link back when rationale matters.
Retire superseded current instructions rather than appending a competing rule that readers must discover later.
Preserve historical evidence separately when it explains a decision or an unresolved result.

When several implementations or branches must adopt a changed shared rule, read [One rule, several consumers](references/shared-rule-adoption.md). The case distinguishes publishing the definition, checking an overlapping condition, and establishing each consumer's adoption.

## Relationship to Task State

Project documentation holds knowledge used across tasks: what the product promises, how its components fit together, and how to operate them.
[Task packets](../svc-task-packet/SKILL.md) hold a task's current questions, owners, plan, evidence, and next action.
Keep temporary investigation and progress in the packet; when a finding becomes a shared project decision, update the existing project document and reference it from the packet.
For example, a storage unit may need a persistent explanation of why its journal is committed before acknowledging a write; that internal invariant belongs with its design, while the current repair and observations belong with the task.
A recovery procedure belongs with operating instructions when another operator must repeat it, while the incident's failed attempt and logs remain task evidence.
Both skills can be used independently; neither requires a fixed set of documents or a specific collaboration tool.
