---
name: svc-task-packet
description: Preserve the current state of a non-trivial task across context boundaries, owners, and dependencies.
metadata:
  version: "16.0.0"
---

# Task Packet

Use this skill when work needs recovery, coordination, or a durable record of current truth. A packet stores the outcome, constraints, evidence, unresolved decisions, owners, and next action; it does not replace requirements, source code, or verification evidence.

Keep packet.md short enough to recover the route without reading the full history. Add a Plan, Inquiry, Design, Decision, Verification, Track, Phase, or Cell only when its distinct owner or integration return lowers recovery or coordination cost.

Read the guidance that matches the current need:

| Need | Read |
| --- | --- |
| Coordinate owners, dependencies, and shared barriers | [Planning topology](references/planning.md) |
| Keep inquiry, design, decision, or verification state addressable | [Information modules](references/information.md) |
| Split or shrink a packet as work topology changes | [Growth guidance](references/growth.md) |
| Decide whether and how to delegate bounded work | [Delegation](../svc-sub-agents/SKILL.md) |

Use [templates](assets/templates/index.md) only when a reusable shape helps; they are optional and do not define a fixed packet layout.

## Core method

Take intended behavior from requirements and current truth from observations.
Name the next return, its owner, dependencies, and completion evidence.
Preserve work already in progress and its result entry point so a recovering owner can inspect it before starting overlapping work.
Update the packet when a finding changes the route, a change is integrated, or evidence changes the completion judgment.
Keep facts, inferences, decisions, and uncertainty distinct.
Retire stale projections instead of leaving competing current truths.

For a task that needs more than one obvious action, create or resume tasks/<task-id>/packet.md directly. Name the source of each material claim and link to supporting files when they exist. At completion, leave implemented source, checks, and task evidence in their appropriate locations; the packet remains task state and does not become another project specification.
