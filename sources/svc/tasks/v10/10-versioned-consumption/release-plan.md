# Distribution and Release Plan

> Status: the release topology remains useful, but its package-rename and consumer-migration references are superseded by the embedded-runtime design in [`../20-embedded-runtime-cli/packet.md`](../20-embedded-runtime-cli/packet.md). Use root `svc_cli/`, root `tools/`, and the current release tests as implementation authority.

## Approved Topology

```text
feature PR + Towncrier fragment
    -> pull-request CI
    -> merge to main
    -> automated Release PR
    -> human review and merge
    -> protected publish workflow
    -> build once + attest
    -> draft GitHub Release + exact assets
    -> PyPI Trusted Publishing
    -> publish immutable GitHub Release
```

Artifact roles:

- Git tag and GitHub Release: canonical release identity and human release record
- GitHub Release assets: exact wheel, sdist, release manifest, and `SHA256SUMS`
- PyPI: pip/pipx/uv-compatible installation projection of the exact built wheel and sdist
- GitHub Actions artifacts: temporary job handoff only, never a release destination
- GHCR: deferred until a real container or OCI consumer exists

## Phase 1: Rename the Python Package

Move `src/svc/` to `src/svc_cli/` and update:

- console entry point to `svc_cli.cli:main`
- PDM build includes and build-hook wheel projection
- imports, tests, mocks, documentation, task evidence, and wheel assertions
- package-resource lookup so canonical payload projection remains source-first

Keep these names independent:

- distribution: `sustainable-vibe-coding`
- import package: `svc_cli`
- executable: `svc`

Acceptance: the wheel contains `svc_cli/`, exposes `svc`, contains the same canonical payloads, and passes the complete existing fixture matrix.

## Phase 2: Contribution and Change-Fragment Protocol

Add root `CONTRIBUTING.md` as the contributor entry point. It owns:

- environment setup and existing verification commands
- commit-message grammar: `feat|fix|ref|docs|chore(<scope>): <summary>`
- concise imperative summary and optional body bullets for expensive context
- examples of acceptable and rejected messages
- the rule that commit type does not determine release impact
- when a Towncrier fragment is required and how to create/check one
- how MAJOR changes declare migration impact
- the Release PR and publication boundary

Configure Towncrier with Markdown fragments under `changes/`:

```text
changes/<issue-or-pr>.major.md
changes/<issue-or-pr>.minor.md
changes/<issue-or-pr>.patch.md
```

Semantics:

- `major`: required obligation/default/authority/task/layout/stable-machine-contract change or supported-capability removal
- `minor`: optional backward-compatible capability or accepted-input expansion
- `patch`: clarification or restoration of the existing declared protocol
- contributor-internal work may omit a fragment only through an explicit `release:none` PR decision

Towncrier renders release notes; a small repository-owned release planner calculates the maximum fragment impact, validates Behavioral SemVer, synchronizes release metadata, and enforces migration requirements. Conventional commit parsing and Towncrier text alone are not version authority.

Acceptance: local checks reject missing/unknown fragment types, invalid filenames, empty fragments, incompatible version bumps, and MAJOR releases without a registered migration or explicit reviewed non-applicability reason.

## Phase 3: Pull-Request CI

Add `.github/workflows/ci.yml` with least-privilege `contents: read` permissions and pinned action revisions.

Required jobs:

- supported-Python test matrix, including the minimum and current stable runtime
- manifest, migration graph, Behavioral SemVer, links, and Towncrier checks
- monolith build
- sdist/wheel build
- clean-environment wheel install
- installed-wheel `svc init`, `status`, and prepared v9.8 migration smoke tests

Upload the built distribution only as a temporary workflow artifact. CI never tags or publishes.

## Phase 4: Changesets-style Release PR

Add `.github/workflows/release-pr.yml`, triggered after changes reach `main`.

The repository-owned release planner must:

1. collect unconsumed Towncrier fragments
2. calculate the maximum Behavioral SemVer impact
3. calculate the next version from the last canonical release
4. render the proposed Changelog section
5. update `pyproject.toml`, `src/manifest.json`, and `pdm.lock`
6. validate release-manifest reasons and migration graph obligations
7. consume only fragments included in the Release PR
8. create or update one `Release vX.Y.Z` PR

Use the built-in, short-lived `GITHUB_TOKEN` with only `contents: write` and `pull-requests: write` in the Release PR job; avoid long-lived PATs. A maintainer must enable the repository Actions setting that permits token-created pull requests and approve the generated PR workflows before review and merge. This approval is an intentional human release gate, not a temporary workaround.

The Release PR is the human checkpoint for version, migration, generated notes, and exact state diff. Merging it authorizes preparation, not external publication.

## Phase 5: Protected Publication

Add `.github/workflows/publish.yml`. It runs only when `main` contains a release version newer than the latest canonical tag and then waits on a protected `release` environment.

Before external mutation it must:

- verify a clean release state with no unconsumed included fragments
- verify version agreement across tag proposal, package metadata, release manifest, migration graph, and Changelog
- rerun tests and wheel-install smoke tests
- build wheel and sdist exactly once
- generate `SHA256SUMS`
- generate GitHub artifact attestations for the release artifacts

Publication sequence:

1. create the immutable version tag and a draft GitHub Release
2. upload the exact wheel, sdist, release manifest, and checksums
3. publish the same wheel and sdist to PyPI through OIDC Trusted Publishing
4. publish the GitHub Release only after PyPI succeeds

Retries must detect existing tag, draft release, assets, and PyPI files and either prove equality or stop. They must never overwrite an artifact with different bytes.

## External Prerequisites

These are not repository-file implementation and require separate authority:

- reserve/configure the `sustainable-vibe-coding` PyPI project
- configure PyPI Trusted Publisher for `xiaoland/svc` and `publish.yml`
- create and protect the GitHub `release` environment with required reviewer policy
- enable the repository Actions setting that permits GitHub Actions to create pull requests, and have a maintainer approve generated Release PR workflows
- configure branch protection and required CI checks
- enable immutable GitHub Releases when available for the repository

## Deliberate Non-goals

- no npm/package.json/Changesets runtime solely for release orchestration
- no commit-message-derived version bump
- no GHCR container or generic OCI wheel bundle
- no moving `v10` major tag
- no automatic downgrade generation
- no publication from pull-request or unreviewed branch contexts

## Execution Slices

1. Package rename with existing tests unchanged semantically.
2. `CONTRIBUTING.md`, Towncrier configuration/fragments, and local release planner.
3. CI workflow and local workflow-contract tests.
4. Release PR workflow and dry-run repository tests.
5. Publish workflow plus mocked/dry-run release verification.
6. Separate human-authorized GitHub/PyPI environment setup and first release.

Each slice receives its own Impact Handshake and verification evidence. Stop if a slice changes the approved distribution topology, version authority, permission model, or external side-effect boundary.
