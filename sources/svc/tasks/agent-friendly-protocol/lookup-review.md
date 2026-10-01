# `svc lookup` Command Review

## Purpose and gate

This review treats `svc lookup` as the local delivery/read interface for the
packaged SVC Corpus. It does not make lookup responsible for Consumer-project
context discovery, CLI help, web search, or semantic interpretation.

The task packet may evolve during review. No product implementation is
authorized by this document.

## 1. Smallest input surface — accepted

### Current surface

```text
svc lookup (--list | --path PATH | --name REGEX | --keyword QUERY)
           [--all] [--limit N] [--json]
```

The current selectors expose three implemented information services:

1. enumerate packaged document identities (`--list`);
2. select candidate documents by local lexical content (`--keyword`);
3. read canonical document content (`--path` or path-regex `--name`).

`--name` is not a document-name selector. It is a full-path regular expression,
and `--all` changes it from one-result selection to intentional bulk read. That
pair exposes regular-expression and ambiguity policy even when the caller
already knows one exact catalog path.

### Real-project and Agent evidence

The available client-web, core-py, InKCre docs, and SFP7 Camera repositories do
not contain a script that parses lookup output. Their currently installed
legacy generated SVC Skills do instruct Agents to run a keyword query and then
turn an exact returned path into a regular expression for `--name`. This
generated repetition is one older SVC source projected into projects, not
independent evidence that regex selection is useful.

Current SVC source has already diverged from those deployed Skills:
`skill_body()` and the retained AGENTS/docs navigation block now instruct the
Agent to run a complete `--list --json`, then `--path --json`, with keyword
search only when titles do not resolve the need. The current source therefore
does not preserve the fake `--name` pattern interaction, but it does explicitly
encourage a full catalog dump as the first discovery move. The planned Skill
removal alone does not remove that pressure because the retained navigation
block shares the same commands.

A bounded structural read of actual Codex rollout records distinguished shell
tool calls from command text repeated in prompts or generated guidance. Among
the available `exec_command` records:

- eight call records used `svc lookup --keyword`;
- eight call records used `svc lookup --name`;
- every recovered `--name` selection was an anchored regex for one already
  exact path such as `^sections/working-protocol\.md$` or
  `^assets/templates/task-packet\.template\.md$`;
- no actual lookup call used `--all`.

These observations prove that current guidance taught `--name` as a needlessly
indirect `--path`. They do **not** prove that regex search lacks value. The
generated Skill never taught a real pattern-search interaction: it told the
Agent to list or keyword-search, escape an already-known path, and then pretend
that exact read was regex selection. Using those induced calls as negative
evidence against pattern search would confuse guidance behavior with the
underlying information need.

The actual missing service is exact-pattern discovery inside packaged Corpus
content. Ordinary `rg` cannot be assumed to have a stable filesystem path to
wheel resources, while reading every document through the CLI just to search it
would defeat lookup's distribution role. SVC can expose the narrow search
result without taking responsibility for interpreting or synthesizing the
Corpus.

### Candidate grammar

```text
svc lookup (--list [PREFIX] | --path PATH | --keyword QUERY | --regex REGEX)
           [--scope path|both] [--limit N] [--json]
```

- `--list [PREFIX]` returns only the immediate children of one logical Corpus
  directory, without reading document bodies. With no prefix it lists only the
  root children; a returned directory path is the next prefix.
- `--keyword QUERY` performs bounded deterministic local lexical discovery and
  returns candidates, never authoritative synthesized guidance.
- `--regex REGEX` performs bounded regular-expression matching over canonical
  Markdown content and returns exact match locations/candidate paths. It does
  not match catalog filenames and does not concatenate every matching document
  body.
- `--path PATH` integrity-checks and reads exactly one normalized
  source-relative Markdown document.
- `--limit N` bounds `--keyword` candidates and `--regex` match results; it does
  not turn `--list` into a partial catalog or truncate an exact document.
- `--scope path|both` applies only to keyword/regex search. `path` means the
  normalized source-relative catalog path, not only its basename; `both` is
  the default and searches paths plus canonical Markdown content after UTF-8
  validation, identifying the matched field in every result.
- `--json` remains the deliberate CI/script projection for each service.

