# Core CLI Interface Consistency Review

## Purpose and scope

This audit consolidates the accepted command reviews into one implementable
core interface. It does not reopen commands for symmetry, invent a universal
result schema, or pull specialist `telemetry`/`analysis` output into this unit.

Historical/current-surface evidence may still mention commands that exist in
today's code. The target contract below is authoritative for the later
implementation plan. No product implementation is authorized by this document.

## 1. Final public tree

```text
svc --version

svc lookup (--list [PREFIX] | --path PATH | --keyword QUERY | --regex REGEX)
           [--scope path|both] [--limit N] [--json]
svc status [REPO] [--json]
svc init [REPO] [--apply PLAN_DIGEST] [--json]
svc upgrade [REPO] [--target config|corpus] [--apply PLAN_DIGEST] [--json]

svc dev identity [--repo REPO] [--json]
svc dev status [TARGET] [--repo REPO] [--json]
svc dev ensure TARGET [--repo REPO] [--json]
svc dev stop TARGET [--repo REPO] [--json]

svc run ENTRY [--repo REPO] [--json]
svc run --follow EXECUTION_ID [--repo REPO] [--json]
svc run --inspect EXECUTION_ID [--repo REPO] [--json]

# Preserved specialist surfaces, explicitly outside this output-refactor scope
svc telemetry agent-thread list|export ...
svc analysis query|read ...
```

Remove public `self-update`, `adopt`, `dev setup`, lookup `--name|--all`, and
init `--agent`. Do not add root `identity`, a generic logs command, an
acceptance/check/task command, a config subcommand, or an all-target dev
launcher/stopper.

Remove generated SVC CLI Skill creation and health coupling. During retirement,
status/init may distinguish a clean generated legacy Skill, a recognizable
modified artifact, and an unproven Consumer file solely to delete the clean
artifact safely. This is migration observation, not a retained Skill feature.

## 2. Version and project-state vocabulary

Use four authorities and no generic `svc_version`:

```text
cli_distribution_version
corpus_version
project_corpus_version
config_schema_version
```

Public projections may nest them compactly:

```text
cli.version
corpus.available_version
corpus.project_version
configuration.schema_version
```

`svc --version` reports only the CLI distribution version. It does not report a
Corpus, project baseline, or configuration schema. Root status owns their
relationship and exposes independent dimensions:

```text
cli             source-tree | current | mismatch
configuration   missing | current | invalid | schema-blocked | orphan-local
corpus          absent | behind | current | ahead
integration     current | repairable | blocked
```

The overall disposition and primary continuation are derived from, but never
replace, these facts. Status removes Human-authorization fields and never
routes package installation through SVC. It routes supported config/Corpus
migration through `svc upgrade`, integration establishment/repair through
`svc init`, and runtime capability work through the relevant `dev` command.

The committed v3 field is `corpus_version`. Init JSON uses
`corpus_baseline:{disposition,version}`. Config migration preserves that value
while renaming legacy v2 `svc_version`; Corpus upgrade alone advances it.

## 3. Workspace, domain, execution, and log vocabulary

`svc_cli/workspace.py` is the sole workspace identity owner. The public
`workspace` object has six meanings:

```text
root
namespace_id
repository_kind
repository_id
worktree_id
instance
```

`repository_id` replaces implementation-shaped `repo_common_id`; Git common
directory derivation is private. Real Consumer scripts continue to read the
unchanged `workspace.instance`. When flattened into an execution receipt, that
same value is `workspace_instance`, never `workspace_id` or `worktree_id`.

Keep domain language distinct:

| Run | Dev | Neutral private mechanism |
| --- | --- | --- |
| `entry` | `target` | `subject` |
| `effective_entry_digest` | `effective_target_digest` | `intent_digest` |
| execute child | ensure/stop capability | `operation` |
| child exit/receipt | readiness/capability result | execution attempt |

The neutral execution mechanism uses `execution_id`, `domain`, `operation`,
`subject`, `workspace_instance`, `intent_digest`, and `coordination_key`.
Coordination key, intent identity, and execution ID remain different concepts.
Public projections restore `entry` or `target`; they never expose generic
`subject` merely because storage needs it.

One `ExecutionLogReference` owner supplies `stream`, `path`, and observed
`bytes`. Domain renderers may say startup log, stop log, stdout, or stderr, but
must not rename the underlying facts or infer project artifact declarations
from native output. Saved PIDs never become later stop authority.

## 4. Presentation and channel law

There is no universal success schema. Choose presentation from the result's
semantics:

- lookup list/search results are bounded navigation/match forms; exact path is
  raw Markdown;
- status is a purpose-ordered observation;
- init/upgrade are plan/apply forms with exact mutation and continuation;
- dev identity is a semantic identity chain;
- dev status compares readiness; ensure/stop combine sparse live coordination,
  one terminal capability result, and stable log references;
