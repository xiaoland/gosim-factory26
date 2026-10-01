# How To Project v9.7 Into Source Files

## Implementation Strategy

Work source-first and keep the blast radius small:

1. normalize naming and release framing
2. rewrite the alignment section around substrate ownership
3. add the handshake trigger where protocol rules already live
4. tighten templates and task language only after the owner split is explicit
5. regenerate `build/monolith.md` and run tests last

## File-By-File Blueprint

### Stage 1: Core Source Of Truth Updates

#### `src/index.md`

- Change type: rewrite plus naming cleanup
- Why this file: it is the framework narrative front door and already contains mixed `Alignment Pack` / `Alignment Substrate` language.
- Required edits:
  - bump version from v9.6 to v9.7
  - replace residual `alignment pack` wording with `alignment substrate`
  - update the alignment core principle so it describes a coordination grammar rather than a doc bundle
  - keep the layer model explicit that `15-alignment/` is optional and pressure-driven
  - fix the section index entry to `Alignment Substrate`
- Watchouts:
  - do not imply that substrate is a new truth layer
  - do not overload the front page with the full seven-field exposition
- Verification target:
  - the front page reads consistently with the rewritten alignment section and no longer contains mixed naming

#### `src/sections/alignment.md`

- Change type: primary rewrite
- Why this file: it is the durable home of the substrate concept.
- Required edits:
  - rename the title to `Alignment Substrate`
  - expand role and admission rule beyond reference drift to include object mismatch, verb-side-effect mismatch, state ambiguity, missing evidence, and poor blast-radius estimation
  - define what alignment owns and explicitly state what it does not own
  - introduce the seven coordination primitives
  - add the three engineering rules:
    - calculable maps over static maps
    - declarative `From -> To` state diff
    - verbs as verification contracts
  - add the stable-anchor rule
  - refer to the request template as the related asset
- Watchouts:
  - invariants, evidence, and runtime truth must be described as referenced inputs, not alignment-owned truths
  - keep the prose compact enough that it remains a section, not a manifesto dump
- Verification target:
  - a reader can tell what substrate is, when to create it, and how it differs from PRD / TDD / tasks / meta-engine

#### `src/sections/meta-engine.md`

- Change type: targeted protocol expansion
- Why this file: reusable execution protocol belongs in meta-engine, not solely in alignment.
- Required edits:
  - keep typed input taxonomy and mode split intact
  - add a rule for when fuzzy intent must be expanded into substrate fields
  - define when a pre-execution Impact Handshake is required, especially before non-local durable mutation or when blast radius is unclear
  - make clear that missing evidence blocks handshake and sends the work back toward diagnosis
- Watchouts:
  - do not turn the dispatcher contract into a mandatory seven-field template for every task
  - do not blur mode choice with durable ownership
- Verification target:
  - a reader knows where the handshake pause belongs and when it triggers

#### `src/assets/templates/alignment-change-request.template.md`

- Change type: template redesign
- Why this file: the current template reflects the older pack model and is too small for the new coordination grammar.
- Required edits:
  - replace simple target / operation / constraints structure with substrate-oriented sections
  - include fields for:
    - object
    - address
    - operation
    - invariants / boundaries
    - applicable state / context
    - evidence
    - protocol / handshake checkpoint
    - `from`
    - `to`
    - blast radius forecast
    - verification contract
- Watchouts:
  - keep the template concise and operational
  - avoid making it look like all tasks must copy this verbatim
- Verification target:
  - the template can support risky alignment-heavy requests without bloating routine work

#### `src/sections/migration-guidance.md`

- Change type: append new migration step
- Why this file: the release needs an explicit upgrade summary from v9.6 to v9.7.
- Required edits:
  - add `v9.6 -> v9.7`
  - describe the rename from Alignment Pack to Alignment Substrate
  - describe the seven primitives
  - describe calculable maps, declarative diffs, and verification-bound verbs
  - describe the Impact Handshake requirement for risky durable mutations
- Watchouts:
  - keep the migration note concise and action-oriented
- Verification target:
  - a returning reader can understand the release delta in one scan

### Stage 2: Owner-Split Tightening And SOP Cleanup

