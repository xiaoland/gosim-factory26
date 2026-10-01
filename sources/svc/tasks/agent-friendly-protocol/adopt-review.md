# `svc adopt` Command/Output Review

> Interface note: this target-specific design now sits behind the accepted
> `svc upgrade --target corpus` interface. The Corpus semantics remain
> relevant; the public `svc adopt` command name is superseded.
>
> **Implementation status:** do not implement the public `svc adopt` candidate
> below. It is retained only as the evidence/semantic precursor to the accepted
> Corpus target of `svc upgrade`.

## Scope

This review starts from the state transition owned by `svc adopt`. It does not
inherit init's public plan or result shape merely because both commands can use
the same neutral file-transaction engine.

No product implementation is authorized by this document.

## 1. Actual state and command purpose — candidate

### Current implementation

The current grammar is:

```text
svc adopt [version] [repo] [--apply PLAN_DIGEST] [--json]
```

`plan_adopt` accepts only the version packaged with the running CLI. A supplied
different version is blocked as `corpus-version-unavailable`. When the project
is schema-v2 and its recorded `svc_version` differs, the plan replaces only
that JSON string span in `svc.json`; it does not apply migrations, rewrite dev
or run declarations, or inspect Consumer-owned work. A missing or invalid base
configuration blocks the plan.

The two optional positional arguments create an avoidable ambiguity:
`svc adopt /path/to/project` treats the path as `version`, even though the only
adoptable version is already determined by the Corpus exposed by this CLI
distribution (or source-tree catalog).

### Real Consumer evidence

Read-only source runs on 2026-08-08 found:

| Real project | Recorded baseline | Available Corpus catalog | Current adopt plan |
| --- | --- | --- | --- |
| InKCre client-web | `10.0.1` | `11.0.1` | one `svc.json` version-span write |
| InKCre core-py | `10.0.1` | `11.0.1` | one `svc.json` version-span write |
| InKCre docs | `10.0.1` | `11.0.1` | one `svc.json` version-span write |
| SFP7 Camera | `11.0.1` | `11.0.1` | noop |
| Anana mvp-HA | absent | `11.0.1` | blocked; init required |

A bounded search found generated guidance telling participants to inspect
status and migration guidance before adopt, but no retained Consumer script or
task that actually applies `svc adopt`. The command therefore has a coherent
state-model purpose, but not yet repeated operational-usage evidence. Do not
invent a Human-to-Agent approval story to justify it.

### Smallest owned transition

`svc adopt` advances one durable project fact:

```text
recorded corpus baseline: behind -> current available Corpus
```

That fact lets later Humans and Agents distinguish “this project still owes a
Corpus transition review” from “the project records the current Corpus
obligations as its baseline.” It does not prove that migrations were performed,
that Consumer-owned files are correct, or that root status is healthy. Those
claims remain outside the command's authority.

The valid source states are deliberately narrow:

- `behind` -> plan one bounded `svc.json` version-span mutation;
- `current` -> noop;
- `ahead` -> blocked, because the available Corpus cannot authorize a
  downgrade;
- absent/invalid/schema-blocked -> blocked with the owning recovery command or
  fact.

This is a declaration boundary, not a general migration framework and not a
Human authorization mechanism. The caller is responsible for deciding that
the project is ready to record the transition; SVC makes the resulting state
change explicit, stale-safe, and inspectable.

### What is actually recorded, and who consumes it?

The current schema-v2 storage is the committed top-level field in `svc.json`:

```json
{"schema_version":2,"svc_version":"10.0.1"}
```

An adopt from Corpus `10.0.1` to `11.0.1` changes only that baseline value. The
name `svc_version` incorrectly conflates Corpus and CLI concerns. The next
configuration schema should call it `corpus_version`; config migration renames
the field without advancing its value. `schema_version` separately describes
the CLI-owned configuration format.

The least misleading name for this fact is the project's **last reviewed SVC
behavioral baseline**: the newest Corpus release whose changed project
obligations a caller asserts have been evaluated and, where applicable,
handled. It is not the installed CLI version, a runtime selection, proof of a
migration, or the freshness of generated integration.

Today the concrete consumer of this field is root `svc status`, which compares
it with the running Corpus and reports an adoption transition as pending. No
real Consumer script found in the reviewed projects branches on
`svc_version`, and `adopt` stores no migration evidence beyond the version
number. Thus the command's current value is a durable cross-participant
checkpoint, not automation.

That creates an explicit product-admission test:

- If SVC releases really impose behavioral obligations that a project may
  intentionally remain behind on, the committed checkpoint prevents a newer
  CLI distribution from silently implying those Corpus obligations were
  reviewed.
