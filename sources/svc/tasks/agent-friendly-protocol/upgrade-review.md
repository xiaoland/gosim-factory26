# `svc upgrade` Unified Interface Review

## Scope

The internal state topology keeps CLI configuration and Corpus adoption
separate. This review asks how much of that topology should be exposed in the
public command interface. A simple interface must not collapse the underlying
authority or falsely combine their effects.

No product implementation is authorized by this document.

## 1. One project-upgrade intent, two exact targets — accepted

### Why the earlier commands are too literal

`svc adopt` is accurate for a Corpus baseline but not for a configuration
format: a project does not “adopt config.” Exposing both `svc adopt` and
`svc config migrate` makes callers learn the internal topology before they can
express the ordinary intent “bring this project's SVC state forward.”

Use one project-facing command:

```text
svc upgrade [<repo>] [--target <config|corpus>]
            [--apply <plan-digest>] [--json]
```

`upgrade`, not `adopt`, is the common verb. The target retains exact semantics
when selection is necessary:

- `config`: CLI-owned deterministic configuration-schema migration;
- `corpus`: Agent/Human-owned semantic migration against `./src` changes,
  followed by recording the project's Corpus baseline.

The target is not required for the common path. Without `--target`, the command
inspects both dimensions and chooses the next mechanically valid stage:

1. no pending dimension -> noop;
2. only one pending dimension -> return that target's exact plan;
3. both pending -> return the config plan first and report Corpus migration as
   still pending; after config apply, the same `svc upgrade <repo>` invocation
   advances to the Corpus stage;
4. config cannot be identified/migrated safely -> block config and preserve any
   Corpus-delta information that can still be determined without guessing.

An explicit target exists for inspection, scripting, and recovery, not because
ordinary callers must understand the topology. Every apply continuation names
its target even when selection was implicit, so a digest cannot move from one
upgrade domain to the other:

```text
svc upgrade /repo --target config --apply <digest>
svc upgrade /repo --target corpus --apply <digest>
```

The command never upgrades the installed CLI distribution. Package managers
remain the owner of that lifecycle. Root and command-local help must call this
“project SVC state” to avoid the conventional interpretation that `upgrade`
updates the executable.

### Shared shell, separate engines

The public command is a router, not one combined migration transaction:

```text
svc upgrade
  -> config target: svc_cli config-schema transformer
  -> corpus target: Corpus delta delivery + baseline recorder
```

The two targets may share neutral file transaction mechanics and presentation
conventions, but not plan identity, blockers, completion claims, or apply
effects. A config apply never advances the Corpus baseline. A Corpus apply
never rewrites the CLI configuration shape.

This preserves the earlier law: same semantics receive the same names and
owners; different semantics remain visibly distinguishable at the point where
the distinction affects action.

## 2. Independent version authorities — accepted

### Current conflation

The current builder passes the Python distribution version directly into
`catalog_bytes`; source fallback also derives the catalog version from the
distribution. Current names include `Catalog.svc_version`,
`packaged_svc_version`, and project `svc_version`.

This creates the exact false transition Sir identified:

```text
CLI implementation changes, ./src unchanged
  -> distribution version increments
  -> catalog version increments anyway
  -> project appears Corpus-behind
  -> no real Corpus migration guidance exists
```

Historical tags `v10.0.0` through `v11.0.0` carried
`src/manifest.json`, including a Corpus-looking version and migration path, but
that file also described CLI telemetry/dev behavior and was deleted when tags
became release authority. Restoring that mixed manifest would repeat the same
domain error.

### Target authorities and names

Use four explicit facts:

```text
cli_distribution_version    Python package/executable release
corpus_version              canonical ./src content release
project_corpus_version      project's last reviewed Corpus baseline
config_schema_version       svc_cli configuration grammar
```

The exact public nesting can stay compact (`cli.version`,
`corpus.available_version`, `corpus.project_version`,
`configuration.schema_version`), but implementation owners and serialized
project fields must not use a generic `svc_version`.

The next config schema can rename project `svc_version` to `corpus_version`
without changing its value. Catalog projection likewise reads a canonical
Corpus version from `src`, not from package metadata. A small Corpus-owned
release/migration index under `src` maps Corpus versions to exact guidance; it
contains no CLI configuration or execution changes.

Release behavior then becomes unambiguous:

