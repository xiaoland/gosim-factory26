# External-System Doubles

- **Objective**: Add an SVC CLI capability named `svc double`,
  that enables a Consumer to verify black-box product behavior when an external
  system is unavailable, unsafe, costly, or unsuitable for deterministic
  automated writes.
- **Guardrails**:
  - Start every double scenario from a named Consumer-visible test claim, not
    from an attempt to reproduce the provider's API or internal lifecycle.
  - Treat the provider contract, captured interactions, and explicit Consumer
    requirements as authority. Generated behavior and convenience defaults
    must not invent business truth.
  - Do not reject mocks or generated data categorically. Reject anonymous,
    test-local answer fixtures and type-correct but semantically meaningless
    values. Examples, matchers, generators, captures, and product assertions
    have separate authority and lifecycle.
  - Make fidelity limits and provenance explicit. Protocol/schema fidelity,
    selected semantics, temporal behavior, and provider currentness are
    separate claims.
  - Support callbacks as explicit inbound stimuli to the Consumer; do not
    assume the outbound stub must simulate a provider lifecycle that schedules
    them.
  - Ordinary local/CI execution must be deterministic, isolated, fail closed,
    require no real write credentials, and never let the responder proxy or
    fall through. Because the MVP does not launch/sandbox the Consumer, it must
    report Consumer-process egress as an explicit non-claim unless the
    Consumer/CI independently enforces it. A configured external materializer
    is also unsandboxed Consumer code and receives its own egress non-claim.
  - The Consumer test owns product assertions and completion. The MVP does not
    own test-process orchestration or a combined `svc double check` verdict.
  - Keep SVC small and mechanically verifiable. Any runtime, descriptor,
    observation, or extension needs a clear owner, lifecycle, and conformance
    path.
  - Do not mutate SVC source until the evidence-backed product contract,
    technical boundary, and Impact Handshake are presented to and explicitly
    confirmed by Sir. This task packet is the permitted working-set exception.
  - Preserve unrelated working-tree changes.
- **Verification**:
  - A real Consumer can route an HTTP product flow through a strict local
    responder and assert its own public state or output.
  - A test can explicitly inject a provider-shaped callback/webhook into the
    real Consumer endpoint, including method, headers, and raw body, and observe
    the acknowledgement.
  - Unmatched requests, undeclared SVC-owned runtime egress, implicit response
    cycling, leaked state, and unsupported semantics fail visibly; configured
    materializer egress remains an explicit non-claim.
  - Every behavior reports a provenance class and fidelity/non-fidelity claims.
  - Every generated nontrivial field reports semantic intent, generator and
    version, locale/seed/clock when applicable, and the matcher or validator
    that accepted the result.
  - Repeated and parallel local/CI runs produce no route, capture, journal,
    timer, or state leakage.
  - A separate opt-in provider-backed lane can refresh or challenge fixtures
    where a safe official sandbox or provider tool exists; its absence does not
    weaken deterministic isolation.
  - Existing SVC tests and quality gates remain green if implementation is later
    authorized.
