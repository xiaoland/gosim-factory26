# Thread Inventory and Navigation

Status: Slice 0 frozen behavior. Implementation friction must return to the
decision register rather than changing these semantics implicitly.

## Purpose

Large thread inventories should be navigated by a workspace-path directory
grouping, presented as project/workspace navigation, not dumped onto one
terminal screen. “Project” is a display concept only; it never asserts a
repository root, ownership, or task relation. A user primarily identifies a
thread from:

1. its project/workspace grouping
2. its title
3. its first user message
4. its lifecycle and recency

Thread identifiers remain selection handles, not the main recognition surface.

## Two Inventory Surfaces

### Automation-safe inventory

The existing non-interactive plain and JSON `list` behavior remains:

- deterministic and scriptable without a TTY
- non-sensitive by default
- bounded by safe returned descriptors
- resilient to isolated unsafe rows without leaking omitted values
- the existing schema-v1 envelope and descriptor-key shape

It must not begin printing titles, message previews, full paths, reasoning, or
tool values merely because the interactive navigator needs them.

`--archive-state active|archived|all` is additive and defaults to `all`.
Lifecycle filtering occurs before the safe-result `--limit`, so archived-only
selection cannot be starved by newer active rows. Unsafe rows in the selected
lifecycle scope still do not consume a safe result slot.
The released limit contract remains 1–100 with default 20.

The released `source_state` field is a compatibility projection, not internal
authority:

| Internal facts | Safe `source_state` |
| --- | --- |
| availability is `missing` | `missing` |
| availability is `unavailable` | `unavailable` |
| availability is `unknown` | `unknown` |
| available and lifecycle is `active` | `active` |
| available and lifecycle is `archived` | `archived` |
| available and lifecycle is `unknown` | `unknown` |

Thus an archived thread with a missing rollout remains `missing` in the released
projection but is still selected by `--archive-state archived`. Lifecycle
`unknown` participates only in `all`. The MAJOR release explicitly permits
`unknown`/`unavailable` where the released adapter guessed from a path.

Safe ordering is normalized recency descending with missing recency last, then
opaque thread ID ascending. `--archive-state all` is the default. Exact
archive filtering occurs before ordering/iteration; the safe limit is applied
only after row safety validation.

### Explicit analysis navigator

`svc telemetry agent-thread analyze` with no selector/input requires a TTY and
opens the navigator. This explicit command permits local rendering of:

- project/workspace label
- title
- bounded first-user-message preview
- active/archived state
- last activity
- provider

The navigator defaults to active threads and can switch to archived or all. It
uses the terminal alternate screen and retains recognition content only in
process memory. It does not log, cache, copy to clipboard, emit, or put title,
message, or workspace values into diagnostics. Entering it does not authorize
export or network transmission.

Recognition-bearing model fields are excluded from dataclass/object repr and
exception details. UI failures report only stable structural codes and counts.
Renderers construct plain Textual/Rich text with markup disabled. Before
painting only, every Unicode control/format/line/paragraph-separator code point
is shown as an ASCII `\u{XXXX}` escape; the in-memory bounded value is not
rewritten. Thus ANSI escapes, bidi controls, newlines, and markup-looking title
or message text cannot control the terminal or tree structure.

## Inventory Model

Lifecycle and local source availability are separate facts:

| Dimension | Values | Meaning |
| --- | --- | --- |
| `archive_state` | `active`, `archived`, `unknown` | Provider-reported lifecycle |
| `source_availability` | `available`, `missing`, `unavailable`, `unknown` | Whether the provider source can currently be collected |

An unavailable source is not automatically archived, and an archived thread
may still have an available source. A path that is unsafe, escapes provider
containment, or cannot be represented safely causes that row to be omitted with
an aggregate warning rather than rendered.

For Codex, `available` means a contained, present, readable, regular non-link
rollout; `missing` means a valid contained path is absent; `unavailable` means
the row has no usable path or safe inspection is denied; and `unknown` is
reserved for a compatible provider that cannot report availability. Invalid,
escaping, symlink, or reparse-point paths are unsafe omissions, not
`unavailable`.

The Codex mapping is exact:

| Observed `rollout_path` / inspection result | Availability or action |
| --- | --- |
| `NULL` or blank text | include as `unavailable` |
| non-text, control character, unrepresentable, over 4,096 code points, or over a stricter platform path limit | unsafe omission |
| lexical/resolved path escapes the selected Codex home | unsafe omission |
| valid contained path returns file/path-not-found | `missing` |
| safe inspection/open returns access denied or sharing/busy denial | `unavailable` |
| final path is a symlink, reparse point, directory, or non-regular file | unsafe omission |
| descriptor identity differs from the inspected regular file | unsafe omission |
| descriptor-bound zero-byte read check succeeds on the same regular file | `available` |
| other non-safety inspection failure | `unavailable` |

