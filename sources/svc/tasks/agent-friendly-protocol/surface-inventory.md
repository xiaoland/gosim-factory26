# Current Command and Output Inventory

This inventory maps current public SVC commands by semantic output rather than
assuming one shared presentation format. Facts come from `svc_cli/cli.py`,
canonical `src/index.md`, focused tests, representative invocations on the
actual SVC and Consumer worktrees, and retained real Agent trajectories through
2026-08-07.

## Shared Transport

- Successful text and compact JSON normally use stdout. Recognized errors use
  stderr in text and JSON modes.
- The current source emitter produces one sorted compact JSON value plus a
  framing newline. The installed 11.0.1 wheel still observed by real Agents
  emits prettified JSON, so source behavior and released field evidence must
  not be conflated. There is no current JSONL command.
- Exit `0` is ready/healthy/applied/no-op, `2` is CLI grammar, `3` is required
  action/conflict/invalid project state, and `4` is an integrity/local
  execution failure. `svc run` also passes through the project command's exit
  code after a normal child exit.
- `argparse` help uses stdout. SVC replaces normal `argparse` usage dumps on
  syntax failure with a short error; only lookup/no-command cases add the
  lookup discovery hint.

## Surface Map

| Surface | Semantic result | Text stdout | Text stderr | Machine result | Continuation/reference |
| --- | --- | --- | --- | --- | --- |
| `lookup --list|--keyword` | Catalog or bounded candidates | Path-oriented tabular lines; keyword includes score/excerpt and list adds exact-read hint | Errors only | Compact metadata/candidate object | Exact normalized path; keyword candidates must be re-read with `--path` |
| `lookup --path|--name` | Canonical corpus content | Raw Markdown, with `---` only between intentional multi-reads | Errors only | Compact object containing metadata and content | Catalog path and SHA-256 |
| `init` / `adopt` | Non-mutating plan or exact-digest apply | Plan header, writes, blockers, digest, apply hint; apply uses generic one-line result | Errors only | Full compact plan/apply object | Plan digest is the apply capability; current CI parses it |
| `self-update` | Installer plan or exact-digest apply | Plan header, installer command, blockers, digest, apply hint; apply uses generic one-line result | Errors only | Full compact plan/apply object | Plan digest |
| root `status` | Declaration-only project preflight and next state | Multi-line checklist, next action/reason/optional command, terminal health line | Errors only | Full compact preflight object | Optional exact next command |
| `dev identity` | Resolved coordination identity | Generic `command: status` line | Errors only | Full compact identity object | Workspace/instance identity fields |
| `dev status` | Runtime observation of one/all targets | Generic `command: status` line | Errors only | Full compact target observations, currently without access or native exec diagnostics | Target names, derived identities, and probe facts |
| `dev ensure` | Reused/started/manual target result | Generic `command: status` line | Errors only | Full compact result | Target/access/log references when present |
| `dev setup` | VS Code/npm bridge plan or apply | Plan/apply forms shared with local plans | Errors only | Full compact plan/apply object | Plan digest |
| `run <entry>` | One bounded execution plus native project evidence | Native child stdout | SVC selected command/lifecycle plus native child stderr | Native display suppressed; one compact receipt | Execution ID addresses lifecycle and captured streams |
| `run --follow` | Replay and wait on an execution | Captured stdout replay/live | Selection/lifecycle plus captured stderr replay/live | Native display suppressed; one settled/detached receipt | Execution ID; follower Ctrl+C detaches |
| `run --inspect` | Current execution facts without replay/wait | No text stdout | One concise terminal lifecycle line | One compact receipt | Execution ID |
| `telemetry agent-thread list` | Bounded provider inventory | Count plus thread ID/state/time rows | Errors only | Compact bounded inventory with truncation facts | Exact thread ID for export |
| `telemetry agent-thread export` | Validated evidence bundle receipt | One exported-path line | Errors only | Compact capture/evidence receipt | Bundle path and evidence ID |
| `analysis query` | Closed structural overview/match | None | Structured errors | Always compact JSON | Stable evidence refs and scope-bound cursor |
| `analysis read` | Forward native evidence read | None | Structured errors | Always compact JSON | Stable native refs and scope-bound cursor |

## Representative Current Observations

The SVC source repository has no `svc.json`, so its real root status is
`unadopted` with exit `3`. Text mode emits the checklist and machine mode emits
one object. Both currently identify `request-adoption-authorization` and
`requires_human_authorization: true` as the next protocol.

