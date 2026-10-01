# Verification Matrix

## Source and Policy

| ID | Proof | Acceptance |
| --- | --- | --- |
| REL-001 | Tag grammar and identity | Only strict unused `vX.Y.Z` refs that peel to exactly one commit are accepted; lightweight and annotated tags have identical meaning, and annotation/signature metadata grants no authority |
| REL-002 | Main reachability | Branch-only, deleted-history, or mismatched tag commits fail before build |
| REL-003 | Monotonic version | Equal, reused, or regressive versions fail before mutation |
| REL-004 | Exact impact | Tag is the exact next single bump required by the maximum Behavioral SemVer impact since the previous release |
| REL-005 | Release-none eligibility | Under protected admission, a tag window with no new fragments remains publishable at the next patch version and contributes no reason |
| REL-006 | Migration guidance | Every added MAJOR fragment has a same-slug non-empty packaged migration note containing steps or an explicit non-applicability explanation |
| REL-007 | No source preparation | Release rehearsal leaves `git status` and tracked file hashes unchanged |
| REL-008 | Append-only fragments | A post-cutover fragment modification, rename, deletion, or path reuse fails qualification |
| REL-009 | Deterministic notes | The same previous tag, candidate tag, and source tree produce byte-identical release metadata and notes |

## Version and Build Projection

| ID | Proof | Acceptance |
| --- | --- | --- |
| REL-010 | One version authority | Tag, sdist/wheel metadata, installed CLI, catalog, filenames, bundle, and Release title agree |
| REL-011 | Lock discipline | `pdm lock --check` passes and release uses frozen dependency groups |
| REL-012 | Full qualification | Python 3.11/3.14 tests, Ruff, mypy, Import Linter, zizmor, monolith, and release planner pass |
| REL-013 | Exact wheel smoke | Fresh venv installs the produced wheel and exercises `svc --help`, lookup, init, and status |
| REL-014 | Artifact contents | Migration/catalog/resources exist; tasks, tests, native telemetry, and quality dependencies do not enter wheel metadata |
| REL-015 | Immutable promotion | One tag-time producer builds both distributions; every later job and recovery path consumes the same manifest-bound bytes without rebuild, using the current exact-tag control verifier rather than artifact-provided code |
| REL-016 | Build cleanliness | No generated version, notes, metadata, or catalog projection mutates the source checkout |
| REL-017 | Sdist round trip | Building a wheel from the produced sdist without Git or a version override preserves exact release version and catalog identity |
| REL-018 | No legacy authority | No release/build/runtime path reads `src/manifest.json`, a static project version, or CHANGELOG as release eligibility or version input |
| REL-019 | Completed predecessor | Candidate build is blocked unless its immediate prior strict tag is the verified v11.0.0 cutover baseline or an exact-complete target-model release |

## Workflow Topology

| ID | Proof | Acceptance |
| --- | --- | --- |
| REL-020 | Normal trigger and single writer | One `v*` tag push starts Publish automatically; all tags/recoveries share one repository-wide concurrency group with `cancel-in-progress: false` |
| REL-021 | No alternate normal path | No release PR, automatic tag, branch push, or normal-path dispatch can publish |
| REL-022 | Build once | One job creates distributions and every downstream job consumes the same checked bundle |
| REL-023 | Publication order | After any subset upload, bounded PyPI filename/hash readback must reach all-exact before GitHub Release creation |
| REL-024 | Fail-closed finalizer | Normal create enumerates manifest assets and includes `--verify-tag`, exact title/notes, and no `--draft`; readback resolves the remote tag object (not `target_commitish`); only 404/verified exact draft states may mutate |
| REL-025 | Explicit recovery | Dispatch probes before build: empty state may rebuild without a run ID; exact-complete state may verify durable Release assets and succeed; any incomplete PyPI/GitHub state requires the exact prior-run bundle, which a current exact-tag verifier must prove semantically equal to the fresh plan except for its qualification proof |
| REL-026 | No mutable-main dependency | Retry succeeds after later `main` changes using only the tag and preserved bundle |
| REL-027 | Bounded bundle retention and provenance | Upload declares `retention-days: 90`; API readback records ID/`expires_at` and at least an 89-day effective window. Before download, recovery binds the supplied run ID to the Publish workflow path, allowed trigger, planned head SHA, terminal state, and one exact named artifact; expiry, early deletion, run deletion, or provenance mismatch blocks incomplete recovery rather than rebuilding |
| REL-028 | Legacy path extinction | No workflow or release command can prepare source, consume/delete fragments, update CHANGELOG, run Towncrier, create a release PR, or create a tag automatically |
| REL-029 | Hash-aware idempotence | PyPI or draft exact subsets receive only missing original files; PyPI is re-read all-exact; exact published state succeeds; unexpected names, metadata/hash mismatch, published partials, and ambiguity fail closed |

