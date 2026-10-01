# mvp-HA External Consumer Acceptance

## Objective & Hypothesis

Replace the running WeChat Pay and Caocao fake-server processes in an isolated
`mvp-HA` worktree with the built `svc double` wheel, then rerun the repository's
real `system-scenario` Vitest project. The hypothesis is that claim-scoped
scenario modules plus explicit events can preserve Consumer-visible behavior
without recreating either provider as a complete backend. The Consumer's
callback-time provider re-query requires a narrow order-phase projection; the
acceptance materializer owns only that explicit script state and reports the
existing materializer state/determinism non-claim.

## Guardrails Touched

- Worktree: `~/development/Anana/mvp-HA-svc-double-e2e` on
  `wsl.win-ws.localhost`, detached from `e8c14ff9`.
- The original `mvp-HA` worktree and its unrelated changes remain untouched.
- The acceptance lane must run the SVC wheel built from the current local source.
- Provider transitions are explicit named events; scenario variants express
  failure or availability claims. The Caocao materializer persists only the
  current phase needed by the Consumer's callback-time detail re-query; it does
  not model provider scheduling, retries, fleets, dispatch, or edge cases.
- Consumer-facing UI/API assertions remain the product oracle.
- Test credentials and signing code may be managed fixtures/materializers; no
  original fake-server process or fake-server runtime module may be imported.

## Verification

1. Baseline: original fake servers pass the full system project.
2. Replacement: global setup launches only `svc double` carriers for these two
   boundaries; no fake server process is started.
3. Run all system scenarios, not a reduced happy-path-only command.
4. Confirm `svc double observe` contains the expected matched requests/events
   while test assertions remain in `mvp-HA`.
5. Stop and seal every double run, including failure cleanup.
6. Record any SVC language/runtime gap with a minimal reproduction and a
   regression test before extending SVC.

## Evidence

- Baseline on 2026-08-10: `11` files and `39` system scenarios passed in
  `137.75s` after starting the repository's Postgres prerequisite.
- First proven gap: Caocao writes use dynamic
  `application/x-www-form-urlencoded`; BSL v0 currently permits only structured
  JSON or byte-exact managed raw request bodies. Neither can semantically match
  dynamic signed form fields. A narrow form-field matcher/capture surface is
  required; ignoring the body would make the acceptance invalid.
- Replacement implementation used the locally built
  `sustainable_vibe_coding-11.0.1-py3-none-any.whl[double]` in an isolated
  Python 3.13 venv on WSL. Six Caocao scenario variants and the parameterized
  WeChat Pay module all passed `svc double validate` before execution.
- The first replacement run exposed a carrier deadlock: `emit` held the engine
  lock while calling the Consumer, while the Consumer synchronously queried
  provider detail from the responder. Event request materialization now stays
  atomic but external I/O runs outside that lock; a re-entrant Consumer
  regression test proves the callback can query the responder before ack.
- The WeChat Pay certificate request exposed a second runtime defect: an
  unrelated structured interaction tried to parse the empty body after its
  method/path had already differed, poisoning the valid route. Exact
  method/path now prefilter body matching; a two-route regression test covers
  the failure.
- WeChat Pay response signatures also proved the replay clock is protocol
  data, not an arbitrary fixture. Acceptance runs let `start` capture the
  current clock because the real SDK rejects signatures more than five minutes
  away; the clock remains immutable within that run.
- Replacement acceptance passed all `11` system-scenario files and all `39`
  tests twice, in `183.19s` and `183.81s`. The focused ride-hailing suite passed
  `9/9`; its full black-box happy path covered Caocao accepted/arrived/in-trip/
  finished callbacks followed by WeChat Pay certificate retrieval, JSAPI
  prepay, signed encrypted success notification, and the paid bill UI.
- A clean-registry lifecycle rerun passed and left the run registry at zero
  bytes with no `svc_cli.double.carrier`, fake Caocao, or fake WeChat Pay
  process. Every stopped run observed in the final window was sealed. The
  acceptance-only Postgres container, network, and volume were removed.
- Final sealed-journal evidence is independently readable after process exit:
  the Caocao happy-path snapshot has `36` retained facts and four acknowledged
  events (`order.accepted`, `order.arrived`, `order.in-trip`, `order.finished`);
  the WeChat Pay snapshot has matched `certificates` and `create-jsapi-prepay`
  requests plus acknowledged `payment.succeeded`. Both report
  `authority=sealed-snapshot`, `control_status=not-required`, and `sealed=true`.
- All `17` generated descriptors left by the iterative acceptance runs validate
  with the installed wheel, and an import scan over the replacement lane finds
  no fake-server package/runtime import.
- The original `/home/yyh/development/Anana/mvp-HA` worktree retained exactly
  its pre-existing unrelated status. All Consumer replacement edits remain in
  the disposable `/home/yyh/development/Anana/mvp-HA-svc-double-e2e` worktree;
  no fake-server runtime module is imported by the replacement lane.
- After the runtime/language findings, the SVC repository passed `236` tests,
  mypy over `53` source files, Ruff, all seven import contracts, CLI output
  schema verification, and `git diff --check`. The acceptance worktree's seven
  changed TypeScript files passed focused oxlint, and all three materializer/
  generator scripts passed Node syntax checks.
