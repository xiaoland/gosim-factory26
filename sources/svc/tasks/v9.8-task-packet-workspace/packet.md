# v9.8 Task Packet Workspace Task Packet

## MVT Core

- Objective & Hypothesis: Make task packets explicit as agent-owned, task-local, human-agent-collaboration-oriented workspaces with progressive poly-file splitting. Hypothesis: the model works if SVC defines the invariants and split principles without prescribing exhaustive folder shapes.
- Guardrails Touched:
  - Keep task packets non-durable; stable knowledge still requires the promotion test before entering durable docs.
  - Keep the framework minimal; define principles and recommended methods rather than a rigid directory taxonomy.
  - Do not treat generated `build/monolith.md` as source truth.
- Verification:
  - Source docs define task packet ownership, collaboration orientation, progressive splitting, and search isolation.
  - Templates provide a compact control surface plus optional supporting files.
  - `pdm run build-monolith` and `pdm run test` pass.

## Exploration Scaffold

- Perturbation: The user identified practical gaps in task packet behavior: single-file bias, unclear agent ownership, weak workspace semantics, search noise, and insufficient human-agent collaboration orientation.
- Input Type: Intent with Constraint sub-problems.
- Active Mode or Transition Note: Execute after user confirmed the high-level model and explicitly requested implementation.
- Governing Anchors:
  - `AGENTS.md`
  - `src/index.md`
  - `src/sections/tasks.md`
  - `src/sections/meta-engine.md`
  - `src/sections/filesystem.md`
  - `src/assets/templates/task-packet.template.md`
  - `src/assets/templates/AGENTS.root.template.md`
- Impact Hypothesis: The change affects task layer semantics, dispatcher obligations, filesystem guidance, root AGENTS template behavior, and the generated monolith.
- Temporary Assumptions:
  - `tasks/<task-id>/packet.md` is the recommended control surface name for directory-mode packets.
  - `work/` should remain a generic scratch area rather than a prescribed set of artifact-type folders.
  - Search isolation should be framed as a default for source/durable-doc search, with explicit opt-in when the task targets volatile directories.
- Negotiation Triggers:
  - A proposed directory structure becomes exhaustive or ceremony-heavy.
  - Agent-owned wording weakens human inspectability or durable mutation guardrails.
  - Search exclusion language makes it difficult to intentionally inspect task history.
- Promotion Candidates:
  - Task packet workspace invariants.
  - Progressive split principles.
  - Search isolation defaults for volatile workspaces.

## Execution Notes

- key findings:
  - Existing source defined MVT and task/mode separation, but did not explicitly define task packets as agent-owned workspaces.
  - Existing workflow opened task packets but did not require continuous packet updates during discussion, exploration, implementation friction, or verification.
  - Existing guidance did not define progressive poly-file splitting or default search isolation for volatile task material.
- decisions made:
  - Define task packet invariants in `src/sections/tasks.md`: agent-owned, task-local, human-agent-collaboration-oriented, recoverable, bounded, non-durable, and search-isolated.
  - Keep MVT as the minimum control surface rather than expanding every packet into a rigid structure.
  - Define directory mode as pressure-driven: `packet.md`, optional supporting notes, and a generic `work/` scratch area.
  - Put search isolation in both task guidance and dispatcher/root template guidance.
- final outcome:
  - Source docs now define task packets as agent-owned, task-local, human-agent-collaboration-oriented workspaces with compact control surfaces.
  - Progressive poly-file guidance is explicit in `src/sections/tasks.md`, `src/sections/filesystem.md`, and `src/assets/templates/task-packet.template.md`.
  - Dispatcher and root template guidance now require keeping packets current and excluding volatile/generated surfaces from ordinary source search.
  - `pdm run build-monolith` passed and regenerated ignored `build/monolith.md`.
  - `pdm run test` passed.
