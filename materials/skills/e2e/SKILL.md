---
name: e2e
description: Use for UI exploration and repeatable application acceptance, especially after shared navigation, routing, authentication or permission changes and when first writing or revising journey checks. Preserve scenario obligations, review coverage against actual check code, and retain real errors and evidence using the executor-owned browser entry or stable local MCP.
---

Read `e2e guide mcp` before browser operation, and the applicable `e2e guide setup`, `writing-tests`, `agent` or `running` before writing or running application checks. These version-matched instructions are independent files in the installed package. Use `--help` for unfamiliar flags.

## Prepare the owned environment

Before opening a session or running application checks, read [Runtime setup](references/runtime-setup.md) for this package's configuration path, service, browser, model connection and output ownership. Keep those values with the work item. TypeScript runner and legacy direct-MCP shell commands must supply their required environment in every invocation; an earlier shell export does not persist. The native owned e2e tool receives its connection recipe from the executor and does not require you to export connection values. Do not substitute another run's configuration or evidence. Manual MCP does not call the inner model; model-backed steps consume the run's authorized budget. Use exact locator assertions when the contract is exact.

## Isolate application check data

A database copy isolates the check service from delivery data, not one case from another. Fresh browser contexts and `workers: 1` do not reset server data, repository files, uploads or search indexes. For independent cases, create separate mutable business objects; use the runner's `beforeEach`, `afterEach` or `test.extend` fixtures when setup or cleanup is needed. In particular, do not merge a seeded PR into the same repository that later file/search cases assume is unchanged.

Keep an intentional stateful journey in one case, or an explicit serial scenario as described in `e2e guide writing-tests`. Do not reset its state between dependent steps. If a case needs an initial database snapshot, stop its owned service before restoring the isolated copy, include associated mutable files/indexes, then restart and check readiness; never overwrite a live database or delivery data. A whole-database reset is not the default.

When a failure may depend on prior cases, run the failing case alone from its documented initial fixture, then compare with the sequence. Retain the fixture and order with the report. A pass after earlier cases is not proof of independence, and a failure in the sequence alone is not proof of an application defect.

## Operate the browser

When the native `e2e` tool is in your catalog, read [Owned session entry](references/owned-session-entry.md) and use its handle-based operations. Its executor fixes connection inputs; do not invoke the raw mcporter E2E alias or manually re-export session environment. The following direct-MCP guidance applies only to executors without that owned entry.

Read [MCP session lifecycle](references/mcp-session-lifecycle.md) before opening a session. Keep one attempt's complete child environment, config path, configured server cwd and command unchanged from open through actions and close. `mcporter` keep-alive reuses a connection only for the same connection identity; a shared daemon alone does not guarantee the same E2E server. Export the required values in every independent shell invocation. Choose `E2E_OUTPUT_DIR` before opening, then change it only after closing that attempt's sessions.

`open_session` returns MCP text beginning with `Session <id>`, not a structured `session_id` property. Pass the returned id explicitly as the `session` payload field to every `tools`, `call` and `close_session`. Do not put it into a newly added `E2E_SESSION` environment variable: changing child environment after open can launch a different server with no such session. Each open creates a new session; do not reopen merely because a call failed.

