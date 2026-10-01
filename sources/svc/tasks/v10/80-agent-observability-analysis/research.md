# Design Evidence

Research snapshot: 2026-07-28. These projects and libraries are design inputs,
not SVC product or implementation authorities.

## Letta Trajectory

Primary sources:

- [letta-ai/trajectory](https://github.com/letta-ai/trajectory)
- [Trajectory product rationale](https://www.letta.com/blog/trajectory/)

Relevant evidence:

- discovery and normalization are separate responsibilities
- a small normalized stream is more useful for Agent analysis than provider
  envelopes
- the trajectory vocabulary includes leading metadata, user/assistant steps,
  reasoning when available, tool calls, and tool results
- stable tool linkage and bounded records matter for downstream evaluation
- harness/UI noise, injected bookkeeping, and oversized tool payloads can be
  removed while reporting diagnostics

SVC should adopt the analysis-oriented semantics, explicit loss reporting, and
small provider-neutral stream. It should own and document its own schema because
the direct bridge/runtime and privacy/path defaults do not match SVC's
Python-first packaged runtime and local safety contract.

## ccxray

Primary sources:

- [ccxray repository](https://github.com/lis186/ccxray)
- [ccxray v2.2.0 tree](https://github.com/lis186/ccxray/tree/v2.2.0)
- [normalized data model](https://raw.githubusercontent.com/lis186/ccxray/main/docs/data-model.md)
- [Agent-facing usage schema](https://raw.githubusercontent.com/lis186/ccxray/v2.1.0/docs/usage.md)
- [package metadata](https://raw.githubusercontent.com/lis186/ccxray/v2.2.0/package.json)
- [license](https://raw.githubusercontent.com/lis186/ccxray/v2.2.0/LICENSE)

As researched, the installable/tagged version is 2.2.0, requires Node.js 18 or
later, and is governed by PolyForm Noncommercial 1.0.0.

ccxray is a transparent Claude/Codex HTTP/WebSocket proxy with a real-time local
browser dashboard. It retains full request/response JSON, writes a thin
`index.ndjson`, streams updates, normalizes provider metadata, and presents
workflow timelines, turn cards, parallel lanes, birdseye navigation, and
prompt/tool differences. Its compact `usage --json` surface is intended for
Agent consumption; it is not a general stable thread-export contract.

Ideas worth adapting:

- thin canonical index plus lazy detail
- provider-parser boundary
- project/session hierarchy
- parent/concurrency metadata
- chronological and birdseye navigation
- compact stable Agent-facing JSON
- retention and sensitivity markers
- isolated synthetic fixtures

Boundaries not to import into the initial SVC capability:

- transparent interception or request-editing authority
- a Node/browser-server runtime dependency
- OAuth, upstream credentials, or provider-account integration
- raw payload retention as the normal analysis source
- pricing and wire-protocol heuristics as SVC core truth
- ccxray code under its noncommercial license

Its credential flags classify risk; they do not redact captured content. The
server can bind beyond loopback and relies on authentication for non-loopback
access, so its displayed localhost URL is not proof of a loopback-only boundary.
SVC should not inherit that topology accidentally.

ccxray's `sessionId` and `convId` are useful local workflow concepts but do not
define a stable cross-provider AgentThread identity.

## Terminal UI Candidates

Primary sources:

- [Textual Tree](https://textual.textualize.io/widgets/tree/)
- [Textual testing guide](https://textual.textualize.io/guide/testing/)
- [Rich Tree](https://rich.readthedocs.io/en/stable/tree.html)
- [prompt_toolkit documentation](https://python-prompt-toolkit.readthedocs.io/en/stable/)

Current assessment:

- Textual 8.2.8 was released on 2026-06-30 and declares Python `>=3.9,<4` plus
  Windows 10/11, macOS, and POSIX Linux support. Its Tree and headless
  `App.run_test()`/Pilot APIs directly address navigation and verification.
- Rich is useful for non-interactive tree rendering but does not by itself own
  an interactive application state model.
- prompt_toolkit is capable but would require more task-specific tree behavior
  and testing structure.

Slice 0 freezes Textual `>=8.2.8,<9` without syntax or `textual-dev` extras as
the v1 selector and human-analysis runtime. It is a normal runtime dependency
because a fresh installed wheel must support `analyze` without a separate
developer setup. Safe `list` and all JSON paths remain render-neutral and must
not import or instantiate Textual.

## Evidence Limits

- External project behavior and versions may change; the dependency range above
  is the reviewed Slice 0 snapshot and must be rechecked at implementation and
  release time.
- The eight SVC field-study cases are private validation material, not public
  research evidence.
- Design similarity is not evidence that ccxray or Letta identifiers, schemas,
  privacy assumptions, or runtime topology are valid SVC contracts.
