# CLI Interface Topology Review

## Purpose

This review asks which public commands SVC should expose before their input and
output protocols are refined. It does not treat the existing parser as the
product model and does not add a command merely to make a taxonomy complete.

The admission test for a public command is:

1. a caller has one recognizable intent or information need;
2. SVC owns a distinct result that the adjacent project/package/Agent tool does
   not already provide;
3. its lifecycle and failure model fit its namespace;
4. a real Agent, Human, IDE carrier, CI carrier, or SVC maintainer consumes it;
5. removing or folding it would lose more clarity or capability than it removes
   interface and maintenance cost.

Top-level symmetry is not a goal. Frequently used project entry points may stay
at the root, while related specialist actions may be nested. Conversely,
different lifecycles must not be merged merely because they share code or an
abstract noun.

## Current Public Tree

```text
svc
├── lookup --list|--path|--name|--keyword
├── init
├── status
├── adopt
├── self-update
├── dev
│   ├── status
│   ├── identity
│   ├── ensure
│   └── setup vscode|npm
├── run <entry>|--follow|--inspect
├── telemetry
│   └── agent-thread
│       ├── list
│       └── export
└── analysis
    ├── query
    └── read
```

The tree currently spans four real product domains plus one questionable
external-tool adapter:

| Domain | Commands | Owned outcome |
| --- | --- | --- |
| Released Corpus | `lookup` | Discover or read exact packaged SVC guidance |
| Consumer integration | `status`, `init`, `adopt` | Observe, establish/repair bounded integration, or record an adopted baseline |
| Development collaboration | `dev`, `run` | Converge on long-lived capability readiness or one bounded observable execution |
| Agent-task evidence | `telemetry agent-thread`, `analysis` | Acquire immutable Agent-thread evidence, then navigate/read it without deciding its meaning |
| Executable installation | `self-update` | Ask the current Python interpreter's pip to upgrade the installed distribution |

## Real Use and Absence Evidence

Four available Consumers were inspected: SFP7 Camera and InKCre's client-web,
core-py, and docs repositories.

- `status`, `lookup`, `init`, and `adopt` appear repeatedly in project guidance,
  task trajectories, and handoffs. `status` is the established preflight;
  `lookup` delivers the Corpus; `init` and `adopt` own different mutation
  checkpoints.
- SFP7 Camera and two InKCre projects have real `dev` declarations. Operational
  calls use `dev status` and `dev ensure`; their worktree/host scoping and
  readiness semantics cannot be replaced by package scripts.
- No Consumer currently has a committed `run` entry. This is weak negative
  evidence because `run` was only just implemented. The SVC and Beluna cases
  already established its distinct collaboration result: concurrent callers
  converge on one execution ID and can follow or inspect native evidence rather
  than rerun solely for handoff.
- The inspected projects already own aggregate bounded checks such as `pnpm
  check`, `pnpm ci`, and `pdm run check`. SVC must invoke these authorities
  through `run`, not duplicate their suites, graphs, or acceptance semantics.
- The first literal-command scan missed constructed argv. Structural follow-up
  found three operational `dev identity` consumers: client-web's database
  runtime and worktree stop scripts, plus core-py's database lifecycle CLI.
  They request workspace identity independently of target observation.
- No inspected Consumer contains a generated `svc:dev:*` package script or
  marked VS Code Task. Current references to `dev setup` are in generated SVC
  Skills, SVC documentation, or SVC tests. Absence does not refute the already
  identified Human-through-IDE carrier need, but it does not justify expanding
  the setup family either.
- No operational `self-update` invocation was found in the bounded August Agent
  tool-call scan. Its references were implementation, tests, documentation, or
  discussion. The command supports only a non-editable pip install in the
  current interpreter.
- The Agent-thread field-study workflow has operationally used `telemetry
  agent-thread list`; query/read are backed by SVC's real immutable-evidence
  analysis workflow. These are specialist SVC-maintainer capabilities rather
  than ordinary Consumer preflight, but their product result is real.

Mention counts and generated Skill text are not treated as independent proof of
value. A newly implemented command can have no Consumer declaration, and a
generated manual can make an unused command look frequent.

## Review Disposition

### Retain the domain spine

The final supported spine, after the later upgrade and lookup reviews, is:

```text
svc lookup
svc status
svc init
svc upgrade [--target config|corpus]

svc dev identity|status|ensure|stop
svc run <entry>|--follow|--inspect

svc telemetry agent-thread list|export
svc analysis query|read
```