#### `src/sections/tasks.md`

- Change type: clarification pass
- Why this file: MVT must remain the default entry point, and substrate should be framed as an optional expansion.
- Required edits:
  - keep MVT unchanged as the required minimum
  - add a short rule that substrate fields are loaded when coordination pressure exceeds what MVT can safely express
  - optionally connect existing scaffold fields to substrate concepts without replacing them
- Watchouts:
  - do not make the section read as if every task needs substrate completeness
- Verification target:
  - MVT remains small, but the path to richer coordination is explicit

#### `src/sections/promotion-rules.md`

- Change type: naming plus ownership precision
- Why this file: current destination language still says `Alignment pack`.
- Required edits:
  - rename the destination to `Alignment Substrate`
  - clarify that ambiguous targeting and coordination grammar live there
  - avoid wording that suggests evidence or reusable execution protocol are alignment-owned by default
- Watchouts:
  - keep durable destination rules crisp
- Verification target:
  - the promotion map no longer blurs alignment with tasks or meta-engine

#### `src/assets/mappings/durable-destination-map.md`

- Change type: naming plus route precision
- Why this file: it is the shortest owner map and should reflect the same split as the rest of v9.7.
- Required edits:
  - rename `Alignment` notes from pack-style wording to substrate-style wording
  - keep ambiguous targeting in alignment
  - keep reusable workflows, route protocols, and ontology rules in meta-engine
- Watchouts:
  - do not overload the compact table with the full theory
- Verification target:
  - the map stays terse but no longer points readers to the wrong conceptual owner

#### `src/sections/ontology.md`

- Change type: minimal concept-loading clarification
- Why this file: substrate introduces additional meta vocabulary, but SVC still wants progressive loading.
- Required edits:
  - add a brief note that substrate concepts are on-demand coordination concepts, not part of the always-loaded root cheat sheet
- Watchouts:
  - do not expand the ontology section into a second alignment section
- Verification target:
  - the loading rule remains small and context-efficient

#### `src/assets/templates/mode-c-execute.template.md`

- Change type: optional execution SOP tightening
- Why this file: execute mode is the most natural place for a short pre-mutation handshake reminder if the meta-engine wording alone feels too abstract.
- Required edits:
  - add a concise reminder to restate exact change, protected invariants, and verification before risky execution
  - if needed, point to the handshake as the pause format for non-local mutation
- Watchouts:
  - keep the template short; the main protocol still belongs in meta-engine
- Verification target:
  - execute mode better reflects substrate discipline without duplicating the full alignment section

#### `src/assets/templates/AGENTS.root.template.md`

- Change type: optional root-template consistency pass
- Why this file: if v9.7 shifts core phrasing around alignment and handshake discipline, the root template should not contradict it.
- Required edits:
  - keep root AGENTS minimal
  - adjust only the smallest wording necessary so the template stays consistent with v9.7 naming and ownership
- Watchouts:
  - do not stuff substrate terminology into the always-loaded cheat sheet
- Verification target:
  - generated or copied root AGENTS files still stay light

#### `src/sections/filesystem.md`, `src/sections/unit-tdd.md`, `src/sections/deployment.md`

- Change type: version wording cleanup only
- Why these files: they contain explicit `v9.6` release text that will otherwise lag behind the new release number.
- Required edits:
  - update release-number references where appropriate
  - keep substance unchanged unless another Stage 1 or Stage 2 edit truly requires it
- Watchouts:
  - do not introduce unnecessary content changes just because the version string is old
- Verification target:
  - release references across the section set are consistent with v9.7

## Build And Verification Pass

After source edits are complete:

1. run `pdm run build-monolith`
2. inspect `build/monolith.md` for naming and owner-split consistency
3. run `pdm run test`
4. confirm no generated wording reintroduces `Alignment Pack` or source/build drift

## Suggested Edit Order

1. `src/index.md`
2. `src/sections/alignment.md`
3. `src/sections/meta-engine.md`
4. `src/assets/templates/alignment-change-request.template.md`
5. `src/sections/migration-guidance.md`
6. Stage 2 consistency files
7. build and test