Remove `--name` and `--all`. Replace the misplaced filename-regex behavior with
the accurately named `--regex` full-text search service, not with a compatibility
alias. `--regex` returns bounded matches that lead to `--path`; it does not
recreate `--all` under another name. An Agent that deliberately needs several
known full documents can issue several exact reads; scripts can select paths
from the catalog with ordinary tools.

`--keyword` and `--regex` remain separate because they serve different caller
knowledge:

| Selector | Caller knows | Result purpose |
| --- | --- | --- |
| `--keyword` | concepts or natural-language terms | ranked document candidates |
| `--regex` | an exact token, phrase shape, identifier, or Markdown pattern | exact bounded source matches |

Use `--regex` rather than `--pattern` in the public grammar. The accepted input
is specifically a regular expression; naming the mechanism avoids making
callers guess whether “pattern” means regex, glob, or literal text. Regex flags
belong in the expression (for example `(?i)`), so no additional case/multiline
switches are introduced.

Keep explicit selectors rather than overloading one positional string as both
path and search query. The extra flag identifies the caller's information need
without heuristic path detection. Keep the three selectors in one command;
their lifecycle is the same local read interaction, so subcommands would add
structure without adding authority.

This correction must update SVC-owned generated navigation and canonical Corpus
examples in the same implementation. New guidance teaches three distinct
moves: browse one directory level or search within a deliberate scope, select a
path, then read that exact path. It must not dump the full catalog first or turn
a returned path into a regex.

### First review decision

Sir accepted removal of `--all` and the correction from filename-regex `--name`
to full-text regex search. Sir then accepted both refinements:

1. retain `--list` as one-level logical tree navigation rather than delete the
   bounded deterministic Corpus browser;
2. let both search selectors use `--scope path|both`, defaulting to `both`,
   rather than introducing separate filename/content commands.

## 2. Progressive browsing and search scope — accepted

### Do not force a complete catalog dump

The current packaged Corpus has 21 documents. Its complete text list is 23
lines and about 1.3 KB, so current size alone does not demonstrate a context
failure. The structural problem is the current source guidance: it makes full
listing the default first move, so output grows with the whole Corpus even when
the caller needs one domain.

Do not justify listing as a recovery path for arbitrary zero-match queries.
`svc lookup` searches the SVC Corpus, not the SVC CLI manual; for example,
`dev server readiness` can correctly return no Corpus match. A zero result says
nothing by itself about retrieval quality or about whether the topic belongs in
the Corpus. Retain listing for its direct information service: bounded,
deterministic navigation of the packaged Corpus topology when the caller wants
to browse it.

Use shallow logical-directory listing instead:

```text
svc lookup --list
  index.md
  assets/       9 documents
  migrations/   3 documents
  sections/      8 documents

svc lookup --list sections/
  deployment.md
  extensions/    2 documents
  implementation-taste.md
  ...
```

Each invocation returns only immediate child directories/documents in stable
path order. Directory rows carry recursive document counts so the caller can
judge cost before expanding. No recursive/full-tree switch is added; a script
that genuinely needs the complete catalog can traverse the compact machine
tree, while SVC-owned release tooling continues to use the catalog API rather
than scraping CLI text.

### One orthogonal search scope

Filename is too narrow a public term: `sections/extensions/alignment.md` gains
meaning from its whole source-relative path. Use one scope selector for both
lexical and regex search:

```text
--scope path       normalized source-relative paths only
--scope both       normalized paths and validated Markdown content (default)
```

Results identify whether a match came from `path` or `content`. Catalog titles
do not require a third scope because they are derived from Markdown headings
and therefore already occur in content. Do not add a content-only value without
a demonstrated caller: Sir identified two useful ranges, and a third range
would be speculative. This keeps scope orthogonal to search mechanism:
`--keyword` answers concept discovery, while `--regex` answers exact pattern
matching.

Do not use `--scope all`: after removing the old `--all`, that word could still
be confused with returning all matches/documents. `both` names the two searched
surfaces without implying unbounded output.

## 3. Default result presentation — accepted

The four modes have different result semantics and should not share one generic
text renderer. Default text is the Agent/Human interface; compact JSON is the
CI/script projection. Current source guidance must stop adding `--json` merely
because the caller is an Agent.

### Progressive list: compact logical children

