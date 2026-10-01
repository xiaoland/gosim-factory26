# Braid Project Instructions

This source directory implements Braid Local: local Issue and pull-request state
become the durable working memory of Coding Agents. Factory26 tracks this directory
in its parent Git repository. Apply these additional instructions only under
`sources/braid`; do not modify user-scope Agent instructions.

<!-- svc:begin navigation sha256=48c8d7b497ed094589c4a192f3ef97450fd7f614712dc1b4b22e9a20578360cd -->
## SVC

Use the installed `svc` CLI when SVC guidance or project integration is relevant. Discover the current interface through `svc --help` and `svc <command> --help`; `svc lookup` reads the SVC Corpus, not CLI help. Treat unmarked project instructions and documentation as Consumer-owned.
<!-- svc:end navigation -->

## Knowledge Owners

- Product purpose, promises, workflows, and scope:
  `docs/10-prd/README.md`
- Real product acceptance oracle: `docs/10-prd/acceptance.md`
- Cross-unit authority, Rust architecture, and durable state:
  `docs/20-product-tdd/README.md`
- Context projection: `docs/20-product-tdd/context.md`
- Event and session state machines: `docs/20-product-tdd/lifecycle.md`
- Provider/Codex contract: `docs/20-product-tdd/app-server.md`
- GitHub contract: `docs/20-product-tdd/github.md`
- Distribution, observability, migration, and operation:
  `docs/40-deployment/README.md`
- Project vocabulary: `docs/10-prd/glossary.md`
- Volatile task control: `tasks/`; retain at most one active packet and delete
  it when the task closes after promoting binding truth.

## Local Working Memory Protocol

Current authority is `docs/20-product-tdd/local.md`. Issue/PR/comment state lives in the local SQLite object store; no GitHub App, webhook, remote PR, or Markdown stage mirror is required. Preserve the projector, queue/group/session and independent-clone boundaries. The run's bare origin owns published refs; each work item owns a local clone. Agent CLI commands obtain their run location and write identity from the active native execution; `--external` is reserved for explicit host input. Local runtime results describe execution state and the current delivery ref, not whether an application meets caller requirements.

## Repository Workflow

- The clean Rust runtime replaces the obsolete Python prototype; do not carry
  old turn-mirror abstractions, schemas, or compatibility aliases into Rust.
- Runtime: Rust 1.93+ for the first implementation; commit `Cargo.lock`.
- Prefer readable deep modules aligned with the Product TDD owners. Do not pass
  `serde_json::Value` across internal boundaries when a typed enum/struct owns
  the contract.
- Object writes and semantic events share SQLite transactions. Git ref mutation uses a durable merge intent because Git and SQLite cannot share one transaction. Migrations are
  embedded, forward-only, checksum-verified, and immutable after release.
- Preserve complete sampled operational evidence. Sampling controls volume,
  not secrecy; treat configured telemetry as sensitive runtime data.
- Compile and static checks cover source integrity. Braid does not maintain or run tests; application-specific acceptance belongs to the caller.
- The Agent may make coherent verified commits in this repository without
  per-commit approval. Pushes, releases, external GitHub mutations, and changes
  outside this repository retain their own authority gates.