`svc lookup --keyword 'working protocol' --limit 3` returned three concise
path/title/score/excerpt candidates. Its compact JSON form added exact SHA-256
values without changing the lookup semantics.

Inspecting the real installed-wheel acceptance execution
`2ebdc656-8c86-414b-9b14-675af88a13e8` returned this complete Human result in
one line:

```text
svc run inspect: exited 0 in 6.3s 2ebdc656-8c86-414b-9b14-675af88a13e8
```

Its JSON receipt additionally carried the exact argv/cwd, caller role,
effective entry digest, timestamps, duration, workspace ID, and exit code.
Neither representation claimed that the tests proved acceptance.

Current error examples expose the cross-surface difference:

```text
{"code":"invalid-cli-usage","message":"svc run requires exactly one entry, --follow ID, or --inspect ID"}
```

```text
svc: invalid-project-configuration: Cannot load declared run configuration.
{
  "reason": "svc.json must be a regular file"
}
```

The first is a compact JSON grammar error. The second is text plus a prettified
JSON detail block. Ordinary JSON `SvcError` uses a third, nested error shape.

## Root Status: Real-Service Review

### Two recurring information services

Root status is not only a first-command router. Real SFP7 Camera task material
uses it in two recurring services:

1. **Preflight routing**: decide whether SVC integration is usable and which
   mismatch or next operation matters before other SVC work.
2. **Environment evidence and handoff**: record that the installed CLI,
   packaged corpus, adopted version, configuration, and generated guidance
   formed the environment under which later work or verification occurred.

The second purpose is not hypothetical. Twenty-five files under the real SFP7
Camera task tree mention `svc status --json`. Handoffs repeatedly reduce the
full payload to forms such as `exit 0; healthy/current/adopted 11.0.1`, or
`exit 3; CLI/corpus 10.0.1 while the project adopts 11.0.0`. They rarely carry
configuration digests forward. This suggests a stable high-value summary, but
does not prove that the detailed object should be removed: exact structured
facts still serve diagnosis, `jq`, CI, and disputed handoffs.

### Real outputs

Current-source `pdm run svc status` was observed read-only in the SVC repository
and three real Consumers:

| Repository | Disposition | Decisive relation | Source text / JSON size |
| --- | --- | --- | ---: |
| SVC | `unadopted`, exit 3 | no `svc.json`; generated integration absent or unanchored | 630 / 951 bytes |
| InKCre client-web | `actionable`, exit 3 | project 10.0.1 versus packaged 11.0.1; four declared dev targets; guidance outdated | 667 / 1373 bytes |
| InKCre core-py | `actionable`, exit 3 | project 10.0.1 versus packaged 11.0.1; one declared dev target; guidance outdated | 646 / 1349 bytes |
| SFP7 Camera | `actionable`, exit 3 | project current; three generated guidance surfaces outdated | 737 / 1383 bytes |

The current source text leads with overall disposition and versions, then a
fixed checklist, then `Next`, then repeats `Healthy` or `Action required`. The
compact JSON is globally alphabetically sorted, so the decisive `status` is
near the end of one long line and `next` is not the first relation seen. JSON
object order is not data semantics, but serialized order is still presentation
to an LLM and to a Human inspecting raw tool output.

The released 11.0.1 wheel on the real SFP7 Camera worktree returned a healthy
55-line, 1201-byte prettified object. Agents consumed that form successfully,
so compactness alone is not a sufficient outcome claim. The current source's
compact projection reduces framing and whitespace, but the two forms also
differ in fields and release state; no causal compact-versus-pretty comparison
has yet been performed.

### Real Agent delivery behavior

A bounded scan of August 2026 local Codex trajectories found 38 direct tool
calls whose execution input contained `svc status --json`: 20 standalone or
multi-line calls, 11 parallel calls, and 7 shell chains. This is use-pattern
evidence, not a complete frequency measure; generated instructions and quoted
handoffs were excluded from the count.

One retained SFP7 Camera trajectory ran a non-healthy status before packet
reads using `svc status --json && ...`. Exit 3 stopped the remaining reads, and
the Agent issued a second tool call for them. Its tool wrapper displayed the
JSON but not the captured exit-code field. This demonstrates a real recovery
turn caused by the interaction of status semantics, shell composition, and
tool framing. It does **not** yet establish that exit 3 is wrong: a CI or gate
consumer may depend on precisely that nonzero disposition, and teaching the
Agent to run preflight alone may be the smaller repair.

### Provisional form implications

The content is a hierarchy, not a flat property bag:

