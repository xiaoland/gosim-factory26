# Versioned Consumption

- **Objective**: Replace manual document copying with a reliably distributable, version-addressable SVC CLI, explicit artifact authority, safe executable migrations, and a reviewable release protocol from change fragment through GitHub Release and Python installation.
- **Guardrails**:
  - Keep the distribution name `sustainable-vibe-coding`, executable `svc`, and Python import namespace distinct; rename the package to `svc_cli`, not generic `cli`.
  - Keep GitHub Releases as the canonical release record and PyPI as the pip-compatible installation registry. Do not represent GitHub Packages as a PyPI registry.
  - Defer GHCR until a real OCI or container consumer justifies the additional artifact, permissions, and verification surface.
  - Towncrier fragments declare release impact; commit messages improve history navigation but never determine Behavioral SemVer.
  - Build release artifacts once and promote the exact same wheel/sdist and digests across attestation, GitHub Release, and PyPI.
  - Keep publication protected, idempotent, provenance-bearing, and separately authorized. Do not create a branch, tag, release, registry package, GitHub App, or external environment without explicit authority.
  - Do not use sub-agents for this task.
- **Verification**:
  - Existing manifest/state/migration fixtures remain green after the package rename.
  - Contribution checks prove valid commit examples, Towncrier fragment policy, maximum-impact version calculation, migration obligations, and release-plan consistency.
  - Pull-request CI tests supported Python versions, builds the distribution, installs the wheel in a clean environment, and exercises init/status/migrate.
  - Release automation creates or updates one reviewable Release PR, synchronizes version/manifest/Changelog/lock state, and consumes only included fragments.
  - A protected publish dry-run proves one-build promotion, artifact hashes, attestation inputs, tag/version agreement, GitHub Release assets, PyPI Trusted Publishing configuration, retry/idempotency, and zero GHCR publication.
- **Current Truth**:
  - This packet's original consumer-copy and executable-migration design was superseded before v10 publication by [`../20-embedded-runtime-cli/packet.md`](../20-embedded-runtime-cli/packet.md). Its detailed design and verification files are historical context, not current implementation guidance.
  - The current Python package is root `svc_cli/` with console entry `svc_cli.cli:main`; the distribution and executable remain `sustainable-vibe-coding` and `svc`.
  - Distribution is named `sustainable-vibe-coding`; the short PyPI project name `svc` is already owned by another project.
  - GitHub Packages does not provide a pip-compatible PyPI registry. The approved topology remains GitHub Releases for canonical release assets plus PyPI for normal Python installation.
  - CI, Release PR, and protected publish workflows exist under `.github/workflows/`; their smoke and release checks now target the embedded corpus/runtime model. No Git tag, branch, GitHub Release, or Python distribution was created or published.
  - Towncrier fragments, the repository release planner, and `CONTRIBUTING.md` own change declaration, Behavioral SemVer calculation, staged/published MAJOR migration guidance, and contribution guidance.
  - The detailed external release prerequisites remain in [`release-plan.md`](release-plan.md), subject to the supersession notice at its top.
- **Next Step**: Keep this control surface only while v10 remains active; use the embedded-runtime packet for current work. External GitHub/PyPI configuration and first publication remain a separate, explicitly authorized slice.

## Supporting Material

- Protocol design: [`design.md`](design.md)
- Existing implementation proof: [`verification.md`](verification.md)
- Distribution and release plan: [`release-plan.md`](release-plan.md)