## Repository Enforcement

| ID | Proof | Acceptance |
| --- | --- | --- |
| REL-030 | Protected main | GitHub API reports PR-required admission, required checks, no force-push/deletion, and explicit bypass policy |
| REL-031 | Required checks | Merge is blocked when any trusted qualification check fails or is absent |
| REL-032 | Exact main result | The admitted commit/tree receives the shared qualification result before release |
| REL-033 | Immutable release tags | GitHub API reports matching `v*` tags cannot be updated or deleted |
| REL-034 | Authorized tag creation | The intended maintainer path can create a new tag without granting workflow-wide write authority |
| REL-035 | Publisher identity | `release` environment and PyPI Trusted Publisher bind only the intended repository/workflow/environment, and its sole custom deployment policy is `type: tag, name: v*` |
| REL-036 | Sole approval | The authorized protected tag is the only human release action; the `release` environment has no required reviewer and no path can abandon a tag for a newer release |
| REL-037 | Immutable GitHub Release | Repository release immutability is enabled before cutover, and the completed Release API reports exact assets plus `immutable: true` |

## Planned Proof Owners

| Range | Primary proof owner |
| --- | --- |
| REL-001–REL-009 | `tests/test_release.py` fixture repositories, notes snapshots, and source-cleanliness assertions |
| REL-010–REL-019 | `tests/test_release.py`, `tests/test_catalog.py`, source-resource tests, negative legacy-authority assertions, and the shared distribution/sdist smoke |
| REL-020–REL-029 | `tests/test_workflows.py`, static legacy-path assertions, and hermetic bundle/draft/PyPI state fixtures |
| REL-030–REL-037 | GitHub API readback, `tests/test_workflows.py`, and one blocked probe PR |
| First production tag | Publish run, PyPI JSON, GitHub Release API, and bundle-hash evidence |

Each implementation slice must name the exact tests or external observations
from these owner groups before mutation.

## Hermetic Histories

Fixture repositories cover:

1. one patch fragment;
2. mixed patch/minor fragments;
3. a MAJOR fragment with guide;
4. a MAJOR fragment with explicit non-applicability;
5. one `release:none` commit after a published tag;
6. a fragment modification, rename, deletion, and globally reused path;
7. multiple unreleased commits and an older main ancestor tag;
8. a tag on a branch-only commit;
9. equivalent lightweight, unsigned annotated, and signed annotated tags, plus
   rejection of a tag ref that does not peel to a commit;
10. reused tag, reused version, over/under-bump, malformed tag, and source race;
11. wheel-from-sdist construction without Git or a version override;
12. named-bundle recovery after later `main` changes but before artifact
    expiry;
13. dispatch without a prior-run ID against empty, exact-complete, and
    incomplete PyPI/GitHub states;
14. PyPI none, exact-subset → upload → bounded all-exact readback, all-exact,
    stale readback timeout, unexpected-name, and mismatched-hash states;
15. GitHub absent, exact draft-subset, wrong tag/commit/title/notes with exact
    assets, a benign `target_commitish: main` with an exact remote tag object,
    published-exact, published-partial, mismatched, and ambiguous states;
16. a recovery canary whose later `main` would produce different bytes, proving
    that no build command or source projection runs;
17. expired, early-deleted artifact, and deleted-run states after simulated
    external mutation, proving that recovery blocks rather than rebuilding;
18. two candidate tags and one recovery attempt, proving global
    serialization, completed-predecessor gating (independent of expired
    completed-run artifacts), and non-cancellation.
