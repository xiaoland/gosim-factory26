# Source Landing Content, Migration, and Review

> **Historical/non-normative**: retain this dossier only for semantic content
> and counterexample evidence. Do not implement its paths, template
> disposition, mutation set, or review proposition; use
> [`design/88`](88-p2-review-and-realization-outline.md).

- **State**: superseded as the integrated landing by
  [`design/85`](85-browse-first-layout-and-task-cli.md); retained for exact
  content contracts and counterexamples that the correction reuses
- **Consumer**: five `P2` Cells, then the source-mutation Impact Handshake
- **Basis**: [`design/83`](83-source-landing-layout-and-writing.md) and accepted
  `D-013..D-090`
- **Boundary**: this file selects a proposed source diff; it neither authorizes
  nor performs that diff

## Exact Source Contracts

| Address | Load when | Owns | Initial internal structure | Does not own |
| --- | --- | --- | --- | --- |
| `sections/working-protocol.md` | every non-trivial Agent task | obligation→return, method↔feedback, action→effect authority, observation→integration/disposition; Human decision/attention seam; honest close | purpose/topology; current truth and owner; next return; Task Packet write-back; effect gate; integration/close; progressive routes | detailed methods, packet filesystem, profiles, proof techniques, taste, corpus prose style |
| `sections/working-methods.md` | the next useful return needs non-obvious problem-solving guidance | stateless/non-ritual use, composition, bounded-incomplete honesty, three method bootstraps and depth routes | common contract; Explore/Design/Implementation comparison; composition/return rules; links | work lifecycle, role selection, verification, Human telemetry |
| `sections/working-methods/explore.md` | key information is non-obvious or evidence is complex/ambiguous | Frame, composed Route, embedded Model/Generate/Discriminate logic, adequacy × continuation value, bounded-incomplete report | purpose/use; Frame; adaptive evidence route; specialist jobs; enough/continue judgment; anti-patterns; Agent task-analysis use case | Explorer delegation contract, generic repository tool catalog, acceptance |
| `sections/working-methods/design.md` | a coherent product/technical arrangement must be proposed under material forces | typed forces↔solution↔representative consequences; Product/Technical/Test projections; horizon-relative adequacy; use-case/taste routing | purpose/use; primitive loop; three projections; consequence/review carriers; progressive taste link; residual | implementation Plan, project truth, verifier execution, universal taste |
| `sections/working-methods/implementation.md` | a bounded intended change must become real through feedback | realization-feedback loop, accepted horizon/effect boundary, method-local observation and revision | purpose/use; prerequisites/bounds; realize→observe→adjust/revisit; local feedback versus qualification; return/residual | implementation Slice ownership, Executor profile, acceptance, claim qualification |
| `sections/task-packet.md` | a non-trivial Task needs a packet or current shape no longer supports control/recovery | universal Human entry, planning vocabulary, work topology, information modules, growth/retirement, write-back projections | purpose; `packet.md`; Task/Track/Phase/Cell/Plan/Slice/Step/Assignment; Shapes 0–3; Inquiry/Design/Decision/Verification modules; growth/retirement; templates | live task truth, Working Methods, implementation/acceptance/RT modules, runtime scheduler |
| `sections/sub-agents.md` | delegated placement may beat direct work | lever-specific economics, Primary/Child authority and context, Assignment sizing, consumer-relative result routes, Explorer/Executor contracts | direct alternative/admission; authority/context; Explorer; Executor; failure/escalation; non-goals | Working Method logic, validator persona, fixed pipeline, universal envelope |
| `sections/verification.md` | a material Product/Technical claim needs qualification or proof composition is non-obvious | claim→surface/oracle→evidence/TCB/residual→consumer disposition; mechanism choice; modular qualification; correlated AI evidence | purpose/topology; responsibility seams; smallest credible mechanism; TCB; module reuse/requalification; distributed placement; failure boundaries | expected claims, Test Design as requirement source, mechanism implementation, acceptance authority, task-wide test ledger |
| `sections/implementation-taste.md` | Technical Design/Implementation faces non-trivial structure or change-cost judgment | use-case-routed implementation consequence knowledge | authority/provenance pressure; semantic/naming pressure; dependency/obscurity and deep-module pressure; data/boundary pressure; propagation/change scenarios; complexity return; code projection | Product/UI taste, project truth, universal architecture, Design method |

