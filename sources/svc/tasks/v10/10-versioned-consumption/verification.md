# Versioned Consumption Implementation Verification

> Historical verification: these results covered the superseded consumer-copy and migration engine. The current proof is [`../20-embedded-runtime-cli/verification.md`](../20-embedded-runtime-cli/verification.md).

## Implemented Surfaces

- Version and distribution authority: `pyproject.toml`, `pdm.lock`
- Canonical release inventory: `src/manifest.json`
- Source-first wheel projection: `pdm_build.py`
- CLI and protocol engine: `src/svc_cli/`
- v9.8 migration registry and fixture evidence: `src/svc_cli/migrations/`, `tests/fixtures/migrations/`, `tests/test_migrations.py`
- Manifest, Behavioral SemVer, CLI, state, and build contracts: `tests/test_manifest.py`, `tests/test_svc_cli.py`, `tests/test_framework_contract.py`
- Durable consumer and migration contract: `src/index.md`, `README.md`, `CHANGELOG.md`, root `AGENTS.md`
- Contribution and change declaration: `CONTRIBUTING.md`, `changes/`, Towncrier configuration in `pyproject.toml`
- Behavioral release planner: `src/tools/release.py`
- CI, Release PR, and protected publication contracts: `.github/workflows/`, `tests/test_release.py`, `tests/test_workflows.py`

## Verified Behavior

- Three file classes are manifest-declared and mechanically distinct.
- Initialization and migration are dry-run by default and bind apply to the exact current plan digest.
- Relevant repository state is checked before staging and again after staged postconditions.
- Consumer-owned files are byte-preserved; managed content without recognized provenance blocks.
- Migration resolves only the registered adjacent `9.8.0-to-10.0.0` step.
- Generated state records installed version, release digest, managed inventory, migrations, plan digest, and verification.
- Commit intent and backups persist under `.svc/transactions/`; exceptions roll back immediately and an interrupted transaction is recovered on the next CLI invocation.
- JSON output carries schema version, identities, operation/status counts, blockers, condition results, migration results, recovery result, and stable exit-code semantics.
- Behavioral impact `major` is mechanically validated against `9.8.0 -> 10.0.0`.
- Distribution/import/executable identities are separated as `sustainable-vibe-coding`, `svc_cli`, and `svc`.
- Release fragments compute the maximum Behavioral SemVer impact; prepared releases require synchronized version, manifest reasons, migration graph, Changelog, and no remaining fragments.
- GitHub and PyPI retry paths compare existing artifact bytes or SHA-256 digests and stop on partial or differing state.

## Verification Results

- `git diff --check`: passed
- `pdm run test`: 49 tests passed
- `pdm run release check-ci`: passed; calculated `9.8.0 -> 10.0.0` as MAJOR
- Towncrier draft render: passed
- Temporary-repository `release prepare`: passed; consumed the included fragment, rendered the 10.0.0 section, added its canonical GitHub Release link, synchronized manifest metadata, and produced a prepared state accepted by the verifier
- All GitHub Actions workflow YAML parsed successfully; every action reference is pinned to a full commit SHA
- `pdm run build-monolith`: passed; 18 canonical files included
- `pdm build`: sdist and `sustainable_vibe_coding-10.0.0-py3-none-any.whl` built successfully
- Clean virtual environment wheel install: passed
- Installed-wheel `svc init` plan/apply and healthy `svc status`: passed
- Installed-wheel prepared v9.8 plan/apply migration: passed

## Deliberate Boundary

The repository now defines the release protocol and builds a release artifact, but no package was published, no Git tag or GitHub Release was created, and no branch or commit was created. GitHub App installation, protected environment, Trusted Publisher, branch protection, and the first external publication remain outside the approved implementation slice.