Render one row per immediate child, using complete Corpus-relative paths so a
row can be copied directly into the next command:

```text
index.md                              Sustainable Vibe Coding
assets/                               9 documents
migrations/                           3 documents
sections/                              8 documents

Expand: svc lookup --list <directory>
Read:   svc lookup --path <document>
```

Nested listing still emits complete paths (`sections/deployment.md`,
`sections/extensions/`), not context-dependent basenames. Directory counts are
recursive document counts; document rows show titles. Do not emit hashes,
descriptions, full descendants, or JSON-oriented continuations in default text.

### Keyword: ranked document candidates, not ranking internals

```text
sections/working-protocol.md          Working Protocol
  …task packet and mutation-gate excerpt…

assets/templates/task-packet.template.md  <Task>
  …bounded task-packet excerpt…

Read one: svc lookup --path <path>
```

Order is the ranking result. Remove the numeric score from public text and JSON:
its magnitude is an implementation detail with no stable cross-query meaning,
and exposing it encourages callers to bind to the current hand-weighted ranker.
Each candidate carries a bounded excerpt when content matched; a path-only
candidate identifies the path match rather than fabricating a content excerpt.

### Regex: exact bounded source matches

Content matches use the familiar path/line/column shape:

```text
sections/working-protocol.md:42:17: mutation gate
sections/unit-tdd.md:81:5: mutation gate
```

Path matches are explicitly distinguished because they have no source line:

```text
[path] assets/templates/task-packet.template.md
```

Line and column are one-based locations in canonical Markdown. A displayed line
may be clipped around the match, but the match and location remain exact.
`--limit` bounds match records, not document bodies. If additional matches
exist, the result says that it is truncated; it does not silently imply
completeness or print every matching document.

Both search modes end with the exact-read continuation when candidates exist.
They never concatenate document bodies.

### Exact path: raw canonical Markdown

Default `--path` output remains the document bytes decoded as validated UTF-8
Markdown, with no SVC header, metadata wrapper, indentation, separator, or
continuation appended. The command already names the selected path, and raw
Markdown is simultaneously the least lossy and easiest Agent/Human form.

### Empty search is a settled search result

A valid keyword or regex query with no matches returns a short statement on
stdout and exit 0, or an empty candidate/match array in JSON:

```text
No SVC Corpus matches for: dev server readiness
```

Do not automatically recommend listing or claim that the query should have
matched: the requested topic may correctly be outside the Corpus. Exact missing
paths/directories remain selection failures rather than empty search results.

### Third review decision

Sir accepted the mode-specific default forms: no public ranking score, rg-like
regex locations, raw Markdown exact reads, and a valid zero-match search as a
settled stdout/exit-0 result.

## 4. Compact JSON projection — accepted

`--json` emits exactly one compact JSON object with stable key order and no text
projection. It is for deliberate CI/script consumption, not the default Agent
interface. Use lookup response schema version 2 because the result collections
and selector semantics intentionally change; retain no aliases for the current
generic `results`/numeric `score` shape.

Every mode carries:

```text
schema_version: 2
command: "lookup"
mode: "list" | "path" | "keyword" | "regex"
corpus_version: exact packaged Corpus version
```

`corpus_version` is a Corpus fact, not the CLI distribution version. It makes a
saved machine result attributable after those independent versions are split.

### List projection

```json
{"command":"lookup","corpus_version":"12.0.0","entries":[{"document_count":9,"kind":"directory","path":"assets/"},{"kind":"document","path":"index.md","sha256":"<sha256>","title":"Sustainable Vibe Coding"}],"mode":"list","prefix":null,"schema_version":2}
```

Root uses `prefix:null`; a nested listing uses its normalized trailing-slash
prefix. Directory entries have `kind`, `path`, and recursive `document_count`.
Document entries have `kind`, `path`, `title`, and `sha256`. Do not add a total,
summary, continuation string, or nested descendants.

### Keyword projection

```json
{"candidates":[{"excerpt":"…task packet and mutation gate…","matched_in":["content"],"path":"sections/working-protocol.md","sha256":"<sha256>","title":"Working Protocol"}],"command":"lookup","corpus_version":"12.0.0","limit":10,"mode":"keyword","query":"task packet mutation gate","schema_version":2,"scope":"both","truncated":false}
```

