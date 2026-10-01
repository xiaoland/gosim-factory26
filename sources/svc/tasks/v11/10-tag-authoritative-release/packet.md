# v11 Release-qualified Main and Tag-authoritative Publication

- **Objective**: Hard-cut SVC's release model so every commit admitted to
  `main` after the cutover is release-qualified, and pushing one unused,
  policy-valid `vX.Y.Z` tag at such a commit automatically publishes the exact
  release without a release-preparation PR, an extra source mutation, a second
  human gate, or an automatic tag-creation workflow.
- **Guardrails**:
  - `main` remains the only integration and release source. A release branch
    may not become a second state or authority.
  - The tag is the release-version authority; the tagged commit is the source
    authority; the checked bundle manifest is the artifact-identity authority;
    the published GitHub Release remains the completion checkpoint; PyPI
    remains the installation projection.
  - "Every commit" means every commit admitted to `main` under the new
    qualification contract, not arbitrary historical commits that predate it.
    "Publishable" means source, policy, metadata projection, build, and package
    verification can succeed for a valid new tag; it cannot promise external
    service availability.
  - Append-only change fragments prove consumer impact and the exact next
    Behavioral SemVer bump. `release:none` continues to mean no release impact;
    neither state may make a qualified `main` commit structurally unpublishable.
  - Normal publication starts only from an explicit authorized `v*` tag push.
    `workflow_dispatch` is retry/recovery-only, must name the tag, and must run
    at `refs/tags/<tag>` (not a branch ref). It may omit the preserved run only
    when read-only probes prove either empty candidate state or an already
    exact-complete immutable Release. Empty state may rebuild; complete state
    verifies durable Release assets and exits.
  - Build the final distributions once per release attempt, smoke-test the
    exact wheel, retain one manifest-bound bundle as a named 90-day Actions
    artifact, complete only the missing members of a hash-verified PyPI set,
    read all PyPI hashes back, and then create one matching immutable GitHub
    Release with all manifest assets and `--verify-tag`. Mismatched or
    ambiguous external state fails closed.
  - The protected tag is the release approval. All normal/recovery runs share
    one repository-wide non-canceling writer, and no candidate may build until
    its immediate predecessor is verified complete.
  - Protect `main` with required qualification checks and protect `v*` tags
    against update/deletion. Repository rules are part of the functional
    contract, not deferred hardening. The `release` environment's tag-ref
    boundary and repository release-immutability setting are also functional
    controls.
  - Keep the published `v11.0.0`, its PyPI files, and its GitHub Release
    unchanged. It is the verified legacy baseline and is not retroactively
    reported as a platform-immutable release. Do not create a sacrificial tag
    or PyPI release without Sir's separate explicit authorization.
  - Preserve unrelated working-tree changes under `tasks/v10/packet.md`,
    `tasks/v10/50-agent-thread-field-study/`, and
    `tasks/v10/70-agent-thread-audit/`.
- **Verification**:
  - Local fixture histories prove append-only feature fragments,
    `release:none`, no-fragment patch windows, and mixed-impact commits are all
    structurally publishable from `main`; invalid, reused, regressive,
    off-main, or incorrectly bumped tags fail before mutation.
  - PR and exact-main qualification use one shared contract and exercise tests,
    quality gates, monolith, version projection, sdist/wheel build, exact-wheel
    installation, metadata/catalog consistency, migration guidance, and
    candidate release notes.
  - Workflow contracts prove the normal graph is exactly tag push → qualify
    tagged source/predecessor → build once → preserve bundle → PyPI readback →
    immutable GitHub Release. They also prove there is no release-candidate PR,
    second approval, or automatic tag path.
  - One tag-time producer must build both distributions and every downstream
    or post-mutation recovery path must promote those exact bytes. Recovery
    records the named artifact's expiry and never promises permanent Actions
    storage.
  - Read-only GitHub API checks prove active `main` and `v*` rules, required
    check sources, no unintended bypass, the release environment's `v*`
    boundary, release immutability, and the intended Trusted Publisher
    identity.
  - The first authorized real tag after cutover triggers Publish without a
    manual dispatch or later approval and ends with matching PyPI hashes and an
    immutable GitHub Release. Recovery reuses its named preserved bundle
    without rebuilding.