This is intentionally not reorganized under abstract parents such as `project`,
`development`, or `evidence` merely for visual symmetry:

- `status`, `init`, and `upgrade` are short project-entry verbs with distinct
  observation, integration-repair, and staged config/Corpus upgrade
  lifecycles. A `project` prefix would add ceremony without resolving
  ambiguity.
- `dev` and `run` remain separate because readiness/reuse/release and bounded
  execution/settlement are different user mindsets, configuration domains, and
  result models.
- telemetry acquisition and immutable-bundle analysis have different authority
  and input lifecycles. Their current split is clearer than a resource-oriented
  unification that makes `query` appear to operate on a live provider thread.
- `lookup`'s accepted shallow-list, exact-path, keyword, and regex selectors all
  serve one local Corpus lookup interaction. Converting each selector into a
  subcommand would enlarge the grammar without adding a distinct owner or
  lifecycle.

### Accepted removal: `self-update`

`self-update` is the only current command whose primary authority is an external
package manager rather than SVC:

- it supports only one installation shape while the real executable may be
  owned by pip, pipx, uv, PDM, an OS package manager, or a project environment;
- its plan digest binds a pip command, not the package index result that command
  will resolve later;
- it adds network mutation, installer failure, and fresh-interpreter
  verification to SVC without improving Agent/Human project collaboration;
- package managers already own installation provenance and upgrade mechanics;
- no real operational consumer was observed.

The executable/project-upgrade distinction remains important, but it does not
require SVC to perform both sides. The smaller interface is: the owning package
manager updates SVC; `svc --version` reports only that CLI distribution;
`svc status` observes the independent CLI/Corpus/config/project relations; and
`svc upgrade` plans one exact config or Corpus stage.
Status should give an external installer-oriented continuation when it can do
so truthfully, not route to another SVC command by default.

Sir accepted removal on 2026-08-07. Implementation remains gated with the rest
of this unit.

### Accepted: retain the exact `dev identity` query

Workspace identity qualifies a dev observation; it is not a competing action.
The exact output is small: 279–285 bytes in two real workspaces, of which the
workspace object is about 227 bytes and an `instance` / `worktree_id` / `root`
projection is about 125 bytes. Configured `dev status --json` already contains
the complete object, so its structured marginal cost there is zero. The
accepted default-text status design already leads with the worktree/capability
scope needed to qualify its observation.

That payload/affinity evidence initially led to a removal recommendation, but
the supporting search was incomplete. It looked for literal command strings
and missed argv assembled as arrays/tuples. Structural search found:

- client-web `database-runtime.mjs`, which supplies the default instance for
  direct ensure/ready/reset/status/stop operations;
- client-web `dev-stop.mjs`, which scopes worktree cleanup before checking and
  signaling Portless routes;
- core-py `dev_database.py`, which supplies the default instance for its entire
  direct database lifecycle surface.

These are independent operational consumers. Replacing identity with
configured `dev status` would execute every selected target's readiness probe,
changing effects, latency, failure horizon, and sometimes availability. The
existing `SVC_DEV_*` environment only helps when SVC itself launches the
Consumer command; it does not serve Humans or scripts invoking those lifecycle
tools directly.

An exact identity query must therefore remain probe-free. `dev status` should
still include workspace identity—including early
`not-configured` and `invalid-configuration` results—because identity qualifies
that observation at zero configured-JSON marginal cost. The two commands share
facts but not lifecycle or consumers.

This correction is a direct application of the fusion rule below: low marginal
payload and apparent affinity cannot outweigh real independent consumption and
an incompatible effect boundary. The previous removal acceptance rested on
false-negative evidence and is superseded.

Root `svc status` is declaration-only and may include workspace identity when
that fact qualifies preflight. It still cannot cheaply replace the exact query:
its broader integration lifecycle returns exit `3` for unrelated actionable or
malformed state, while three current identity consumers use nonzero-raising
process APIs. Sir accepted retaining `svc dev identity` on 2026-08-07. The
earlier root `svc identity` rename candidate is rejected: public namespace
placement follows the demonstrated dev resource-scoping intent, not the fact
that `run` and `dev` share an internal workspace resolver. Root/dev status may
project the same workspace facts without becoming their authority or sole
query. See [`identity-review.md`](identity-review.md).

### General command-fusion rule

Before retaining two adjacent observation commands, evaluate:

1. **Semantic subordination** — is one result a qualifier/detail of the other,
   or does it drive a genuinely different action?