Candidate array order is rank. `matched_in` is stable-order `path` and/or
`content`; `excerpt` exists only when content supplied bounded evidence. Numeric
rank score and rank number are absent: array position is sufficient and does
not expose ranking internals.

### Regex projection

```json
{"command":"lookup","corpus_version":"12.0.0","limit":10,"matches":[{"column":17,"excerpt":"mutation gate","line":42,"path":"sections/working-protocol.md","sha256":"<sha256>","surface":"content"},{"path":"assets/templates/task-packet.template.md","sha256":"<sha256>","surface":"path"}],"mode":"regex","query":"mutation[ -]gate","schema_version":2,"scope":"both","truncated":false}
```

Content locations are one-based and include a bounded excerpt. Path matches do
not invent line/column fields. Match-array order is stable Corpus path then
source occurrence. `limit` bounds flat match records, so `truncated:true`
unambiguously means more occurrences exist.

### Exact-document projection

```json
{"command":"lookup","corpus_version":"12.0.0","document":{"content":"# Working Protocol\n...","path":"sections/working-protocol.md","sha256":"<sha256>","title":"Working Protocol"},"mode":"path","schema_version":2}
```

The singleton is `document`, not a one-element generic result array. JSON
content preserves every decoded Markdown character; it is not excerpted or
normalized. Scripts that only need bytes can use default raw output instead of
parsing JSON.

Valid empty searches use an empty `candidates` or `matches` array with
`truncated:false`; they do not become error envelopes.

## 5. Channels, exits, and failures — accepted

Lookup is a bounded local read and has no progress stream:

```text
0  successful list/path/search, including valid zero-match search
2  invalid CLI grammar or selector value: missing/conflicting selector,
   malformed regex, invalid scope/limit, or scope/limit on an inapplicable mode
3  a normalized exact document path or logical directory prefix does not exist
4  packaged Corpus/resource/integrity/UTF-8 failure
```

Resolved results use stdout. Usage, missing exact selections, and integrity
failures use stderr. Default text and compact JSON follow the same semantic
channel. JSON errors reuse the core compact error envelope rather than a
lookup-specific shape; default errors render selected structured details as
purpose-written lines, never as a prettified JSON object inside text.

Do not automatically attach the complete catalog command to every error.
Malformed regex/scope/limit errors explain the rejected input. A missing path
or directory may name the nearest valid logical parent when one exists, but it
does not guess a keyword or claim the desired guidance exists. Integrity errors
name the affected resource and expected/actual digest where available.

SIGINT before settlement follows ordinary CLI process behavior and exits 130;
there is no mutation or recovery receipt to synthesize.

## 6. Self-sufficient layered help — accepted

Root help owns only selection:

```text
lookup   Browse, search, or read the packaged SVC Corpus
```

`svc lookup --help` must state the boundary the real zero-match correction made
important:

- lookup searches SVC Corpus guidance, not SVC CLI usage; use
  `svc <command> --help` for the latter;
- `--list [PREFIX]` browses one logical directory level;
- `--keyword` ranks concept candidates, while `--regex` returns exact source
  matches;
- `--scope path|both` and `--limit` apply only to search;
- `--path` returns one exact document as raw Markdown;
- default text is for Agent/Human reading; `--json` is one compact scripts/CI
  object;
- zero matches is stdout/0, missing exact selection is stderr/3, and invalid
  Corpus data is stderr/4.

Examples use default text and teach direct intent, not a mandatory funnel:

```text
svc lookup --list
svc lookup --list sections/
svc lookup --keyword "mutation gate"
svc lookup --regex 'SVC_[A-Z_]+'
svc lookup --regex '^sections/' --scope path
svc lookup --path sections/working-protocol.md
```

SVC-owned AGENTS/docs navigation should say when lookup is relevant and defer
the exact grammar to help. It must not prescribe full-list-first, add `--json`
for an Agent, or reconstruct a removed CLI Skill.

### Final lookup review decision

Sir accepted the compact machine projections, channel/exit boundaries, and
layered-help contract. The `svc lookup` design review is closed. No product
implementation is authorized by this review.

## Evidence boundary

All Consumer repositories, rollout records, the packaged Corpus, and CLI
commands were read-only. No product or Consumer file was mutated.
