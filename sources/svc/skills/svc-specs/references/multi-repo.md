# Multi-Repo Extension

Mono-repo is the default. Use this extension only when one product spans repositories, shared truth would otherwise be duplicated or drift, and the team can enforce freshness mechanically.

## Contract

Use one authoritative shared source and nearby read-only consumption in each code repository.

- **Hub**: shared product truth, cross-unit contracts, and any genuinely shared protocol extensions.
- **Spoke**: local code, unit design, Deployment, local instructions, and local task state.
- **Shared mount**: a deterministic reference inside each Spoke, such as `docs/_shared/`.

A Git submodule is a valid default transport. Another mechanism is acceptable only when it preserves one upstream authority, nearby access, default read-only consumption, and machine-verifiable freshness.

## Read and Mutation Rules

In a Spoke, read shared truth from the mounted reference and treat it as read-only during ordinary local execution.

When local work exposes a missing shared rule:

1. capture the local seam, missing shared claim, consequence, and return verification in the active Spoke task
2. confirm that another unit truly depends on the claim
3. update the Hub-owned source
4. update the Spoke shared reference in a separate change
5. resume and verify the local work

Do not mix Hub edits, Spoke reference bumps, and Spoke-local code changes in one commit. Automation should report stale shared references; freshness must not depend on memory.

Shared versus local ownership follows the core registry. A cross-unit payload or authority contract may belong in Product TDD; one service's private storage design does not become shared merely because repositories are separate.

Use [the shared-doc edit template](../assets/edit-shared-docs.template.md) when this extension is active.