| Release content | CLI version | Corpus version | Config schema | Project result |
| --- | --- | --- | --- | --- |
| CLI implementation only | advances | unchanged | unchanged | no project upgrade |
| CLI config format | advances | unchanged | advances | config target only |
| Corpus text/behavior | advances to distribute | advances | unchanged unless separately needed | corpus target only |
| Both domains | advances | advances | may advance | ordered independent targets |

Corpus releases with no project migration obligation still carry an explicit
Corpus-owned `not-required` fact. They must not rely on “no guide was found,”
which is indistinguishable from broken release metadata.

### First review decision

Sir accepted:

1. replace the two public candidates with `svc upgrade` and an optional
   `--target config|corpus`;
2. make the default command advance one exact stage, choosing config before
   Corpus only when both are pending;
3. keep target plans/applies separate even behind one router;
4. establish an independent canonical `corpus_version` under `src` rather than
   stamping the catalog with CLI distribution version;
5. remove generic `svc_version` naming from the next config/catalog protocols.

The public shell and version authorities are closed. Target-specific output
follows only after the Corpus release/migration index and exact CLI config
transform are stable.

## 3. Smallest Corpus release/migration index — accepted

### Required facts

The Corpus needs one canonical, source-owned index under `src/`. It must let a
caller answer, without Git history or keyword search:

```text
What Corpus version is available?
Which Corpus releases lie after the project's baseline and at/before it?
Which exact migration guides apply to each release?
Was guidance explicitly unnecessary, or is release metadata broken?
```

The index does not describe CLI distribution changes, configuration schemas,
commands, or runtime protocols merely because the wheel distributes both
domains. It does not inventory project document instances or prescribe their
edits.

### Candidate source shape

Use one small release projection in the SVC framework repository itself:
`src/version.json`. It is derived at release preparation from retained
`component=corpus` Changie fragments, becomes part of the canonical released
Corpus, and is packaged read-only by SVC CLI. Corpus guidance blocks are
likewise projected into exact Markdown paths under `src/migrations/`; those
generated Corpus documents are appropriate there because semantic Corpus
migration is itself document work. Consumer repositories do not copy the index;
they record only their own `corpus_version` in `svc.json`.

```json
{
  "schema_version": 1,
  "releases": [
    {
      "version": "11.0.0",
      "previous_version": "10.0.2",
      "migration": {
        "status": "guide",
        "paths": ["migrations/11.0.0.md"]
      }
    },
    {
      "version": "11.0.1",
      "previous_version": "11.0.0",
      "migration": {"status": "not-required"}
    },
    {
      "version": "12.0.0",
      "previous_version": "11.0.1",
      "migration": {
        "status": "guide",
        "paths": [
          "migrations/agent-task-performance-analysis.md",
          "migrations/local-trust-boundary.md"
        ]
      }
    }
  ]
}
```

The current Corpus version is the last release entry; it is not duplicated in
a second field. `previous_version` makes gaps, forks, reordering, and accidental
history deletion mechanically invalid. Multiple guide paths support one
release with independent migration concerns without introducing a migration
graph.

`migration.status` is a closed distinction:

- `guide`: at least one normalized Markdown path under `src/migrations/`;
- `not-required`: the release explicitly has no project document migration
  obligation.

Missing migration metadata is invalid. “No matching guide” is never interpreted
as `not-required`.

### Projection and release rules

The catalog builder reads `src/version.json`, validates the complete release
chain, guide paths, and current guide content, and projects `corpus_version`
plus the stable release records into the wheel catalog. It no longer accepts
Python package version as the Corpus version.

A Corpus change requires a new Corpus release entry. A CLI-only/config-only
release does not edit this file, even though a new wheel may package the same
Corpus bytes. Release validation fails when canonical Corpus content changes
without advancing the Corpus record, or a guide record points at absent or
unindexed content.

The index is not a changelog replacement and is never derived by parsing
`CHANGELOG.md`. The same retained structured `component=corpus` fragments
produce the concise changelog entry, release-chain record, and generated
migration guidance. Ordinary Corpus documents remain available through
`lookup`; the index only provides exact version ordering, applicability, and
continuation identity.

### Projection-source follow-up decision

Sir accepted one structured release-change source with separate projections:

1. versioned Changie YAML fragments are the authored change facts;
2. each fragment has one owning `cli|config|corpus` component, with separate
   fragments when one product change crosses authorities;
