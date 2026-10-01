# Decisions Needed

## Resolved: Skill Provider Boundary

Decision: the first provider is Codex only, through explicit `svc init --agent codex`. The installed skill is a substantial operational guide to SVC and the CLI, but it does not copy SVC's canonical lookup corpus. Its repository target is `.agents/skills/svc/SKILL.md`.

Evidence: Codex's documented repository scope scans `.agents/skills` from the current working directory to the repository root. `SKILL.md` requires `name` and `description` metadata. The source is [Build skills](https://learn.chatgpt.com/docs/build-skills).

## Deferred: Semantic Lookup Contract

Exact path-regex lookup and local keyword search are straightforward and dependency-free. Genuine semantic search needs a query encoder in the same vector space as the prebuilt document vectors; a static index file alone is insufficient.

Decision: semantic lookup is not in the first implementation slice. Preserve an internal lookup query/result boundary so it can be added later without a public-command or caller rewrite.

When resumed, benchmark a packaged static-embedding model plus an exact, quantized corpus-vector file. For SVC's small corpus, avoid HNSW/vector-database complexity unless measurements disprove linear cosine search. The semantic pack may be a separately installed/versioned local artifact, but must never download implicitly or send query data remotely.

## Resolved: Project Adoption after Self-update

Decision: `svc self-update` changes only the executable. `svc adopt` records the installed version in `svc.json` after the user/Coding Agent has applied the release's lookup migration guide.

This preserves consumer-owned migration judgment.

## Resolved: First Busybox Delivery Scope

Decision: the first slice includes lookup/init/status, the Codex skill, self-update, and explicit project adoption. Thread export, task collaboration, and dev-server assurance remain later slices.

Decision: the first `self-update` adapter is the current interpreter's non-editable pip installation only. It plans `sys.executable -m pip install --upgrade sustainable-vibe-coding` and runs it only after exact-plan approval. Unsupported installers and editable development installs are reported without mutation; additional adapters require their own evidence and tests.

## Deferred: Agent-thread Evidence Format

Recommendation: emit a local JSONL/JSON record with source adapter, timestamps, task reference, explicit redaction result, and original-file hash; no automatic upload or collection endpoint.

Needed decision: which agent transcript format should the first adapter support, and should export preserve raw text locally or require redaction-only output?

## Resolved: `docs/index.md` Creation Policy

Decision: `svc init` creates `docs/index.md` by default when absent. The file becomes Consumer-owned immediately; only the bounded marked SVC navigation block has generated provenance.
