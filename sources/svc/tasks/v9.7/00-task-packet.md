# v9.7 Alignment Substrate Task Packet

## MVT Core

- Objective & Hypothesis: Define a source-first v9.7 rollout plan that upgrades SVC from Alignment Pack to Alignment Substrate without breaking durable ownership. Hypothesis: the new model works if alignment owns the coordination grammar, meta-engine owns the execution protocol, and existing layers keep owning the underlying truths.
- Guardrails Touched:
  - Do not turn alignment into a new truth layer or a replacement for PRD, TDD, tasks, or local `AGENTS.md`.
  - Do not turn the seven primitives into mandatory bureaucracy for every task; MVT must remain the default lightweight entry point.
  - Do not promote `build/monolith.md` back into source truth; `src/` remains authoritative.
- Verification:
  - `tasks/v9.7/` contains stable why / what / how notes that can drive source edits without reopening the core framing debate.
  - The blueprint states a clear durable owner for each new rule or concept.
  - The eventual implementation path can update `src/`, regenerate `build/monolith.md`, and keep `pdm run test` green.

## Exploration Scaffold

- Perturbation: The user wants SVC v9.7 to absorb Symmetric Substrate Theory, centered on alignment pack evolving into alignment substrate.
- Input Type: Intent with Constraint sub-problems.
- Active Mode or Transition Note: Solidify now; the conceptual direction is accepted, but the file-level rollout and owner split must be stabilized before editing framework sources.
- Governing Anchors:
  - `AGENTS.md`
  - `src/index.md`
  - `src/sections/alignment.md`
  - `src/sections/meta-engine.md`
  - `src/sections/ontology.md`
  - `src/sections/tasks.md`
  - `src/sections/promotion-rules.md`
  - `src/assets/mappings/durable-destination-map.md`
  - `src/assets/templates/alignment-change-request.template.md`
- Impact Hypothesis: v9.7 will affect framework narrative, alignment ownership, execution protocol, task expansion rules, migration guidance, templates, and naming consistency across the monolith build.
- Temporary Assumptions:
  - `Symmetric Substrate Theory` is the design rationale, while `Alignment Substrate` remains the operative SVC term.
  - The current `build/monolith.md` already contains a useful but non-authoritative draft of parts of v9.7.
  - The cleanest migration path is a staged source update: first narrative and ownership, then SOP and template tightening.
- Negotiation Triggers:
  - A proposed rule makes alignment own truths that already belong to PRD, TDD, deployment, or tasks.
  - A proposed template makes seven explicit fields mandatory for all ordinary tasks.
  - A proposed rule implies stable anchors must be added everywhere rather than only where drift pressure exists.
- Promotion Candidates:
  - `Alignment Substrate` as the stable framework term for `15-alignment/`
  - Impact Handshake trigger language in `00-meta`
  - Conditional substrate expansion language in `tasks`
  - Alignment request template upgraded around the seven coordination primitives

## Execution Notes

- key findings:
  - `src/index.md` already named `15-alignment/` as `Alignment Substrate`, but `src/sections/alignment.md` and part of the section index still used `Alignment Pack`.
  - `build/monolith.md` contained a partial v9.7-style draft before the source files were updated, which confirmed direction but also exposed source/build drift.
  - The current framework already had substrate fragments: MVT, evidence-first diagnosis, blast-radius thinking, stable anchors, and verification contracts were present but not yet unified.
- decisions made:
  - Use `tasks/v9.7/` as the working directory for rationale, scope, and file-by-file design.
  - Keep `10-why-alignment-substrate.md` and `20-what-v9.7-scope.md` as the canonical why/what notes, and remove the duplicate shorter filenames.
  - Keep MVT as the default compact protocol; treat substrate as an on-demand expansion when coordination pressure rises.
  - Split ownership explicitly: alignment owns grammar, meta-engine owns protocol, existing truth layers keep their own invariants and evidence.
  - Complete phase 1 source edits first, with adjacent v9.7 wording cleanups where source/build drift would otherwise persist.
  - Use phase 2 to tighten consistency only where the owner split or load-path wording was still loose: tasks, promotion rules, owner map, ontology, execute SOP, and root template.
- final outcome:
  - `tasks/v9.7/` is now a single-path task container with why / what / how notes.
  - Phase 1 source edits are complete in `src/`, `pdm run build-monolith` passed, and `pdm run test` passed.
  - Phase 2 consistency pass is also complete: MVT vs substrate expansion, alignment vs meta-engine ownership, and template load rules are now aligned.
  - The regenerated `/Users/lanzhijiang/Development/svc/build/monolith.md` and local test suite both pass after the full v9.7 edit set.
