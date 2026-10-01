# Release Contract Diagnostics

## Reproduced Mismatch

On 2026-07-29 the exact current `main` commit was
`3973de07a18e345b6e55b661a1ce036c5b7d6db7`.

```text
$ pdm run release check-ci --json
{"impact": "major", "previous_version": "10.0.2", "version": "11.0.0"}

$ pdm run release tag-plan --commit HEAD --json
release: Release tag v11.0.0 points to
f99baad7cf9b8798475c3037636dbc8a0e7a738b, not requested commit
3973de07a18e345b6e55b661a1ce036c5b7d6db7
```

The main CI run for that commit was green:
<https://github.com/xiaoland/svc/actions/runs/30434859814>.
Therefore current CI success and current release eligibility are different
states.

## Repository Enforcement Evidence

Read-only GitHub API observations on 2026-07-29:

```text
main.protected = false
main.required_status_checks.enforcement_level = off
repository rulesets = []
default workflow token = read
Actions-created PR approval = enabled
release environment protection rules = []
```

The last three values are compatible with automatic publication. The first
three disprove that PR checks currently control admission to `main`.

## Failure Matrix

| Confirmed Cause | Evidence | Contract Effect | Likely Owner |
| --- | --- | --- | --- |
| Prepared-source dual state | `verify_prepared()` requires no fragments, a prewritten release version, Behavioral SemVer metadata, and a matching CHANGELOG section | Most green `main` commits cannot be tagged directly | `tools/release.py`, release metadata model |
| Static source version owns the tag | `verify_tag()` compares `vX.Y.Z` with `pyproject.toml` and `src/manifest.json` | A post-release `release:none` commit remains stuck at an already-used version | build metadata projection |
| Release PR performs required mutations | `release-pr.yml` consumes fragments and changes manifest, project version, changelog, and lockfile | Release qualification exists only after a second PR | release workflow topology |
| Automatic tag requires compensating dispatch | `release-tag.yml` pushes with `GITHUB_TOKEN`; GitHub suppresses ordinary workflow recursion | Normal release needs two workflows and two trigger mechanisms | workflow topology |
| Main has no enforced rule | branch protection API returned 404 and rulesets returned `[]` | A PR can merge or code can reach `main` without the advertised checks | GitHub repository settings |
| CI artifact is not the release artifact | `ci.yml` builds/uploads distributions; `publish.yml` builds again and ignores them | PR success does not identify the bytes later published | qualification/build boundary |
| Sdist rebuild is not reproducible | v11 retry produced an identical wheel but a different gzip-wrapped sdist | Rebuild-based recovery and exact pre-tag artifact claims are false | build normalization or artifact promotion |
| Finalizer conflates absence and error | any nonzero `gh release view` enters the create path | Network/auth/API ambiguity may lead to mutation instead of a closed failure | `publish.yml` finalizer |
| Fragment discovery is inconsistent | `release-pr.yml` tests any top-level `*.md`; `fragments()` ignores `README.md` and validates a strict filename regex | A non-fragment Markdown file can spuriously enter release planning | workflow/release parser boundary |

## Already-fixed v11 Symptoms

- The GitHub finalizer now checks out the exact tag before using `gh`.
- Recovery can select a prior run's preserved bundle and verifies its checker,
  tag, commit, and hashes before reuse.
- Generated release PRs declare `release:none`.

These fixes remain valuable in the target design. They solve recovery and
finalization defects after a release bundle exists; they do not solve
release-qualified `main`.

## Slice 0 Projection Evidence

- PDM-Backend 2.4.9 natively supports dynamic SCM versions, strict tag
  filtering/extraction, `PDM_BUILD_SCM_VERSION`, a custom formatter, and
  build-directory file projection. Its dynamic hook runs before the local
  `pdm_build.py` hook, so the catalog hook can consume one resolved metadata
  version.
- The current unpinned `[build-system].requires = ["pdm-backend"]` is outside
  `pdm.lock` and can resolve a different backend on a later isolated build.
- A clean v11.0.0 checkout resolves to `11.0.0`; the current post-tag checkout
  resolves through the default formatter to a development/local version. The
  release planner must validate the exact tag and pass its derived stable
  version explicitly rather than treating general SCM output as release
  authorization.