Availability inspection opens the descriptor but reads no rollout body. Unsafe
omissions, invalid IDs, and ambiguous duplicate IDs all contribute only to the
existing aggregate `thread-source-omitted` count.

The inventory path inspector is not the released export `_resolve_path`
helper. It validates lexical containment first, `lstat`s every existing
component from the selected Codex home, and rejects any symlink/reparse point
in the chain, including a final link whose target remains inside the home.
It opens the final component read-only with no-follow semantics where the host
provides them, then requires a regular-file `fstat` whose device/inode/type
identity matches the lexical `lstat`; on Windows the equivalent reparse and
post-open identity checks are mandatory. A missing component after a verified
non-link prefix is `missing`. Export/resolve keeps its released helper and
semantics until Slice 2.

The v1 interactive item contains:

- opaque provider/thread reference
- provider name
- optional bounded workspace/CWD provenance
- optional bounded title and first-user-message value
- truncation flags for each bounded value
- created, updated, and recency timestamps where the provider supplies them
- source warning metadata that contains no sensitive value

For the Codex adapter, field authority is deliberately narrow:

| SVC field | Codex state authority | Rule |
| --- | --- | --- |
| thread reference | `id` | Required non-blank exact value |
| archive state | `archived` | `0 → active`, `1 → archived`; missing/invalid → unknown; never infer from a path |
| source availability | `rollout_path` plus read-only file inspection | Separate from lifecycle |
| workspace | `cwd` | Lexical sensitive provenance; never walk or infer ownership |
| title | `title` | No rollout scan and no fallback to unrelated preview fields |
| first user message | `first_user_message` | No rollout scan and no `preview` fallback |
| safe created time | `created_at` | Optional exact non-negative SQLite integer rendered as its decimal schema-v1 string; otherwise null |
| safe updated time | `updated_at` | Optional exact non-negative SQLite integer rendered as its decimal schema-v1 string; otherwise null |
| recency | `recency_at_ms`, then `updated_at_ms`, then `updated_at` | Provider mapping normalizes units and tests each fallback |

Model, Git hints, `preview`, agent nickname/role, and other observed state columns
are outside the v1 inventory projection.

The three observed current-host schemas declare `archived`, `created_at`,
`recency_at_ms`, `updated_at_ms`, and `updated_at` as SQLite `INTEGER`. Every
sampled created/updated value was a SQLite integer; every sampled `archived`
value was integer `0|1`; `_ms` values were 13 decimal digits and `updated_at`
values 10 digits. V1 therefore accepts:

- archive lifecycle only from exact SQLite integer `0|1`; every other/null/
  absent value is `unknown`
- `recency_at_ms` and `updated_at_ms` only as non-negative SQLite integers in
  milliseconds
- `updated_at` only as a non-negative SQLite integer in seconds, multiplied by
  1,000 after overflow/range validation
- schema-v1 `created_at`/`updated_at` display values only as non-negative SQLite
  integers, rendered to bounded decimal ASCII without unit rewriting; absent,
  null, or invalid values project to null

Invalid or out-of-range time candidates fall through to the next authority and
ultimately to missing recency. Recency normalizes to an integer millisecond
sort key in the signed 64-bit range; seconds must be no greater than
`9_223_372_036_854_775` before multiplication. It is not copied into the
schema-v1 descriptor. Ordering is descending recency, missing last, then exact
thread ID UTF-8 bytes ascending. No locale, case folding, path, title, or
message participates in ordering.

Thread IDs are exact, unnormalized UTF-8 text with 1–512 Unicode code points,
no leading/trailing whitespace, and no control characters. If an ID occurs in
more than one row of the compatible threads table before lifecycle filtering,
every row for that ID is an unsafe ambiguous omission in every filter; the
adapter never lets lifecycle or recency choose one.

Here, leading/trailing whitespace follows Unicode `str.isspace`; a forbidden
control is any Unicode general-category `Cc`, `Cf`, `Cs`, `Zl`, or `Zp` code
point. The same control definition applies to rollout-path safety. Lone
surrogates/unencodable SQLite text are unsafe, never replacement-decoded.

Hard bounds are:

- interactive inventory: 5,000 safe rows after lifecycle filtering
- thread ID: 512 Unicode code points, never truncated
- rollout path candidate: 4,096 Unicode code points, never truncated
- workspace value: 4,096 Unicode code points
- title: 160 Unicode code points
- first user message: 512 Unicode code points