3. generated changelog Markdown is never parsed back into migration authority;
4. config fragments generate a compact CLI migration descriptor, not a
   per-schema-step Markdown file under `svc_cli`;
5. Corpus fragments alone advance Corpus SemVer and generate
   `src/version.json` plus referenced Corpus migration documents;
6. config schema steps come from explicit schema-pair metadata rather than
   package or Corpus SemVer.

Published Markdown-only history is too lossy to reconstruct these facts. The
retained structured history begins at the fixed supported anchor already
accepted below; current unreleased fragments must be classified before the
first release using this model.

Follow-up correction: Changie does not make retained/versioned fragments
immutable. Release version/order/change association remains stable, while the
`Guidance` content is living documentation that may be clarified or corrected
and reprojected in a later Corpus patch. `src/version.json` does not seal
permanent paths or guide hashes; each upgrade plan binds the current reference
and content it actually presented.

### Upgrade selection

For project baseline `B` and available Corpus `C`, the Corpus target selects
the unique ordered releases in `(B, C]`. It reports every guide path and every
explicit `not-required` hop. If `B` is absent, ahead, not on the retained
chain, or the chain is incomplete, it blocks rather than inventing a range.

Guide content is read through exact path lookup. Default upgrade output should
name compact release/guide references and exact continuations; it should not
inline all Markdown and consume the Agent's context window.

### Third review decision

Sir accepted, with the canonical filename corrected from `src/corpus.json` to
the contextually sufficient `src/version.json`:

1. one canonical `src/version.json` release chain rather than package-version
   stamping or one mutable current-only manifest;
2. current Corpus version derived from the last record;
3. closed `guide|not-required` migration status with one or more exact guide
   paths;
4. strict contiguous-chain and referenced-content validation;
5. no CLI/config facts and no generic consumer-file migration graph.

The next Corpus question is retention: whether the installed catalog must keep
the entire published chain or a declared supported adoption horizon. That must
be decided before ahead/too-old recovery output.

## 4. Release-chain retention — accepted

Retain the complete Corpus release chain from the first baseline supported by
this upgrade protocol. Do not introduce a moving “last N major
versions” or time-based horizon without demonstrated package-size or obsolete-
guidance pressure.

The first record's `previous_version` is the fixed supported anchor. A project
at that version or any recorded release has an exact path to the available
Corpus. A project baseline older than the anchor or absent from the chain is
reported as `unsupported-corpus-baseline`; SVC must not guess a migration range
or silently treat it as fresh initialization.

Once published, the release record remains in the chain and retains migration
coverage. The release fact is stable; guide content and its current projection
path may improve as living migration documentation:

- old projects and long-lived branches can still determine the complete
  semantic delta;
- an Agent receives the same release/change identities and the newest packaged
  guidance regardless of which older baseline it starts from;
- no policy machinery, horizon negotiation, or “upgrade through an older CLI
  first” protocol is needed;
- metadata is tiny, while guide content is legitimate Corpus history rather
  than runtime baggage.

This is retention of guidance, not a promise that current CLI config migrators
support every historical configuration schema. Config-schema support remains a
separate CLI policy and may have a bounded explicit range.

If accumulated guidance later creates a measured distribution problem, SVC can
introduce an explicit minimum supported Corpus baseline in a Behavioral SemVer
release. Until then, truncation would add complexity and make long-lived project
state less maintainable without evidence.

### Fourth review decision

Sir accepted:

1. retain the complete chain from one fixed initial supported anchor;
2. never prune published records or a release's migration coverage silently;
3. treat off-chain/older baselines as unsupported, not as init or noop;
4. keep Corpus-history retention independent from CLI config-schema support.

The Corpus metadata topology is closed. Review moves to the exact CLI config
v2 -> next-schema transform.

## 5. Explicit target versus default ordering — accepted

### Default order is routing, not an authority boundary

Without `--target`, `svc upgrade` reduces the ordinary decision to one next
stage: config before Corpus when both are pending. That ordering prevents the
common caller from having to understand two version dimensions and ensures the
next invocation observes the new config shape.

An explicit target has a different information service: execute or inspect the
exact requested upgrade domain. It should therefore override the router's
default order. Otherwise `--target corpus` would be a misleading spelling for
“show config again” whenever config migration is pending.

