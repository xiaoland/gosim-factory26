# Corpus Migration Guidance Authoring and History Review

## Scope

This review addresses two connected problems discovered while shaping
`svc upgrade --target corpus`:

1. current migration notes spend too much context restating the new system;
2. deriving guidance from Changie fragments needs an explicit release-fact and
   post-release guidance-maintenance boundary.

It proposes the durable authoring contract that should eventually replace the
small migration paragraph in `CONTRIBUTING.md`. New generated files under
`src/migrations/` are projections, not authoring surfaces; the published legacy
note is handled explicitly below.

No product or durable Corpus implementation is authorized by this document.

## 1. Current-note evidence

| Note | Words | Largest sections | Release state |
| --- | ---: | --- | --- |
| `11.0.0.md` | 498 | archive consumers 159; unsupported archives 126 | published in v11.0.0 |
| `agent-task-performance-analysis.md` | 671 | query/read replacement 223; schema-v3 authority 169 | unreleased after v11.0.1 |
| `local-trust-boundary.md` | 268 | schema-v3 consumers 60; interrupted export 51 | unreleased after v11.0.1 |

The 671-word note is not long because the migration requires 671 words of
action. It mixes three information services:

```text
migration       what an affected Consumer must change now
new contract    the complete schema-v3/query/read behavior
rationale       why the authority and trust model changed
```

Only the first belongs in a migration note. The second already belongs to CLI
help and canonical Corpus owners such as deployment/Product TDD. The release
fragment body supplies the concise rationale/changelog summary.

Specific duplication pressure:

- `Understand schema-v3 authority` restates member ownership, digest,
  projection, pagination, and status semantics rather than naming only changed
  consumer assumptions;
- `Replace analyze with query and read` restates request kinds, cursors,
  framing, encoding, provenance, and response semantics after giving the exact
  replacement commands;
- negative guarantees such as “does not convert/fallback/summarize/score” recur
  across the note and canonical owners;
- broad “update callers” paragraphs combine independent bundle, command, option,
  and response migrations without an applicability gate.

The 268-word local-trust note is closer to the desired shape because its
headings are actions and its sections name exact removed assumptions. It can
still replace full retained-contract lists with canonical references.

## 2. Authoring contract — accepted

### One guidance block, one migration concern

Author Corpus migration guidance in the structured `Guidance` block of one
`component=corpus` Changie fragment. Split independent consumer obligations
into separate fragments even when they ship in one Corpus release. A fragment
may contain several steps only when they share one applicability trigger and
one verification horizon.

Use this order:

```markdown
### Applies when
<one exact old command, field, artifact, document contract, or behavior>

### Required change
<imperative before -> after actions; exact commands/paths where useful>

### Verify
<the smallest project-owned observation proving the caller's work>

### If migration is impossible
<only when data loss, missing source, or unsupported recovery is real>

### Reference
<exact canonical Corpus paths for the complete new contract>
```

Omit sections that have no semantic content, but never omit `Applies when`,
`Required change`, or `Verify`. The generated note title and release context
come from fragment metadata rather than repeated prose.

### Content test

Every sentence must serve at least one of these decisions:

- am I affected;
- what must I change;
- what cannot be preserved or automated;
- how do I verify my migration;
- where do I read the complete new contract if needed.

Move or delete sentences that merely explain the entire new architecture,
repeat Behavioral SemVer labels, inventory every unchanged guarantee, or
duplicate CLI help. Reference the canonical owner instead.

Do not use vague instructions such as “review consumers,” “update as needed,”
or “run tests.” Name the old fact, the replacement fact, and the relevant
project-owned check. Do not guess Consumer file paths; the guidance names the
contract or search token, while the Agent uses `rg`, ast-grep, and project tools
to find actual consumers.

### Size pressure, not blind truncation

Aim for roughly 100-250 words per independent guidance block. More than about
300 words is a review signal to split independent concerns or replace contract
restatement with references, not a mechanical truncation rule. Destructive
recovery or irreversible data loss may justify more text; completeness wins
over an arbitrary limit.

Commands and exact removed/renamed field lists are high-value content. General
architecture descriptions and exhaustive retained-property lists are the first
content to move out.

### Projection behavior

The release projection:

1. groups exact `component=corpus` fragments by Corpus release;
2. emits one focused Markdown note per fragment/change identity;
3. writes ordered guide references into `src/version.json`;
4. lets `svc upgrade` list exact `svc lookup --path` continuations;
5. validates non-empty required sections and canonical referenced paths.

