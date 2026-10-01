# Acceptance Plan

## Portable Baseline

Create a scrubbed Codex source fixture that represents all required record classes:
user/assistant messages, reasoning, tool calls, tool results, status metadata,
unknown future fields, Unicode, large values, and `tasks/...` references. Each
host runs the installed wheel against this fixture and asserts the ZIP manifest,
hashes, record ordering, task-packet provenance, collision refusal, and no source
or repository writes.

## Host Matrix

| Host | Access | Required acceptance | Optional live-source check |
| --- | --- | --- | --- |
| macOS | local workspace | installed-wheel fixture export | consented local Codex App/extension data only after source adapter evidence exists |
| Windows | `ssh win-ws.localhost` | installed-wheel fixture export on native Windows paths | only if an eligible Codex source is present |
| Linux | `ssh wsl.win-ws.localhost` | installed-wheel fixture export on Linux paths | only if an eligible Codex source is present |

## Safety Checks

- Use a newly created temporary output directory and an absent ZIP destination.
- Verify that an existing ZIP is refused without changing its bytes.
- Verify that source fixture and the repository task packet stay byte-identical.
- Inspect only archive structure, hashes, field-presence metadata, and controlled
  fixture content; never copy real conversation data into test logs or this task
  packet.
- If a real source is used, perform only metadata discovery until the user
  explicitly approves export of that particular private thread.

## Result (2026-07-16)

The portable fixture ran from a freshly installed wheel and exercised metadata
listing, exact state-DB selection, raw JSONL retention, opaque reasoning,
tool calls/results, Unicode task references, nested packet copies, private output,
and repeated-output refusal. It used no real conversation data and no Codex CLI.

| Host | Python | Result |
| --- | --- | --- |
| macOS | 3.12.10 | accepted; 2,658-byte ZIP |
| Windows (`ssh win-ws.localhost`) | 3.14.0 | accepted; 2,653-byte ZIP |
| Linux (`ssh wsl.win-ws.localhost`) | 3.13.5 | accepted; 2,658-byte ZIP |

The locally built acceptance wheel still carries the staged package metadata
`10.0.0`; `pdm run release check-ci --json` resolves the pending release as
`10.0.1` under the existing one-time version exception. Release preparation is
deliberately outside this sub-task's implementation mutation.

## Release-Hardening Regression (2026-07-16)

GitHub Linux CI exposed immediate inode reuse after a published archive was
unlinked and replaced. The archive now compares device, inode, file type, size,
and mtime rather than only the first three fields; it deliberately excludes
ctime because Windows can change it during read-only inspection.

- macOS: the local archive suite passed under the workspace interpreter.
- Windows (`ssh win-ws.localhost`, Python 3.14.0): a newly installed wheel
  rejected the replacement with `archive-output-mutated` and preserved the
  untrusted replacement for inspection.
- Linux (`ssh wsl.win-ws.localhost`, Python 3.13.5): the same freshly installed
  wheel regression passed.

Both remote temporary installation directories were removed after validation.
