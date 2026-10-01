# Versioned Consumption

> Historical design: this consumer-copy and executable-migration model was superseded before v10 publication by [`../20-embedded-runtime-cli/packet.md`](../20-embedded-runtime-cli/packet.md). It remains task-local decision history only and must not be used as current implementation guidance.

## Outcome

Replace manual document copying with a version-addressable SVC distribution, explicit file authority, observable installed state, and safe executable migrations.

This design was implemented locally, then deliberately replaced before publication. Durable current behavior lives in the embedded-runtime CLI, release metadata, consumer contract, package configuration, and tests; this file remains task-local context only.

## Confirmed Decisions

- Ship SVC as an installable, version-addressable Python CLI distribution and unify the framework and package version authority at `10.x`.
- Ship a canonical release manifest with each distribution.
- Store consumer installation evidence in Generated `.svc/state.json`; do not mix it into the upstream release authority.
- Require apply to bind to an approved plan digest.
- Initially support migration from the formally released `9.8.0`; do not treat the current Unreleased state as a stable source version.
- Keep downgrade, plugins, heuristic merge, automatic adoption of unknown files, and outbound telemetry out of the first slice.
- Do not use sub-agents for this task.

## File Authority

| Class | Meaning | Initialization | Upgrade behavior |
| --- | --- | --- | --- |
| SVC-managed | Exact projection of a versioned upstream artifact; upstream remains authoritative. | Materialize the declared artifact. | Replace only when current content matches the recorded installed digest. Local drift is a blocking conflict. |
| Consumer-owned | Consumer truth, including instances seeded from SVC templates. Template provenance does not retain write authority. | Create from a template only when absent. | Validate or advise, but never overwrite. |
| Generated | Reproducible projection with a named generator and authoritative inputs; never a truth owner. | Generate explicitly and record provenance. | Rebuild through its generator, disclose the operation in the plan, and verify the result. |

File class and install action are separate manifest concepts. Class must be declared by artifact identity rather than inferred from a target path.

The initial four consumer documents classify naturally as:

- SVC-managed: `docs/00-meta/working-protocol.md`, `docs/00-meta/implementation-taste.md`
- Consumer-owned: `AGENTS.md`, `docs/10-prd/README.md`
- Generated control state: `.svc/state.json`

Task packets remain volatile consumer work and are not release-manifest artifacts. Optional extensions may combine an SVC-managed protocol document with separate Consumer-owned enablement or project truth.

## Release Manifest and Installed State

One mutable file cannot safely own both upstream release truth and downstream installation history.

The canonical release manifest is shipped inside the versioned distribution and declares at least:

- manifest schema version and SVC version
- stable artifact identity
- source payload and default consumer target
- file class and initialization/upgrade action
- content digest or generator identity
- optional feature or admission metadata
- release behavioral-impact declaration

Generated `.svc/state.json` records at least:

- installed SVC version and release identity
- installed target-to-artifact mapping and managed digests
- applied migration IDs
- last applied plan digest and final verification result

The release manifest is authority. Consumer state is replaceable evidence about one installation. A separate Consumer-owned configuration file is admitted only when a real consumer choice cannot be represented as a CLI input or existing project truth.

## Minimal CLI Contract

- `svc status <repo>` reports installed and target versions, missing artifacts, drift, conflicts, and unknown state; deterministic JSON is part of the machine contract.
- `svc init <repo>` emits a plan by default and creates a new installation only when given the matching plan digest for apply.
- `svc migrate <repo> --to <version>` resolves registered adjacent migrations, emits a plan by default, and applies only the exact matching plan digest.

The plan digest covers the source snapshot relevant to preconditions, target release identity, ordered migration IDs, operations, and expected postconditions. Any intervening relevant change makes the plan stale and causes zero writes.

A repository-local PDM command is a development entry, not the distribution mechanism. The installed distribution must bundle its matching managed payloads, manifest, schema support, and migration registry.

## Migration State Machine

```text
inspect -> plan -> approve digest -> revalidate -> stage -> verify staged tree
        -> commit with journal -> verify committed tree -> record state
```

Failure before commit produces zero writes. Failure during commit restores the complete pre-run tree from the journal and reports the rollback result.

Migration invariants:

- Resolve and validate the full adjacent sequence before the first write; never skip an intermediate migration.
- Evaluate step preconditions against an immutable snapshot.
- Make every create, update, delete, no-op, drift, conflict, and state write explicit in the plan.
- Run the full migration and all postconditions in a shadow tree before committing.
- Treat repeated apply of a completed migration as a verified no-op.
- Block on managed drift, missing provenance, unknown source version, stale plan, or failed pre/postcondition.
- Keep Changelog prose as release communication rather than executable migration authority.

`rollback-safe` means automatic restoration after an apply failure. It does not imply a downgrade command after a successful migration.

## SVC Behavioral SemVer

Classification applies to the declared consumer protocol, not accidental faulty behavior:

- **MAJOR**: changes a required obligation, default behavior, authority or permission boundary, task-packet semantics, required consumer layout, stable CLI or manifest machine contract, or removes a supported capability
- **MINOR**: adds an optional backward-compatible capability or expands accepted inputs without changing existing obligations or defaults
- **PATCH**: clarifies the contract or fixes implementation to satisfy it without changing consumer obligations, defaults, authority, required layout, or stable machine contracts

An optional additive layout may be MINOR. A fix may change observed buggy behavior and remain PATCH when it restores an already-declared contract. Each release declares its behavioral impact; automation validates that the declared category is compatible with the version bump, while review remains responsible for classification truth.

## Measurement Contract

The first slice produces deterministic local evidence rather than outbound telemetry:

- installed, source, and target versions
- identities and counts for planned creates, updates, deletes, no-ops, drift, and conflicts
- migration, precondition, postcondition, commit, rollback, and final verification results
- stable exit codes and deterministic JSON
- managed-file digest agreement after verification

## Required Fixture Proof

- dry-run leaves the consumer tree byte-for-byte unchanged
- clean initialization and migration from `9.8.0`
- exact plan-digest apply and stale-plan refusal
- adjacent sequential execution with no skipped step
- repeated apply is a verified no-op
- managed drift blocks with zero writes
- Consumer-owned content is preserved
- Generated output is reproducible
- precondition and staged postcondition failures produce zero writes
- injected commit failure restores the complete pre-run tree
- manifest inventory, migration graph, JSON schema, exit codes, and behavioral-impact declaration satisfy contract tests

## Implementation Gate

The user explicitly approved implementation. The Impact Handshake covered packaging/version authority, release manifest, CLI and migration engine, consumer contract documentation, tests/fixtures, and Changelog. See [`verification.md`](verification.md) for the resulting surfaces and proof.
