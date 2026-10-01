# Agent-friendly Command and Output Protocol

- **Objective**: Define and deliver a small, semantic command-and-output
  protocol that helps Agents operate and hand off SVC work on large real
  projects with less ambiguity, re-reading, and recovery work, while keeping
  the same commands effective for Humans.
- **Guardrails**:
  - Optimize for SVC's two root outcomes: Agents maintain large software
    projects well, and Agents and Humans collaborate more effectively.
  - Treat output shape as a semantic choice, not a universal serialization
    policy. JSON is not inherently Agent-friendly; when JSON is appropriate,
    compact JSON is preferred over prettified JSON unless evidence proves a
    different need.
  - Optimize both information selection and presentation. Select and shape a
    representation under three simultaneous pressures: the content's own
    semantics, the Agent's actual reading/reasoning/tool characteristics, and
    the information service's intended purpose. Presentation is protocol, not
    cosmetic formatting.
  - Keep the framework simple. Do not add features, modes, schemas, or limits
    without a distinct recurring consumer need and verification path.
  - Do not make SVC responsible for project-context discovery already served
    by tools such as `rg`, `jq`, code graphs, or `ast-grep`.
  - Preserve the separate product semantics and lifecycles of `svc run` and
    `svc dev`; this unit may make their evidence easier to consume but must not
    reunify them.
  - Start from real SVC command surfaces and real project/Agent interactions.
    Papers and other tools supply evidence and counterexamples, not a product
    definition by analogy.
  - Keep Human-readable operation viable. IDE Tasks may call SVC, but neither
    caller replaces the other.
  - Do not start product implementation until the protocol, impact handshake,
    implementation plan, and mental rehearsal have been reviewed. Do not use
    fixture projects as product acceptance.
  - Use this packet as the live design workbench: write an evidence-backed
    candidate before presenting it for Sir's review, retain accepted text, and
    revise or remove rejected text. Design-document mutation remains separate
    from the explicit gate for product implementation.
- **Verification**:
  - A current-surface inventory maps every public command's intent, stdout,
    stderr, exit status, identifiers/references, truncation behavior, and
    Human/Agent consumers without guessing from one command.
  - Representative output forms are evaluated through the information move
    they are meant to support—such as scan, select, compare, continue,
    diagnose, or hand off—not by syntax validity or byte count alone.
  - Research claims are traceable to primary papers, official specifications,
    official source, or real SVC/consumer evidence, with external facts kept
    separate from SVC inferences.
  - The approved protocol is exercised through real Agent calls in actual
    projects and demonstrates bounded improvements in interpretation,
    recovery, handoff, or task cost; fixture-only success is insufficient.
  - Implementation, once separately authorized, protects the protocol with
    focused contract tests and passes the repository's normal gates and real
    acceptance.