`src/index.md` remains the product/corpus entry. Its early navigation names the
Agent work guidance addresses above, while its existing Knowledge Owners table
continues to mean Consumer project truth destinations. It does not copy the
operational contracts.

## Maintainer Authoring Contract

Add a compact `Author the Corpus` section to `CONTRIBUTING.md`, distilled from
[`design/36`](36-corpus-writing-standard-draft.md) and `design/83`:

- scope and semantic-owner rule;
- direct/stable language and semantic compression;
- progressive disclosure and SVC concept budget;
- representation-by-relation table;
- negative-boundary, uncertainty, and authority discipline;
- proportionate review and mechanical-verification boundary.

Root `AGENTS.md` names this section as the owner and requires it before a
material `src/` content edit. Do not add another source template, linter,
controlled dictionary, required front matter, or dedicated authoring file in
the first landing.

## Selected Task Packet Path Disposition

The P2 proposal deliberately selects one clean transition rather than a
permanent compatibility shadow:

1. make `sections/task-packet.md` the canonical guidance path and remove the
   currently uncommitted `sections/task-packet-growth.md` candidate;
2. move the existing packet template to
   `assets/templates/task-packet/packet.template.md` and update its deterministic
   CLI carrier;
3. remove `assets/templates/task-diagnostics-matrix.template.md` rather than
   preserving an alternate whole-Task type or inventing an unproved Inquiry
   template;
4. ship only `packet.template.md` in the Task Packet template family initially.

The packet and diagnostics template paths have existed in prior packaged
catalogs, so their removal is a Behavioral SemVer **major** change unless
release evidence proves those paths were not supported. The current
growth-guide path and CLI command are uncommitted, so they should be corrected
before release rather than supported as legacy.
No alias file is proposed: it would either duplicate the template authority or
stop behaving as the path's previous template contract.

This transition earns the cost because the path itself currently teaches
“packet equals one file,” while the accepted product model makes the family
boundary a Human/Agent mental-model concern rather than cosmetic
future-proofing. Diagnostics retirement removes a competing whole-Task shape;
it does not justify pre-creating an Inquiry template.

## Existing Narrow Contract Moves

- Move the canonical Agent Task Analysis method section from universal Working
  Protocol into `working-methods/explore.md`. Update the analysis schema's
  packaged method path/section reference and its focused tests; this
  machine-exposed path change joins the template changes in the declared major
  Corpus transition. The method ID remains stable unless the eventual wording
  changes its meaning. The CLI still provides deterministic evidence
  navigation, not semantic analysis.
- Update the two Agent-analysis migration guides and PRD/Deployment references
  to the new method address where they name it. Preserve the method ID unless
  its semantics materially change beyond the accepted Explore correction.
- Revise `assets/templates/AGENTS.root.template.md`: installed SVC method/taste
  guidance is reached through `svc lookup`, not Consumer-owned
  `docs/00-meta/working-protocol.md` or `implementation-taste.md`. Consumer
  Product/Technical/Deployment owners remain project-local.
- Update current Task Packet CLI constants and tests only to carry the selected
  canonical guide/template paths. Add no task graph, semantic grow engine,
  Agent orchestrator, verifier, or writing linter.

## Current-to-target Content Moves

