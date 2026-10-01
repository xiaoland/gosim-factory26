# SVC Configuration Migration Review

> Interface note: this target-specific design now sits behind the accepted
> `svc upgrade --target config` interface. The CLI configuration semantics
> remain relevant; the public `svc config migrate` command is superseded.

## Scope

This review covers an independent SVC CLI concern noticed while reviewing
`svc adopt`. Corpus document migration requires judgment, while the CLI's own
configuration format migration can often be deterministic. Sharing one Python
distribution does not put configuration format inside the Corpus. Neither
silent config rewriting nor forcing the two migration domains into one
lifecycle is acceptable.

No product implementation is authorized by this document.

## 1. Responsibility and command boundary — accepted

### Independent state dimensions

Keep four facts separate:

```text
CLI distribution version      installed/source executable metadata
available Corpus version      catalog projection of ./src
project Corpus baseline       svc.json corpus_version (legacy: svc_version)
CLI configuration format      svc.json / svc.local.json schema_version
```

Changing the CLI configuration schema does not mean the project's PRD/TDD truth
has adopted a newer Corpus. Conversely, completing a Corpus document migration
does not make an old CLI config shape parseable. Therefore config migration
must not be described as a Corpus migration or hidden inside adopt.

The earlier decision that init does not rewrite an existing dev/run structure
still holds. Init establishes or repairs bounded SVC integration; it should not
silently turn into a general configuration transformer.

### Accepted public entry

The accepted unified public entry is:

```text
svc upgrade [<repo>] --target config [--apply <plan-digest>] [--json]
```

`svc status` diagnoses whether the base or this workstation's local overlay
requires migration and returns this exact continuation. A separate
`svc config status` is unnecessary while root status already owns the
diagnosis.

The command is implemented and versioned by `svc_cli`, not `src`. It owns only
deterministic CLI configuration transforms. It:

1. shallowly identifies the source schema without requiring the current model
   to parse it;
2. selects a packaged transform from that exact schema to the current schema;
3. plans exact base and, when present, local-overlay file effects;
4. validates the transformed base, overlay authority, and merged effective
   configuration under the current strict model before exposing an applicable
   plan;
5. uses the neutral stale-safe file transaction and verifies exact after
   states;
6. preserves the project Corpus baseline and therefore does not close Corpus
   adoption.

The next config schema should rename the legacy top-level `svc_version` field
to `corpus_version`. That rename is a configuration-format effect owned by the
CLI migrator; the value remains semantically unchanged. It makes future code
and output distinguish the project Corpus baseline from the CLI distribution
version.

If a transform is ambiguous or lossy, it blocks with the exact unsupported
fact and leaves the caller to edit deliberately. “Automatable” means a total,
semantics-preserving transform for the observed shape, not permission to guess.

### Real shape pressure

The reviewed real schema-v2 projects all use one selected dev profile:

- client-web: `local`, four targets;
- core-py: `local`, one target;
- SFP7 Camera: `f43-builder`, one target;
- InKCre docs: no dev declaration.

The client-web and core-py local overlays also override one profile. These
natural states make the accepted profile-flattening migration mechanically
possible, but the transform must still reject a hypothetical multi-profile
shape unless an exact preservation rule is deliberately designed.

### Local overlay lifecycle

Current `svc.local.json` files are sparse and contain no `schema_version`; they
implicitly depend on the base schema. That fails once a committed base is
migrated on one machine while another participant retains an old local
overlay.

The accepted correction is:

- from the next config schema onward, a present local overlay carries its own
  `schema_version` but never `corpus_version`;
- absence of the marker is recognized only as the exact legacy-v2 overlay
  convention, not guessed generically;
- config migrate includes the current machine's local overlay in the same plan
  when present;
- after another participant pulls a migrated base, root status can still
  diagnose and migrate that participant's legacy local overlay independently;
- no local overlay is created when absent.

This does not make local state Corpus-adoption authority. It only makes its CLI
config format origin explicit enough to migrate safely.

### First review decision

The accepted unified interface keeps CLI config-schema migration independent
from Corpus adoption behind `svc upgrade --target config`. The exact lossless
transform, local-overlay schema, and boundary between automatic file mutation
and project-owned config consumers are closed by the following sections.

## 2. Exact v2 -> v3 transform — accepted

### Real external consumers make this more than a file rewrite

The configuration files themselves can be transformed mechanically, but real
project code consumes the old public shape:

- client-web `scripts/check-local-runtime-contract.mjs`, invoked by both
  `pnpm check:runtime` and `doctor`, reads
  `svcConfig.dev.profiles.local.targets`;
- core-py `scripts/dev_database_provider.py` reads
  `config["dev"]["profiles"][profile]["targets"]`;
- SFP7 Camera's real build-readiness test reads the committed profile path.

Therefore the config target has two different responsibilities:

```text
automatic   exact svc.json / present svc.local.json transformation
guidance    changed public paths/tokens/env for Agent/Human project edits
```

SVC does not search or rewrite those external consumers. The target plan must
ship one CLI-owned v2 -> v3 migration guide naming the changed contracts. Apply
records only successful config-file conversion; it is a caller assertion that
project-owned consumers have been handled, not proof that every script is
compatible.

This guide belongs to the CLI distribution, not `src/version.json` and not
Corpus lookup.

### Base `svc.json`

For a valid schema-v2 base, produce schema v3 as follows:

```text
schema_version: 2 -> 3
svc_version             -> corpus_version (same value)
dev.profile             -> removed
dev.profiles.<only>.targets -> dev.targets
run                     -> preserved
```

Rules:

1. No `dev` declaration: rename the version field and preserve the remaining
   base data.
2. Exactly one profile, selected by `dev.profile`: flatten its complete target
   map.
3. More than one profile: block. Selecting the active profile and discarding
   the others is data loss, even if current runtime ignores the inactive data.
4. Any `${dev.profile}` occurrence inside a migrated dev value is replaced by
   the selected profile's literal name, preserving its old resolved value.
5. The automatic environment variable `SVC_DEV_PROFILE` has no config-file
   replacement; its removal is stated in the CLI migration guide for external
   consumer review.
6. Target declarations preserve every existing field. Schema v3 admits the
   optional target-local `stop`, but migration never invents one or infers it
   from a prior PID/script.

This multi-profile branch is legacy-input handling, not retention of profiles
in v3. Every successful v3 result has only `dev.targets`; a legacy shape that
cannot reach it without discarding data is outside the automatic path.

### Mature migration stack

Do not build a custom JSON mutation or generic migration framework. Use:

- Python's standard JSON decoder with the existing duplicate/non-finite/null
  rejection for lossless JSON-domain parsing;
- explicit strict Pydantic v2 source and v3 target models (`extra="forbid"`),
  using `model_validate`/`model_validate_json` and target revalidation;
- `python-json-patch` for RFC 6902 `test`, `move`, `remove`, `add`, and
  `replace` operations;
- `python-semanticversion` for SemVer parsing and ordering instead of the
  repository's handwritten regex/comparison logic;
- the accepted neutral file-transaction engine plus mature `filelock` and OS
  atomic replace primitives for cross-file stale-state/rollback semantics.

SVC code owns only the domain rule that selects a migration and generates an
explicit patch. For the one-profile base, the patch tests schema/profile facts,
moves `/svc_version` to `/corpus_version`, moves the selected target map to
`/dev/targets`, removes the obsolete profile container, replaces any resolved
profile token strings, and updates `schema_version`. The local patch follows
the same standard operations.

Do not use an automatically generated object diff as migration authority: it
can produce valid but opaque/reordered operations. The checked-in v2 -> v3 rule
generates explicit RFC operations; the library owns their correct application
and conflict behavior.

The patched object is serialized as deterministic UTF-8 JSON with a final
newline and revalidated with the v3 strict model. A whole-file formatting
change is an explicit schema-migration effect; source-span surgery is not worth
a custom JSON editor. The neutral plan engine preserves original meaningful
file mode and exact bytes for rollback.

### Present `svc.local.json`

Schema v3 local overlays carry their own `schema_version: 3` and never a
`corpus_version`. Transform a present legacy overlay in the same plan:

```text
missing schema_version  -> schema_version: 3
dev.profile             -> removed when provably redundant
dev.profiles.<only>.targets -> dev.targets
run                     -> preserved
```

Lossless conditions:

- zero or one legacy profile only;
- a local profile selector, when present, must agree with the one profile whose
  overrides are being flattened;
- every local dev target must already exist in the migrated base; local state
  refines committed capabilities and cannot create one;
- after transformation, base + overlay must validate as one effective v3
  configuration.