2. **Marginal payload** — measure the additional information after deduplication,
   not the standalone output size.
3. **Observed affinity** — how often is the smaller command used with the
   larger one, and is there a real independent consumer?
4. **Lifecycle compatibility** — would fusion change side effects, latency,
   freshness, authority, or failure horizons?
5. **Recovery coverage** — can the merged command still serve error,
   unconfigured, partial, and diagnostic paths where the smaller observation
   was useful?
6. **Net interface cost** — does removing a command eliminate more grammar,
   help, testing, and caller round trips than it adds to the surviving command?

High affinity plus low marginal payload is evidence for fusion only when the
lifecycle difference has no demonstrated consumer and recovery paths remain
covered. This prevents both command fragmentation and a universal `status`
dump that absorbs unrelated information merely because it is short.

### Accepted removal: `dev setup`

The Human-through-IDE value comes from the IDE Task invoking the same
`svc dev ensure <target>` capability identity as the Agent, not from SVC
generating the IDE Task. A Consumer-owned VS Code Task can already make that
one direct call. The package-script adapter is an even thinner alias for the
same CLI command.

Against that result, the current adapter owns roughly 700 lines of runtime code
plus 160 lines of focused tests for JSONC parsing, surgical edits, markers,
digests, conflicts, orphan reporting, package.json mutation, and plan/apply
semantics. None of the four inspected Consumers uses a generated Task or
`svc:dev:*` package script. This is high implementation and public-contract
cost for a carrier declaration the carrier already owns.

The current evidence therefore favors removing the whole `dev setup` command,
not renaming `npm`. IDE Tasks, package scripts, CI, and other carriers remain
free to call `svc dev status|ensure` directly. This preserves the accepted
carrier topology while removing SVC ownership of carrier configuration. The
candidate should be rejected only if a real Human workflow demonstrates that
manual carrier declaration causes material duplicate execution or
mis-coordination that `dev ensure` itself cannot solve.

Sir accepted removal on 2026-08-07. Implementation remains gated with the rest
of this unit.

### Add no unrelated public command now

In particular, do not add `check`, `accept`, `task`, `list`, `config`, `logs`,
or a combined runnable catalog:

- project tools already own checks and aggregate suites;
- `run` supplies SVC's distinct bounded-execution identity, follow, inspect,
  and receipt;
- root status already summarizes committed run names, while `svc.json` remains
  directly inspectable with normal project tools;
- native output is already addressable through the execution ID;
- no real unmet interaction currently distinguishes another command.

An additional acceptance command becomes admissible only if real projects need
a semantic operation that cannot be expressed as one declared run without
duplicating project-tool authority.

## Proposed Review Order

The topology questions should be closed before resuming per-command protocol
work:

1. ~~remove or retain `self-update`~~ — accepted removal;
2. ~~merge standalone `dev identity` into `dev status`~~ — superseded after
   structural search found three independent probe-free operational consumers;
   retain the command;
3. ~~remove or retain `dev setup`~~ — accepted removal while preserving direct
   IDE/package/CI calls to `dev status|ensure`;
4. ~~freeze the remaining command tree and record that no additive command is
   currently admitted~~ — accepted as the per-command review baseline;
5. ~~resume command-input/output review at `dev ensure`~~ — candidate accepted;
6. ~~review the real lifecycle evidence for the narrowly reopened `dev stop`
   candidate~~ — accepted;
7. ~~review moving the independently justified identity query from `dev` to
   the root~~ — rejected; retain `svc dev identity`, while status results may
   include workspace facts when they qualify their own observations.

The identity correction remains accepted. Later evidence and review
deliberately replaced public `adopt` with staged `upgrade` and changed lookup's
selectors, so this earlier freeze is a historical per-command baseline rather
than the final tree. New contradictory Consumer evidence may still reopen the
tree; symmetry or an abstract desire for completeness may not.

### Accepted addition: `dev stop`

The `dev ensure` review exposed contradictory real Consumer evidence after this
freeze. Durable released capabilities require explicit cleanup, and InKCre
client-web/core-py already implement instance-scoped stop/teardown commands
outside SVC. One implementation reconstructs SVC identity and has a recorded
Unix-only ownership-check defect.

This supports `svc dev stop <target>` plus a Consumer-declared stop action. It
does not support generic PID takeover, implicit all-target cleanup, or merging
stop into `ensure`/`run`. See [`dev-stop-review.md`](dev-stop-review.md). Sir
accepted the command direction on 2026-08-07; implementation remains gated.