| Current content | Disposition |
| --- | --- |
| WP `Interpret the Request` | compress into typed task meaning/authority in the kernel; request labels do not select a workflow |
| WP `Resolve the Owner` | retain as universal semantic-owner/integration law |
| WP `Agent Task Analysis` | move behind Explore as the existing narrow specialist use case; update machine reference |
| WP `Choose the Working Posture` | replace with a link and three return-oriented Working Method bootstraps |
| WP `Keep a Task Control Surface` | keep only read/write-back seam; move packet shape/content into `task-packet.md` |
| WP `Load and Search Progressively` | retain universal loading law; move Explore-specific search/evidence behavior |
| WP `Mutation Gate` | retain typed effect authority and proportional Impact Handshake |
| WP `Execute and Verify` | split into Implementation and Verification routes while retaining universal effect/integration rule |
| WP `Documentation Quality` | keep one-owner/no-duplication law; move `src/` authoring rules to `CONTRIBUTING.md` |
| current `task-packet-growth.md` | replace with the complete compact Task Packet guidance owner |
| current Implementation Taste | preserve useful claims, reorganize by recurring Technical Design pressure, add counter-pressure/observable consequences where they change choice |

## Counterexample Review

| Case | Expected route | Failure prevented |
| --- | --- | --- |
| rename one local variable with clear test | WP entry is sufficient; no method/capability depth required | ceremony and irrelevant context |
| ambiguous bug across two repos | WP → Explore; Task Packet topology only if the work acquires multiple real owners/barriers | fixed pipeline or premature packet tree |
| compare two payment interaction designs | WP → Design Product projection → relevant UI carrier/Human taste; Test Design challenges owned claims | implementation taste or tests inventing product expectation |
| bounded codemod with compiler and focused tests | WP → Implementation; delegate to Executor only if placement economics win; compiler/test qualify the candidate | Reviewer persona or Primary evidence relay |
| explore an unfamiliar architecture | Explorer may return a question-shaped semantic report; no generic delegated validator | “Child completed work” verdict replacing the needed answer |
| reuse a qualified button component | Verification checks consumer connection/assumptions and new composition behavior, not every internal guarantee | duplicate low-value AI tests |
| corpus wording edit | root Agent reads CONTRIBUTING authoring section; semantic owner still determines the claim | WP becoming a prose-style umbrella or packaged maintainer rules |

These cases support the initial file boundaries. They do not prove real-task
outcome gains and do not justify more files.

## Proposed Mutation Set

The later Impact Handshake should cover one coherent source-first batch:

- **add**: `working-methods.md`, its three method files, `task-packet.md`,
  `sub-agents.md`, and `verification.md`;
- **rewrite/refine**: `working-protocol.md`, `implementation-taste.md`,
  `index.md`, root `AGENTS.md`, `CONTRIBUTING.md`, affected consumer template
  and narrow product/migration references;
- **move/remove**: the packet template path, diagnostics template, and current
  task-packet-growth candidate;
- **project mechanically**: Task Packet and Agent-analysis path constants,
  focused tests, catalog/wheel/monolith output, and release-impact evidence.

The exact file list must be resolved against the dirty worktree immediately
before the Impact Handshake. Existing Task Packet/CLI edits are not disposable;
the implementation must adapt them rather than overwrite them.

## Verification Plan

1. `pdm run check-documents`
2. `pdm run build-monolith`
3. focused Task Packet and Agent-analysis tests
4. `pdm run test`
5. `pdm build -p svc_cli`
6. install/read smoke checks for every new packaged path plus `svc task init`
   and `svc task grow`
7. content review against the seven counterexamples and the writing contract

Only steps 1–6 are substantially deterministic. Step 7 is the semantic review
that verifies routing/owner claims at source-landing depth; representative real
tasks remain the later outcome horizon.

## Review Proposition

Accept this P2 landing if:

1. `working-protocol.md` can remain the single cheap entry without owning the
   methods and capabilities it routes to;
2. the one `working-methods.md + working-methods/` depth is easier to discover
   than either one new methods monolith or many flat peer files;
3. Task Packet gets one canonical guidance owner and one universal template,
   with the old flat template path intentionally paid as a major transition;
4. corpus-authoring rules begin in the maintainer surface rather than the
   packaged Consumer corpus; and
5. the proposal adds no speculative profile, verifier, UI/UX, Architecture,
   assurance, authoring, or template taxonomy.