The rule is:

```text
no --target       choose the next stage: config first, then corpus
--target config   plan/apply only the config target
--target corpus   plan/apply only the Corpus target
```

This does not let an explicit target bypass its own prerequisites. Config still
requires an admitted source shape and lossless transform. Corpus still requires
a recognizable committed base, a project baseline on the retained chain, and
complete release/guidance metadata. An unreadable or unknown base schema blocks
Corpus because SVC cannot safely locate or update the baseline field.

An unrelated config blocker does not automatically block an explicit Corpus
target. For example, a recognized schema-v2 base with multiple dev profiles may
be outside the automatic config transform while its legacy `svc_version` field
is still exact. Corpus apply can update only that field; a later config migration
renames the already-updated value to `corpus_version`. Likewise, a malformed
local overlay does not prevent an exact Corpus baseline update in the valid
committed base. Neither path silently changes config structure.

### Natural-project pressure

The current client-web project has a valid schema-v2 base at baseline `10.0.1`
while the available packaged version is `11.0.1`. Under the accepted v3 design,
both config and Corpus dimensions would be pending, so the targetless command
selects config. The current read-only `adopt` plan proves the baseline itself is
an exact one-file update; after the redesign, an explicit Corpus request can
still address that independent fact rather than being redirected to config.

This is not evidence that Corpus should normally go first. It proves only that
the two targets remain independently actionable when their own facts are
sound—the reason the explicit selector exists.

### Post-apply handoff is part of the router receipt

Sir's condition on config-first routing is essential: after a successful config
apply, the receipt must report that Corpus remains pending when it was also
pending in the selected plan. Otherwise the simple targetless interface hides
the second half of the caller's original “bring project SVC state forward”
intent as soon as the first stage completes.

The plan binds the other target's expected post-apply disposition. A config
transform preserves the project Corpus baseline, so a plan that observed both
targets pending can prove that Corpus remains pending after the exact config
postcondition. The apply receipt reports that bounded fact and the ordinary
continuation, without computing, inlining, or applying a Corpus plan:

```text
Remaining: Corpus upgrade pending (10.0.1 -> 11.0.1)
Next:
  svc upgrade /repo
```

Use the same handoff law after either selected target: a successful target apply
reports any other upgrade target still pending. This matters when an explicit
`--target corpus` intentionally runs before config as well. It is an observation
of remaining project-upgrade work, not a combined transaction or an automatic
retry.

### Fifth review decision

Sir accepted, with the post-apply handoff condition:

1. config-first applies only to targetless routing;
2. an explicit target ignores the other target's pending/blocked state unless
   that state destroys a fact the selected target itself needs;
3. Corpus apply updates only the baseline field appropriate to the recognized
   source schema and never performs config migration;
4. unknown/unreadable committed configuration blocks Corpus rather than
   guessing where authority lives;
5. every successful target apply reports another still-pending upgrade target,
   and config-first apply therefore preserves a direct continuation to Corpus.

This boundary is closed. The next review shapes targetless and target-specific
plan/apply text without conflating selection with execution.

## 6. Selected plan states — accepted

### Mechanical applicability is not migration completion

The old `adopt` plan reports `ready` as soon as SVC can rewrite one version
field. That word is misleading for both accepted upgrade targets:

- config v2 -> v3 is mechanically transformable, but real client-web/core-py
  code still reads the old profile path and requires Agent/Human migration;
- a Corpus delta may require semantic edits to project PRD/TDD documents that
  SVC cannot perform or verify.

A valid plan digest proves only that the selected SVC-owned mutation is exact.
It does not prove that project-owned migration guidance has been completed.

Use four selected-plan states:

```text
noop                 selected/project upgrade state is already current
ready                pending target has no project migration duty
migration-required   exact plan exists, but bounded guidance must be completed
blocked              no safe exact plan exists
```

`migration-required` is not `blocked`: it includes the complete guidance
delivery required by that target and a valid apply continuation. The caller
uses that continuation only after completing the project-owned work. Apply is
the caller's assertion of completion; SVC records its own exact config/baseline
effect without pretending to verify every project document or script.

`ready` is reserved for a mechanically applicable transition whose structured
change facts are all explicitly `not-required`. Missing migration metadata is
invalid and blocks; it never falls through to `ready`. For a multi-release
Corpus range, any `guide` hop makes the aggregate selected plan
`migration-required`.

