# v10 Tag-bound Release Pipeline

- **Objective**: Replace SVC's branch-derived release and recovery workflow with a deliberately boring, tag-bound PDM package pipeline. When a reviewed `release/svc` candidate merges, its exact merge commit receives one `vX.Y.Z` tag. That tag owns one rerunnable release path: frozen PDM validation → build once → install and smoke-test the exact wheel → preserve one artifact bundle → PyPI → published GitHub Release. Later changes on `main` must not affect that release or its retry.
- **Guardrails**:
  - This task is about functional release reliability, operability, and repeatability. Branch protection, credential policy, and Actions supply-chain hardening are not its subject.
  - Preserve the existing Behavioral SemVer review and release-candidate PR. A published GitHub Release remains the product's completion checkpoint, but a draft GitHub Release must no longer be the durable recovery state for a PyPI publish.
  - A release tag is an immutable handoff, not an observation made later from `main`. Tag creation must bind the version to the exact reviewed merge commit and be idempotent only when both already agree.
  - The top-level `Publish` workflow runs on `v*` tag pushes or an explicit-tag dispatch. Because a `GITHUB_TOKEN` tag push does not start a second run, candidate-merge tagging dispatches that top-level workflow with the resolved tag. Its manual recovery path requires the same explicit tag and never defaults to the current branch tip.
  - Keep the PDM foundation deterministic: use the pinned PDM version, make `pdm.lock` freshness an explicit gate, then install the release group without changing the lock before validation or build.
  - One build job is the only producer of release distributions. It writes a manifest containing tag, resolved commit, package version, filenames, and SHA-256 values; downstream jobs consume that uploaded bundle and never rebuild it.
  - Retrying a tag is narrow and explicit: if PyPI has none of the expected files, upload the bundle; if it has all matching files, continue to finalization; if files are partial or any hash differs, stop with a diagnosis. Do not mask duplicates with `skip-existing`.
  - GitHub Release finalization occurs only after PyPI has every expected file. It must attach or verify the manifest-bound assets idempotently, without creating a second release lifecycle or relying on an old draft's self-checksum.
  - Do not mutate source, workflows, tags, releases, or PyPI under this packet until an Impact Handshake names the exact files, migration sequence, and verification evidence.
- **Verification**:
  - A hermetic candidate-to-tag test proves that a prepared release commit stays the target even if a later `main` commit adds a new `changes/` fragment. It also rejects a tag/version/commit disagreement.
  - The tag release rehearsal runs `pdm lock --check`, frozen release-group installation, `release verify-tag` (which verifies the prepared release), `pdm run test`, `pdm run build-monolith`, `pdm build`, and an isolated installation of the produced wheel that exercises `svc --help` and packaged-resource lookup.
  - The build job emits a checked manifest and uploads the wheel, sdist, release metadata, notes, and checksums as one artifact bundle. Tests assert that the PyPI job receives only this bundle and does not check out source or invoke a build; the GitHub finalizer may check out only the exact release tag to establish repository context for `gh`, but it must not rebuild or source release data from that checkout.
  - Fixture-backed release tests cover a tag that remains pinned despite later `main` changes, tag/version/commit disagreement, bundle tampering, no PyPI files, all matching files after a retry, one-or-more missing files, and hash mismatch. Workflow contracts cover GitHub Release title, notes, asset, draft, and publication ordering; every ambiguous external state stops before a mutation.
  - Workflow contracts assert tag-only automatic triggering, mandatory explicit-tag dispatch recovery, exact tag checkout, artifact handoff order, and GitHub Release finalization after verified PyPI completion rather than before it.
  - `pdm run test`, `pdm run build-monolith`, `pdm build`, and an isolated wheel-install rehearsal pass. A successful release can be rerun with its tag without consulting package source from mutable `main` or Actions logs.