The provider query must bound strings before materializing them and report a
truncation flag without retaining the discarded suffix.

Title and first-message preview retain their leading bound. An over-4,096 CWD
returns no path value plus `workspace_truncated=true` and is placed in an
explicit truncated-workspace group; an incomplete path is never rendered as a
real directory tree. SQL `CASE`/`substr`/`length` performs these decisions
before Python materialization.

The interactive provider query retains the first 5,000 safe rows in frozen
order and probes only until one additional safe row establishes
`inventory_truncated=true`; it does not claim an exact remaining/omitted total.
The TUI renders that state and asks the user to narrow lifecycle scope. Lazy
tree expansion is in-memory navigation over this bounded model, not unbounded
background pagination.

The automation-safe list keeps its released exact aggregate omission count, so
its cursor scans the selected lifecycle scope while retaining at most
`--limit` safe descriptors.

The automation-safe query does not select `cwd`, `title`,
`first_user_message`, `preview`, message, reasoning, or tool-content columns.
The sensitive projection is a separate provider query invoked only by the
explicit Textual flow. This prevents the safe CLI from transiently
materializing private recognition data merely to discard it later.

Neither query materializes an unbounded SQLite text value. For `id` and
`rollout_path`, SQL projects the SQLite type, an embedded-NUL flag, and at most
513 or 4,097 Unicode code points respectively, using `CASE` so non-text values
return no text prefix. Python accepts only a prefix at or below the exact bound
after whitespace/control/representability checks; observing the extra code
point proves oversize and omits the row. Exact duplicate-ID counting remains
inside SQLite and returns only a count. The sensitive query uses the same
bound-plus-one shape for CWD/title/first-message and returns only the retained
prefix, original code-point count, and truncation flag; it never returns a
discarded suffix. An over-bound CWD prefix is discarded by the mapper as
specified above, while title/message retain their bounded head.

The safe query requires exact `id` and `rollout_path` columns. A missing threads
table or either required column remains a command-level incompatible-source
failure. Missing `archived`/recency columns degrade row facts to
unknown/missing as defined above; aliases such as `state`, `status`, or a path
name never become lifecycle authority.

## Project/Workspace Tree

The navigator groups threads by provider-reported workspace/CWD provenance.
It detects POSIX versus Windows/UNC path flavor lexically, renders a directory
tree without resolving or walking it, and places missing/invalid provenance in
an explicit unknown group. It must not invent:

- repository ownership
- a canonical project root
- task ownership
- a causal relationship to a task packet

Provider and path-component siblings sort by exact UTF-8 bytes, independent of
host locale/filesystem case rules; spelling/case is preserved. Lifecycle groups
use fixed active, archived, unknown order; truncated-workspace then
unknown-workspace groups follow valid paths. Thread leaves retain the global
recency/ID order.

Conceptually:

```text
Provider
└── Workspace or project grouping
    ├── Active
    │   └── Title — first user-message preview
    ├── Archived
    │   └── Title — first user-message preview
    └── Unknown lifecycle
        └── Title — first user-message preview
```

Required interaction behavior:

- lazy expansion for large inventories
- stable selection while nodes expand or filters change
- `active`, `archived`, and `all` filtering
- a clear representation for missing title/message/workspace fields
- keyboard navigation and a non-color-only selection state
- bounded preview rendering with no hidden full-message fetch
- deterministic ordering within a group
- a stable `(provider_id, thread_id)` selection reference stored in node data;
  Textual runtime node IDs are never domain identity
- explicit disabled/error state for a thread whose source is not available

## Technology Direction

Textual `>=8.2.8,<9` without syntax or `textual-dev` extras is the frozen v1 UI
dependency. It provides a Tree widget and headless `App.run_test()`/Pilot
interaction tests across supported Python platforms.

The selector consumes a pure inventory/tree model and returns a stable thread
reference to the service layer. Textual is never the inventory authority.
Provider loading and filter transitions own cancellation/stale-result checks;
widgets do not fetch private data directly.

## Acceptance Focus

Verification must cover:

- inventories much larger than one terminal screen
- missing optional values
- active-only, archived-only, and combined filtering
- unsafe and malformed provider rows
- identical titles under different workspaces
- stable selection under lazy loading
- unchanged safe plain/JSON envelope, descriptor keys, and non-sensitive
  behavior
- filtering before both the safe-list limit and interactive 5,000-row cap
- 80×24 and narrow/resize behavior without relying on color or Unicode glyphs
- no TTY, logging, cache, clipboard, or hidden full-value regressions
- markup, ANSI, bidi, newline, and other control-bearing recognition fixtures
  render as plain visible escapes without changing the terminal
