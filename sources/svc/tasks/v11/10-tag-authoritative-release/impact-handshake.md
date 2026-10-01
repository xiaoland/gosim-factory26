# Per-slice Impact Handshakes

These handshakes bound later work; they do not authorize implementation or
external mutation. Each slice still requires Sir's explicit start. New evidence
that changes an address, state diff, external boundary, or irreversible action
returns to discussion first.

## Shared Invariants

1. Published v11.0.0 tag, PyPI files, GitHub Release, and assets remain
   unchanged; platform immutability is not claimed retroactively.
2. `main` remains the only integration and release source.
3. GitHub Release publication remains the completion checkpoint after exact
   PyPI files exist.
4. Final distributions are built once, installed/smoked exactly, hashed, and
   retained as a named artifact before PyPI mutation.
5. The protected tag is the sole release approval; no later human gate can
   abandon an already reserved version.
6. One repository-wide non-canceling writer serializes every normal/recovery
   run, and an exact-complete predecessor is required before candidate build.
7. Recovery after any PyPI file or GitHub draft exists never rebuilds or reads
   newer `main`; while state is incomplete, an expired, deleted, or missing
   original bundle blocks automatic recovery. An exact-complete immutable
   Release remains independently verifiable.
8. Exact external subsets may be completed only from the original bundle;
   PyPI is read back all-exact before GitHub; mismatches and ambiguity fail
   closed.
9. Behavioral SemVer and MAJOR migration guidance remain enforced.
10. Workflow tokens remain least-privilege and third-party Actions remain
   commit-pinned.
11. Published target-model GitHub Releases are immutable.
12. Agent-observability runtime behavior, consumer schemas, and unrelated
   working-tree changes remain untouched.

## Slice 1 — Dark Release Model

### Address and Object

- `tools/release.py`: new tag-range planning, fragment/migration validation,
  deterministic notes, and external-state classification operations;
- `tests/test_release.py`: hermetic histories and bundle/state fixtures.

### State Diff

From current-tree fragments and prepared-source validation only → additive
pure operations for the target tag-authoritative model, with current
production command behavior unchanged.

### Blast Radius

Local release-tool imports and tests only. No workflow calls a new operation;
no package metadata, catalog, source document, dependency, tag, or remote state
changes.

### Verification

REL-001 through REL-009, REL-019, and the pure portions of REL-024 through
REL-029 pass in fixture repositories. Existing release and workflow tests
remain green.

## Slice 2 — Stable Admission Interface

### Address and Object

- `.github/workflows/ci.yml`: stable job/check names, PR/main trigger parity,
  and required fetch depth;
- `tests/test_workflows.py`: check-name and trusted-source contracts;
- task-local evidence: proposed repository-control payloads and read-only
  validation.

### State Diff

From incidental job names and advisory CI → stable trusted check identities
that can safely be required before the semantic cutover.

### Blast Radius

GitHub check labels and merge UI change. Test/build behavior remains on the
current prepared-source contract. No repository control is activated.

### Verification

Every proposed required check runs on a PR and on `main`, succeeds on the
default branch, and is reported by the GitHub Actions app. The proposed rule
payload references no absent or matrix-ambiguous check.

## Slice 3 — Admission and Publication Controls

### Address and Object

- GitHub `main` branch rule/ruleset;
- GitHub `v*` tag rule/ruleset;
- GitHub `release` environment deployment policy;
- GitHub repository release-immutability setting;
- task-local request/readback evidence.

No tracked repository file is the external-state authority.

### State Diff

From advisory CI, direct-push-capable `main`, and movable release tags → PR-only
admission with required checks, no force-push/deletion, explicit narrow bypass,
protected tag update/deletion with authorized creation retained, a `v*`-only
publisher environment, and immutable future GitHub Releases.

### Blast Radius

Merge availability, emergency/bot paths, tag administration, publisher tag
eligibility, and repository operator access change immediately. A wrong check
name can lock `main`; a wrong environment tag pattern can block publication.

### Verification

REL-030 through REL-037 pass through API readback and deployment evidence. A
deliberately failing probe PR remains blocked without merge. No destructive
branch/tag probe is used.

This slice requires a fresh explicit external-mutation approval.

## Slice 4 — Atomic Hard Cut

### Address and Object

Build and version projection:

- `pyproject.toml`, `pdm.lock`, `pdm_build.py`;
- `tools/build_catalog.py`;
- `svc_cli/resources.py`;
- `src/manifest.json` (deletion).

Release logic and automation:

- `tools/release.py`;
- `.github/workflows/ci.yml`;
- `.github/workflows/publish.yml`;
- `.github/workflows/release-pr.yml` (deletion);
- `.github/workflows/release-tag.yml` (deletion).

Durable contributor/runtime truth:

- `AGENTS.md`, `README.md`, `CONTRIBUTING.md`;
- `src/index.md`;
- `CHANGELOG.md`.

Verification owners:

- `tests/test_release.py`;
- `tests/test_catalog.py`;
- `tests/test_workflows.py`;
- resource/project tests only if exact source-mode behavior requires their
  assertions to change.

`src/migrations/` gains files only when a future MAJOR fragment requires one;
the cutover itself does not invent migration guidance.

### State Diff

From:

- duplicated static future version and prepared release metadata;
- mutable/current-tree fragments consumed into CHANGELOG;
- release PR, automatic tag, and compensating dispatch;
- release bytes retained only by an expiring run artifact;
- separate advisory CI and prepared-source publication qualification.

To:

- tag-derived dynamic metadata and build-directory catalog projection;
- append-only tag-range fragments and same-slug MAJOR migration notes;
- frozen historical CHANGELOG and generated future GitHub Release notes;
- one tag-triggered Publish path with bounded named-bundle retention,
  completed-predecessor enforcement, repository-wide serialization,
  hash-aware exact-subset recovery, post-PyPI readback, and immutable one-call
  GitHub finalization;
- protected PR, exact-main, and tagged-source qualification under the same
  stable checks.

### Blast Radius

- editable/source-mode and built package version reporting;
- wheel, sdist, catalog, source fallback, and lock/build behavior;
- contributor fragment and MAJOR migration conventions;
- release commands and notes;
- CI required checks without renaming them;
- Actions permissions and artifact retention, publisher tag restriction,
  Trusted Publishing, exact-subset recovery, release immutability, and
  finalization.

No consumer configuration schema, agent-observability behavior, or published
release changes.

### Verification

REL-001 through REL-029 pass locally/workflow-statically; required PR checks
pass on the protected cutover PR; exact-main checks pass after merge. The merge
creates no tag, draft, PyPI file, or published Release. Source status and
tracked hashes remain clean after rehearsal.

This slice requires explicit implementation approval after review of this
handshake.

## Slice 5 — Acceptance and First Release

### Address and Object

- read-only local/GitHub verification surfaces;
- one separately authorized new strict `vX.Y.Z` tag on a named green `main`
  commit;
- the resulting Publish run, immutable GitHub Release, and PyPI version.

### State Diff

From verified but unexercised target topology → one completed real release and
recorded recovery proof.

### Blast Radius

The tag, uploaded PyPI files, and published GitHub Release are irreversible.

### Verification

The full [`verification.md`](verification.md) matrix passes and records exact
tag, commit, run, bundle, wheel/sdist, PyPI, and GitHub hashes/state.

This slice always requires separate release authorization; implementation
approval does not imply it.