19. a recovered bundle with an altered `release-check.py`, a mismatched
    workflow path/head SHA, or an uncompleted prior run, proving the current
    control verifier rejects it before any artifact-provided program can run.

## Local Implementation Evidence — 2026-07-29

- `pdm run test`: 226 passed.
- `pdm lock --check`, `pdm run lint-tests`, `pdm run typecheck`,
  `pdm run lint-imports`, `pdm run lint-workflows`, and
  `pdm run build-monolith`: passed.
- `PDM_BUILD_SCM_VERSION=11.0.1 pdm build` produced exactly one wheel and one
  sdist; their core metadata and packaged catalog agreed on `11.0.1`.
- Fresh installed-wheel smoke (`--help`, lookup, init, and status) passed
  locally, on `wsl.win-ws.localhost` with Python 3.13, and on
  `win-ws.localhost` with Python 3.14. Remote temporary test directories were
  removed after verification.

These are local/static proofs only. The authorized GitHub-control mutation and
API readback satisfy REL-030 through REL-037's control portion; the first real
tag result below supplies the Publish/PyPI/Release proof.

## Live Acceptance

Before merge:

- local full matrix passes;
- PR required checks are green;
- a read-only workflow/repository settings audit matches the intended payload.

Before repository-rule mutation:

- exact-main CI passes with stable check names;
- no release workflow or tag is created by the merge;
- the proposed rule payload names only observed checks from the GitHub Actions
  app.

After rule activation but before the hard cut:

- API and environment readback satisfies REL-030 through REL-037;
- a deliberately failing probe PR is blocked without merging;
- the old prepared-source release remains the only production path.

Observed on 2026-07-30: all target contexts completed successfully on bootstrap
main `fa478617f0898cdbcefcf8eef2717fbc7bb7bebb`; the main and tag rulesets,
release environment, and immutable-release setting read back exactly as
specified. Empty probe PR #17 deliberately failed `Release policy` in 14
seconds and was reported `BLOCKED`; it was closed and its remote branch deleted
without merging.

After the Slice 4 cut, the presence or successful invocation of
`release-pr.yml`, `release-tag.yml`, automatic tag creation, or a normal-path
Publish dispatch is a failed acceptance, not a tolerated compatibility path.
The cutover merge itself creates no tag, draft, PyPI file, or Release. No
direct production push or destructive tag probe is performed merely for
testing.

## First-Tag Acceptance — 2026-07-30

The authorized annotated `v11.0.1` tag peels to the qualified hard-cut commit
`1d4028a0bdedcb99c3694dfe9996f6538f9a5364`. Its automatic push run built the
bundle but exposed a real environment-policy defect before any external
publication: the request body omitted `type`, which GitHub interpreted as a
branch policy. Replacing it with the only live `type: tag`, `name: v*` policy
allowed recovery to use the original bundle without rebuilding.

- Recovery run [`30472401002`](https://github.com/xiaoland/svc/actions/runs/30472401002)
  published the exact two-file PyPI set and immutable GitHub Release
  [`v11.0.1`](https://github.com/xiaoland/svc/releases/tag/v11.0.1).
- The PyPI wheel hash is
  `84dd93e1c0956fb1c724cb4a661fc8f8753a285813fbe2fddbccbd91df67d4af`; the
  sdist hash is
  `7c8c916033bd4eba460b4e7ca7f30de16ceef69c953a000cacb254673ddc52b8`.
  API readback confirms the same hashes on PyPI and on the Release assets.
- Original artifact `8732154215` (`svc-release-v11.0.1`) is 403,310 bytes and
  expires `2026-10-27T16:45:09Z`. Both actual Release distributions pass
  GitHub attestation verification; a fresh PyPI install passed `svc --help`
  and the JSON lookup smoke.
- Exact-complete dispatch
  [`30472677788`](https://github.com/xiaoland/svc/actions/runs/30472677788)
  took 20 seconds, accepted the already complete candidate, and skipped
  bundle, PyPI, and Release mutation jobs. This closes the no-bundle
  idempotence path required by REL-025 and REL-029.

The detailed timing, artifact, control, and readback record is
[`v11.0.1-acceptance.md`](v11.0.1-acceptance.md).
