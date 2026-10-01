# PDM Workspace / CLI Source-Test Layout Plan

## Status

- **Decision**: Use a PDM workspace and make `svc_cli/` the sole distributable
  member.
- **Plan state**: Implemented and verified on 2026-08-09. No commit has been
  created.
- **PDM constraint**: Workspace support begins in PDM 2.28.0 and is explicitly
  experimental. A repository-external compatibility spike is therefore the first
  implementation gate, not an optional cleanup.
- **Compatibility baseline**: The current `sustainable-vibe-coding` distribution,
  `svc` entry point, SCM version, wheel paths, CLI behavior, packaged Corpus,
  migration descriptors, and nine output schemas must remain unchanged.

## Implementation Result

- The root is a non-distribution PDM workspace and `svc_cli/` is its sole
  distributable member. PDM 2.28.0 is pinned in CI and release workflows.
- Runtime source/static data now live under `svc_cli/src/svc_cli`; 25 root
  Corpus/tool cases remain under `tests`, while 133 CLI cases and their support
  live under `svc_cli/tests`.
- `svc_cli.catalog` owns one projection primitive shared by editable source mode,
  the member build hook, and the root tool wrapper. The member sdist carries only
  the canonical Corpus build input needed to rebuild its wheel.
- Checkout-direct, checkout-sdist-derived, and repository-external
  sdist-rebuilt wheels have identical installed payloads. Their installed path set
  also matches the baseline wheel exactly.
- Local macOS verification passes all 158 tests, mypy across 45 source/support
  files, seven import contracts, test/source lint, nine unchanged output schemas,
  release/Corpus/workflow gates, monolith generation, and installed-wheel smoke.
- Baseline and candidate installed wheels match exact exit code/stdout/stderr for
  20 read-only observations across five real Consumer roots. Linux WSL on Python
  3.13.5 passes the same 158 tests and independently builds the member sdist and
  wheel.

## Objective

Make filesystem ownership match product ownership:

```text
repository Corpus and tooling       installable SVC CLI component
-----------------------------       -----------------------------
src/                                svc_cli/src/svc_cli/
tools/                              svc_cli/tests/
tests/                              svc_cli/pyproject.toml
root workspace orchestration       svc_cli/pdm_build.py
```

The migration should achieve four concrete outcomes:

1. The root project owns the canonical Corpus, repository tooling, monolith
   behavior, release projections, and their tests.
2. The `svc_cli` member owns the Python runtime package, its static package data,
   build metadata, and its tests.
3. PDM owns one workspace environment and one root lock while build/publish target
   only the `svc_cli` member.
4. A member sdist remains self-contained: a wheel rebuilt from an extracted sdist
   must contain the same Corpus/catalog and runtime payload as a wheel built from
   the repository checkout.

This is an ownership and packaging change, not a test-count reduction or product
behavior redesign.

## Non-goals

- Do not move the canonical Corpus out of root `src/` or commit a second Corpus
  authority under `svc_cli/`.
- Do not move root tools or their tests into the CLI component merely because a
  tool imports `svc_cli`.
- Do not combine this layout change with command, output, config, telemetry, or
  analysis redesign.
- Do not rewrite retained tests for coverage or introduce layout snapshot tests.
- Do not publish or build a root workspace distribution.
- Do not change the public distribution name, console entry point, Python
  requirement, dependency ranges, version semantics, or wheel resource paths.
- Do not count temporary fixture repositories as product acceptance.

## Baseline Evidence

### Tool and project state

- Local and CI PDM are currently 2.27.0. PDM workspace support was added in
  2.28.0, so current tooling cannot parse the target workspace contract.
