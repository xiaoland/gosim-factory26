# Changelog

This release record is assembled by Changie from versioned release files.
SVC uses Behavioral SemVer: MAJOR changes required obligations, defaults,
authority, task semantics, required layout, or stable machine contracts; MINOR
adds backward-compatible optional capability; PATCH restores or clarifies the
existing protocol without changing those contracts.

## [14.0.0] - 2026-08-17

### Behavioral breaking changes

- Move Agent-thread analysis guidance into CLI help and advance query/read machine responses from v1 to v2 without packaged method references.
- Separate Agent guidance, project specifications, and SVC's own durable project truth while simplifying the top-level Corpus navigation.

## [13.0.0] - 2026-08-16

### Behavioral breaking changes

- Add local Agent-instruction bootstrap and task-packet init/growth guidance, advancing the stable `svc init` result schema.
- Reorganize the SVC Corpus around symmetric capability owners and replace the monolithic Task Packet model with progressive task-local packages.
### Backward-compatible capabilities

- Let lookup path reads use a Corpus concept directory, with or without a trailing slash, while returning its canonical index.md document identity.

## [12.0.0] - 2026-08-16

### Behavioral breaking changes

- Migrate legacy Agent-thread evidence to the schema-v3 native authority.
- Adopt the explicit same-user trust boundary for local Agent evidence.
- Replace the repository-owned tag-range planner and recovery transaction with Changie release-preparation PRs and standard release tooling.
- Replace normalized-only `analyze` and its TUI with schema-v3 native evidence plus machine-first `analysis query|read`.
- Replace normalized Agent-thread analysis with Agent-owned query and native read.
- Flatten project configuration into schema v3 and separate the Corpus baseline.
- Remove obsolete local evidence privacy controls and enforce the narrower same-user runtime boundary.
- Reshape the core CLI around independent upgrade targets, Agent-readable output, shared bounded runs, declared dev lifecycle actions, and discoverable versioned schemas for typed machine output.
### Backward-compatible capabilities

- Add progressive `svc lookup --list`, exact `--path`, bounded relevance `--keyword`, and exact full-text/path `--regex`; make layered CLI help self-sufficient and retire the generated SVC CLI Skill.
- Add `svc run` for one project-declared bounded command, allowing local Human and Agent callers to converge on one foreground execution, follow captured native output, and inspect a compact execution receipt without transferring project-tool semantics into SVC.
- Add `svc double validate|start|emit|observe|stop` for strict, replayable HTTP boundary scenarios with explicit callbacks, carrier-owned active state, and a sealed graceful-stop observation.
- Define the boundary scenario language, Consumer-owned test oracle, explicit callback model, deterministic replay facts, and honest egress non-claims for managed external-system doubles.
### Protocol fixes

- Make `svc status` a read-only project preflight with independent CLI, config, Corpus baseline, integration, workspace, and declaration facts plus one primary continuation; keep settled JSON compact without a false JSONL stream.

## [11.0.1] - 2026-07-30

_No consumer-facing Behavioral SemVer changes._

## [11.0.0] - 2026-07-29

### Behavioral breaking changes

- Replace raw agent-thread export with a bounded normalized trajectory, directly cut off schema-v1 archives, and add deterministic Agent analysis plus an explicitly sensitive Textual workspace/thread navigator. (`v11-agent-observability`)

## [10.0.2] - 2026-07-20

### Protocol fixes

- Restore safe Codex thread metadata listings when unrelated state rows have unsafe rollout paths. (`v10-windows-thread-list-isolation`)

## [10.0.1] - 2026-07-16

### Behavioral breaking changes

- Add the schema-v2 development-runtime protocol, including local configuration overlays, worktree-safe capability coordination, and bounded editor/package setup projections. (`v10-dev-runtime`)

### Backward-compatible capabilities

- Add explicit local `svc telemetry agent-thread list|export` evidence capture with a Codex rollout adapter, sensitive-export acknowledgement, and a provider-neutral extension seam. (`v10-agent-thread`)

## [10.0.0] - 2026-07-15

### Behavioral breaking changes

- Replace copied SVC-managed documents and the consumer-file migration engine with a packaged on-demand corpus, plan-first project adoption, and explicit migration guidance for Consumer-owned material. (`v10`)


### Added

- **Packaged SVC corpus**: the installable `sustainable-vibe-coding` distribution ships the canonical Markdown corpus with a deterministic path catalog and local `svc lookup` command
- **Project adoption**: plan-first `svc init`, `svc status`, and `svc adopt` establish `svc.json`, a Codex operational skill, and bounded navigation anchors without taking ownership of project documentation
- **Self-update boundary**: `svc self-update` plans and applies only a supported current-interpreter pip update, separately from project adoption
- **Codex skill integration**: initialization installs `.agents/skills/svc/SKILL.md`, which teaches command selection and safe use without duplicating SVC guidance

### Changed