- **Current Truth**:
  - SVC exists to make Vibe Coding sustainable; external integrations are a
    high-value verification gap because their writes may be unsafe or costly
    and their sandboxes incomplete or unavailable.
  - Sir rejects the existing Anana Caocao Mobility and WeChat Pay fake servers
    as requirements sources. They may contain over-simulation, fictional
    provider behavior, excessive edge cases, and responsibilities that should
    remain outside a double. All conclusions derived from their complexity are
    superseded.
  - The renewed evidence base is recorded in
    [`application-practice-research.md`](application-practice-research.md). It
    uses empirical research and primary evidence from mature application
    projects such as pretix, Zulip, GOV.UK Pay, GitLab, and Home Assistant,
    supplemented by deliberately scoped provider/platform doubles.
  - Mature application practice repeatedly tests the real Consumer while
    replacing the smallest uncontrollable boundary. Outbound dependencies are
    commonly supplied deterministic responses; inbound webhooks are commonly
    injected from captured fixtures; occasional sandbox/contract checks form a
    separate drift lane.
  - OpenAPI is valuable for method/path/parameter/schema mechanics, as
    `stripe-mock` demonstrates, but does not specify provider business behavior.
  - Callback coverage is required, but a provider simulator is not. Responder,
    event injector, observer, and optional provider probe are separate roles
    that may compose without sharing a fictitious domain model.
  - Strict defaults are product behavior. GOV.UK Pay's runtime migration
    documents that case-insensitive matching, implicit response alternation,
    and unmatched empty `200` responses can hide Consumer defects.
  - Agent convenience cannot be the main criterion. Recent empirical evidence
    finds coding agents add mocks more often than humans and warns that easily
    generated mocks may validate real interactions less effectively.
  - Sir's original objection to mocks was too broad. Mature mock libraries,
    matchers, and semantic data generators are useful. The actual objection is
    to unmanaged fixtures embedded in tests, fixture/provider drift, fixtures
    that also encode the expected product answer, and generators that satisfy
    only a storage type while violating field meaning—for example, treating a
    vehicle registration as an arbitrary random string.
  - [`mock-data-governance.md`](mock-data-governance.md) separates constant,
    example, captured, derived, generated, and synthetic values. It requires
    semantic intent, a pinned generator, replay context, post-generation
    validation, and managed fixture provenance.
  - [`double-requirements-v2.md`](double-requirements-v2.md) defines the new
    requirement model: a claim-scoped boundary harness, explicit fidelity
    vector and provenance, strict isolation, an outbound responder, an
    independent inbound event injector, and limited boundary observations.
  - [`runtime-decision-v2.md`](runtime-decision-v2.md) rejects a universal
    service DSL and code-backed fake service as the default MVP. The current
    recommendation is a managed boundary interaction model driven by contracts,
    matchers, semantic generators, captures, and managed examples, with a
    narrow code escape boundary for dynamic signing/transforms and a separate
    code-backed driver only when independently justified.
  - Runtime semantic ownership is decided: SVC owns a small engine-independent
    interaction model. The completed bake-off keeps WireMock `3.13.2` as a
    reference/possible opt-in adapter but does not justify its Java runtime and
    19.5 MB artifact as the default. The implementation target is a narrow
    native loopback executor; its concrete Python foundation remains subject to
    review and source evidence.
  - `boundary scenario descriptor` is the artifact's role, not its language.
    YAML can be an initial surface syntax but does not define the abstract
    grammar, types, matching/generation semantics, effects, phases, or runtime.
  - [`language-decision.md`](language-decision.md) recommends a composite
    Boundary Scenario Language: a small SVC host grammar and normalized IR,
    Pact-inspired example/matcher/generator separation, CEL as a conditional
    typed expression sublanguage, and a versioned semantic generator registry.
    Exact grammar and dependencies remain unapproved.
  - Sir accepts the composite BSL direction as the current best middle path:
    it reuses mature language semantics where they fit, while supplying the
    missing boundary-scenario host grammar instead of choosing either a fully
    invented DSL or no DSL. This accepts the language architecture, not a
    concrete grammar, dependency, generator catalog, or runtime.
  - The completed no-source spike is recorded under
    [`spikes/bsl-authoring-conformance/`](spikes/bsl-authoring-conformance/).
    It proved a local typed-node surface, normalized IR, restricted CEL profile,
    independently validated/replayable generation, strict native and WireMock
    projections, two-process isolation, explicit callback delivery, and a
    local-only OpenAPI 3.1 selected-operation schema profile.
  - The spike also produced decisive counterexamples: Faker `40.1.0` generated
    `IC10 YNI` for `en_GB` seed `123`, violating the independently sourced DVLA
    current-style rules; JSON Schema `format: uuid` accepted `not-a-uuid`
    without explicit format assertion; and default YAML scalar resolution
    turned an ISO-looking clock into a datetime object.
  - The accepted language refinement is a local typed value node compiled to a
    path-indexed IR, an explicit CEL environment excluding iterative macros,
    mutually exclusive raw/structured body modes, and a closed portable
    generator registry with domain semantics outside SVC by default.
  - Current SVC schema v3 has strict `dev` and `run` declarations. The V2 design
    now recommends explicit-path `*.double.yaml` modules for v0, so no project
    configuration migration or top-level `double` field is needed.
  - Sir accepts the command family
    `svc double validate|start|emit|observe|stop` and the absence of `check` in
    the MVP.
  - The final pre-implementation review is recorded in
    [`final-review.md`](final-review.md). It retains the product/command
    direction while correcting active-versus-sealed runtime authority,
    replacing client-authored `lost` with `control-unavailable`, removing
    product assertions from BSL, making event target bindings origin-only,
    bounding materializer execution/non-claims, and keeping CEL/YAML/JSON Schema
    behind an optional `double` dependency extra.
  - The exact final candidate surface is recorded in
    [`bsl-v0-contract.md`](bsl-v0-contract.md): `language: svc.double/v0`, one
    strict scenario, phase-legal local `$bsl` nodes, a closed matcher/generator
    algebra, origin-only event targets, and a whole-envelope materializer.
  - [`design-v2.md`](design-v2.md) and
    [`impact-handshake-v2.md`](impact-handshake-v2.md) are the replacement
    review candidates. They recommend
    `svc double validate|start|emit|observe|stop`, one HTTP boundary/scenario
    per module, a native loopback executor, and honest
    `consumer-egress: not-enforced` / conditional
    `materializer-egress: not-enforced` report boundaries.