- **Current Truth**:
  - A private exported v10 release thread records that v10.0.0 and v10.0.1
    eventually published, but only after reactive fixes around tag-only
    recovery, draft assets, stale prepared metadata, and deletion of the last
    change fragment. The sensitive evidence archive remains outside the
    repository and its identifier/path are intentionally not retained here.
  - Implemented: `.github/workflows/release-tag.yml` accepts only a merged `release/svc` PR to `main` (or an explicit merge commit), checks out that exact commit, verifies it is in `main`, creates or verifies its annotated version tag, and dispatches top-level `Publish` with that tag. The dispatch is necessary because a tag pushed by `GITHUB_TOKEN` does not create a second `push` run, while PyPI Trusted Publishing must remain in a top-level rather than reusable workflow.
  - Implemented: `Publish` runs only for a `v*` tag push or required explicit-tag dispatch; it checks out and verifies the tag, lockfile, release metadata, tests, monolith, and built wheel once. It uploads a portable artifact bundle containing the distributions, metadata, notes, checker, checksums, manifest, resolved tag, commit, and SHA-256 file map.
  - Implemented: downstream PyPI and GitHub Release jobs download and re-verify that bundle without rebuilding source. PyPI has no checkout and allows only none or all matching distribution hashes; partial/mismatched state fails. The GitHub finalizer checks out only the exact release tag so `gh` has repository context, then verifies existing title/notes/assets and publishes only a matching draft after PyPI succeeds.
  - Integrated pre-publication evidence: 224 pytest items, Ruff, mypy, Import
    Linter, zizmor, PDM lock validation, release planning, monolith, sdist/
    wheel build, exact package inspection, and the same SHA-bound installed
    wheel on macOS, WSL, and Windows all pass.
  - Controlled v11.0.0 publication bound annotated tag `v11.0.0` to reviewed
    release merge `f99baad7cf9b8798475c3037636dbc8a0e7a738b`. The original
    Publish run `30432201868` built and verified one bundle, published PyPI,
    then exposed that the GitHub finalizer lacked repository context. Its wheel
    SHA-256 is
    `f57fbe6a212a37ae49a8736f648667f0e42b6e56375c346546cebeae828af507`;
    its sdist SHA-256 is
    `377cd1ab36fc8f227566743019775f96ef3324b5a7a7ba1ff8e150ac9f6900b0`.
  - A naive explicit-tag retry correctly stopped before mutation: the wheel was
    byte-identical but the rebuilt gzip-wrapped sdist differed, so PyPI's
    all-match gate rejected the mixed state. Recovery now therefore requires an
    explicit numeric `bundle_run_id`, downloads that preserved prior-run bundle
    with cross-run artifact authorization, first byte-compares its checker
    against `tools/release.py` from the exact tag checkout, validates its tag
    and commit, and re-uploads the unchanged bundle into the current run. It
    skips dependency installation, tests, rebuilding, attestation, and PyPI
    upload during that recovery path.
  - Recovery run `30433280124` reused the bundle from `30432201868`, observed
    both PyPI files with exact matching hashes, skipped upload, checked out the
    exact tag only for `gh` repository context, verified normalized release
    notes and assets, and published GitHub Release `SVC 11.0.0`. Both PyPI and
    GitHub expose the two original distribution hashes; the release is no
    longer a draft.
  - The recovery fix landed on `main` as
    `38440db85894a2db89694c879b66b45537969257` through PR `#14`.
    Post-merge CI run `30434211658` passed its Python 3.11, Python 3.14,
    type/architecture, and distribution jobs. Release PR run `30434210866`
    found no unconsumed fragment, made no release mutation, and left no open
    release PR.
  - The PDM project's own current release workflow is tag-triggered and linear: build, install/smoke-test the wheel, `pdm publish --no-build`, then create the GitHub Release. `pdm-backend` follows the same tag → build → test-built-artifacts → upload shape. Neither official reference reconstructs an old release from a newer `main` state.
  - PyPA's current publishing guide strengthens that pattern: build distributions once, upload them as a workflow artifact, then use a dependent tag-only publish job to download and publish those exact files. Its publish action advises failing loudly on PyPI duplicates rather than routinely enabling `skip-existing`.
- **Next Step**: No automated release work remains and no new package release
  is required. Keep the reviewed v11.0.0 tag, PyPI files, and GitHub Release
  immutable. The wider agent-observability task now awaits only Sir's manual
  TUI review.

## Supporting Material

- Evidence: the v10.0.0/v10.0.1 chronology and current workflow; [PDM build and publish documentation](https://pdm-project.org/latest/usage/publish/); [PDM release workflow](https://github.com/pdm-project/pdm/blob/main/.github/workflows/release.yml); [pdm-backend release workflow](https://github.com/pdm-project/pdm-backend/blob/main/.github/workflows/release.yml); and the [PyPA GitHub Actions publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
- Decisions: use PDM's `build` / `publish --no-build` separation and the PyPA artifact boundary, while retaining SVC's product rule that GitHub Release is published only after PyPI completion. Treat tag rerun as the primary recovery mechanism, rather than trying to infer an older release from the latest branch state.
- Work: 1) bind a candidate merge to a version tag, 2) build and verify one manifest-bound distribution bundle, 3) publish and finalize from that bundle, and 4) make the small set of retry outcomes observable and testable.