When a schema-v3 base has already been pulled onto a machine with an unversioned
legacy overlay, missing local `schema_version` is recognized specifically as
the v2 convention. A single-profile overlay can still be flattened if all its
target names exist in the v3 base. Multiple profiles, selector-only state,
local-only targets, unknown fields, or an invalid merged result block without
changing either file.

An absent local overlay remains absent. An empty legacy `{}` becomes
`{"schema_version":3}` because the present file now needs an explicit format
identity.

### Transaction and results boundary

- Base v2 + present local v2 migrate in one stale-safe transaction; any
  blocker publishes zero applicable operations.
- Base v2 + absent local changes only the base.
- Base v3 + legacy local changes only the local overlay.
- Both current returns noop.
- Failure restores bytes and meaningful modes per path using the accepted
  neutral transaction engine.
- Config apply verifies only exact config after-states and effective-model
  validity. It does not claim external scripts/tests are compatible.

### Second review decision

Sir accepted, with two clarifications:

1. schema v3 mapping and exact single-profile automatic admission;
2. block multi-profile or otherwise lossy shapes instead of choosing one;
3. give local overlays their own schema marker and prohibit local-only targets;
4. replace `${dev.profile}` with its literal resolved value but treat
   `SVC_DEV_PROFILE`/direct JSON consumers as guided project work;
5. the mature stack above, explicit RFC 6902 operations, canonical whole-file
   JSON serialization, and byte/mode-exact rollback;
6. make config apply a config-state receipt, not a project-compatibility claim.

Multi-profile handling is only a legacy-v2 blocker; v3 retains no profile
concept. The implementation uses the mature migration stack above rather than
home-grown parsing, patching, or SemVer machinery.

## 3. CLI-owned guidance derivation and presentation — accepted

### One authored change-set, several projections

Sir accepted the delivery behavior but challenged a separately authored
Markdown guide per schema step. That challenge is correct: transform code,
Changie fragment, changelog prose, and a hand-maintained guide would create
avoidable drift.

Use structured Changie YAML fragments as the only authored release-change
facts. Use Changie's built-in component field as the single owning domain and
extend its custom fields only for migration-specific facts. A fragment belongs
to exactly one of `cli`, `config`, or `corpus`; a change spanning domains uses
one fragment per domain instead of one ambiguous multi-owner fragment. A
config-schema fragment has a shape conceptually like:

```yaml
kind: major
component: config
body: Flatten the project dev configuration onto dev.targets.
custom:
  Migration: guide
  FromSchema: "2"
  ToSchema: "3"
  Guidance: |-
    Update direct readers from dev.profiles.<name>.targets to dev.targets.
    Remove dependencies on SVC_DEV_PROFILE.
time: ...
```

`Migration` is closed metadata: `not-applicable` for CLI-only facts,
`not-required` when a config/Corpus change has no project migration duty, and
`guide` when a non-empty guidance block is required. Schema fields are present
only for a config-schema transition. Repository validation enforces these
cross-field rules; Changie remains the fragment capture, versioning, and
rendering tool rather than being wrapped in a second changeset system.

Changie's generated `CHANGELOG.md` remains a concise Human release summary; it
is not parsed as migration authority. The structured fragments are archived at
batch time under a package-version directory (using Changie's fragment move/
retention support) instead of being deleted after Markdown generation. The
fragment filename plus containing release is its stable change identity.

A release projection step validates the archived fragments and derives:

```text
CHANGELOG.md / changes/v*.md       concise release history
CLI migration descriptor          schema pair + ordered guidance facts
Corpus version/guidance projection only from component=corpus fragments
```

Thus config guidance is CLI-owned because it is derived from
`component=config` change facts and packaged as data with `svc_cli`; it is not
separately authored. Likewise, CLI-only fragments cannot advance or populate
Corpus migration guidance.

The existing Behavioral SemVer `kind` remains useful without conflating
versions:

- Changie's package release uses the highest `kind` across all fragments;
- the independent Corpus release uses the highest `kind` across only
  `component=corpus` fragments and does not advance when that set is empty;
- config schema steps come only from explicit `FromSchema`/`ToSchema` facts and
  are never inferred from either SemVer.

A Corpus `not-required` fragment still advances the Corpus version while
proving that no project document migration is owed. A CLI-only or config-only
fragment cannot create an empty Corpus release. This is the mechanical guard
against the false migration guidance caused by today's package-version stamp.

