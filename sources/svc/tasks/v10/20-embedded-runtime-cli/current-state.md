# Current State

## Implemented Outcome

The embedded-runtime foundation is now implemented and verified. `src/` contains only canonical SVC Markdown and release metadata; root `svc_cli/` contains the runtime and root `tools/` contains repository tooling. The wheel ships a deterministic catalog plus one read-only corpus projection, while the sdist carries the canonical source and builder necessary to recreate it.

The public foundation is `lookup`, `init`, `status`, `adopt`, and `self-update`. Consumer repositories receive only `svc.json`, the Codex operational skill, and marked navigation anchors. The old consumer-copy authority model is gone: SVC guidance is queried from the installed corpus, and Consumer-owned migration judgment remains with the project.

## Pre-Pivot Baseline (Superseded)

The committed v10 implementation has this topology:

```text
canonical src Markdown + templates
    -> wheel payload + src/manifest.json
    -> svc init / svc migrate
    -> consumer copies of SVC-managed documents
    -> .svc/state.json provenance and migration journal
```

The present manifest classifies `working-protocol.md` and `implementation-taste.md` as SVC-managed consumer files. `AGENTS.md` and product truth are Consumer-owned; `.svc/state.json` is Generated. `svc init`, `svc status`, and `svc migrate` enforce that model transactionally.

The package-resource layer already resolves payloads from the installed wheel first and the source tree while developing. This can become the read-only SVC corpus boundary.

## Repository Boundary Problem

Before this slice, `src/` contained both the canonical SVC corpus and Python implementation directories (`src/svc_cli/`, `src/tools/`). That was an accidental collision between two meanings of `src`: framework source and Python source-layout.

The approved target makes the filesystem itself express authority:

```text
src/        canonical SVC corpus only
svc_cli/    Python import package and installed runtime
tools/      repository build, catalog, and monolith tooling
tests/      verification
```

This also makes every catalog path mechanically simple: it is the normalized path relative to `src/`, never a Python-package path.

## Why the Model Must Change

The new desired topology is not an incremental migration policy:

```text
canonical src Markdown
    -> versioned wheel corpus + catalog
    -> svc lookup
    -> Coding Agent reads guidance on demand

consumer repository
    -> svc.json adopted baseline
    -> provider-specific SVC skill + navigation anchors
    -> Consumer-owned project truth and task packets
```

No downstream SVC-managed document exists in the target topology. Therefore managed-document digest tracking, consumer copy replacement, and the associated migration graph would protect a contract that no longer exists.

## Historical Agent-Skill Evidence

Earlier revisions contained `.agents/skills/init-svc/SKILL.md` and a Codex-agent installer. The current framework explicitly removed them because they were stale, self-contained copies of framework content. Reintroducing a skill is appropriate only if it is a substantial operational guide whose authority remains `svc lookup`, not a copied framework corpus.

## Authority Map

| Fact or content | Proposed authority | Projection / consumer |
| --- | --- | --- |
| SVC guidance | Canonical `src/` content, released with the CLI | Read-only packaged catalog, `svc lookup` |
| Project-adopted SVC baseline | `./svc.json` | `svc status`, Coding Agent |
| Installed executable version | Package manager / installed distribution metadata | `svc --version`, `svc self-update` |
| Project-specific process commands and product truth | Consumer repository | `svc dev ensure` arguments; Coding Agent |
| Task collaboration state | Consumer task packet | `svc task` helpers |
| Exported agent evidence | Explicit local export file | Human review; future separately-authorized collection flow |
