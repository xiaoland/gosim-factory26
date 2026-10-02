# Investigation Delegation

Use Explorer when an information question has a noisy retrieval path that benefits from separate attention.
Apply the [delegation criteria](../../svc-sub-agents/SKILL.md) before creating the assignment.
Specify which decision needs the answer, relevant sources, scope and freshness, the read-only boundary, and what answer is sufficient.

Use the workflow in this skill to distinguish observations from explanations and stop when the answer is useful enough.
Return a concise finding, supporting provenance, important unknowns, and the next useful observation if needed.
The result should enable the consumer's decision without requiring the consumer to repeat the search.
Keep downstream decisions with the consumer and return questions that exceed the assignment's scope or authority.
