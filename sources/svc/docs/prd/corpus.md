# Corpus Delivery and Project Evolution

Use this [Product Truth](index.md) projection when a Consumer adopts, queries,
or upgrades SVC. It owns the observable Corpus-delivery and baseline-evolution
promise; CLI grammar, configuration transforms, and release mechanics remain
with their executable owners.

The SVC CLI is the local delivery and distribution surface for the versioned
SVC Corpus. Agents and Humans can progressively browse one logical level,
search bounded path/content evidence, and read one exact canonical document
without copying the framework into every project. CLI help owns the executable
interface; Corpus lookup owns framework guidance and is not a substitute CLI
manual.

Three evolution axes remain visibly independent: the installed CLI version,
the project configuration schema, and the project-declared Corpus baseline. A
supported configuration transform may be automated through an exact plan. A
Corpus migration cannot be reduced to a file rewrite: SVC presents the exact
release guidance, an Agent/Human changes Consumer-owned SVC documents, and SVC
records only the reviewed baseline. An unchanged Corpus must not manufacture
empty migration work merely because CLI implementation changed.

Ordinary command text is shaped for Agent/Human decisions from the command's
actual semantics. Compact JSON is a deliberate scripts/CI projection, not the
definition of agent-friendly output. Expected non-success domain results stay
self-contained; grammar, invalid requests, and infrastructure failure remain
errors. SVC does not add a universal result schema across unrelated commands.

## Consumer Project Contract

Initialization is dry-run by default. It creates no copied SVC documents and never silently overwrites consumer content.

```bash
svc init /path/to/project --json
svc init /path/to/project --apply <plan-digest>
svc status /path/to/project --json
```

The exact-plan apply may create:

```text
svc.json
.gitignore                 (a bounded generated ignore block for svc.local.json)
AGENTS.md                  (a bounded generated SVC navigation block)
AGENTS.local.md            (ignored, Consumer-owned local Agent guidance)
docs/index.md              (created when absent, with a bounded generated navigation block)
```

`svc.json` is the complete, committed project configuration. Schema v3 records
the adopted Corpus baseline independently from the CLI version and can
optionally declare development capabilities and bounded runs:

```json
{
  "schema_version": 3,
  "corpus_version": "15.0.0"
}
```

`svc.local.json` is an optional, ignored sparse overlay for `dev` and existing
`run` declarations. It must declare schema 3, cannot change the Corpus baseline, create a
local-only run name, or produce an invalid effective configuration. `init`
maintains just its marked ignore block; it never writes a local configuration
file. It creates a missing `AGENTS.local.md` as ignored, Consumer-owned local
Agent guidance and never rewrites it. Version 15 rejects older configuration;
`init` does not hide or perform configuration migration.

Start with `svc status --json` in any repository. It is read-only and returns a
compact JSON preflight with independent CLI, config, Corpus-baseline,
integration, and workspace facts plus one primary continuation. Status
summarizes declared dev target names and committed run-entry names without executing them; use
`svc dev status` when runtime observation is needed. Every current `--json`
response is one compact JSON value; JSONL is reserved for a future command with
meaningful progress events.

Everything unmarked in `AGENTS.md` and `docs/index.md` remains Consumer-owned.
CLI help is self-sufficient; there is no installed SVC CLI Skill. A clean
legacy generated Skill is retired by an exact init plan, while a modified or
unproven file is never silently deleted. Modified generated navigation or
local-config-ignore blocks stop repair for review.