This yields the natural targetless sequence for the current client-web shape:

```text
svc upgrade
  -> select config
  -> migration-required (v2 -> v3 guidance + exact config plan)
  -> caller performs guided project work and applies config plan
  -> receipt reports Corpus still pending
svc upgrade
  -> select Corpus
  -> migration-required or ready from exact Corpus release facts
```

The default representation must phrase the continuation accordingly:

```text
After completing the migration guidance, apply this exact plan:
  svc upgrade /repo --target config --apply <digest>
```

It must not use the ordinary `Apply exact plan` wording for
`migration-required`.

### Sixth review decision

Sir accepted:

1. `ready` means no project-owned migration duty, not merely that SVC can write;
2. `migration-required` carries guidance plus a valid digest/continuation;
3. applying that digest is the caller assertion that guided work was completed;
4. missing guidance metadata blocks rather than silently becoming `ready`;
5. any guided hop makes a multi-step target plan `migration-required`.

These states are fixed. Their default text can now be shaped without hiding the
Human/Agent work between plan and apply.

## 7. Default selected-plan text — accepted

### One selected target, one decision

Targetless and explicit selection use the same target plan and digest. The
default representation does not explain whether the router or `--target`
selected it; that fact does not change the required work. It identifies:

- plan state, canonical repository, and selected target;
- the exact config schema or Corpus baseline transition;
- migration duty and the information needed to perform it;
- SVC's complete planned file effects;
- another target that will remain pending after this stage;
- one continuation appropriate to the state.

Do not print CLI distribution version, fragment archive paths, internal
descriptor/resource paths, patch operations, file hashes, or both automatic
and explicit-selection narratives. Those facts do not serve the migration
decision.

### Config `migration-required`

Config guidance is bounded data owned by the CLI descriptor, so the default
plan renders it completely. The real client-web shape would have this form:

```text
svc upgrade: migration-required
Repository: /Volumes/WorkSSD/Development/InKCre/client-web
Target: config (schema 2 -> 3)

Automatic config changes:
  svc_version -> corpus_version (value unchanged)
  dev.profiles.local.targets -> dev.targets
  remove dev.profile and legacy profile container
  migrate the present local overlay to schema 3

Project migration guidance (config-v2-to-v3, sha256:...):
  Update direct JSON readers from dev.profiles.<name>.targets to dev.targets.
  Replace dependencies on SVC_DEV_PROFILE; it is no longer provided.
  Review project scripts for the removed dev.profile/${dev.profile} contract.
  Run the project's own config/runtime checks after applying the config plan.

Would change (2):
  rewrite svc.json (whole config file) - schema 2 -> 3
  rewrite svc.local.json (whole local overlay) - legacy overlay -> schema 3

Reminder: this plan only migrates config; Corpus upgrade remains pending
  (10.0.1 -> 12.0.0)

After completing the migration guidance, apply this exact plan:
  svc upgrade /Volumes/WorkSSD/Development/InKCre/client-web --target config --apply <digest>
```

The exact profile literal comes from the admitted source shape; it is not a
retained v3 profile concept. Do not inline RFC 6902 operations or transformed
JSON. Semantic transforms plus complete affected files are the useful review
surface.

### Corpus `migration-required`

Corpus guides are legitimate, potentially long Corpus documents: the current
three notes total 1,437 words. Repeating them inside the plan would consume
context and duplicate `lookup`. The plan instead lists every release hop and
gives an exact read continuation for each applicable guide:

```text
svc upgrade: migration-required
Repository: /repo
Target: corpus (baseline 11.0.1 -> 12.0.0)

Corpus releases (1):
  12.0.0  guidance required
    migrations/agent-task-performance-analysis.md
    migrations/local-trust-boundary.md

Read required guidance:
  svc lookup --path migrations/agent-task-performance-analysis.md
  svc lookup --path migrations/local-trust-boundary.md

SVC will only record the reviewed Corpus baseline; it will not modify project
PRD, Product TDD, Unit TDD, or other project-owned documents.

Would change (1):
  update svc.json (corpus_version field) - record baseline 12.0.0

After completing all listed Corpus guidance, apply this exact plan:
  svc upgrade /repo --target corpus --apply <digest>
```