- With PDM 2.27.0, PDM-Backend 2.4.9, and the tag commit epoch supplied through
  `SOURCE_DATE_EPOCH`, two temporary v11 input builds produced identical
  wheels and identical uncompressed tar payloads. The gzip-wrapped sdists
  still differed in the outer gzip timestamp. A later rebuild is therefore not
  the selected recovery proof.
- An Actions artifact is immutable only for its retention window. Current
  `svc-release-v11.0.0` artifacts expose a 90-day expiry. Recovery must record
  that bound instead of claiming permanent Actions storage.

The decisions and implementation consequences are recorded in
[`slice-0-decisions.md`](slice-0-decisions.md).

## Comparable-project Correction

The initial Slice 0 projection selected persistent draft staging before PyPI.
The subsequent official-workflow benchmark in
[`release-benchmark.md`](release-benchmark.md) changed that conclusion:

- PDM, pipx, uv, and Ruff complete PyPI before the GitHub Release;
- Poetry and Towncrier expose the GitHub Release first;
- Hatch starts with an external draft, but its actual 1.17.1 run reached PyPI
  success and repeatedly failed while adding draft assets before later manual
  recovery;
- almost every inspected publisher builds its publishable distributions once
  and passes the same bytes between jobs;
- most public workflows have weaker same-version recovery than SVC already
  demonstrated.

The target now treats the protected tag as the sole release approval,
serializes the entire release stream, requires a completed predecessor,
retains the original bundle for an explicit 90-day Actions window, completes
only hash-matching PyPI subsets with post-upload readback, and then calls
`gh release create` with every manifest asset plus `--verify-tag`. GitHub CLI
performs draft → upload → publish internally, after which repository release
immutability locks the tag and assets.

Read-only live observations on 2026-07-29 also found:

```text
repository release immutability = disabled
release environment protection rules = []
repository writers/admins = xiaoland only (user ID 37663413)
```

Slice 3 must restrict the environment to `v*` tag refs and enable release
immutability before the source cutover. It intentionally retains no required
environment reviewer because a rejectable post-tag gate would strand the
authority tag. Slice 0 did not mutate external state.

## Legacy Baseline Readback

Read-only GitHub/PyPI checks on 2026-07-29 verified that `v11.0.0` can serve as
the one legacy cutover baseline:

```text
tag commit = f99baad7cf9b8798475c3037636dbc8a0e7a738b
tag object = annotated, unsigned
GitHub Release = published, non-draft, immutable:false
wheel SHA-256 on manifest/GitHub/PyPI =
  f57fbe6a212a37ae49a8736f648667f0e42b6e56375c346546cebeae828af507
sdist SHA-256 on manifest/GitHub/PyPI =
  377cd1ab36fc8f227566743019775f96ef3324b5a7a7ba1ff8e150ac9f6900b0
```

The GitHub Release API reports `target_commitish: main` for this existing-tag
release, so target commit verification must resolve the remote tag object; it
must not compare the literal `target_commitish` field with the commit SHA.
Future releases must report `immutable: true`; the baseline is only a verified
legacy exception.

The target contract gives lightweight and annotated tags identical meaning:
the strict tag name and the exact commit obtained by peeling its remote ref
are authoritative. Annotation text, tagger metadata, and signatures are not
additional version, notes, or release-approval channels. Signed tags remain
permitted but are not required.

## External Semantics

- A workflow configured with `push.tags` runs for matching tag pushes:
  <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onpushbranchestagsbranches-ignoretags-ignore>.
- Events caused by the repository `GITHUB_TOKEN` generally do not start a new
  workflow; `workflow_dispatch` is an exception:
  <https://docs.github.com/en/actions/concepts/security/github_token>.
- Required checks and pull-request admission are enforced only through branch
  protection or rulesets:
  <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches>.
- Required environment reviewers hold a job before it runs; allowing
  self-review is an explicit environment policy:
  <https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments>.
- Environment deployment policies can distinguish tag rules and restrict them
  by pattern:
  <https://docs.github.com/en/rest/deployments/branch-policies?apiVersion=2026-03-10>.
- Immutable GitHub Releases lock their published tag/assets, and
  `gh release create` with assets performs draft → upload → publish:
  <https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases>,
  <https://cli.github.com/manual/gh_release_create#immutable-releases>.
- PDM-Backend dynamic version, build-hook, and reproducibility controls:
  <https://backend.pdm-project.org/metadata/#dynamic-project-version>,
  <https://backend.pdm-project.org/hooks/>,
  <https://backend.pdm-project.org/build_config/>.
