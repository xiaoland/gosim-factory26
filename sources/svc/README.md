# Sustainable Vibe Coding Skills

SVC is a collection of eight Agent Skills for software work. Select the skill whose description matches the current need; they can be installed together or independently.

```text
skills/svc-specs/        canonical owners of product, technical, operational, and local Agent knowledge
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

`svc-specs` is independently copied from the complete development SVC `corpus/svc-specs` at revision `45fe1b42ed3670c8d77df1c3603c016b8500481f` (skill version 16.0.0). Its source and content identity are recorded in Factory26 `harness/dependencies.lock.json`; the other skills retain their existing source identity. This addition does not rename or replace `svc-documentation`, and optional cross-skill references do not require installing the full development Corpus.
