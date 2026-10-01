# Verification Plan

## Executed Evidence

- `pdm run test` passes 50 unit and fixture tests, including exact-plan dry-run/apply/no-op behavior, generated-surface drift refusal, stale-plan refusal, injected commit and postcondition rollback, and rollback conflict preservation.
- `pdm run build-monolith`, `pdm run release check --json`, `pdm run python -m compileall -q svc_cli tools`, and a Towncrier draft all pass.
- A fresh virtual environment installs the built wheel outside the source tree, performs path-regex lookup, applies `init`, reports healthy `status`, and produces a ready but unapplied self-update plan.
- Rebuilding a wheel from the produced sdist yields byte-identical `svc_cli/data` catalog and corpus payloads.

## Foundation

- Package build produces a catalog plus corpus projection from canonical SVC source and ships both in the wheel. The sdist contains canonical `src/` plus the builder needed to reproduce exactly that wheel payload.
- `src/` contains no Python runtime or build-tool code; `svc_cli/` and `tools/` contain no canonical SVC documentation authority.
- Installed `svc lookup --name` returns the expected immutable entry with stable machine-readable identity.
- Keyword results are deterministic, ranked, and contain only packaged corpus data.
- `lookup` causes no writes and no network use in all base modes.
- `svc init` dry-run is byte-stable; explicit apply creates only `svc.json`, the Codex skill, root/document navigation anchors, and their declared parent directories.
- Existing user files, unmarked text, and edited marked blocks are never silently overwritten.
- A second successful init is a verified no-op.
- `svc.json` schema and installed/adopted version distinction are validated.
- The Codex skill at `.agents/skills/svc/SKILL.md` explains SVC's operating model and CLI when-to/know-how, points to CLI lookup, and does not duplicate framework Markdown.

## Future Semantic Capability

- Lookup query/result contracts are independently tested before any semantic backend is added.
- A future semantic backend must prove model/provider provenance, deterministic fixture results, and zero hidden network use.

## Busybox Commands

- Each command has a JSON output schema, exit-code contract, precondition tests, and idempotence test where it writes.
- Thread export fixtures prove source parsing, redaction, provenance, and no outbound transmission.
- Task helpers preserve the five-field task control surface and do not create a competing task-state authority.
- Dev-server fixtures prove healthy-process reuse, explicit command execution, failed readiness rollback, and no duplicate process.

## Removal and Release Proof

- No packaged or consumer-facing claim remains that `svc init` installs SVC-managed framework documents.
- The old manifest artifact classes, `.svc/state.json` provenance model, migration graph, and related fixtures are removed or replaced in one coherent slice.
- Documentation, `CONTRIBUTING.md`, release planner, changelog fragment, and workflows match the new Behavioral SemVer contract.
- Full test suite, monolith build, package build, clean wheel install, and end-to-end init/lookup smoke test pass.
