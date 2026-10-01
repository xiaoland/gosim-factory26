---
name: svc-investigation
description: Obtain missing information or diagnose concrete failures with evidence that distinguishes plausible explanations.
metadata:
  version: "16.0.0"
---

# Investigation

Use this skill when a decision lacks information, an observation is ambiguous, or a concrete failure needs a causal explanation.

State the missing answer, its decision boundary, relevant scope and freshness, and the observation that would distinguish the remaining explanations. Inspect enough context to form a useful question, then stop when the supported answer enables the next action.

Read [the investigation workflow](references/workflow.md) for the core method and a saved-setting example that separates competing explanations, [debugging](references/debugging.md) for concrete failures, and [delegation](../svc-sub-agents/SKILL.md) to decide whether and how to assign an information question.
Use the [Explorer guidance](references/delegating-investigation.md) for its investigation-specific boundary and return.
Return findings with provenance, remaining uncertainty, and consequence for the next action.