- **Current Truth**:
  - Sir authorized product implementation on 2026-08-08 after the integrated
    plan and rehearsal were committed as `227ea00`. All ten slices are now
    implemented in the working tree and are undergoing final qualification;
    the product changes are intentionally not committed yet.
  - Existing SVC surfaces mix native text, lifecycle text on stderr, compact
    single-value JSON, JSONL evidence, exit codes, file references, and
    execution IDs. Their semantics must be inventoried before convergence is
    proposed.
  - `svc run` intentionally preserves native stdout/stderr in text mode and
    emits SVC lifecycle facts on stderr; JSON mode suppresses native display
    and returns one compact receipt. This is one protocol case, not a presumed
    universal model.
  - Primary research does not establish a universally best serialization.
    It supports bounded action-result feedback, strict structure where a
    machine consumes fields, explicit error/terminal state, and recoverable
    references to larger evidence. Format performance varies by task, model,
    output size, and required reasoning.
  - Sir approved that Agent-friendly is a semantic routing contract rather
    than a universal output envelope. Sir then corrected an incomplete first
    formulation: the contract must optimize both what information is selected
    and how it is presented. Form selection must respond jointly to content
    semantics, Agent characteristics, and information-service purpose.
  - Sir explicitly delegated exploration, review, and design reasoning without
    requiring per-step approval. Human statements and accepted hypotheses
    remain challengeable inputs; contradictory product, project, or research
    evidence must be surfaced rather than normalized away.
  - SVC's actual surfaces already contain useful semantic differences: raw
    corpus content, compact plans and receipts, native command streams,
    diagnostics, and paginated evidence. Their presentation must now be
    evaluated rather than merely preserved.
  - Current cross-surface candidates include inconsistent JSON error shapes,
    prettified JSON inside text errors, generic text emitters that hide useful
    `dev` result facts, uneven command discovery, and a status authorization
    field that conflicts with this task's Human-Agent permission boundary.
  - Root-status field evidence now distinguishes two real services: preflight
    routing and environment-evidence handoff. Real Agents repeatedly compress
    the detailed JSON to disposition/version/configuration facts, while one
    non-healthy status chained with `&&` caused an additional recovery call.
    Neither observation alone proves that detail or nonzero exit should be
    removed.
  - The smallest current status candidate is purpose-ordered default text for
    Agent/Human preflight and handoff plus the existing compact full JSON for
    exact diagnosis, `jq`, and CI. It adds no output mode or shared envelope.
    Exit 3 stays provisionally; generated Agent guidance should run preflight
    alone and should not demand JSON merely because the caller is an Agent.
    Stable sorted JSON order also stays provisionally: no real field-reading
    failure justifies a status-specific ordering mechanism yet.
  - Status's Human-authorization boolean and authorization-directed reason are
    semantically invalid: repository inspection cannot know the caller's
    Human-granted authority. Report state, consequence, and a valid SVC
    continuation instead; existing plan/apply semantics carry mutation shape.
  - Root status currently checks a generated Codex Skill in addition to
    `AGENTS.md` and `docs/index.md`; `init` creates/refreshes it and exposes a
    Codex-only `--agent` option. Real project evidence shows substantial
    overlap between the Skill and AGENTS router, with no observed Skill-only
    need. The preferred candidate is no SVC Skill: one short AGENTS trigger
    plus self-sufficient layered CLI help.
  - `--help` is not self-sufficient yet. Root discovery is useful, but status,
    run, and other subcommand help omits result, channel, exit, and continuation
    semantics currently carried by docs or the Skill. Skill removal and help
    repair are one product change, not two independent cleanups.
  - The SVC trigger belongs in `AGENTS.root.template.md`, but a template alone
    does not migrate existing projects. Keep one bounded generated AGENTS
    trigger. Sir chose to retain generated `docs/index.md` navigation and its
    status check for now; its Human role remains separate from the Agent
    trigger and may be reviewed later.
  - Minimal layered-help obligations are now mapped per command family. They
    expose information purpose, side-effect boundary, mode relation, material
    channel/exit behavior, and continuation without copying configuration or
    corpus guidance.
  - Sir clarified the authority boundary: `svc lookup` queries the SVC Corpus,
    not documentation for using the SVC CLI. Public CLI help must be fully
    self-sufficient; corpus lookup cannot repair an incomplete command help
    surface.
  - `svc dev status` is the next command under review. Three real Consumers
    prove that its generic text output discards the entire target-level service;
    its JSON retains coordination identity but drops bounded exec diagnostics,
    access, provision kind, and continuation. Real core-py output shows the
    missing diagnostic can contain the exact readiness mismatch.
  - The smallest `dev status` candidate keeps one command and two projections:
    comparable anomaly-aware default text, and compact exact JSON augmented
    with resolved access, provision kind, exec exit code, and bounded native
    output. Exit 0/3 and the no-provision status boundary remain.
  - The recommended native-output boundary is explicit responsibility rather
    than false redaction: SVC does not serialize secret config/env itself;
    Consumer probe stdout/stderr is bounded native evidence and must be safe to
    preserve. One-target text gives an exact continuation; all-target text
    compares rows and groups targets sharing the same continuation.
  - `dev status` is not universally side-effect-free: SVC does not provision or
    take over anything, but it executes Consumer-declared probes, including
    arbitrary exec probes whose behavior the project owns. Help and output must
    preserve that distinction instead of calling the whole command read-only.
  - Sir accepted the `dev status` candidate, then correctly moved the review
    frontier outward: the public command tree must be right before more effort
    is spent refining the grammar and output of commands that may be removed or
    reorganized.
  - The current topology review finds no evidence for an additional acceptance,
    task, check, list, config, or log command. `run` already supplies the
    SVC-specific bounded-execution collaboration result while project-native
    tools own acceptance semantics.
  - Sir accepted removal of `self-update`: package managers own executable
    installation, while SVC observes version relations and retains the separate
    `adopt` judgment. Sir also accepted removal of `dev setup`: direct carrier
    calls to `dev ensure` preserve Human-Agent convergence without SVC owning
    roughly 700 lines of editor/package-file projection machinery.
  - Sir supplied a general fusion test for adjacent observations: if a result
    is small and normally consumed with another command, prefer one interface.
    An initial literal-command scan incorrectly appeared to support merging
    `dev identity` into `dev status`. Structural search then found three real
    argv-constructed operational consumers in client-web/core-py. They need
    probe-free workspace identity for direct database and stop lifecycles;
    replacing it with status would change effects, latency, and failure paths.
    Retain `dev identity`. Status still includes workspace facts because they
    qualify its observation at low marginal cost.
  - The generalized rule also checks semantic subordination, deduplicated
    marginal payload, observed affinity, lifecycle compatibility, recovery
    coverage, and net interface cost. Short output and co-occurrence alone do
    not justify turning status into an unrelated universal dump.
  - At that review stage, the reduced command tree was frozen as a baseline:
    `lookup`, `status`, `init`, `adopt`, `dev identity|status|ensure|stop`,
    `run`, telemetry, and analysis. Contradictory real Consumer evidence may
    reopen it; interface symmetry may not. Later accepted evidence did replace
    public `adopt` with `upgrade` and revise lookup selectors.
  - `dev ensure` has two output moments: sparse live coordination during a
    potentially long start/join, and one terminal capability result. Real
    Consumer probes show that bounded native output and exit code can contain
    the actual dynamic attachment or mismatch evidence currently discarded.
  - The smallest `dev ensure` candidate keeps one-target input, adds no mode,
    distinguishes reused/started/joined, resolves access, returns bounded probe
    evidence and shared startup-log references, and uses one result shape for
    ready and expected non-ready outcomes. Default text reports state changes;
    compact JSON remains one terminal result and suppresses progress.
  - Sir accepted the `dev ensure` candidate. JSON is the stable exact interface
    for CI/scripts and deliberate field consumers, not the default Agent/Human
    presentation. The JSON object itself should embody that role through
    compact stable fields and absence of progress/prose duplication, not carry
    a redundant audience marker.
  - Dev capability persistence was already canonical: after readiness SVC
    records `released`, relinquishes the child handle, and later trusts probes
    rather than a historical PID. POSIX isolation is implemented; current
    Windows terminal-loss survival is not yet proved by its process-group flag.
  - Real client-web/core-py cleanup paths reopen one narrow topology question:
    `svc dev stop <target>` backed only by a Consumer-declared stop action. SVC
    must never infer later kill authority from a saved PID. Sir accepted this
    command direction.
  - Sir resolved the identity namespace and stop topology: retain the existing
    probe-free `svc dev identity` command and add `svc dev stop <target>`.
    Internal reuse of workspace identity by `run` does not require a root
    `svc identity`; public command placement follows the demonstrated dev
    resource-scoping intent rather than internal ownership symmetry. Status
    results may still carry workspace facts when those facts qualify the
    observation. Both command decisions are now implemented under the accepted
    boundary.
  - Sir accepted the `dev identity` input/output contract. Keep
    `svc dev identity [--repo <repo>] [--json]` with no additional selector or
    mode. Replace the generic default receipt with a concise semantic chain of
    instance, canonical root, repository kind/identity, worktree identity, and
    execution namespace. Preserve the current compact JSON envelope and all
    six workspace meanings because real client-web/core-py scripts consume
    `workspace.instance`; the later vocabulary review accurately renames
    `repo_common_id` to `repository_id` while preserving that consumed field.
    Do not add a meaningless completion status. Help
    identifies JSON as the scripts/CI projection and makes the probe-free,
    config-independent boundary self-sufficient.
  - Adding target-local stop reopened the older `dev.profile` / `dev.profiles`
    layer. Its intended committed-alternative role has no demonstrated
    Consumer: every observed real project declares exactly one profile and
    real local overlays refine fields without switching it. Sir accepted
    flattening the schema to `dev.targets.<target>` and removing profile
    interpolation, environment, output, and coordination-key dimensions. This
    is a schema/identity migration requiring explicit planning, not a
    mechanical output edit.
  - The accepted stop declaration is consequently
    `dev.targets.<target>.stop`, alongside probe/provision/access. It introduces
    no separate stop map or public configuration namespace; the Human/Agent
    invocation remains `svc dev stop <target>`.
  - Sir accepted the `dev stop` live/terminal protocol. Default mode emits only
    start/join/opposite-intent-wait state changes to stderr, captures native
    cleanup output in one shared log, and emits a self-contained terminal
    result to stdout with target/scope, exact command, execution/caller
    relation, log reference, and final probe. Compact JSON suppresses progress
    and returns one exact object. Capability status and caller role remain
    orthogonal; `stopped`, `manual-action-required`, `stop-failed`,
    `still-ready`, and `stop-unverified` cover the terminal boundaries.
    Ctrl+C detaches a follower but interrupts an owner-held stop action; no
    owner-loss path grants PID authority. Stop always executes its declared
    idempotent cleanup before the final probe rather than treating an initial
    non-ready observation as proof that resources are gone.
  - Sir accepted the focused dev-family consistency pass: distinguish `instance` from
    `worktree_id` and per-target scope; route resolved exit-3 results to stdout;
    separate Consumer action failure from SVC execution failure; probe the
    current state even when stop is manual; and represent follower Ctrl+C as a
    caller detach receipt rather than a capability status. It also makes the
    ensure/stop coordination requirement concrete: ensure cannot return its
    current pre-lock `reused` fast path while an opposite stop intent owns the
    capability boundary. These corrections are now synchronized into the
    accepted status, ensure, and stop reviews without introducing a shared
    result schema.
  - The next command review is now written for `svc run`. No available real
    Consumer has adopted a run entry yet; the only persisted real execution is
    SVC's implementation-acceptance test run. The candidate therefore preserves
    the accepted grammar/native-channel/convergence model and limits changes to
    self-sufficient help, self-contained terminal/inspect text, accurate
    `workspace_instance` naming, bounded unknown-entry recovery, and returned
    stdout/stderr log references for ordinary-tool inspection. Beluna remains
    product-admission evidence, not post-implementation usage evidence.
  - Sir accepted the `svc run` candidate and required the implementation
    architecture to enforce consistent, accurate, self-explanatory names for
    shared facts while visibly separating different run/dev semantics. Current
    code already violates that law: the neutral execution record uses `entry`,
    `workspace_id`, and `effective_entry_digest` for dev target/declaration
    facts, while one `slot_key` conflates coordination boundary, intent, lock,
    and pointer storage. A focused architecture/vocabulary candidate now
    separates workspace, domain subject, operation intent, coordination key,
    execution ID, and log references.
  - Sir accepted that shared execution architecture/vocabulary candidate. The
    implementation plan must use canonical workspace/log/attempt owners,
    domain-specific `entry` versus `target` projections, and distinct
    coordination-key, intent, and execution-ID concepts rather than preserving
    the current run-shaped neutral record names.
  - Sir corrected the initial `svc init` framing. Init owns project-wide SVC
    integration, not dev, and current code validates but never rewrites an
    existing dev/run configuration. The accepted dev-profile flattening needs
    its own configuration/release migration; it is not an init responsibility.
    Sir also rejected the unsupported implication that
    `plan -> digest -> apply` is itself Human-Agent collaboration. Real SVC CI
    uses it as deterministic exact-state automation. Its demonstrated services
    are request-to-plan binding and stale-plan rejection; any collaboration
    value comes from shared project integration, not the digest.
  - Sir accepted the corrected starting point and began an ordered `svc init`
    command review. The first candidate retains one command with two
    state-derived paths: initial project/adoption establishment when base state
    is absent, and later repair of the same bounded integration surfaces. They
    are not the same adoption lifecycle: repair never advances the existing
    baseline. The candidate explicitly excludes adoption advancement,
    configuration migration, local-overlay mutation, package installation, and
    runtime operations; self-sufficient help must explain the
    broader-than-first-call `init` behavior.
  - Sir accepted that `svc init` purpose, ownership, trigger, and retained
    grammar. The next candidate defines a freshly recomputed optimistic
    plan/apply state machine: `ready|noop|blocked` plans, exact-digest selection,
    distinct digest-mismatch versus during-apply stale-plan conflicts,
    `applied|noop` success, and explicit rollback outcomes. It also blocks an
    orphan `svc.local.json` instead of silently activating it by creating a
    missing base configuration.
  - Sir accepted that state machine. The default-plan candidate now identifies
    canonical repository, establish/repair intent, corpus version, and adoption
    baseline disposition before listing complete semantic operations. Ready
    plans give one full repo-scoped apply command; noop plans stay concise;
    blocked plans lead with blockers and no applicable digest. Default text
    omits hashes and whole-file diffs while naming each owned extent.
  - The accepted removal of the generated SVC CLI Skill has one necessary init
    migration effect: a clean, provably SVC-generated whole-file Skill must
    appear as a bounded `delete` operation. Stopping generation without cleanup
    would leave the rejected interface installed in real Consumers; modified or
    unproven files are never silently deleted.
  - Sir accepted the default-plan contract and corrected its mutation heading.
    Use `Would change (<count>):`: unlike `Changes` or `Will change`, the
    conditional form makes the non-mutating plan boundary explicit. No inline
    diff/preview mode is added.
  - The apply-result candidate pairs that plan with past-tense realized
    operations and exact path extents. Success reports only approved path
    postconditions and points to root status as an independent observation;
    it does not claim project health or adoption. Failure distinguishes no
    mutation, fully restored state, preserved external changes, and uncertain
    recovery, with per-path evidence rather than one aggregate rollback word.
  - Sir accepted that apply result and delegated compact JSON without a review
    gate. The decided init-local schema distinguishes plan/apply mode, uses
    `corpus_version` and explicit Corpus-baseline disposition, represents exact
    before/after file states including intended modes and deletion, and keeps
    `plan_digest` for the demonstrated CI consumer. It removes redundant
    summary and presentation prose from plan identity; no compatibility alias
    is kept.
  - The channel/exit candidate routes resolved blocked plans to stdout/3 but
    explicit apply rejections to stderr/3, keeps infrastructure failure on
    stderr/4, and adds a transaction-safe Ctrl+C boundary. Interrupt normally
    returns 130 after rollback; rollback failure returns 4 because repository
    state is uncertain.
  - Sir accepted that channel/exit contract. The layered-help candidate uses
    root help only for command selection and makes `svc init --help`
    operationally self-sufficient: purpose, bounded owned/non-owned effects,
    plan/apply relation, result/channel/exit classes, and valid continuations.
    It removes `--agent`, Human-authorization prose, and any dependency on a
    Skill or Corpus lookup for CLI usage.
  - Sir accepted layered help. The final init candidate makes root status expose
    independent runtime/configuration/Corpus-baseline/integration dimensions,
    repairs managed integration before upgrading to a newer Corpus, and blocks
    unsafe init/upgrade writes when the project baseline is ahead. Init and
    upgrade share one deep file-transaction engine but retain separate public
    semantics.
  - Implementation rehearsal found a real mode bug: current rollback can report
    success after restoring original bytes while changing an existing file from
    `0640` to `0600`. The target engine therefore owns explicit before/after
    file states, meaningful POSIX modes, delete, per-path rollback, and a
    SIGINT-safe attempted-operation boundary.
  - Real acceptance uses natural states in actual client-web, core-py, InKCre
    docs, SFP7 Camera, and unadopted Anana project content, with mutation only in
    a user-authorized disposable real checkout. Temporary fixtures and injected
    failures remain mechanical tests and cannot satisfy acceptance.
  - Sir accepted the final status/project-upgrade closure, implementation rehearsal, and
    real-project acceptance plan. The `svc init` design is closed.
  - Sir corrected a domain conflation: Corpus is canonical `./src` content;
  configuration grammar and schema migration belong to `svc_cli`. One package
  currently distributes both, but that does not merge CLI distribution,
  available Corpus, project Corpus baseline, and config-schema state. The
  legacy `svc_version` name should become `corpus_version` in the next config
  schema without advancing its value.
  - Sir challenged directly exposing that internal topology as two commands.
    The new candidate uses one project-facing `svc upgrade` router with optional
    `--target config|corpus`; target engines, plan identities, and apply effects
    remain separate. Without a target, it advances one exact stage and chooses
    config first only when both are pending.
  - Current build mechanics stamp the Corpus catalog with CLI distribution
    version. That creates false Corpus-adoption gaps and empty guidance after a
    CLI-only release. The candidate restores an independent Corpus version
    authority under `src`, renames generic `svc_version` facts, and treats
    config schema as a separate CLI version dimension.
  - Sir accepted the unified `svc upgrade` interface, optional target,
    config-first staged routing when both dimensions are pending, separate
    target plans/applies, and the four independent version authorities.
  - Sir confirmed the version index belongs to this SVC framework repository,
    not Consumer projects, accepted its minimal release-chain shape, and
    renamed it to the contextually sufficient `src/version.json`. Consumers
    retain only their project `corpus_version`.
  - Sir accepted full Corpus-chain retention from one fixed supported anchor,
    without silent pruning; off-chain baselines are unsupported. Corpus
    guidance retention remains independent from CLI config-schema support.
  - Real Consumer code proves config migration is not only a JSON rewrite:
    client-web doctor/check, core-py database provider, and an SFP7 test
    directly read the old profile path. The config target therefore combines
    an exact automatic base/local transform with CLI-owned migration guidance,
    while its apply receipt verifies only configuration state.
  - Multi-profile handling is only a legacy-v2 admission check; v3 still has no
    profiles. The transformer should use strict Pydantic v2/v3 models,
    `python-json-patch` RFC 6902 operations, `python-semanticversion`, standard
    JSON serialization, and the existing mature locking/atomic primitives. SVC
    owns only its exact schema rule and transaction semantics, not a home-grown
    parser, patch engine, SemVer implementation, or generic migration framework.
  - Sir accepted the exact v2 -> v3 transform and mature migration stack.
  - Sir accepted the config-guidance delivery behavior but rejected a separately
    authored Markdown guide per schema step. The accepted design makes
    retained structured Changie fragments the only authored change facts;
    changelog, a compact CLI migration descriptor, and Corpus version/guidance
    are separate generated projections selected by the fragment's single owning
    component. Generated changelog prose is never parsed as authority, and no
    per-step Markdown guide is needed under `svc_cli`.
  - Package SemVer continues to use all fragments, Corpus SemVer uses only
    Corpus-owned fragments, and config schema identity comes only from explicit
    schema-pair metadata. Published Markdown history is too lossy to reconstruct
    complete structured release facts; existing published guidance can be
    imported once as an editable version-associated guidance source.