It does not concatenate every Corpus fragment into one release-sized essay.
Multiple small exact references are preferable to one document that makes every
caller read unrelated scenarios.

## 3. Can derived history be edited? — accepted after correction

### Changie does not impose immutability

The prior candidate incorrectly turned a repository policy into a Changie
constraint. Changie `batch` merges unreleased fragments and normally removes
them; `--keep` retains them and `--move-dir` relocates them. Changie does not say
that a relocated/versioned YAML fragment becomes immutable, nor does it own a
historical guide hash protocol.

Therefore permanent `{path, sha256}` sealing, append-only guide bytes, and
correction-only patch notes were unnecessary restrictions introduced by this
review, not mature-tool behavior.

### Stable release facts, living migration guidance

Keep two different things separate:

```text
release history       version, previous version, change identity/domain
migration guidance    current best instructions for crossing that old change
```

Release-chain facts remain stable because baseline range selection depends on
them. Migration guidance is living documentation: its purpose is to help the
next Agent/Human migrate correctly, not to prove which exact prose a historical
caller read.

The corrected lifecycle is:

```text
unreleased fragment
  -> edit Body/Guidance and regenerate projections
versioned fragment
  -> release association remains stable
  -> Guidance may later be clarified, shortened, or corrected
guidance change
  -> regenerate the current migration projection from the maintained source
  -> ship as a new Corpus patch content change
```

The generated Markdown still should not be edited independently when a
structured fragment owns it; edit `Guidance` and regenerate. The restriction is
single-source consistency, not historical immutability.

`src/version.json` keeps the current guide references, not permanent paths or
content hashes. An individual `svc upgrade` plan computes and binds the exact
reference/content it actually presented. If a newer installed Corpus changes
that guidance, an old plan digest becomes stale and the caller replans against
the improved text.

### Two kinds of correction

1. If a clarification only helps projects that have not crossed the historical
   transition, update that historical fragment's `Guidance` directly and
   regenerate its current projection. The Corpus patch release can be
   `migration: not-required` for projects already at the latest baseline.
2. If the correction means projects that already followed the old instruction
   may now require repair, update the historical guidance for future crossers
   **and** add current-release repair guidance. That new hop makes the duty
   visible to already-adopted projects.

This distinction follows actual project impact instead of forcing every typo,
clarification, and safety correction through one immutable-history ceremony.
No `supersedes` graph or correction metadata is needed unless real cases later
demonstrate an ordering problem.

### Bootstrap boundary for current history

The current repository predates retained structured fragments:

- `src/migrations/11.0.0.md` is already published and has no retained YAML
  source. Import its exact content once into an editable version-associated
  guidance record; do not pretend to reconstruct unavailable release metadata.
  It may then be improved under the same living-guidance rule.
- `agent-task-performance-analysis.md` and `local-trust-boundary.md` are not in
  v11 tags. Their current Changie fragments can be enriched, their guidance
  shortened/split under the authoring contract, and their projections replaced
  before the next release.

The “one authored structured change source” law applies after this explicit
guidance import. It does not require freezing the imported prose forever.

## 4. Current-note rewrite direction — accepted, implementation gated

Do not edit the notes yet. The likely pre-release rewrite is:

```text
agent-task-performance-analysis (671 words)
  -> old v1/v2 bundles: recollect or state impossible recovery
  -> analyze/TUI callers: move to query/read exact commands
  -> removed options/response fields: update affected automation
  -> reference canonical schema-v3/query/read owners for full semantics

local-trust-boundary (268 words)
  -> keep one note if the shared applicability remains same-user evidence use
  -> retain exact removed assumptions and required caller changes
  -> reference deployment for the full retained trust/runtime contract
```

The 11.0.0 note need not be rewritten as part of this unit, but it is no longer
declared immutable. Its verbosity can be improved later through the maintained
guidance source when that work has a real consumer/review horizon.

## 5. Review decision

Sir accepted after removing the self-imposed immutable-guidance policy:

1. action/applicability/verification-led guidance authored in Changie fragments;
2. canonical references instead of restating the complete new system;
3. a soft 100-250 word concern budget with split/reference pressure above 300;
4. stable release-chain facts with living, directly maintainable guidance;
5. current guide references in `src/version.json`, with only the current plan
   binding the exact reference/content it presented;
6. direct historical clarification when prior adopters need no action, versus a
   new repair hop only when already-migrated projects are affected;
7. one editable legacy guidance import for published pre-fragment content;
8. rewrite only the two unreleased notes after implementation is explicitly
   started.

## Evidence boundary

All inspections were read-only. No migration note, change fragment, release
record, or Consumer project was modified.
