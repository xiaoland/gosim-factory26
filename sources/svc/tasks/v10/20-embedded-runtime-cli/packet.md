# Embedded Runtime CLI

- **Objective**: Reframe unreleased SVC v10 as a packaged, on-demand SVC corpus plus a small project-local runtime CLI. Replace copied SVC-managed documents and their migration machinery with extensible path-regex/name and keyword `svc lookup`; minimal `svc.json` project metadata; an installed Codex skill; explicit navigation anchors; self-update; and a focused software-development/human-collaboration busybox.
- **Guardrails**:
  - The canonical SVC source remains under `src/`; packaged content is a read-only release projection, never a second authoring surface.
  - `src/` contains only canonical SVC core content and metadata. Python runtime code lives in root `svc_cli/`; build and reference tooling lives in root `tools/`.
  - Consumer-owned material remains consumer-owned. `init` may propose or apply narrowly declared edits, but never silently overwrite an existing `AGENTS.md`, `docs/index.md`, skill, task packet, or project truth. Its locally generated skill and navigation blocks carry self-verifying provenance markers rather than a central consumer-state file.
  - `svc.json` records the project's adopted SVC baseline; the installed distribution version remains package-manager authority. Updating the CLI and adopting new SVC guidance are distinct actions.
  - `lookup --name` resolves paths from the packaged catalog, never document IDs. Keyword lookup is local and read-only. Its internal query/result boundary leaves room for a later semantic backend, but semantic lookup is not a first-slice public CLI contract.
  - Thread export is local, consentful, and redaction-aware; no telemetry or upload is implied.
  - A busybox command needs a distinct owner, trigger, input/output contract, failure semantics, and verification path. Do not create a generic plugin framework before stable variation exists.
  - No automatic discovery of project commands, agent locations, package managers, or remote embedding providers may become an unreviewable authority boundary.
  - This pivot happens before the first v10 publication. It may replace the unreleased v10 contract without a consumer migration, but must remove every obsolete claim and test in the same implementation slice.
  - Do not use sub-agents for this task, per the user's explicit instruction.
- **Verification**:
  - A clean installed wheel can look up SVC content by stable path name and deterministic keyword search without writing to the consumer repository or contacting a network service.
  - `svc init` produces an inspectable plan and, when explicitly applied, creates only `svc.json`, a selected-provider skill, and non-destructive guidance anchors; repeated execution is idempotent.
  - `svc status` distinguishes installed CLI version from project-adopted SVC version and reports missing, drifted, or user-modified generated guidance without claiming authority over consumer content.
  - Lookup query/result contracts are tested independently from ranking implementations, proving a later semantic backend can be added without changing path-regex/keyword callers or machine output.
  - Each admitted utility command has fixture tests for success, precondition failure, idempotence, and zero unintended writes; process helpers prove they do not duplicate a healthy dev server.
  - The release payload, docs, manifests, migration logic, contribution protocol, and workflows contain no stale claim that SVC-managed documents are copied into consumer repositories.
- **Current Truth**:
  - Commit `986ef6a`'s unreleased copy-and-migrate model has been replaced before v10 publication. The current runtime has no SVC-managed downstream documents, `.svc` installation state, or `svc migrate` command.
  - `src/` is now pure canonical SVC content and release metadata; root `svc_cli/` owns the installed runtime, and root `tools/` owns catalog, monolith, and release tooling.
  - The wheel projects every canonical Markdown document into one read-only corpus plus a deterministic catalog. `svc lookup --name` performs full-path regex lookup; deterministic keyword lookup shares an internal query/result boundary with a future semantic backend.
  - `svc init`, `svc status`, and `svc adopt` implement exact-plan project adoption through `svc.json`, a Codex skill at `.agents/skills/svc/SKILL.md`, and bounded Consumer-owned navigation anchors. Modified generated surfaces block rather than being overwritten. `svc self-update` is a separate, current-interpreter non-editable-pip operation.
  - Local plans revalidate preconditions, stage bytes outside the project, write atomically, verify postconditions, restore ordinary failures, and preserve intervening consumer content rather than overwriting it during a conflicted rollback.
  - Local verification passed with 51 unit/fixture tests, monolith build, Behavioral SemVer release check, clean wheel lookup/init/status/self-update planning, and sdist-to-wheel corpus-payload equivalence.
  - v10.0.0 has a tag and an attested GitHub draft release. The first PyPI attempt correctly failed before publication because no Trusted Publisher existed. Recovery has three explicit states: create from `main` when the tag is absent; rebuild from the tag when the Release is absent; and, for a draft Release, checksum-verify then reuse its immutable, attested assets. The protected Releases API query distinguishes those states; a published Release is the completion checkpoint.
- **Next Step**: Merge the draft-state detection fix, rerun Publish, and verify the PyPI distribution plus the published GitHub Release before closing this packet.

## Supporting Material

- Current evidence: [`current-state.md`](current-state.md)
- Proposed topology and command contracts: [`proposal.md`](proposal.md)
- Decisions and remaining choices: [`open-questions.md`](open-questions.md)
- Static semantic-search research: [`semantic-research.md`](semantic-research.md)
- Planned proof: [`verification.md`](verification.md)