- **Upgrade Output Decision**: The unified `svc upgrade` review returned to
  target selection and terminal output. Sir accepted config-first as a
  targetless routing rule and explicit target independence, with the condition
  that every successful target apply reports any other still-pending upgrade
  target. The selected-plan states and default plan structure are now accepted.
  Another pending target is phrased as
  a reminder/warning, not `Later stage`; long Corpus guidance is delivered by
  exact `lookup --path` references rather than inlined.
- **Corpus Guidance Decision**: Corpus migration-note authoring and history use
  action/applicability/verification-led fragments, narrow guide projections,
  stable release facts with living historical guidance, current-content hashes
  bound only by individual plans, impact-based repair hops, and a one-time
  editable legacy guidance import. Sir accepted this corrected model; Changie
  does not impose fragment immutability, and SVC will not add it as policy.
- **Upgrade Apply Decision**: Sir accepted `applied` rather than
  `migration-completed`, explicit caller assertion versus SVC verification,
  past-tense realized effects, remaining-target reminder/continuation, and shared
  neutral transaction failure vocabulary. The Corpus handshake is plan/read,
  Agent/Human document migration, then
  `svc upgrade --target corpus --apply <plan-digest>` to record only the new
  baseline; project document edits are expected outside digest preconditions.
- **Upgrade Protocol Closure**: Delegated compact JSON now uses target-specific
  `configuration` or `corpus` facts, shared exact file operations, explicit
  caller assertion versus bounded SVC verification, and independent
  `remaining_targets`. Resolved `migration-required|blocked` plans use
  stdout/3; apply conflicts use stderr/3; infrastructure or uncertain recovery
  uses stderr/4. Layered help owns config-first default routing, explicit-target
  independence, and the Corpus read/edit/check/apply handshake. The upgrade
  review is closed without product implementation authorization.