- run preserves native stdout/stderr plus SVC lifecycle text and exact receipts.

Default text is the Agent/Human interface. `--json` means one compact exact
CI/script value, not “Agent mode.” JSON suppresses progress/native display when
the command contract says it is a terminal receipt. Arrays use semantic names
such as lookup `entries|candidates|matches`; do not force unrelated commands
into a generic `results` field.

Shared channel rule:

1. a resolved result uses stdout even when its command-specific disposition
   requires action and exits 3;
2. invalid grammar/selection, state conflicts that prevent a requested action,
   and infrastructure/integrity failures use stderr;
3. sparse live coordination uses stderr so terminal stdout remains capturable;
4. run is the deliberate exception that preserves Consumer native channels and
   passes through a normally exited child code;
5. no command emits JSONL without a real event-stream contract.

Examples of resolved stdout/3 results include unhealthy root/dev status,
blocked init plan, migration-required/blocked upgrade plan, and expected
non-ready ensure/stop capability outcomes. Lookup zero matches is a normal
stdout/0 search result. Command-specific reviews own exact exit mapping; shared
infrastructure/uncertain recovery remains exit 4 and ordinary grammar remains
exit 2.

Long or multi-participant native evidence is returned by stable file reference.
Default output may show bounded decisive native evidence, but it must state
truncation and preserve the exact log path for ordinary tools.

## 5. Common error transport, command-local results

Core commands that support `--json` use one compact recognized-error envelope,
including grammar errors:

```json
{"error":{"code":"...","details":{},"message":"..."},"schema_version":1}
```

Command/domain details remain inside `details`; this common transport does not
make success objects share a schema. Default errors use
`svc: <code>: <message>` plus selected purpose-written detail lines. Never dump
prettified JSON details into default text or print a text hint beside JSON.

The specialist analysis protocol remains outside this refactor and may retain
its existing strict tool envelope. Native run child failure is a receipt/exit,
not rewritten as an SVC error.

## 6. Self-sufficient help and project trigger

Root help selects commands and states that `svc <command> --help` owns the
complete operational contract. Each core command help covers:

- intent and important non-ownership boundary;
- complete grammar and defaults;
- state-changing or Consumer-execution effects;
- result forms, stdout/stderr, and exit classes;
- valid continuations and Ctrl+C behavior when lifecycle-relevant;
- default Agent/Human text versus compact scripts/CI JSON.

`svc lookup` retrieves Corpus guidance and never repairs incomplete CLI help.
Its help explicitly distinguishes Corpus content from CLI usage. The generated
AGENTS block contains only a short trigger describing when SVC CLI/Corpus is
relevant and points to CLI help/lookup by purpose; it does not embed a CLI
manual, force list-first, or force JSON. The retained generated docs/index block
is Human navigation and follows the same boundary.

## 7. Shared implementation owners without semantic collapse

Implementation must deepen a few shared owners rather than duplicate facts:

- canonical workspace resolver/projection;
- neutral exact file-state transaction, lock, rollback, and interrupt engine
  shared by init and upgrade;
- neutral execution-attempt/store/log mechanics shared by run and dev;
- independent CLI distribution, Corpus release index, project Corpus baseline,
  and configuration-schema owners;
- one compact JSON serializer and recognized-error transport;
- command/domain-specific controllers and text/JSON result renderers.

Sharing mechanics does not grant them product authority: file transactions do
not decide migration semantics; the execution store does not decide readiness;
the workspace resolver does not choose dev scope; a common error envelope does
not imply a common success result.

## 8. Resolved cross-review conflicts

This audit applies the later accepted decision where earlier task text froze a
temporary baseline:

1. public `adopt` is superseded by `upgrade --target corpus`; configuration
   migration is `upgrade --target config`;
2. public workspace keeps six meanings but corrects `repo_common_id` to
   `repository_id`; `workspace.instance` remains compatible;
3. init/status say `corpus_baseline`/`corpus`, not a generic adoption object;
4. root `--version` is CLI-distribution-only; Corpus/config/project relations
   belong to status;
5. deployed legacy Skill guidance is evidence to retire, not the target help;
6. lookup uses shallow progressive list, path/content search scopes, and exact
   path reads rather than filename regex/all-body concatenation;
7. specialist telemetry/analysis interfaces remain unchanged by explicit scope
   decision, not accidental omission.

## Audit result

No unresolved core product-interface question remains in the accepted command
reviews. The next gate is one integrated implementation plan, dependency/order
analysis, mental rehearsal against known failure paths, and real-project
acceptance matrix. Product mutation still requires Sir's separate explicit
start.

Sir accepted this final consistency audit on 2026-08-08. The integrated
implementation plan is now recorded in
[`implementation-plan.md`](implementation-plan.md); that plan does not itself
authorize product mutation.