- **Current Truth**:
  - Sir's initial 2026-07-29 expectation was that tagging `main` should create
    the release automatically and PR admission should make every resulting
    commit publishable. Sir then explicitly reopened that sequence for an
    industry benchmark. The resulting target keeps release-qualified `main`
    and the tag as sole approval, while changing artifact recovery and GitHub
    finalization.
  - Current `publish.yml` listens to `v*` pushes, but `tools/release.py`
    accepts only a specially prepared source whose static project/manifest
    version and CHANGELOG already match the tag.
  - Current `main@3973de07a18e345b6e55b661a1ce036c5b7d6db7` has green CI and
    passes `release check-ci`, yet `release tag-plan --commit HEAD` fails
    because `v11.0.0` belongs to the earlier release commit. This is a direct
    counterexample to the desired invariant.
  - GitHub reports `main` as unprotected and the repository has no rulesets, so
    current CI is advisory rather than an enforced merge boundary.
  - The v11.0.0 exercise fixed missing finalizer repository context and added
    preserved-bundle recovery, but also proved that rebuilding the same sdist
    can change its hash. Those fixes make one prepared release recoverable;
    they do not make arbitrary `main` commits publishable.
  - The previous v10 release task deliberately preserved the release PR and
    excluded branch protection. The new user-owned contract supersedes those
    decisions; its evidence remains useful history, not present authority.
  - Slice 0 is complete. It selected pinned backend-native dynamic SCM
    versioning, append-only tag-range Markdown fragments with same-slug MAJOR
    migration notes, and frozen post-v11 CHANGELOG ownership. A benchmark of
    nine comparable projects then replaced pre-PyPI persistent-draft staging
    with globally serialized PyPI-first exact-set completion and one-call
    immutable GitHub Release finalization.
  - Slice 0 also found that repository admission/tag rules must be activated
    before the atomic release-model cut. Release-environment tag restriction
    and repository release immutability join that prerequisite. The earlier
    workflow-first, rules-second sequence is superseded.
  - On 2026-07-29, Sir explicitly started implementation. Local Slice 1,
    version/corpus projection, and workflow work may now proceed under their
    recorded handshakes; no GitHub repository setting, tag, PyPI file, or
    remote release mutation is authorized by that start.
  - Historical pre-cutover snapshot: before PR #18, the local Slice 1/2/4
    implementation was integrated but not committed or merged, so production
    behavior and external controls remained unchanged. Those changes later
    became the merged hard cut recorded below.
  - Recovery gained a separate trust boundary during implementation. A current
    run first packages the exact-tag `tools/release.py` and fresh plan as its
    short-lived control artifact. Before an incomplete release can download or
    use a prior bundle, raw run evidence must bind its ID to the Publish
    workflow, an allowed trigger, the planned commit, a terminal state, and
    the exact live artifact. The current trusted verifier then compares the
    bundle's persisted plan with the fresh plan, allowing only the
    normal-versus-recovery qualification proof to differ. Artifact-provided
    `release-check.py` is never executed.
  - Local evidence is complete: 226 tests; lock, Ruff, mypy, Import Linter,
    zizmor, and monolith checks; a dynamic `11.0.1` wheel/sdist build and
    installed-wheel smoke; and clean wheel installation/lookup/init/status
    acceptance on macOS, WSL Python 3.13, and Windows Python 3.14. The remote
    temporary acceptance directories were removed after the successful run.
  - A final pre-mutation GitHub audit reported no repository rulesets and an
    unrestricted `release` environment (`protection_rules: []`, no deployment
    branch policy). Slice 3 was therefore a real external prerequisite, not a
    paperwork-only acceptance item.
  - On 2026-07-30, Sir authorized the external controls and one real
    `v11.0.1` release to complete acceptance, including step-duration evidence.
    The release is correctly PATCH: the hard cut changes repository delivery
    mechanics but not a published Consumer obligation, stable CLI, or catalog
    contract. Its PR must explicitly declare `release:none`; it adds no
    fragment, migration note, static version, or CHANGELOG entry.
  - Exact readback showed a bootstrap prerequisite: the five future check
    names have not yet run on `main`, so adding them immediately as required
    could lock the branch. Execution therefore follows the task's original
    Slice 2 → Slice 3 → Slice 4 order: merge a CI-name-only bootstrap PR while
    the old release path remains live, observe its exact-main checks, apply and
    probe the external controls, then merge the hard cut PR and tag it.
  - The bootstrap merged as PR #16 and its five target checks succeeded on
    `main`. Slice 3 controls were then applied and read back: main ruleset
    `19984694`, tag ruleset `19984704`, the single `release` `v*` deployment
    policy, and immutable releases. A deliberately invalid PR #17 was blocked
    by the required `Release policy` check and then removed without merging.
  - The hard cut merged as PR #18 at
    `1d4028a0bdedcb99c3694dfe9996f6538f9a5364`; its exact-main CI passed. The
    annotated `v11.0.1` tag object
    `a38657422e1ba4d995c20ce59c53f1ba28f41005` peels to that commit.
  - The automatic tag push run `30472179651` built and preserved the release
    bundle, but correctly stopped before PyPI or GitHub Release mutation when
    the environment policy unexpectedly read back as `type: branch`. The
    malformed policy was replaced by the sole live `type: tag`, `name: v*`
    policy `55951894`.
  - Recovery run `30472401002` reused original artifact `8732154215` without a
    rebuild, published the hash-exact PyPI files, and finalized immutable
    GitHub Release `361909769`. A no-bundle exact-complete dispatch
    `30472677788` then succeeded in 20 seconds with the three mutation jobs
    skipped. Full timing, asset, attestation, installation, and API-readback
    evidence is in [`v11.0.1-acceptance.md`](v11.0.1-acceptance.md).
- **Next Step**: Human acceptance of the recorded `v11.0.1` release evidence;
  then delete this volatile task packet under the root retention rule.

## Supporting Material

- Evidence and root causes: [`diagnostics.md`](diagnostics.md)
- Comparable-project and platform evidence:
  [`release-benchmark.md`](release-benchmark.md)
- Target invariants, authority, and topology: [`contract.md`](contract.md)
- Resolved Slice 0 decisions and projection matrix:
  [`slice-0-decisions.md`](slice-0-decisions.md)
- Ordered hard-cut sequence: [`migration-plan.md`](migration-plan.md)
- Exact per-slice mutation boundaries:
  [`impact-handshake.md`](impact-handshake.md)
- Prepared Slice 3 request payload and readback procedure:
  [`repository-controls.md`](repository-controls.md)
- Completion matrix: [`verification.md`](verification.md)
- Actual first-tag timing and publication evidence:
  [`v11.0.1-acceptance.md`](v11.0.1-acceptance.md)
- Prior release-reliability evidence:
  [`../../v10/60-release-reliability/packet.md`](../../v10/60-release-reliability/packet.md)