```text
overall disposition and environment identity
  -> decisive mismatches / anomalies
  -> next valid SVC operation, when one exists
  -> supporting checks and declaration-only inventory
  -> exact diagnostic state
```

Candidate implications for later comparison are therefore:

- optimize default text as a concise, purpose-ordered summary that can be
  understood directly and carried into a Human handoff;
- put the next operation adjacent to the disposition in non-healthy cases,
  rather than after every healthy or secondary check;
- show anomalies before routine `current` checks, while retaining enough
  environment identity to qualify later evidence;
- keep compact JSON as the exact structured projection; treat semantic
  top-level order as a testable possibility rather than changing stable
  deterministic order without observed interpretation failures;
- reconsider whether generated Agent guidance should always demand `--json`;
  an Agent is not necessarily a machine-field consumer for this service;
- keep exit semantics open until Agent preflight, shell composition, and CI
  gate consumers are evaluated together.

These are review candidates, not an approved redesign. In particular, the
observed handoff summaries could reflect the current project's unusually
strict environment-evidence protocol rather than a universal Consumer need.

### Candidate comparison

| Candidate | Preflight / next move | Exact diagnosis / CI | Human handoff | Main cost or failure |
| --- | --- | --- | --- | --- |
| Current fixed-checklist text | Overall state is early, but the next operation follows all checks | Exit is useful; details are incomplete versus JSON | Readable, but Agents still restate it | Routine and anomalous facts have equal weight; terminal line repeats the disposition |
| Current sorted compact JSON | Exact fields and low whitespace | Strong for `jq` and stable machine consumption | Raw one-line state must be interpreted and compressed | Agent is treated as a field parser merely because it is an Agent; semantic order is weak for raw scanning, but no field-interpretation failure has been observed |
| Purpose-ordered concise text | Strong: disposition, decisive relation, and next operation can lead | Deliberately incomplete; detailed diagnosis needs JSON | Matches the concise evidence form already written by Agents | Must retain enough environment identity to avoid an unqualified `healthy` claim |
| Summary plus full detail in one projection | Strong first lines and complete tail | Complete | Verbose but readable | Duplicates facts, recreates a pretty dump, and makes one call pay for two consumers |

The smallest current candidate is therefore **purpose-ordered default text plus
the existing full `--json` projection**, not a new mode or universal envelope:

- default text leads with disposition and qualified environment identity;
- a non-healthy next operation and reason appear immediately after that lead;
- only anomalous checks are expanded by default; declared `dev`/`run` names
  remain a bounded declaration summary when present;
- the final `Healthy` / `Action required` repetition disappears;
- `--json` remains one compact deterministic object with the exact supporting
  state; no status-specific key-order mechanism is added without evidence that
  stable sorted order causes material failure;
- generated Agent guidance uses default status for normal preflight and names
  `--json` only when exact structured state is required.

Illustrative shapes, using real observed states rather than a proposed global
grammar, are:

```text
SVC healthy — CLI/corpus/project 11.0.1 (wheel); configuration current
Dev: f43-builder — x86_64-f43-custom-kernel
```

```text
SVC actionable — generated integration outdated (3 surfaces)
Next: inspect the integration repair plan
  svc init /Volumes/WorkSSD/Development/sfp7-camera --json
Environment: CLI/corpus/project 11.0.1 (source); configuration current
Outdated: .agents/skills/svc/SKILL.md, AGENTS.md, docs/index.md
Dev: f43-builder — x86_64-f43-custom-kernel
```

Exact wording and whether routine declaration summaries belong in every status
remain test questions. The examples demonstrate ordering and density, not a
frozen text grammar.

### Separate semantic corrections

`requires_human_authorization` and reasons such as `obtain Human authorization`
claim authority that root status does not possess. The same repository state
can be observed by Agents with different Human-granted scopes, so a static SVC
boolean cannot truthfully answer that question. Root status should report the
state, consequence, and next valid SVC operation. Existing plan/apply semantics
already distinguish inspection from mutation; no replacement permission field
is currently justified.

For an unadopted repository, status may therefore route to the non-mutating
`svc init <repo> --json` plan after it has discovered the missing state, rather
than treating `init` itself as discovery or deciding whether the caller may
later apply that plan. Invalid Consumer-owned configuration can instead return
an exact repair action and reason without inventing an executable repair or
permission decision.

Exit 3 remains provisionally correct for non-healthy status. It gives CI and
shell gates a direct disposition, and the current Agent router already says to
run status as the first command. The first candidate repair for the observed
`&&` recovery turn is to make that isolated-call expectation and the status
result unmistakable, not to add `check`, weaken exit semantics, or make status
always succeed. This conclusion must be revisited if real Agents continue to
lose work after the presentation/router change.