Existing published `changes/v*.md` files are lossy projections and cannot be
promoted back into structured authority. The retained structured history starts
at the already accepted fixed support anchor; current unreleased fragments are
classified before the first release using this model, and future batch steps
archive their original YAML.

### Derived transition descriptor

Each supported config-schema step has one derived CLI descriptor, not a generic
migration graph:

```text
from_schema       2
to_schema         3
transform         explicit SVC rule generating RFC 6902 operations
change_ids        exact archived Changie fragment identities
guidance          canonical ordered summary/guidance facts
guidance_sha256   exact canonical guidance bundle
```

The generated descriptor is a compact package resource read through
`importlib.resources`. There is no per-step Markdown file under `svc_cli`.
Default CLI text renders the bounded guidance directly from the descriptor. It
is not placed under `src`, not indexed by the Corpus catalog, and not
accessible through `svc lookup`.

The schema pair is the migration identity. CLI distribution version is useful
diagnostic provenance but does not select the transform. The plan digest binds
source file states, the exact patch/effects, target schema, and guidance hash;
changing any one invalidates the continuation.

### Rendered guidance boundary

The descriptor combines the ordered `Guidance` blocks for the exact schema
step with mechanically derived automatic effects. The default renderer makes
that information concise and complete enough for an Agent/Human to handle
project-owned consumers. For v2 -> v3 it names:

- exact automatic base/local file transformations;
- `dev.profiles.<name>.targets` -> `dev.targets` for direct JSON consumers;
- removal of `dev.profile`, `${dev.profile}`, and `SVC_DEV_PROFILE` semantics;
- the optional new target-local `stop` field, explicitly not synthesized;
- legacy shapes outside the automatic path;
- the safe sequence for making scripts temporarily compatible, applying the
  config plan, and running project-owned checks.

It does not search the project, list guessed affected files, or prescribe
project-specific edits. Ordinary tools such as `rg`, ast-grep, and the
project's test commands remain the Agent's context/verification tools.

### Default text: deliver, do not make the caller rediscover

Do not add `--guide`, `--explain`, a CLI-doc lookup namespace, or an installed
filesystem path contract. `svc upgrade --target config` is already the exact
low-frequency migration intent. Its default plan text includes the complete
bounded guide after a compact plan header and before the apply continuation.

This intentionally differs from ordinary status output: migration guidance is
the semantic payload the Agent needs, not incidental verbosity. Guidance blocks
are required to stay bounded; one supported multi-step upgrade emits applicable
blocks once in schema order.

Conceptual shape:

```text
SVC project config upgrade: schema 2 -> 3
Repository: /repo

Automatic changes:
  rewrite svc.json       schema 2 -> 3
  rewrite svc.local.json legacy overlay -> schema 3

Project migration guidance (config-v2-to-v3, sha256:...):
  ...complete bounded guide...

Would change (2):
  ...exact planned file effects...

Apply with:
  svc upgrade /repo --target config --apply <digest>
```

Default successful apply output does not repeat the guidance. It returns the
schema transition, guidance identity/hash, realized config effects, exact config
postcondition, and a project-check reminder without claiming those checks
passed.

### Compact JSON

JSON is for CI/scripts and does not embed migration prose. It includes a
compact guidance-bundle identity such as:

```json
{"from_schema":2,"guidance":{"id":"config-v2-to-v3","sha256":"..."},"target":"config","to_schema":3}
```

The exact automatic operations and blockers remain structured. The absence of
guidance prose in JSON is intentional: scripts apply exact config state; they do
not perform semantic project migration. An Agent needing guidance uses the
self-contained default representation.

### Third review decision

Sir accepted:

1. structured, archived Changie fragments as the only authored migration facts;
2. one owning Changie component per fragment, with separate fragments for a
   cross-domain change;
3. one generated CLI-owned data descriptor per supported config-schema step,
   coupled to the transform by schema pair, fragment identities, and hash, but
   no per-step Markdown file under `svc_cli`;
4. default config-upgrade plan includes the complete bounded guidance;
5. no `lookup`, `--guide`, `--explain`, or package filesystem path interface;
6. compact JSON carries guidance identity/hash but not prose;
7. apply receipt names the guidance and config postcondition without claiming
   project checks passed.

The config target's responsibility and information-delivery shape are closed.
Review returns to the unified upgrade router's target-selection/terminal output
before the broader implementation plan.

## Evidence boundary

All real project inspections were read-only. No base or local configuration
was rewritten.