- The [official workspace contract](https://pdm-project.org/latest/usage/workspace/)
  uses `[tool.pdm.workspace].members`; members share the root environment and
  lock. `install`, `lock`, and `sync` run from the root, while `run`, `build`, and
  `publish` may target a member project.
- The current root project is both the repository orchestrator and the published
  `sustainable-vibe-coding` package. Runtime dependencies, build metadata, PDM
  scripts, test configuration, and repository tools are consequently mixed in one
  `pyproject.toml`.
- The current build hook imports `tools.build_catalog` and only projects the
  Corpus/catalog for a wheel. It does not make that external build input available
  inside the member sdist.
- [PDM Backend build hooks](https://backend.pdm-project.org/hooks/) permit arbitrary
  source paths to be added to either artifact via the artifact-relative file
  mapping. That is the mature mechanism for carrying the canonical root Corpus
  into the member sdist without copying it in Git. Its
  [build configuration guidance](https://backend.pdm-project.org/build_config/)
  also treats an sdist-to-wheel rebuild as a required packaging path.

### Test ownership

The current suite contains 158 collected cases:

| Owner | Cases | Current files | Target |
| --- | ---: | --- | --- |
| Root Corpus/repository tooling | 25 | `test_build_monolith.py`, `test_catalog.py`, `test_framework_contract.py`, `test_release_projections.py` | Stay under root `tests/` |
| Installable CLI runtime | 133 | All other test modules plus `project_contract.py` and `agent_thread_contract.py` | Move under `svc_cli/tests/` |

`test_catalog.py` remains a root integration test even though it imports runtime
catalog types: its owner and trigger are the root Corpus-to-wheel projection. The
test should prove the resulting projection/build behavior rather than retain a
unit-shaped dependency on the old root hook location.

### Path assumptions that must change deliberately

- `svc_cli/resources.py` assumes the package is adjacent to root `src/`.
- CLI subprocess tests derive their working directory from
  `Path(__file__).parents[1]`; that would become the component directory after the
  move.
- CLI tests import support code through `tests.*`, coupling them to the current
  root test namespace.
- `tools/build_cli_output_schemas.py` and `tools/build_release_projections.py`
  address static package data at `svc_cli/data/...`.
- mypy enumerates runtime and test-support files with current root-relative paths.
- CI and publish workflows build the root project and pin PDM 2.27.0.
- README and AGENTS describe `svc_cli/` and root `tests/` as undivided owners.

## Target Topology

```text
pyproject.toml                       # non-distribution workspace + repo commands
pdm.lock                             # one workspace lock
src/                                 # only canonical Corpus source
tools/                               # repository/build/release tools
tests/                               # 25 root/tool behavior cases
pdm_build.py                         # removed from root

svc_cli/
  pyproject.toml                     # sustainable-vibe-coding distribution
  README.md                          # member/package metadata, not Corpus guidance
  pdm_build.py                       # member build hook + SCM version formatter
  src/
    svc_cli/
      __init__.py
      ...                            # complete runtime package
      data/
        migrations/
        output-schemas/
  tests/
    svc_cli_test_support/            # CLI-only test builders/contracts
    test_*.py                         # 133 CLI behavior cases
```

The repeated name is intentional and follows the ordinary src-layout distinction:

- outer `svc_cli/`: workspace component/project root;
- `svc_cli/src/`: import source root;
- inner `svc_cli/src/svc_cli/`: import package.

The outer component directory must not become an importable Python package. Test
support therefore uses the unambiguous `svc_cli_test_support` name instead of
creating `svc_cli.tests` or retaining the generic root `tests` namespace.

## Metadata and Command Ownership

### Root workspace `pyproject.toml`

The root becomes a non-distribution orchestration project:

- use a private orchestration identity such as `svc-workspace`, with
  `distribution = false`;
- declare `[tool.pdm.workspace] members = ["svc_cli"]`;
- retain the shared Python requirement, quality/test dependency groups, PDM
  repository scripts, pytest configuration, Ruff configuration, mypy, and
  import-linter contracts;
- declare no published runtime package and no build backend;
- keep one root lock and one root environment;
- make repository commands explicit:
  - `test-root = pytest tests`;
  - `test-cli = pytest svc_cli/tests`;
  - `test = pytest tests svc_cli/tests`;
  - lint/type/import/schema/release/monolith commands remain root orchestration.

`pdm install`, `pdm lock`, and `pdm sync` continue to run only from the workspace
root. The workspace member must be installed editable into that shared environment,
so `pdm run svc --help` continues to work from the root.

### Member `svc_cli/pyproject.toml`

The member owns everything required to build and publish the existing package:

- project name `sustainable-vibe-coding`;
- dynamic SCM version and current tag rules;
- runtime dependencies;
- `svc = "svc_cli.cli:main"`;
- PDM Backend and build-system requirements;
- `package-dir = "src"` and package discovery for `src/svc_cli`;
- member build hook and member sdist inputs;
- a member-local packaging README so metadata never points outside the sdist.

Build and publish become explicitly member-targeted:

```text
pdm build -p svc_cli
pdm publish -p svc_cli
```

The implementation will pin one validated PDM 2.28+ release in CI. It will not
float CI on an unbounded latest PDM while workspace behavior is experimental.

## Build Authority and Artifact Data Flow

The canonical Corpus and the installable projection have different owners:

```text
Git checkout
  root src/  ------------------------------------+
  svc_cli/src/svc_cli/catalog.py ----------------+--> member build hook
  svc_cli/src/svc_cli/data/{migrations,schemas} /       |
                                                        +--> wheel
                                                        |    svc_cli/data/catalog.json
                                                        |    svc_cli/data/corpus/**
                                                        |    svc_cli/data/migrations/**
                                                        |    svc_cli/data/output-schemas/**
                                                        |
                                                        +--> member sdist
                                                             src/svc_cli/**
                                                             _build_inputs/corpus/**
                                                             pdm_build.py

extracted member sdist
  _build_inputs/corpus/** + member package source
                                      |
                                      +--> semantically identical wheel payload
```

### Corpus/catalog projection

The deep projection primitive moves into the existing `svc_cli.catalog` owner so
the build hook and editable runtime can use it without importing repository tools.
`tools/build_catalog.py` remains the root repository wrapper/compatibility surface
and delegates to that one implementation. The primitive accepts explicit inputs
instead of assuming one monolithic project root:

- canonical Corpus source directory;
- generated output directory.

Static package-owned migrations and output schemas should be collected from
`svc_cli/src/svc_cli/data` by the member build configuration. The custom hook only
owns the derived catalog/Corpus projection.

For a checkout build, the member hook resolves:

- Corpus: `../src` relative to the member root;
- projection implementation: member-local `svc_cli.catalog`;
- package source/data: member-local `src/svc_cli`.

For an sdist build, the hook maps the exact canonical Corpus inputs into private
`_build_inputs` paths inside the sdist. For a wheel build from that extracted
sdist, the same hook uses those staged inputs and its member-local projection
implementation. The hook must establish its own member source path before importing
the projection owner; it must never accidentally import an older installed
`svc_cli` package.

The staged build inputs are artifact inputs, not a second source authority:

- they are never committed under the member;
- they are present in the sdist because the sdist must be rebuildable;
- they are excluded from the wheel;
- direct-wheel and sdist-derived-wheel content is compared by path and bytes.

### Development source fallback

`resources.source_root()` must stop relying on the current positional parent.
Source mode should resolve and validate one of two explicit development inputs:

1. workspace checkout: member root's parent `src/`;
2. extracted member sdist: member-local staged Corpus input.

Validation must require the Corpus version index and expected directory shape.
Installed wheel mode continues to use only packaged resources and must not search a
checkout.

### Stable artifact contract

The following paths remain stable inside the wheel even though their repository
paths move:

```text
svc_cli/**
svc_cli/data/catalog.json
svc_cli/data/corpus/**
svc_cli/data/migrations/**
svc_cli/data/output-schemas/**
```

The wheel must not contain `tests/`, root `src/`, `_build_inputs/`, root tools, or
workspace metadata. The member sdist may contain CLI tests and the minimal staged
build inputs needed to reproduce the wheel, but never root tool tests.

## Test Migration Rules

### Root tests retained in place

```text
tests/test_build_monolith.py
tests/test_catalog.py
tests/test_framework_contract.py
tests/test_release_projections.py
```

These tests own root Corpus/tool behavior. They may exercise the member artifact as
an integration boundary but must not migrate merely because they import a runtime
type.

### CLI tests moved as one ownership batch

All other current test modules move with `git mv` to `svc_cli/tests/`, including
analysis and telemetry tests because those modules are part of the installable
distribution. This layout decision does not redesign those product areas.

The two shared test-support modules move under
`svc_cli/tests/svc_cli_test_support/`. Imports become component-local and no
production package receives test helpers.

Subprocess tests must use an explicit repository/workspace resolver or a temporary
Consumer working directory according to the behavior under test. They must not
recover the old behavior by adding another fragile `parents[n]` expression.

No test is deleted solely because it moves. If relocation exposes an
implementation-shaped test, removal still requires the existing retention rules
and a separate behavior-proof judgment.

## Planned File Impact

### Move

- `svc_cli/**/*.py` -> `svc_cli/src/svc_cli/**/*.py`.
- `svc_cli/data/**` -> `svc_cli/src/svc_cli/data/**`.
- root `pdm_build.py` -> `svc_cli/pdm_build.py`.
- all CLI-owned tests/support -> `svc_cli/tests/**`.

### Add

- `svc_cli/pyproject.toml`.
- `svc_cli/README.md` for distribution metadata.
- CLI test-support package under `svc_cli/tests/`.
- only the smallest build-path helpers required to select checkout versus sdist
  inputs; no general workspace abstraction.

### Update

- root `pyproject.toml` and `pdm.lock`.
- `tools/build_catalog.py`, `tools/build_cli_output_schemas.py`, and
  `tools/build_release_projections.py`.
- `svc_cli/resources.py` after its move.
- mypy file paths, pytest collection, Ruff test paths, and import-linter execution.
- CI and publish PDM pins plus member-targeted build commands.
- README, AGENTS, and any release/build documentation that names old paths.
- output-schema history lookup so the one-time repository path move does not erase
  comparison with schemas stored at the old path in earlier Git refs.

### Remove

- root distribution/build metadata and root `pdm_build.py` location.
- old empty runtime directories and root CLI test files after successful moves.
- no unrelated task files or user changes.

## Implementation Sequence and Dependency Order

### 0. Freeze baseline and prove PDM workspace viability

Before editing source paths:

1. Record the current 158-case collection, test IDs, schema hashes, release
   projections, wheel/sdist file inventories, package metadata, SCM version, and
   `svc` entry point.
2. Build and install the baseline wheel in a repository-external virtual
   environment; capture the read-only real-project matrix below.
3. In a repository-external minimal spike using the selected PDM 2.28+ version,
   prove:
   - root lock/install sees an implicit editable member;
   - a root script can invoke the member console entry point;
   - `pdm build -p <member>` selects the member rather than the root;
   - member-targeted publish configuration resolves the member artifact without
     contacting or uploading to an index;
   - nested SCM version discovery works from a Git checkout;
   - an extracted member sdist rebuilds without its parent workspace.
4. If any of those mechanics fails under the pinned version, stop before the
   repository move and review the workspace decision with evidence. Do not hide a
   workspace limitation behind custom orchestration.

### 1. Establish workspace/member metadata and move the package atomically

In one coherent source-layout batch:

1. Convert root metadata to non-distribution workspace orchestration.
2. Add member project/build metadata and package README.
3. Move runtime sources and static data with `git mv`.
4. Move the build hook to the member and update SCM formatter ownership.
5. Update import discovery, source fallback, type paths, and root tool data paths.
6. Regenerate the root workspace lock with the pinned PDM.

The intermediate checkout need not be runnable between individual file moves; the
batch must finish with install, import, schema, and focused catalog/resource tests
working.

### 2. Make member artifacts self-contained

1. Refactor catalog projection inputs so no function invents a monolithic root.
2. Implement checkout/sdist input selection in the member hook.
3. Add exact Corpus/build-support mappings to the sdist and derived Corpus/catalog
   mappings to the wheel.
4. Prove static migrations/output schemas are included by member package data
   ownership, not by accidental checkout discovery.
5. Build a wheel from the checkout and a second wheel from an extracted sdist in a
   repository-external directory.
6. Compare their installed payload path-by-path and byte-by-byte, allowing only
   ordinary archive metadata differences outside installed file content.

This stage must pass before moving tests, because otherwise test-path churn would
obscure a packaging failure.

### 3. Split tests by owner

1. Keep the four root/tool modules in `tests/`.
2. Move every CLI-owned module and both support modules to `svc_cli/tests/`.
3. Replace `tests.*` support imports with `svc_cli_test_support.*`.
4. Replace subprocess cwd guesses with explicit behavior-owned paths.
5. Update root test/lint/type orchestration and confirm the split remains exactly
   25 root cases plus 133 member cases before any independent test simplification.
6. Run each suite independently and then together to expose hidden collection or
   import coupling.

### 4. Update repository integration and documentation

1. Pin the validated PDM 2.28+ version in CI/publish jobs.
2. Keep install/lock commands at root; target member builds and publication.
3. Update schema/release comparison paths while retaining access to pre-move Git
   paths.
4. Update README and AGENTS ownership/commands.
5. Search outside `tasks/`, `.venv/`, and generated `build/` for every stale source,
   test, data, hook, and build path.

### 5. Run full verification and real acceptance

Run the complete matrix below. Any behavior or artifact mismatch is fixed at its
owner before the task is considered implementation-complete. Do not add a test
that merely snapshots the new layout to make the mismatch disappear.

## Mental Rehearsal and Failure Handling

| Failure mode | Expected symptom | Planned resolution/proof |
| --- | --- | --- |
| PDM 2.27 parses the repository | Unknown workspace behavior or member omitted | Pin and verify one 2.28+ version before metadata changes |
| Experimental workspace behavior changes | Lock/install/build differs locally and in CI | Exact CI pin plus repository-external spike; stop for review rather than wrap PDM |
| Member-relative artifact destination is mistaken for root-relative | CI writes under `svc_cli/release` and later upload finds nothing | Use an explicit `../release/...` member-relative destination and verify the uploader's exact path |
| Root still acts as a distribution | `pdm build` emits a bogus workspace package or discovers root `src/` | Root `distribution=false`, no root build backend; build only with `-p svc_cli` |
| Member is not installed into root environment | `pdm run svc` or root tools cannot import runtime | Assert editable member in root lock/environment and smoke from root |
| Nested SCM lookup loses Git root | Candidate version becomes `0.0.0` or differs from baseline | Verify checkout wheel and sdist metadata, including `PDM_BUILD_SCM_VERSION` workflow |
| Member README points outside sdist | Isolated metadata/build failure | Use member-local packaging README |
| Src-layout package discovery is wrong | Empty/namespace wheel or imports from checkout | Inspect wheel inventory and import from repository-external site-packages |
| Outer `svc_cli/` shadows inner package | Import resolves component namespace instead of runtime | No outer `__init__.py`; editable/install smoke from root and member-target build |
| Development fallback finds `svc_cli/src` as Corpus | `lookup` fails in editable checkout | Resolve validated workspace/staged Corpus candidates explicitly |
| Hook imports an already-installed old CLI | Catalog silently comes from the wrong implementation | Lazy input/import setup; isolated builds; compare catalog bytes with root projection |
| Sdist omits root Corpus | Extracted sdist wheel has no catalog/documents | Stage exact Corpus inputs and rebuild with the original checkout unavailable |
| Staged build inputs leak into wheel | Wheel contains `_build_inputs` or `tools` | Explicit wheel inventory rejection |
| Static data relies on checkout | migrations/schema discovery fails after install | Member-owned package data plus repository-external installed-wheel commands |
| Schema history gate loses pre-move baseline | A schema change evades major-fragment check | Compare current repository path and legacy pre-move path when reading Git refs |
| CLI tests use the component as cwd | subprocess configs/resources resolve differently | Explicit workspace root or Consumer cwd helper based on each test's semantic |
| Test helper becomes production code | runtime package contains test builders | Unique support package only under `svc_cli/tests`; reject it from wheel inventory |
| Root tool test is moved by import affinity | monolith/catalog ownership becomes unclear | Keep the four root modules and test the artifact boundary explicitly |
| Workspace lock contains stale root distribution | duplicate editable/project entries or wrong deps | Regenerate once after metadata split; inspect lock; frozen install in clean env |
| CI builds/publishes the workspace root | missing artifact or wrong name | Member-target every build/publish command and inspect artifact metadata before upload |
| Directory move captures user task changes | unrelated files appear in diff/commit | Use explicit `git mv` paths, inspect status before/after, exclude unrelated task trees |

## Verification Matrix

### Repository and static gates

```text
pdm install --frozen-lockfile -d -G quality -G test
pdm run test-root
pdm run test-cli
pdm run test
pdm run lint-tests
pdm run typecheck
pdm run lint-imports
pdm run check-cli-output-schemas
pdm run check-release-projections
pdm run check-documents
pdm run lint-workflows
pdm run build-monolith
pdm run svc --help
```

Required observations:

- root suite collects 25 cases;
- member suite collects 133 cases;
- combined suite collects 158 cases;
- nine output schema bytes and result-schema versions are unchanged;
- import contracts run against `svc_cli/src/svc_cli`;
- no stale executable source/test/data path remains outside historical task notes.

### Artifact gates

1. `pdm build -p svc_cli` produces only the existing
   `sustainable-vibe-coding` sdist and wheel family.
2. Inspect metadata for name, version, dependencies, Python requirement, README,
   and `svc` entry point.
3. Extract the sdist into a repository-external temporary directory.
4. Rebuild its wheel with the original checkout unavailable to the build process.
5. Compare direct and sdist-derived wheel installed paths and bytes.
6. Reject root tests, CLI tests, `_build_inputs`, repository tools, or canonical
   root `src` from either wheel.
7. Confirm the sdist contains all member sources and only the canonical Corpus
   build input needed for an independent rebuild.

### Installed-wheel gates

Install each candidate wheel into a separate repository-external virtual
environment and prove imports resolve from `site-packages`, then run:

```text
svc --help
svc lookup --path sections/working-protocol.md
svc lookup --pattern 'mutation gate'
svc status --json-schema
svc dev identity --json-schema
```

The direct and sdist-derived wheels must produce identical exit codes, stdout, and
stderr for this read-only matrix.

### Real Consumer differential acceptance

Use the baseline and candidate installed wheels, not the source checkout, against:

```text
/Volumes/WorkSSD/Development/InKCre/client-web
/Volumes/WorkSSD/Development/InKCre/core-py
/Volumes/WorkSSD/Development/InKCre/docs
/Volumes/WorkSSD/Development/sfp7-camera
/Volumes/WorkSSD/Development/Anana/mvp-HA
```

For each applicable root, compare exact exit code/stdout/stderr for read-only:

- `svc status <repo> --json`;
- `svc init <repo> --json` without `--apply`;
- `svc upgrade <repo> --json` without `--apply`;
- `svc dev identity --repo <repo> --json`.

Also compare plan digests where a plan is returned. Do not run `init --apply`,
`upgrade --apply`, `dev ensure`, `dev stop`, or `run` against these projects.

Finally, use the available WSL host (`wsl.win-ws.localhost` or the confirmed SSH
alias) for a clean workspace install/build/test and repository-external wheel smoke.
That is a real cross-platform build acceptance, not a temporary Consumer fixture.

## Completion Criteria

Implementation is ready for review only when all of the following are true:

- filesystem ownership matches the target topology;
- PDM root/member commands and the one-lock contract work from a clean environment;
- only the member can produce/publish `sustainable-vibe-coding`;
- direct and sdist-derived wheels are semantically identical and independently
  installable;
- root and member test ownership is exact, with no test-count drift attributable to
  the move;
- source checkout, installed wheel, and real Consumer read-only behavior match the
  baseline;
- documentation and workflows name the new paths/commands accurately;
- unrelated working-tree changes remain untouched;
- no commit is created without explicit authority.