Every `not-required` hop is still listed compactly, because omission cannot
distinguish an explicit no-migration decision from broken history. A range with
only `not-required` hops uses `ready`, says that no project migration is owed,
and uses the ordinary `Apply this exact plan` continuation.

### Noop and blocked

Targetless noop is an aggregate result and stays short:

```text
svc upgrade: noop
Repository: /repo
Configuration: schema 3 (current)
Corpus: baseline 12.0.0 (current)
Project SVC upgrade state is current.
```

An explicit-target noop names only that target's current fact. Neither form
prints an apply continuation in default text.

A blocked plan names the selected target, every decisive blocker, zero
hypothetical file effects, and no digest/apply continuation:

```text
svc upgrade: blocked
Repository: /repo
Target: config
No changes can be applied.

Blockers (1):
  svc.json [multiple-dev-profiles] - schema 3 cannot be selected without discarding a profile

Other target: Corpus upgrade pending (10.0.1 -> 12.0.0)
Next: resolve the blocker, then recompute this target:
  svc upgrade /repo --target config
```

Blocker-specific messages own recovery detail; the renderer does not append a
generic “contact support,” “run init,” or destructive reset suggestion.

### Seventh review decision

Sir accepted, with one presentation correction:

1. automatic and explicit selection share one target plan representation;
2. config guidance is rendered completely, while long Corpus guides use exact
   `lookup --path` continuations;
3. plan text separates semantic automatic transforms from exact file effects;
4. another target's remaining work is one compact handoff fact, not a second
   inline plan;
5. noop has no default apply continuation; blocked has no digest, hypothetical
   effects, or apply continuation;
6. present another pending target as a warning/reminder, never as `Later stage`
   or wording that implies this invocation will execute it automatically.

Apply receipts remain the next separate review item.

## 8. Apply receipt and remaining-work handoff — accepted

### Receipt horizon

A successful apply receipt answers three questions without replaying the plan:

1. which exact selected target and plan were applied;
2. which SVC-owned postconditions were actually verified;
3. what project-upgrade work, if any, remains for another participant.

Its terminal status is `applied`, not `migration-completed`. For a
`migration-required` plan, invocation of the selected digest is the caller's
assertion that the listed guidance was completed. SVC records that assertion
but does not claim it inspected every project document, script, artifact, or
project-owned check.

Do not repeat the full guidance, release-hop list, automatic-transform
explanation, before hashes, or generated patch operations. The plan served that
decision; the receipt serves realized effects and handoff.

### Config apply

```text
svc upgrade: applied
Repository: /Volumes/WorkSSD/Development/InKCre/client-web
Target: config (schema 2 -> 3)
Applied plan: <digest>
Migration guidance: config-v2-to-v3 asserted complete by caller; project checks not run by SVC

Changed (2):
  rewrote svc.json (whole config file)
  rewrote svc.local.json (whole local overlay)

Verification: planned file postconditions and effective schema-3 config passed

Reminder: Corpus upgrade is still pending (10.0.1 -> 12.0.0)
Next upgrade:
  svc upgrade /Volumes/WorkSSD/Development/InKCre/client-web
```

The receipt does not say the project's direct config consumers are compatible.
It names the exact guidance identity so a later participant can understand what
the caller asserted without receiving the prose again.

### Corpus apply

The complete Corpus handshake is:

```text
svc upgrade /repo --target corpus
  -> read every referenced guide
  -> Agent/Human updates project-owned SVC documents and runs project checks
svc upgrade /repo --target corpus --apply <plan-digest>
  -> SVC records only the new project Corpus baseline
svc status /repo
  -> independent project-state observation
```

The plan digest binds the selected target, current baseline/config file state,
available Corpus release range, current guide references/content, and exact
baseline after-state. It deliberately does not bind project-owned PRD, Product
TDD, Unit TDD, or other documents: editing them between plan and apply is the
expected migration work. A changed `svc.json`, Corpus range, or guidance makes
the digest stale and requires a fresh plan/review.

```text
svc upgrade: applied
Repository: /repo
Target: corpus (baseline 11.0.1 -> 12.0.0)
Applied plan: <digest>
Migration guidance: all selected Corpus guides asserted complete by caller; project documents not verified by SVC

Changed (1):
  updated svc.json (corpus_version field) - baseline 12.0.0

Verification: project Corpus baseline postcondition passed

Remaining upgrade targets: none
Next observation:
  svc status /repo
```