- The independent source-execution plan is recorded in
  [`implementation-plan.md`](implementation-plan.md). It sequences dependency,
  base-install, language, in-process engine, carrier, Consumer acceptance, and
  release work through the earliest falsifiable gate rather than leaving the
  five Impact Handshake slices as a high-level checklist.
- The repository-aware mental rehearsal and advance troubleshooting record is
  [`preflight-rehearsal.md`](preflight-rehearsal.md). It traces the happy path
  and failure branches through the current CLI/import, output-schema,
  workspace, execution, packaging, and workflow seams. It records closed risks
  plus five implementation-time red gates.
- **Implementation status**: Sir explicitly authorized implementation on
  2026-08-10 after asking that the task packet be committed first; the packet
  was committed as `88ece68`. Slices 0-5 now have executable evidence: the
  optional dependency/base-import boundary, strict compiler and immutable
  recursive OpenAPI registry, in-process responder/materializer/event engine,
  carrier-owned active authority, sealed stop, five CLI commands, output
  schemas, two-run isolation, and control-unavailable/no-PID behavior. Slice 5
  adds the black-box Consumer product oracle, base/extra installed-wheel proof,
  release facts, and CI/publish preflight coverage. The final local gate passed
  236 tests plus every documented quality/projection/workflow/lock check; an
  independent final review has no remaining blocker. The implementation was
  committed as `f2c4df0` after Sir's separate command. A subsequent CLI-help
  hardening pass makes all six `double` help surfaces self-contained about the
  experimental status, command lifecycle, result protocol, fidelity and
  materializer non-claims, and the Agent's obligation to report and confirm any
  choice that could reduce test credibility or validity.
- **External Consumer acceptance (complete)**: Sir requested a real replacement
  trial in an isolated `mvp-HA` worktree on `wsl.win-ws.localhost`: replace the
  WeChat Pay and Caocao Mobility fake servers with `svc double`, then run the
  existing system scenarios at their Consumer assertion boundary. The
  replacement passed all `11` files / `39` tests twice (`183.19s`, `183.81s`),
  after first proving and fixing dynamic form matching, event-to-responder
  re-entry, and unrelated-route body parsing. A focused lifecycle rerun left a
  zero-byte registry and no carrier/fake-server process. The original worktree
  remains untouched, the acceptance Postgres resources were removed, and all
  Consumer adapters/modules remain only in the disposable worktree. Detailed
  evidence and the honest external-materializer state boundary are recorded in
  [`mvp-ha-acceptance.md`](mvp-ha-acceptance.md).
- **Implementation handoff evidence**:
  - `pdm lock --check`, `pdm run test`, `pdm run lint-tests`,
    `pdm run lint-imports`, `pdm run typecheck`, `pdm run check-documents`,
    `pdm run check-release-projections`, `pdm run check-cli-output-schemas`,
    `pdm run lint-workflows`, and `git diff --check` pass.
  - The latest wheel passes a clean base-install smoke with no YAML, JSON
    Schema, or CEL imports and the exact quoted extra continuation. The same
    wheel installed with `[double]` passes validate/start, a real Consumer
    outbound write, explicit callback, Consumer-owned public `paid` assertion,
    observe, sealed stop, and idempotent stop outside the repository import
    path.
  - Local execution used Python 3.12 on macOS. CI and publish now admit Python
    3.11/3.14 Linux double-wheel jobs, and the lock contains the pinned CEL
    Linux wheels for both versions; those hosted jobs remain execution evidence
    available only after a committed branch runs CI.