- **Consumer contract**: SVC guidance is queried from the installed corpus on demand instead of copied into consumer repositories
- **Repository topology**: `src/` is now canonical SVC content only; `svc_cli/` holds runtime code and `tools/` holds build/release tooling
- **Release metadata**: `src/manifest.json` records corpus version, Behavioral SemVer impact, and migration-guide policy rather than a consumer-file inventory
- **Major-release guidance**: future major releases require a packaged migration guide or explicit non-applicability declaration, while consumers retain the judgment and writes for their own material

### Removed

- **Managed-document installer**: SVC-managed consumer copies, `.svc/state.json`, digest tracking, consumer-file migration graph, and `svc migrate`
- **Ambiguous source layout**: Python runtime and build tools no longer live below canonical `src/`

### Migration

This is the first unreleased v10 release shape. No v10 package, tag, or GitHub Release exists, so there is no published v10 consumer state to migrate. Future published major releases provide lookup migration guidance for Consumer-owned material before `svc adopt` records the new baseline.

## [9.8.0] - 2026-06-07

### Added

- **Agent-owned task workspaces**: task packets are now explicit task-local workspaces for volatile reasoning, exploration, evidence, and human-agent collaboration state
- **Progressive poly-file task packets**: task packets may start as single files and split into directories when collaboration pressure requires separate state, evidence, decisions, verification, or temporary work surfaces
- **Search isolation defaults**: ordinary source and durable-doc search now excludes volatile workspaces, generated output, dependencies, caches, and virtual environments by default
- **Implementation taste**: non-trivial code design and implementation changes now have language- and tech-stack-neutral guidance for SSoT, trust and provenance, durable semantic naming, and complexity ROI

### Changed

- **Task packet semantics**: task packets now preserve a compact human-inspectable control surface instead of behaving like append-only task notes
- **Mode composition semantics**: creative engineering is now explicit as a non-linear loop where design formation, verification preparation, implementation shape, execution, and diagnosis can reshape each other

## [9.5.0] - 2026-04-04

### Added

- **Typed input taxonomy**: every external perturbation is classified as Intent, Constraint, Reality, or Artifact before any durable update or code change
- **Minimal viable task protocol**: non-trivial task packets now require Objective & Hypothesis, Guardrails Touched, and Verification anchors
- **Progressive ontology system**: root AGENTS carries a cheat sheet while `00-meta/concepts.md` becomes the on-demand system dictionary
- **Mode overlay model**: Explore, Solidify, Execute, and Diagnose remain available as reusable SOPs and mind-patterns that can be revisited within the same task

### Changed

- **Dispatcher mental model**: routing now starts from input type and blast radius; Mode Dispatch remains as a secondary SOP layer instead of the sole front-door dispatcher
- **Business vocabulary boundary**: business terms move to `10-prd/glossary.md`, separate from framework ontology
- **Reality workflow hardening**: bug work stays evidence-first and records recurrence tripwires in local `AGENTS.md`
- **Task layer upgrade**: exploration fields are now optional scaffolding rather than mandatory ceremony

## [9.4.0] - 2026-04-04

### Changed

- **PRD restoration baseline**: PRD now follows one-way derivation from `_drivers/` to `behavior/` to `domain-structure/`
- **Claim-centered PRD**: major product claims now require intent, evaluation dimensions, evidence expectation, source rationale, and realization pointers
- **PRD purity boundary**: implementation details are explicitly delegated to Product TDD, Unit TDD, and Deployment layers

## [9.3.0] - 2026-04-04

### Added

- **Pacing Layers**: Isolate architectural structure (slow-moving) from tactical hazards (fast-moving) to maintain clarity across teams and time scales
- **Dispatcher Pattern**: Dynamically load mutually exclusive (MECE) workflows without bloating the context window

### Changed

- **Evidence-first diagnosis**: Strict read-only troubleshooting before any fix attempts

## [9.2.0]

### Added

- **Colocation principle**: How to colocate complexity-dissolving memory as close to the target code as possible to ensure agents automatically consume it

## [9.1.0]

### Added

- **Dynamic navigation framework**: How agents should dynamically navigate ambiguity without falling into rigid waterfall processes or chaotic guesswork

[Unreleased]: https://github.com/xiaoland/svc
[9.8.0]: https://github.com/xiaoland/svc/releases/tag/v9.8.0
[9.5.0]: https://github.com/xiaoland/svc/releases/tag/v9.5.0
[9.4.0]: https://github.com/xiaoland/svc/releases/tag/v9.4.0
[9.3.0]: https://github.com/xiaoland/svc/releases/tag/v9.3.0
[9.2.0]: https://github.com/xiaoland/svc/releases/tag/v9.2.0
[9.1.0]: https://github.com/xiaoland/svc/releases/tag/v9.1.0
[10.0.0]: https://github.com/xiaoland/svc/releases/tag/v10.0.0
[10.0.1]: https://github.com/xiaoland/svc/releases/tag/v10.0.1
[10.0.2]: https://github.com/xiaoland/svc/releases/tag/v10.0.2
[11.0.0]: https://github.com/xiaoland/svc/releases/tag/v11.0.0
[11.0.1]: https://github.com/xiaoland/svc/releases/tag/v11.0.1