For a `ready` plan whose release facts are all `not-required`, replace the
assertion line with `Migration guidance: not required`; do not invent caller
work. If explicit Corpus apply ran before pending config, the receipt instead
warns that config remains pending and returns ordinary `svc upgrade /repo`.

### Shared transaction failures, target-specific facts

Reuse the neutral plan/apply vocabulary already accepted for init:

- pre-mutation digest mismatch or blocked/stale plan says no files changed and
  returns the exact target replan command;
- a failed multi-file config transaction reports `restored`,
  `external-changes-preserved`, or `uncertain` plus per-path outcomes;
- a failed one-file Corpus baseline update uses the same transaction terms
  without pretending it changed project documents;
- no failure reports another target as the next upgrade. Recovery/observation of
  the selected failed target comes first.

These names and result types should come from shared implementation owners, not
parallel init/upgrade string vocabularies. Target-specific renderers add config
schema, Corpus baseline, guidance assertion, and remaining-target facts.

### Eighth review decision

Sir accepted and confirmed the explicit Corpus handshake:

1. successful status is `applied`, never `migration-completed`;
2. a migration-required apply records an explicit caller assertion and SVC's
   narrower verification boundary;
3. receipt lists past-tense realized file/field effects but does not repeat
   guidance or plan rationale;
4. another pending target returns as a reminder plus ordinary targetless
   continuation; no remaining target returns root status as the next observation;
5. transaction conflict/failure vocabulary is shared with init, while target
   postconditions remain accurately distinct;
6. after Agent/Human completes project document migration, it runs
   `svc upgrade <repo> --target corpus --apply <plan-digest>` to record only the
   new baseline; project-owned document edits are expected between plan/apply
   and therefore are outside the digest's filesystem preconditions.

## 9. Compact JSON projection — decided

Sir delegated compact JSON without a separate field-by-field review. This is a
command-local scripts/CI projection, not a shared SVC result schema. `--json`
emits exactly one compact object with stable key order and no default text.

### Shared selected-plan facts

Use upgrade response schema version 1 for this new command. Every resolved plan
carries:

```text
schema_version: 1
command: "upgrade"
mode: "plan"
status: "noop" | "ready" | "migration-required" | "blocked"
repo: canonical repository path
target: "config" | "corpus" | null
operations: ordered exact SVC-owned file effects
remaining_targets: other still-pending target facts
```

Automatic and explicit selection of the same target produce the same plan
object and digest. Do not serialize a `selection`/`requested_target` distinction
that has no effect on the selected plan. Targetless all-current noop uses
`target:null`; explicit already-current target noop retains that target and its
target-specific facts.

`ready` and `migration-required` carry top-level `plan_digest`. `noop` has
neither an applicable operation nor digest. `blocked` has `operations:[]`, an
ordered `blockers` array, and no digest. `remaining_targets` never contains the
selected target; it describes the independent work that would remain after the
selected plan, without embedding a second plan.

Neutral filesystem operations reuse the accepted transaction projection:
`action`, repository-relative `path`, semantic `surface` and `extent`, plus
exact before/after file state, digest, and meaningful POSIX mode. Config and
Corpus renderers do not invent parallel write vocabularies.

### Config target

The selected config plan adds one target-specific object:

```json
{"command":"upgrade","configuration":{"from_schema":2,"guidance":[{"id":"config-v2-to-v3","sha256":"<sha256>"}],"to_schema":3},"mode":"plan","operations":[{"action":"rewrite","extent":"whole-file","path":"svc.json","surface":"configuration"}],"plan_digest":"<digest>","remaining_targets":[{"from_version":"10.0.1","status":"pending","target":"corpus","to_version":"12.0.0"}],"repo":"/repo","schema_version":1,"status":"migration-required","target":"config"}
```

The real operation also carries exact before/after states omitted from this
shortened example. JSON carries config-guidance identity/current-content hash,
not prose. The default text is the bounded complete guidance renderer already
accepted; a script deliberately consuming JSON owns its control flow.

### Corpus target