- **Implementation Planning**:
  - Sir accepted the final cross-command consistency audit on 2026-08-08. It
    closes the core public tree, shared vocabulary, command-local output forms,
    common error transport, and self-sufficient help without changing
    telemetry/analysis.
  - The whole-unit implementation plan, strict dependency order, mental
    rehearsal, and non-fixture real-project acceptance matrix are now written
    in [`implementation-plan.md`](implementation-plan.md). It treats the work
    as one release unit with internally verifiable slices and identifies
    Windows long-lived-process survival as a must-prove release boundary.
  - Sir supplied that explicit start after review. Implementation and exact
    real-project evidence are recorded in [`acceptance.md`](acceptance.md); no
    fixture result is counted as product acceptance.

  `telemetry agent-thread list|export` and `analysis query|read` are specialist
  maintainer evidence surfaces, not this unit's core SVC business capability.
  Preserve their current interfaces and behavior; do not pull them into the
  agent-friendly output refactor or use their differences to justify a common
  response schema.

  Root-status large-declaration evidence remains unavailable; do not
  manufacture a Consumer fixture.

- **Lookup Review**: Sir accepted removal of `--all` but identified an
  evidence error in the first input candidate. Real `--name` calls only express
  exact paths because the generated Skill taught Agents to list/search and then
  escape a returned path; that induced misuse does not show that pattern search
  lacks value. The revised candidate uses
  `--list|--path|--keyword|--regex [--limit] [--json]`: `--path` owns exact
  document reads, `--keyword` owns ranked lexical discovery, and accurately
  named `--regex` owns bounded full-text Corpus matches. Filename regex,
  concatenated `--all` reads, and pseudo-pattern guidance are removed. Output
  selection and presentation follow after this corrected grammar decision.
  Verification distinguishes deployed legacy Skills from current source: the
  four real Consumer Skills still teach keyword-to-escaped-`--name`, while
  current source teaches full `--list --json` then `--path --json`. Sir
  correctly identified that the latter may train Agents to dump the whole
  Corpus. The revised candidate retains deterministic recovery but changes
  `--list [prefix]` to one-level tree navigation, and adds one orthogonal search
  scope `path|both` for keyword/regex queries. The current 21-document,
  1.3-KB list is not itself a demonstrated overload; the accepted justification
  is bounded progressive Corpus browsing, not recovery from an arbitrary
  zero-match query. `dev server readiness` is CLI-manual subject matter and its
  Corpus miss is normal. Input grammar is now accepted. The default-output
  candidate uses shallow full-path rows, ranked keyword candidates without
  public scores, rg-like exact regex locations, raw Markdown exact reads, and a
  settled stdout/0 empty-search result; Sir accepted it. The final lookup
  candidate now adds mode-specific compact JSON collections (`entries`,
  `candidates`, `matches`, or singleton `document`), explicit independent
  `corpus_version`, stdout/0 empty searches, stderr/3 missing exact selections,
  stderr/4 Corpus integrity failures, and help that explicitly separates Corpus
  lookup from CLI usage. Sir accepted the final protocol; the lookup review is
  closed.

