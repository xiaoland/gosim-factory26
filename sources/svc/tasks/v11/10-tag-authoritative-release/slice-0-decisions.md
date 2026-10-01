# Slice 0 Projection Decisions

Status: resolved on 2026-07-29 and amended after the same-day
[`release-benchmark.md`](release-benchmark.md). These decisions bound later
implementation; they do not authorize a code, workflow, repository-setting,
tag, or release mutation.

## Decision 1 — Backend-native Tag Version Projection

Use PDM-Backend's built-in dynamic SCM version support, not a copied temporary
source tree and not synchronized static future-version fields.

The target source shape is:

- `[project]` declares `dynamic = ["version"]` and no static `version`;
- `[tool.pdm.version]` uses `source = "scm"`, a strict `vX.Y.Z` tag filter and
  parser, a source-development fallback, and no `write_to`;
- `[build-system].requires` pins the reviewed PDM-Backend version exactly;
- PR/main rehearsals set `PDM_BUILD_SCM_VERSION` to the planner's synthetic
  eligible version;
- Publish derives the version from its already-validated tag and passes that
  same value through `PDM_BUILD_SCM_VERSION`;
- the local formatter projects the latest matching stable tag for an untagged
  source checkout so source-mode catalog behavior remains stable, but this
  development projection can never authorize publication;
- `pdm_build.py` reads the backend-resolved metadata version and generates the
  catalog only under `context.build_dir`;
- `tools/build_catalog.py` accepts the projected version explicitly instead
  of reading `src/manifest.json`.

The release planner, not PDM's general SCM parser, remains responsible for
strict tag grammar, tag/commit identity, clean exact checkout, main
reachability, monotonicity, and Behavioral SemVer. The environment override is
a derived projection after those checks, never an independent version command.

`src/manifest.json` is removed at the hard cut. It cannot remain as a stale
second version or impact authority. Source-mode catalog construction uses the
installed/editable distribution version, with `0.0.0` only as a clearly
non-release source fallback when no distribution metadata exists.

The resulting sdist must contain a resolved static version in its generated
`pyproject.toml`. Building a wheel from that sdist without `.git` and without a
version environment variable must reproduce the same version and catalog
identity. This is a required proof, not an assumption about backend behavior.

### Why this option

- PDM-Backend already owns dynamic metadata resolution and runs that hook
  before the local build hook.
- The exact version reaches wheel metadata, sdist metadata, filenames, and the
  local catalog hook through one backend metadata object.
- No third-party SCM plugin, temporary source copy, tracked rewrite, or
  post-release version synchronization is required.
- Pinning the backend closes the current unreviewed build-tool drift without
  adding it to runtime or development dependency groups.

Official capability references:

- <https://backend.pdm-project.org/metadata/#dynamic-project-version>
- <https://backend.pdm-project.org/hooks/>
- <https://backend.pdm-project.org/api/>
- <https://backend.pdm-project.org/build_config/>
- <https://github.com/pdm-project/pdm-backend/blob/main/src/pdm/backend/hooks/version/scm.py>

## Decision 2 — Append-only Tag-range Fragments

Keep the existing human-readable Markdown fragment shape:

```text
changes/<stable-slug>.major.md
changes/<stable-slug>.minor.md
changes/<stable-slug>.patch.md
```

After the hard cut, fragments are an append-only release-evidence ledger:

- a fragment path is globally unique;
- a merged fragment may not be modified, renamed, or deleted;
- the previous-release-tag → candidate-tag diff selects only newly added
  fragments;
- the candidate-tag blob supplies the validated summary;
- the maximum selected impact determines the exact next single SemVer bump;
- a window with no new fragment is an internal-only release and requires the
  next patch version;
- `release:none` remains a PR admission decision and creates no synthetic
  fragment or release reason.

Every new MAJOR fragment must add one non-empty packaged migration note at the
deterministic path:

```text
src/migrations/<stable-slug>.md
```

That note either gives migration steps or explicitly explains why no consumer
action applies. Review owns the semantic truth; tests own path identity,
presence, non-empty content, and inclusion in the projected corpus.

There is no fragment cleanup or post-release bookkeeping PR. `CHANGELOG.md`
becomes a frozen historical record through v11.0.0 with a pointer to GitHub
Releases. Tag-range fragments are the notes authority and the published GitHub
Release is the canonical future human presentation. Towncrier has no remaining
owner; its configuration, dependency, and now-empty release dependency group
are removed at the hard cut.

### Why this option

- Retaining Markdown preserves the current low-friction contributor surface.
- Append-only paths make range selection a simple tree diff rather than a
  reconstruction of add/modify/delete history.
- A deterministic migration-note path avoids a second manifest, front matter,
  or sidecar schema.
- Freezing CHANGELOG removes the only remaining reason for a release
  preparation commit.

## Decision 3 — PyPI-first Immutable-bundle Promotion