```json
{"command":"upgrade","corpus":{"from_version":"11.0.1","releases":[{"guides":[{"path":"migrations/local-trust-boundary.md","sha256":"<sha256>"}],"migration":"guide","version":"12.0.0"}],"to_version":"12.0.0"},"mode":"plan","operations":[{"action":"rewrite","extent":"json-field","path":"svc.json","surface":"project-corpus-baseline"}],"plan_digest":"<digest>","remaining_targets":[],"repo":"/repo","schema_version":1,"status":"migration-required","target":"corpus"}
```

Release facts use `migration:"guide"|"not-required"`. Guide references bind
their current path/content hash for this plan but are not permanent immutable
release identifiers. Corpus guide prose remains accessible through exact
`svc lookup --path`; it is not copied into JSON.

### Apply receipt

A successful apply uses `mode:"apply"`, `status:"applied"`, selected target,
selected `plan_digest`, realized operations, target-specific transition facts,
and:

```text
migration.disposition: "caller-asserted" | "not-required"
migration.guidance: exact config-guide identities or Corpus guide references
verification: {scope, status:"passed"}
remaining_targets: independent pending target facts after apply
```

The caller-asserted disposition records the accepted handshake without claiming
that SVC inspected project-owned PRD/TDD/scripts or ran their checks. The
verification scope names only exact configuration postconditions or the
project-Corpus-baseline postcondition. Do not include `healthy`, prose
continuations, repeated guidance, a generic version, or an audience marker.

Errors reuse the common compact error envelope and add selected target, digest,
repository-effect, and per-path rollback facts where relevant. They never
return a newly computed digest as an apply shortcut.

## 10. Channels, exits, and interruption — decided

Route by whether the requested information service settled, matching the
accepted init transaction law:

```text
0    ready/noop plan; successful applied receipt
2    invalid CLI grammar or target selector
3    migration-required/blocked resolved plan; digest mismatch; stale/blocked
     apply selection; configuration/Corpus state conflict with no uncertain
     repository effect
4    staging/commit/postcondition/integrity failure; failed rollback or
     uncertain final repository effect
130  caller Ctrl+C when transaction recovery did not fail
```

All resolved plans, including `migration-required` and `blocked`, use stdout.
Successful apply uses stdout. Grammar errors, apply rejections/conflicts, and
infrastructure/transaction failures use stderr. Compact JSON follows the same
channel and emits one object; the other channel stays empty. Upgrade has no
progress stream because its SVC-owned mutations are bounded local file
transactions.

`migration-required` is exit 3 because the selected plan is complete but the
Agent/Human migration duty remains before apply. A valid `noop` is exit 0. An
explicit apply against a migration-required digest is the caller assertion
already accepted; SVC does not prompt for a second confirmation.

SIGINT uses the shared transaction-safe boundary: before commit, no mutation;
after any commit, ownership-safe per-path rollback. Recovered or externally
conflicted state preserves exit 130; failed rollback/uncertain state becomes
exit 4. SIGKILL, power loss, or a second interrupt cannot promise a receipt.

## 11. Self-sufficient layered help and continuations — decided

Root help owns selection only:

```text
upgrade   Plan or apply one config-schema or Corpus-baseline upgrade stage
```

`svc upgrade --help` owns the operational contract:

- config and Corpus are independent targets behind one project-facing intent;
- without `--target`, choose config first only when both are pending and plan
  exactly one stage;
- explicit `--target config|corpus` selects only that target when its own
  prerequisites hold;
- config apply performs exact supported configuration transforms but does not
  prove project-owned config consumers migrated;
- Corpus plan references exact migration guides; Agent/Human edits and checks
  project documents, then `--apply DIGEST` records only the new baseline;
- resolved plan states, channels, and exits; transaction failure boundaries;
- default text is Agent/Human output and `--json` is one compact scripts/CI
  result.

Examples show the actual handshake:

```text
svc upgrade /repo
svc upgrade /repo --target config
svc upgrade /repo --target corpus
svc lookup --path <guide-returned-by-the-plan>
svc upgrade /repo --target corpus --apply <plan-digest>
```

After a successful apply, another pending target continues with ordinary
targetless `svc upgrade /repo`; no remaining target continues with
`svc status /repo`. Failed apply output first owns selected-target recovery and
does not route to another target.

The `svc upgrade` product and command/output protocol are now closed. No product
implementation is authorized by this document.

## Evidence boundary

The version/build findings come from current source and historical release
tags. No release metadata, config, or Consumer project was mutated.