- **Completed reuse/convergence spike and first implementation slice**: Sir
  accepted a focused post-MVP spike on
  2026-08-11 after the implementation audit found that test count alone did not
  prove reinvention, but the 3,088-line compiler, broad optional-field IR, CEL
  source scanning, and duplicate compiler/runtime reference handling were
  credible reuse and maintenance risks. The spike preserved all existing
  double cases while testing narrower Pydantic discriminated models, a
  mechanically checked CEL binding surface, a single local-only immutable JSON
  Schema reference authority, and a non-flat test topology. Its decision table
  is recorded in [`spikes/reuse-convergence/result.md`](spikes/reuse-convergence/result.md).
  Sir then reviewed the test-topology Impact Handshake and said “同意，开始”.
  The implemented first slice replaces the four flat modules with explicit
  interface/language/runtime owners plus scenario, HTTP, run-lifecycle, and
  projection-fact support owners. The collection-derived case identity remains
  78/78 with digest
  `8c0b2e1b78328b5c4d46c5afecd578244d6e2b0bb1770650ca0348db27325231`;
  all 15 fixtures are byte-identical after their move; the complete suite is
  236 passed. No production implementation or behavior changed in this slice.
- **Completed tagged-model stage**: the exact model/compiler/runtime impact and
  serialization invariants are recorded in
  [`tagged-model-impact-handshake.md`](tagged-model-impact-handshake.md).
  Sir authorized continued implementation and one commit per stage on
  2026-08-11. Exact tagged variants now reject contradictory shapes while
  preserving the representative serialized payload, scenario digest, carrier
  manifest round-trip, and historical 78-case identity. Two focused model
  cases raise the complete suite to 238 passed.
- **Completed reference-authority stage**: the shared registry adapter,
  retained stable-URN compatibility projection, dependency boundary, digest
  invariants, and verification evidence are recorded in
  [`reference-authority-impact-handshake.md`](reference-authority-impact-handshake.md).
  Pointer resolution, recursive graph checks, and runtime instance validation
  now share one immutable no-retrieval authority; selected-operation scope and
  scenario identity are unchanged. The complete suite is 240 passed and the
  same wheel passes clean base/extra installation checks.
- **Completed CEL-profile stage**: the shared environment, scanner limitation,
  compiler/runtime projections, and compatibility evidence are recorded in
  [`cel-profile-impact-handshake.md`](cel-profile-impact-handshake.md).
  Compiler and runtime now use the same CEL/RE2 authority; the static scanner is
  isolated and frozen because the selected binding exposes no checked AST. The
  full suite is 242 passed with unchanged scenario identity.
- **Next Step**: Bound the remaining compiler-convergence stage around deep
  authoring, BSL semantic, and OpenAPI adapter interfaces; do not mechanically
  split the compiler merely to reduce its line count.
- **Completed YAML-surface convergence stage**: strict parser construction,
  admitted feature/resource guards, parser diagnostics, source-coordinate
  ownership, and compatibility evidence are recorded in
  [`yaml-surface-impact-handshake.md`](yaml-surface-impact-handshake.md).
- **Next Step**: Define an OpenAPI-profile Impact Handshake that separates
  selected-operation and schema-profile semantics from local artifact loading;
  retain the existing immutable registry and scenario identity.
- **Completed OpenAPI-profile convergence stage**: selected-operation
  semantics, reachable references, schema selection/projection, artifact
  callbacks, and compatibility evidence are recorded in
  [`openapi-profile-impact-handshake.md`](openapi-profile-impact-handshake.md).
- **Next Step**: Close the remaining authoring-shape decision explicitly:
  determine whether Pydantic can replace handwritten YAML object-shape checks
  without weakening stable, source-located diagnostics; adopt only where the
  adapter is deeper than the current compiler policy.
- **Completed authoring-shape decision**: the production probe and decision are
  recorded in [`authoring-shape-decision.md`](authoring-shape-decision.md).
  Direct IR TypeAdapter reuse rejects valid authored collection representation
  and loses BSL diagnostics; separate authoring variants would create a third
  authority. Tagged IR plus the source-aware host compiler remains the v0
  boundary.
- **Next Step**: Evaluate the optional Pact matcher-vector follow-up as
  supplemental conformance evidence only; do not import Pact runtime/provider
  state semantics or add a production dependency.
- **Completed Pact conformance follow-up**: the pinned, license-checked matrix
  and executable external-checkout probe are recorded in
  [`pact-conformance-result.md`](pact-conformance-result.md). Exact and simple
  body-regex facts align, but Pact whole-value query/header regex rejects
  trailing content that CEL substring semantics currently accepts.
- **Decision required**: choose whether BSL keeps explicit CEL substring
  semantics, changes v0 regex to implicit whole-value matching as a
  compatibility correction, or versions a separate whole-value matcher. No
  production behavior changes until Sir confirms that language decision.