Choose immutable-bundle promotion, not a promise that a later rebuild will
reproduce the wheel and gzip-wrapped sdist byte-for-byte.

One tag-triggered producer:

1. verifies the exact tagged source, requires its immediate predecessor to be
   complete, and classifies candidate PyPI/GitHub state before any build;
2. builds wheel and sdist once;
3. installs and smokes the exact wheel;
4. creates and verifies one tag/commit/version/hash-bound bundle;
5. uploads the bundle as a named Actions artifact with explicit
   `retention-days: 90` and records its API ID and actual expiry;
6. verifies or completes the exact PyPI file set, then performs a bounded
   post-upload hash readback until every expected file is visible and exact;
7. invokes `gh release create` with the exact tag and every
   manifest-enumerated asset; the command includes `--verify-tag`,
   `--title "$TITLE"`, and `--notes-file "$NOTES_FILE"`, with no `--draft`;
8. reads back the release tag, resolves its remote tag object to the exact
   commit, and compares title, notes, assets, and immutable state. The
   `target_commitish` display field is not used as commit authority.

There is no persistent draft in the normal pre-PyPI path. With release
immutability enabled, `gh release create <tag> <assets...>` internally creates
a draft, uploads all assets, and publishes only after those uploads complete.
An interrupted command may leave a partial draft; that is a recovery residue,
not an additional normal authority.

Recovery names the exact tag and the prior Publish run that owns the original
bundle. PyPI states are `none`, `exact subset`, `all exact`, `mismatch`, or
`ambiguous`; an exact subset may receive only its missing original files.
GitHub states are `absent`, `exact draft subset`, `published exact`,
`mismatch`, or `ambiguous`; "exact" covers tag/target commit, title, notes, and
assets. An exact draft subset may receive only its missing original assets
before publication. Mismatch and ambiguity fail closed.

Before any PyPI file or GitHub draft exists, a failed attempt may rebuild from
the exact tag as a new attempt. `workflow_dispatch` therefore allows an omitted
prior-run ID only after a read-only probe proves candidate external state is
empty or exact-complete. Empty state may start a pre-mutation rebuild.
Exact-complete state verifies the manifest-bound assets on the immutable
Release and exits idempotently. Any incomplete PyPI, draft, or Release state
requires a prior-run ID and rejects before invoking a build command. Once
incomplete external state exists, recovery may not rebuild and must use the
named original artifact while it still exists and before its recorded expiry.
Early artifact deletion or workflow-run deletion blocks just like expiry. The
workflow does not claim that Actions storage is permanent.

### Evidence

Two temporary builds of the v11 inputs with PDM 2.27.0 and PDM-Backend 2.4.9
reproduced the wheel. With `SOURCE_DATE_EPOCH` set to the tag commit epoch, the
uncompressed tar payload also reproduced, but the `.tar.gz` files still
differed in the outer gzip timestamp. Recompressing with `gzip -n` removed that
observed difference, but would add a new cross-toolchain normalization
contract. The current unpinned backend and floating runner make that contract
strictly larger than preserving and promoting one checked bundle.

The cross-project benchmark found no common PyPI/GitHub ordering, but PDM,
pipx, uv, and Ruff all complete PyPI before the GitHub Release. It also found
that public same-version recovery is generally weak. The selected sequence
keeps their simpler completion order while retaining SVC's stronger
manifest-bound, no-rebuild recovery within an explicit 90-day operational
window.

GitHub recommends draft → assets → publish for immutable releases; the current
GitHub CLI performs those calls internally when assets are passed to
`gh release create`. A long-lived pre-PyPI draft would add another mutable
state without being required by that recommendation. The completed immutable
Release, not its temporary draft, is the durable release owner. GitHub locks
the published tag and assets, not title/body metadata; the final exact
title/notes comparison remains a workflow contract.

Official capability references:

- <https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases>
- <https://cli.github.com/manual/gh_release_create#immutable-releases>
- <https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts>

## Decision 4 — Protected Tag Approval and One Release Writer

A protected `vX.Y.Z` tag is both the only normal trigger and the sole release
approval. Qualification, bundle construction, PyPI publication, and GitHub
finalization proceed without a second rejectable human gate. The `release`
environment retains the PyPI Trusted Publisher identity and admits only
the custom deployment policy `type: tag, name: v*`, including recovery
dispatched at the exact tag, but has no required reviewer.

Both lightweight and annotated tags are eligible. The planner resolves the
exact remote ref and peels it to one commit before using that commit as release
source; tag-object messages, tagger metadata, and annotation signatures are
not version, notes, or approval authorities. Signed annotated tags remain
allowed but are not required. A tag that cannot be resolved and peeled to
exactly one commit fails before build or external mutation.

All normal and recovery runs share one repository-wide `svc-publish`
concurrency group with `cancel-in-progress: false`. Before a candidate may
build, its immediate prior strict tag must be:

- the declared legacy cutover baseline `v11.0.0`, whose exact completed state
  is verified without pretending it is retroactively immutable; or
- a target-model release whose PyPI set and immutable GitHub Release are exact
  and complete.

`tools/release.py` owns `v11.0.0` as one reviewed historical cutover constant.
It bounds legacy history and the first append-only fragment window; it is not a
future version authority or mutable release field.

A pushed tag is therefore a release commitment, not a proposal that can later
be abandoned. An incomplete tag must be recovered before a newer tag can
publish. A newer run that observes an incomplete predecessor fails before
build or mutation and may be rerun after predecessor recovery.

This topology does not reintroduce a release branch, release PR, source
mutation, automatic tag creation, or normal-path dispatch.

### Why this option

- PyPA recommends an environment approval, while uv and Ruff use explicit
  release gates before their workflows create tags.
- Transplanting that gate after SVC's protected authority tag creates an
  abandoned-version state and ambiguous next release window.
- PDM and pipx demonstrate the simpler tag-triggered automatic path for
  comparable Python CLI/package tools.
- Main admission, authorized tag creation, tag-ref environment restriction,
  exact remote-ref resolution, one release writer, exact predecessor
  completion, and fail-closed state checks supply the compensating controls.

## Signed-off Projection Matrix

| Concern | Authority | Source representation | Build / release projection | Installed or human projection | Durable owner | Primary proof owner |
| --- | --- | --- | --- | --- | --- | --- |
| Release source | eligible tag's resolved commit on protected `main` | Git commit/tree | exact tag checkout | sdist source and GitHub source links | Git + repository rules | `tests/test_release.py`, tag workflow |
| Release version | validated strict tag | no static future version | PDM dynamic metadata plus derived environment override | wheel metadata, filenames, catalog, bundle, Release title | tag and `pyproject.toml` projection config | `tests/test_release.py`, `tests/test_catalog.py` |
| Development version | latest matching stable tag, or `0.0.0` without release provenance | SCM state only | custom SCM formatter | editable/source-mode CLI and catalog | `pdm_build.py` | catalog/resource tests |
| Behavioral impact | newly added append-only fragments in tag range | `changes/<slug>.<impact>.md` | exact single SemVer bump | grouped release notes | fragment blobs and `tools/release.py` | fixture Git histories |
| Migration obligation | MAJOR fragment slug | `src/migrations/<slug>.md` | verified link in bundle metadata/notes | packaged corpus lookup | fragment + migration document | release and catalog tests |
| Future release notes | selected tag-range fragments | append-only Markdown summaries | deterministic `RELEASE_NOTES.md` | published GitHub Release body | fragments; GitHub Release is presentation | release/workflow tests |
| Historical changelog | released history through v11.0.0 | frozen `CHANGELOG.md` | none | repository reader redirect | `CHANGELOG.md` | static contract assertion |
| Cutover baseline | reviewed historical `v11.0.0` anchor | release-planner constant | first tag range and predecessor exception | none | `tools/release.py` plus Git tag | release fixture and live baseline check |
| Runtime corpus identity | validated tag version plus canonical `src/*.md` | versionless source corpus | build-dir catalog | wheel catalog and source fallback | tag + `src/` | catalog, resource, wheel smoke tests |
| Distribution identity | checked bundle manifest and hashes | none before tag | one producer output retained as a named Actions artifact | exact PyPI files and immutable Release assets | named run until completion; PyPI plus published Release afterward | bundle and workflow tests |
| Release authorization | authorized protected tag | none | tag starts the single-writer workflow and cannot be abandoned | tag/audit history | GitHub tag rule | workflow tests and live readback |
| Release completion | exact PyPI files followed by matching immutable Release | none | CLI-internal draft → asset upload → published transition | GitHub Release | GitHub Release API and attestation | workflow tests and live acceptance |

## Consequences for the Migration Plan

1. `AGENTS.md`, `README.md`, `src/index.md`, and `svc_cli/resources.py` join the
   hard-cut owner set; the provisional handshake omitted them.
2. The new planner can land dark behind existing commands, but dynamic project
   metadata, manifest removal, append-only lifecycle, dependency removal, and
   workflow replacement must switch atomically.
3. Stable check names and `main`/tag rules must exist before the hard cut. The
   original workflow-first, rules-second sequence had an unprotected target
   window and is reversed.
4. Slice 3 restricts the `release` environment to `v*` tag refs and enables
   repository release immutability before cutover; it adds no second approval.
5. Publish serializes every tag/recovery run, requires a completed predecessor,
   retains the bundle for an explicit 90-day window, supports exact-subset
   completion plus post-upload readback, and creates the immutable Release with
   all assets only after PyPI is exact. It does not pre-stage a persistent
   draft.
6. No post-release CHANGELOG or fragment-cleanup slice remains.
