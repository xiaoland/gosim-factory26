# Installed-Wheel Acceptance

> Historical migration acceptance. The macOS 268-item result predates the
> later cost/value hard cut; the cross-host wheel behavior remains relevant
> because the hard cut changes test topology and development-only tooling, not
> shipped runtime behavior.

The locally built wheel
`sustainable_vibe_coding-11.0.0-py3-none-any.whl` had SHA-256
`805d0e07f22fa1f8bc0ec6cccb59c3045cfd9ff714e06c851a4b14ac2c0b3d33`.

| Host | Base Python | Slice | Result |
| --- | --- | --- | --- |
| macOS source authority | 3.12.10 | local full pytest/build gates | historical 268 pytest items passed; build and CLI smoke passed |
| `wsl.win-ws.localhost` | 3.13.5 | `all` | inventory, bundle, analysis, UI, and cleanup passed |
| `win-ws.localhost` | 3.14.0 | `all` | inventory, bundle, analysis, UI, and cleanup passed |

Each remote run copied the reviewed wheel and standard-library harness to an
exact host-local temporary directory, downloaded only binary runtime wheels to
its wheelhouse, and installed with the harness's offline child-venv path. The
shared `F:`/`/mnt/f` worktree was not read or mutated. WSL ran before Windows.

One preliminary Windows transfer encountered a PowerShell path-separator and
line-ending issue before the harness executed. Its exact temporary directory
was removed, then the successful run above used a normalized path. This was an
acceptance staging issue, not a product failure.