### State-path stress review

| State path | Evidence horizon | Required default-text fact | Current gap |
| --- | --- | --- | --- |
| Healthy | Real released-wheel SFP7 Camera status | qualified healthy state, CLI/corpus/project version relation, resource mode, configuration state, useful declared capability names | current released text takes eight lines, omits resource mode and declaration names; current source adds a fixed checklist and terminal repetition |
| Integration drift | Real current-source SFP7 Camera status | count/paths of anomalous generated surfaces and exact non-mutating repair-plan command | facts exist but the next command follows all routine checks |
| Adoption pending | Real current-source InKCre client-web and core-py status | installed/corpus version versus adopted project version, migration-review consequence, declared capability names | text says `adoption-pending` but omits the adopted version that explains it |
| Unadopted | Real current-source SVC repository status | missing adoption/configuration, exact plan continuation if valid, absent/unanchored integration anomalies | output substitutes an invalid Human-authorization decision for a usable SVC continuation |
| Runtime mismatch | Source contract and focused tests only | installed versus packaged version and self-update plan command | current text already exposes the version relation and command; no real Consumer mismatch was observed in this pass |
| Malformed | Source contract and focused tests only | exact invalid path and parse/configuration reason; no invented repair command | current text prints `invalid` but drops the detailed `message` available in JSON, forcing a second read or guess |

This stress review narrows the proposed text contract: the lead is not merely
`healthy` or `actionable`; it qualifies that disposition with the smallest
environment relation that makes it trustworthy. Non-healthy output then shows
the decisive anomaly and valid continuation before routine declaration facts.
Malformed details are decisive content, not verbose diagnostics to hide.

The repository's real CI and release workflows call default `svc status` after
initializing an installed wheel and consume only its exit status; they do not
parse JSON. This supports retaining default text plus meaningful exit status.
Those workflows exercise only the healthy path, so they do not by themselves
prove which non-healthy states should fail a gate.

The available local Consumer inventory contains at most four declared dev
targets and no committed run entries. It provides no real large-declaration
case from which to derive truncation, a new listing command, or a reference
scheme. The candidate therefore keeps declared names inline and leaves the
large-Consumer question open rather than adding a speculative cap.

## Command Discovery and the SVC Skill

### Current topology

Current `svc init` plans and maintains three generated guidance surfaces:

```text
.agents/skills/svc/SKILL.md      Codex-specific trigger and CLI/corpus router
AGENTS.md                        Agent/project navigation block
docs/index.md                    Human/project documentation navigation block
```

Root status inspects all three, and any missing, outdated, or modified surface
can prevent `healthy`. The Skill also causes `init` to expose a Codex-only
`--agent codex` option. This is therefore not merely an optional documentation
file: it shapes adoption, command grammar, health, repair plans, tests, and the
Consumer file set.

The released SFP7 Camera Skill is 4,838 bytes / 41 lines, beside a 695-byte /
9-line generated `AGENTS.md` block. The current source has already reduced
those bodies to 1,170 and 777 bytes respectively, but both still route status,
lookup, Consumer authority, and mutation behavior. No real task in this pass
required a fact available only from the Skill. The official Agent Skills
progressive-disclosure model remains useful for workflows with distinct
instructions or resources; it is not by itself evidence that every CLI needs
a Skill-shaped manual.

### Why `--help` is not yet sufficient

The root `svc --help` currently gives a useful command catalog and points to
local corpus lookup. Several subcommand help surfaces are only argparse grammar:
`svc status --help` is 134 bytes / 8 lines and explains neither the four
dispositions, exit behavior, declaration-only horizon, nor its continuation;
`svc run --help` names selectors but not native channels, shared execution,
follow/detach, or receipt semantics. Deleting the Skill without improving these
surfaces would move hidden protocol knowledge out of one duplicate file but
would not make the CLI self-describing.

For normal CLI discovery, layered help should own:

- one-line information-service purpose and side-effect boundary;
- selector and mode relationships that grammar alone does not express;
- stdout/stderr and exit behavior when they affect shell composition;
- the smallest valid continuation or example needed to use the result.

It should not copy the SVC corpus, project working protocol, or every config
field. Deep framework guidance remains addressable through `svc lookup`.

### Smallest candidate

The current evidence supports removing the SVC Skill rather than shrinking it
again:

- remove Skill creation, refresh, inspection, and root-status health coupling;
- remove the now-meaningless `svc init --agent codex` option, making project
  integration Agent-agnostic;
- make root and subcommand `--help` sufficient for command discovery and basic
  execution semantics;
- keep one short bounded SVC trigger in project `AGENTS.md`, including in
  `assets/templates/AGENTS.root.template.md`, for example: use the installed
  `svc` CLI when SVC guidance or project integration is relevant, and discover
  the current interface through `svc --help` / `svc <command> --help`;
- keep that trigger generic and stable; do not encode status, lookup, mutation,
  or version-specific workflow inside it.

The template alone cannot update existing Consumer repositories. The smallest
coherent migration is therefore for `init` to keep maintaining one short
bounded `AGENTS.md` trigger while the corpus template shows the same
Consumer-facing shape. Whether the runtime should project the marked template
fragment directly or maintain equivalent wording is an implementation-design
question; two independently edited canonical copies would be a drift risk.

The current `docs/index.md` navigation block does not share the new short
Agent-trigger purpose. Sir chose to retain its creation, refresh, inspection,
and root-health participation for now rather than infer deletion from the lack
of an observed independent Human path. Its exact Human information service and
future content remain separately reviewable; the AGENTS trigger must not be
copied there merely to reuse one body.

### Minimal layered-help contract

Argparse grammar stays the implementation mechanism, but each family needs a
small semantic description owned beside its parser:

| Command family | Minimum additional help—not corpus documentation |
| --- | --- |
| root | Command catalog and convention for deeper `svc <command> --help`; it may separately point to corpus lookup for framework guidance, but lookup is not CLI documentation |
| `lookup` | candidate-versus-exact-read distinction, intentional multi-read, output choice, and exact continuation; mostly present now |
| `status` | read-only/declaration-only horizon, disposition/exit meaning, and that a reported command is the next non-mutating inspection where applicable |
| `init`, `adopt`, `self-update`, `dev setup` | plan-by-default behavior, exact-digest apply relation, and bounded owned effect |
| `dev identity`, `dev status`, `dev ensure` | identity versus observation versus coordination, no-start status boundary, readiness/provision consequence, and target selection |
| `run` | entry/follow/inspect relationship, convergence on one execution, native text channels versus settled JSON receipt, wait/detach behavior, and execution-ID continuation |
| telemetry | local/provider evidence horizon, bounded selection, exact source/output effect, and returned evidence reference |
| analysis | always-structured immutable evidence query/read distinction, schema discovery, stable refs, and cursor continuation |

Help should give one representative invocation only where grammar does not
make the relationship obvious. It should not teach project configuration or
repeat the SVC framework corpus. `svc lookup` retrieves that corpus; it is not
a fallback for missing CLI usage, mode, output, exit, or continuation
documentation. No caller should need to query corpus guidance to learn how to
invoke or interpret a public CLI command.

### Removal and migration constraints

Existing generated Skills cannot simply be forgotten: a stale project-local
Skill may continue to trigger and contradict the new help. A future migration
must distinguish:

- a clean SVC-generated Skill, which SVC can plan to remove exactly;
- a modified or malformed former Skill, whose content may now be
  Consumer-owned and must not be silently deleted;
- empty parent directories, which need not be removed merely for tidiness.

Status should not permanently keep a removed Skill in its health model. During
the migration horizon it may report a clean removable legacy artifact or a
modified residual without treating the latter as proof that current SVC
integration is invalid. Exact transition behavior belongs in the later impact
handshake and implementation rehearsal.

## Presentation Review Method

Each surface will be reviewed in this order:

1. Name the exact information service and the Agent/Human move it should make
   easier. Do not optimize an output without its consumer action.
2. Describe the content's semantic structure and authority: scalar, list,
   hierarchy, diagnostic, receipt, exact content, stream, uncertainty, and
   available continuation.
3. Observe the real delivery path, including shell/tool framing, channel
   merging, truncation, and the Agent's available follow-up tools.
4. Compare candidate forms by factual interpretation, correct continuation,
   recovery turns, unnecessary rereads, handoff fidelity, and repeated
   reliability. Record token/byte size only as explanatory evidence.
5. Select the smallest form that makes the intended relationships obvious and
   preserves authority. Do not generalize its syntax to a semantically
   different command without evidence.

Root `svc status` is the first review target because the canonical product
contract calls it the Agent's first SVC command, it already has both text and
compact-JSON projections, and its output must support both preflight routing
and later Human handoff. Its current Human-authorization field is a separate
semantic defect that must not be hidden by presentation changes.
