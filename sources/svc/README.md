# Sustainable Vibe Coding Skills

SVC is a collection of seven Agent Skills for software work. Select the skill whose description matches the current need; they can be installed together or independently.

```text
skills/svc-documentation/ product purpose, technical and internal design, operation, and knowledge upkeep
skills/svc-task-packet/  current reasoning, evidence use, task state, planning, and templates
skills/svc-sub-agents/   delegation value, useful assignments, affordable judgment, and result use
skills/svc-investigation/ missing information, diagnosis, and Explorer work
skills/svc-design/       product, technical, and engineering choices
skills/svc-implementation/ intended changes and Executor work
skills/svc-verification/ check design and result interpretation
```

To install the collection, copy `skills/` into the consuming agent's skill location. To install one capability, copy that skill directory with its `SKILL.md` and local references/assets intact.
Each skill is a versioned source; no wrapper, CLI, or Python installation is needed. Cross-skill links are optional routes to related methods; install the linked skill alongside it when that method is needed.
Discovery entries contain only the name, description, and path. Load the skill and its references from their independent files as needed; do not inline their body into system, profile, role, or task prompts.
See [usage](USER_MANUAL.md) and [contribution guidance](CONTRIBUTING.md).

`AGENTS.md`, repository documentation, task history, and inherited `cli/`/`tools/` sources are maintainer material, not part of the skill payload.
The inherited CLI build and release workflows do not publish this skill.
The complete development SVC CLI and its analysis capabilities are maintained separately.