- **Standing exploration authority**: Sir explicitly authorizes research,
  exploration, and disposable spikes without asking for further approval. Work
  should continue until it needs Sir's review, missing information, a product
  decision that cannot be resolved from evidence, source mutation, or another
  separately gated action. This does not authorize source implementation,
  dependency changes to the repository, commits, or irreversible/external
  mutations.

## Active Supporting Material

- Renewed application-layer research:
  [`application-practice-research.md`](application-practice-research.md)
- V2 requirement model:
  [`double-requirements-v2.md`](double-requirements-v2.md)
- V2 semantic/runtime decision:
  [`runtime-decision-v2.md`](runtime-decision-v2.md)
- Mock data and fixture governance:
  [`mock-data-governance.md`](mock-data-governance.md)
- Boundary scenario language decision:
  [`language-decision.md`](language-decision.md)
- Completed BSL/runtime/OpenAPI spike:
  [`spikes/bsl-authoring-conformance/result.md`](spikes/bsl-authoring-conformance/result.md)
- Completed compiler/test convergence spike:
  [`spikes/reuse-convergence/README.md`](spikes/reuse-convergence/README.md)
- Authorized test-topology Impact Handshake:
  [`reuse-convergence-impact-handshake.md`](reuse-convergence-impact-handshake.md)
- Authorized tagged-model Impact Handshake:
  [`tagged-model-impact-handshake.md`](tagged-model-impact-handshake.md)
- Authorized reference-authority Impact Handshake:
  [`reference-authority-impact-handshake.md`](reference-authority-impact-handshake.md)
- Authorized CEL-profile Impact Handshake:
  [`cel-profile-impact-handshake.md`](cel-profile-impact-handshake.md)
- Authorized YAML-surface Impact Handshake:
  [`yaml-surface-impact-handshake.md`](yaml-surface-impact-handshake.md)
- Authorized OpenAPI-profile Impact Handshake:
  [`openapi-profile-impact-handshake.md`](openapi-profile-impact-handshake.md)
- Authored-shape reuse decision:
  [`authoring-shape-decision.md`](authoring-shape-decision.md)
- Pact matcher conformance result:
  [`pact-conformance-result.md`](pact-conformance-result.md)
- Replacement MVP design:
  [`design-v2.md`](design-v2.md)
- Concrete BSL v0 authoring contract:
  [`bsl-v0-contract.md`](bsl-v0-contract.md)
- Replacement Impact Handshake:
  [`impact-handshake-v2.md`](impact-handshake-v2.md)
- Final pre-implementation review:
  [`final-review.md`](final-review.md)
- Independent implementation plan:
  [`implementation-plan.md`](implementation-plan.md)
- Repository-aware preflight rehearsal:
  [`preflight-rehearsal.md`](preflight-rehearsal.md)

## Superseded Historical Material

These files remain only to preserve the reasoning history. They are not inputs
to an implementation decision:

- [`evidence.md`](evidence.md)
- [`requirements-research.md`](requirements-research.md)
- [`real-double-requirements.md`](real-double-requirements.md)
- [`service-boundary.md`](service-boundary.md)
- [`runtime-decision.md`](runtime-decision.md)
- [`dsl-benchmark.md`](dsl-benchmark.md)
- [`design.md`](design.md)
- [`impact-handshake.md`](impact-handshake.md)

- **Decisions admitted**: Sir accepts the V2 managed-boundary direction, the
  composite BSL language architecture, and the command family
  `validate|start|emit|observe|stop` without `check`. Spike evidence admits
  local typed-node authoring, a restricted CEL profile, raw/structured
  event-body separation, and WireMock as reference rather than default. Sir
  confirmed the amended concrete grammar, dependency/runtime boundary, Impact
  Handshake, and explicit source start. A whole-envelope event materializer
  owns its query/headers/body so authored dead configuration is rejected.
- **Work authorization**: Sir explicitly authorized the amended Impact
  Handshake, requested a task-packet commit, and started source implementation
  on 2026-08-10. The authorization covers the paths and state diff in
  [`impact-handshake-v2.md`](impact-handshake-v2.md); further commits,
  publishing, release, irreversible external mutation, and economically
  material actions still require separate authority. Sir separately authorized
  the behavior-preserving test-topology slice on 2026-08-11 under
  [`reuse-convergence-impact-handshake.md`](reuse-convergence-impact-handshake.md).