- If SVC cannot identify such obligations or no workflow meaningfully consumes
  the distinction, `svc_version` and `svc adopt` are ceremony. In that case the
  simpler design is to remove the command and stop presenting package version
  difference as project state.

`init` must not advance this field merely because it refreshed SVC-owned
markers: that would claim completion of a broader behavioral review which init
did not perform. But this separation only justifies `adopt` if the reviewed
baseline itself survives the admission test above.

### Corrected product role: migration handoff and closure

Sir supplied the missing real requirement: Corpus changes can require semantic
migration of project SVC document instances such as PRD, Product TDD, and Unit
TDD. SVC CLI must not edit those documents because selecting relevant facts,
reconciling project intent, and deciding the new durable wording require an
LLM and/or Human. That does not make adopt useless; it changes adopt from a
version setter into the bounded handoff and closure for that work.

The smallest useful sequence is:

```text
status detects baseline behind
  -> adopt plan names exact from/to Corpus delta
  -> plan names exact packaged change/migration references
  -> Agent/Human reads those references and migrates project-owned SVC truth
  -> caller rechecks project-specific results
  -> adopt apply records the current reviewed baseline in svc.json
```

The CLI supplies the authoritative Corpus delta and exact lookup continuations;
the Agent/Human supplies project interpretation and edits. Adopt apply remains
a caller assertion that this semantic work is complete, not a false validator
of PRD/TDD content.

To support this role, the current command is insufficient. Its plan must expose
at least:

- exact `from` and `to` Corpus versions;
- the relevant packaged release changes and migration-guide references for
  that interval, with exact `svc lookup --path ...` continuations;
- independently diagnosed CLI configuration state and managed-integration
  state, without presenting either as part of the Corpus delta;
- the only SVC-owned apply effect: update the baseline field after the caller
  has completed project-owned work.

It should not inline an unbounded Corpus or attempt to discover every project
document instance. Project context remains the caller's/tooling's job. The
adopt plan digest may bind the exact Corpus/migration references plus its one
mechanical effect; it cannot and must not claim to bind the semantic document
edits.

This gives the project `corpus_version` baseline a real consumer: it selects the
Corpus interval whose behavioral changes the next participant must evaluate.
Retaining the command now depends on providing that exact interval metadata,
not on the old naked version-span write.

### Corpus/CLI boundary

Corpus means the canonical content under `src/` and its read-only catalog
projection. SVC CLI means the runtime under `svc_cli/`, including command
grammar, configuration models, execution protocols, and config-schema
transforms. One built distribution currently ships both and stamps them from
one release version, but that packaging fact does not merge their ownership or
state:

```text
CLI distribution version         executable/package fact
available Corpus version         src/catalog content fact
project Corpus baseline          svc.json corpus_version (legacy: svc_version)
configuration schema version     svc.json schema_version, owned by svc_cli
```

Adopt compares only the available Corpus version with the project Corpus
baseline. A configuration parse failure may prevent a safe write because the
baseline is stored in `svc.json`, but config migration is not a Corpus
migration step and must not appear among Corpus change references.

### Candidate grammar and ownership

Use:

```text
svc adopt [<repo>] [--apply <plan-digest>] [--json]
```

Remove the positional `version`:

- the running CLI exposes one exact packaged/source Corpus version;
- current code cannot adopt any other supplied version;
- the plan can state the exact `from` and `to` baselines;
- a single optional repository position matches `init` and `status` and makes
  `svc adopt /path/to/project` unambiguous.

Do not add `--version`: it would preserve a choice the command cannot honor.
Historical-Corpus adoption would require actually running that Corpus version,
not asking a newer executable to impersonate it.

`adopt` owns only the exact baseline span in the committed base `svc.json`. It
does not own:

- managed integration repair (owned by `init`);
- schema/configuration migration;
- `svc.local.json` mutation;
- migration discovery or execution;
- Consumer-owned source, documentation, runtime, or package installation;
- project-health certification.

### First review decision

The reviewed behavioral baseline has a real project role because it selects
the Corpus changes that an Agent/Human must apply to project-owned SVC truth.
The corrected candidate retains adopt, but requires it to surface that exact
migration interval and packaged references before it may record the new
baseline. Configuration schema migration is a separate CLI protocol lifecycle
described in `config-migration-review.md`; init repair remains a separate
managed-integration lifecycle. Root status may report all of them together,
but adopt must not collapse them into one migration domain.

## Evidence boundary

The real-project commands above were read-only plan invocations. No Consumer
project was mutated. Temporary tests can verify mechanics later, but they do
not establish real adoption behavior.
