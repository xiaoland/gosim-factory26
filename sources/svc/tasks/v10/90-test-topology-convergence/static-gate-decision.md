# Static-Gate Decision

## Implemented Gates

The hard cut uses mature tools directly. It adds no local parser, source scan,
or wrapper script.

| Claim owner | Tool and local command | CI owner | Dynamic proof intentionally retained |
| --- | --- | --- | --- |
| `navigation` has no direct provider, UI, or filesystem dependency | `pdm run lint-imports` → Import Linter forbidden contract | `typecheck` job on Python 3.11 | lexical workspace behavior, inventory bounds, stale generation, and TUI interaction |
| GitHub Actions are hash-pinned and avoid workflow security regressions | `pdm run lint-workflows` → `zizmor --offline .github/workflows` | same `typecheck` job | project-specific release/tag/build choreography |

Both tools are bounded, development-only `quality` dependencies in the PDM
lock. They never enter wheel metadata.

## Import Boundary

The configured contract has one authority: direct imports from
`svc_cli.telemetry.navigation` may not reach `svc_cli.telemetry.providers`,
`textual`, `rich`, `os`, or `pathlib`. Indirect imports stay allowed because
the navigation model intentionally consumes `agent_threads`, which has its own
data responsibilities.

This replaces the removed AST/source-string navigation test. A temporary
`import os` probe broke the actual contract before it was discarded.

## Workflow Security

zizmor replaces the removed regex-based action-SHA test with a broader,
offline-capable policy. The implementation trial exposed two high-confidence
template-injection findings in CI: `github.base_ref` was expanded directly in
a shell command. CI now passes it through `BASE_REF` and uses normal shell
variable expansion. Read-only checkouts set `persist-credentials: false`.

Release PR and Release Tag deliberately persist the built-in token because
they push a branch or immutable tag. Each has a narrow, explanatory zizmor
ignore attached to that checkout; the scanner otherwise reports no findings.
A temporary `actions/checkout@main` probe produced zizmor's high-confidence
`unpinned-uses` error before it was discarded.

## Boundaries Not Claimed

Pydantic, mypy, Ruff, Import Linter, and zizmor do not prove data redaction,
SQL projection, file descriptor identity, ZIP publication, installed-wheel
isolation, or Textual keyboard behavior. Those remain dynamic test evidence.
