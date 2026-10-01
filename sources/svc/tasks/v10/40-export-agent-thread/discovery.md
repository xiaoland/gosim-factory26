# Codex Source Discovery Matrix

This ledger records verified local reconnaissance as of 2026-07-15. It does not
authorize reading, logging, or committing real conversation content.

| Surface | macOS evidence | Windows evidence | Linux evidence | Initial treatment |
| --- | --- | --- | --- | --- |
| Codex home | App's active `app-server` has open `~/.codex/sessions/.../rollout-*.jsonl`; `state_5.sqlite` has a `threads` table | `C:\Users\yyh\.codex` exists even though no `codex` is on PATH and Codex App is installed | `~/.codex` exists with sessions and archived sessions | Support only a validated explicit rollout source or exact state-DB mapping; do not infer a front end from container presence. |
| Rollout JSONL | Outer envelopes use `timestamp`, `type`, `payload`; observed payloads include message, reasoning, function/custom-tool calls and outputs | Candidate JSONL containers observed, contents intentionally not read | Candidate JSONL containers observed, contents intentionally not read | `rollout-v1` fixture contract; preserve unknown fields and opaque encrypted reasoning. |
| `state_5.sqlite` | `threads` has ID, rollout path, archive/source/model/cwd/title metadata; WAL/SHM may be active | Large data store present but schema/content uninspected | Candidate store present | Read-only exact-ID locator after table-signature validation; never export its full database or WAL. |
| VS Code storage | `openai.chatgpt` extension is an app-server client; generic `chatSessions/*.jsonl` cache is not canonical | Official extension present; global storage lacks an independently verified canonical transcript | Windows extension is visible through mount; no Linux-side extension store | Never scrape workspaceStorage/state.vscdb as a thread source. |
| Codex runtime | App bundle contains a runtime and exposes app-server protocol | no PATH CLI | standalone CLI installed | No runtime requirement in rollout-v1. A future app-server adapter requires a separate contract. |

## Discovery Principles

1. Resolve `$CODEX_HOME`, otherwise `Path.home() / ".codex"`; accept an explicit
   home/source override. Do not recursively scan unrelated homes or scrape editor
   databases.
2. Treat every OS storage root as a candidate container. Metadata listing validates
   the state-table signature and source-path safety without reading transcript
   bodies; exact export validates the rollout signature before capture.
3. Keep discovery output to IDs, timestamps, source state, and redacted location
   metadata. Never log message text, tool arguments, tokens, reasoning, or titles.
4. Fixture adapters are the cross-platform contract. Live local state is an
   opt-in acceptance input, never a test prerequisite.
5. The App/extension share an app-server/Codex-home architecture on the examined
   macOS system, but the exporter promises only a validated local source—not a
   private Electron/VS Code storage format or cloud history recovery.