## Supporting Material

- Research synthesis: [`research.md`](research.md)
- Current command/output inventory: [`surface-inventory.md`](surface-inventory.md)
- `svc lookup` command review: [`lookup-review.md`](lookup-review.md)
- `svc dev status` review: [`dev-status-review.md`](dev-status-review.md)
- `svc dev ensure` review: [`dev-ensure-review.md`](dev-ensure-review.md)
- `svc dev stop` lifecycle review: [`dev-stop-review.md`](dev-stop-review.md)
- Dev command-family consistency review:
  [`dev-family-consistency-review.md`](dev-family-consistency-review.md)
- `svc run` command/output review: [`run-review.md`](run-review.md)
- Shared execution architecture/vocabulary review:
  [`execution-vocabulary-review.md`](execution-vocabulary-review.md)
- `svc init` corrected starting point: [`init-review.md`](init-review.md)
- Superseded `svc adopt` evidence/Corpus-transition review:
  [`adopt-review.md`](adopt-review.md)
- SVC configuration migration review:
  [`config-migration-review.md`](config-migration-review.md)
- Unified project-upgrade interface and version authorities:
  [`upgrade-review.md`](upgrade-review.md)
- Corpus migration-note authoring/history review:
  [`corpus-migration-authoring-review.md`](corpus-migration-authoring-review.md)
- Final core CLI interface consistency audit:
  [`core-interface-consistency-review.md`](core-interface-consistency-review.md)
- Integrated implementation plan, failure rehearsal, and real acceptance:
  [`implementation-plan.md`](implementation-plan.md)
- Executed mechanical and non-fixture real-project acceptance:
  [`acceptance.md`](acceptance.md)
- Dev configuration topology review: [`dev-config-review.md`](dev-config-review.md)
- Workspace identity review: [`identity-review.md`](identity-review.md)
- CLI interface topology review:
  [`interface-topology-review.md`](interface-topology-review.md)