Use `tools` to inspect the actual catalog and `locate` with semantic role/name, label, placeholder or exact text to check a locator. Do not find controls by regex over rendered observation lines. Observe before acting, use node ids from the newest observation, and re-locate after an action changes the screen. A successful action or a closed session does not establish acceptance. The [same-attempt example](references/mcp-session-lifecycle.md#one-complete-exploration-attempt) opens, reads the catalog, observes and locates, then closes its own id in `finally`; extend its action block according to the actual catalog and requirement.

Read both the real CLI exit status and MCP result, including `isError`, error text and action observations. In the frozen mcporter CLI, MCP `isError` sets exit 1; wrappers must not discard that exit or treat an observation accompanying failure as success. Preserve the first failure and cleanup output. Always attempt to close your own known id in `finally`, with the same connection inputs, while retaining any original failure. Do not stop the run-owned daemon or another agent's sessions.

For pixels, call tool `screenshot` with `--save-images <owned-evidence-directory>`. Read the saved image with the native read tool or the assigned vision/browser operator; do not print base64 into model context. Coordinate tools need a current screenshot. Trace files are saved under the config output's `artifacts/`; explicit start/stop_recording saves video. Video is not masked. Secret-filled sessions may withhold pixels; continue through semantic nodes when appropriate. Read close cleanup text: exit 0 alone does not prove cleanup. Agent-browser remains available for console/network diagnosis or a documented capability gap.

## Preserve the acceptance contract

Before changing shared UI entry points, routes, authentication or permission behavior, read the installed svc-verification skill's check-design guidance. Record the changed component, affected public scenario locations, and required visible behavior in the current task packet. After the change, exercise journeys through those shared entries; a passing destination-page check does not establish that the entry remains usable. Reuse applicable evidence and keep unexamined effects explicit rather than rerunning every unrelated case.

Before writing final acceptance checks, map each supplied scenario to its initial state, visible entry path, required observations, and check case. Keep stable source scenario identifiers or locations and the mapped case/assertions beside the existing acceptance code and results; the supplied requirements remain authoritative, rather than a copied specification. Reuse a case for multiple scenarios only when it observes every required step and outcome; record missing or blocked scenarios explicitly. A passing case count is not a requirement coverage count.

For a user journey, begin at the required entry and follow visible navigation. Deep links and API setup can support local diagnosis but do not establish that the user can reach the feature. Include required reload, another browser or account, permissions, and persistence observations. Distinguish a list row from an opened detail view, a transient success message from retained state, and a numeric count from its required visible meaning. Use accessible roles and names when the supplied contract requires them.

After the first acceptance code is written, use the existing advisor, when available, for one bounded comparison of the original public scenarios, actual check code and relevant shared-component changes. Follow svc-verification's independent translation review: ask for missing obligations and titles or comments unsupported by the executed steps, not approval of the implementation. Give source paths and candidate identity; the implementer's summary alone is insufficient. Resolve returned gaps or record them as unverified. If no independent collaborator is available, record that limitation and perform the comparison directly.

If a check fails, decide from the requirement whether the application or the check is wrong. Do not weaken exact matching, remove navigation or reload, or substitute an internal test id merely because the current implementation passes the replacement. Keep the original failure and the requirement-based reason for a changed assertion. Recheck materially changed criteria, skipped steps or reduced coverage against the original obligations, using a bounded advisor comparison of the affected changes when available; ordinary locator repairs that preserve the observation do not need another whole-suite review. At delivery, report covered, failed, blocked, and unverified scenarios separately; claim complete acceptance only for the mapped requirements actually observed on the delivered candidate. A source association or a completed review is not itself evidence that the product meets the requirement.

When a later action depends on a submit, login, logout or save, read [Business state transitions](references/business-state-transitions.md) for observing the required visible terminal state and retaining the first failure and changed rerun conditions. Action completion, URL changes and HTTP200 do not establish the required page outcome.

## Application E2E results

Run `e2e run --config "$E2E_CONFIG" <application-check-file> --reporter list,markdown --ai-trace` through the existing durable command record; export the config and owned service URL in this invocation. If that record omits full output or the real exit status, use the application-check execution reference in the installed agent-browser skill for its `with-service --check-only` wrapper. Record the frozen candidate commit, actual service and isolated data prerequisites. A report is valid only for the attempt that produced it; startup errors can leave old reports unchanged. Use a fresh output directory for each acceptance attempt.

Read `run.errors`, final attempts, steps and artifact paths in `report.json`. A verified pass requires the applicable observations and successful execution, rather than an exit code alone. `--ai-trace` records model round trips but replaces image bytes with counts; retain screenshots separately. Keep reporters within the run's authorized local evidence destinations.

When interpreting nonzero exits, repaired model responses, exploration limits or usage totals, read [Frozen runner result interpretation](references/runner-results.md). Check the installed runner identity first; version-specific report omissions are diagnostic conditions, not common acceptance rules.
