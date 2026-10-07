---
name: e2e
description: Operate the current application through local e2e MCP; write and run TypeScript application E2E checks with the frozen e2e runner, retaining screenshots, traces and actual errors.
---

Read `e2e guide mcp` before browser operation, and the applicable `e2e guide setup`, `writing-tests`, `agent` or `running` before writing or running application checks. These version-matched instructions are independent files in the installed package. Use `--help` for unfamiliar flags.

## Prepare the current checkout

Use the application service owned by this work item, its actual portless URL, and isolated test data. Do not operate another checkout's changing service or mutate the delivery application's initial data. `E2E_CONFIG_TEMPLATE` names the supplied config. Create `.factory-e2e/` in the current checkout, copy that template as `.factory-e2e/e2e.config.ts`, and symlink `.factory-e2e/node_modules` to `E2E_NODE_MODULES`. Keep this directory ignored by Git. The config's directory is e2e's project root; write application E2E files under `.factory-e2e/tests/`. Checks needed in the delivered application must be integrated into its actual tooling separately.

Export `E2E_APP_URL` to the actual owned service URL in every mcporter/e2e shell invocation. The supplied config does not start another service. Its model is `factory26/glm-5.3-flash` through the run's `FACTORY26_BASE_URL` and `FACTORY26_API_KEY`; the experiment supplies the selected OpenAI-compatible endpoint and credentials, without an ARC-specific restriction in this template. Do not substitute credentials or enable a hosted browser or subscription sign-in outside the frozen experiment inputs. Manual MCP does not call that model. Model-backed `agent.*` steps consume the run's model budget and are bounded per step; choose exact locator assertions when the contract is exact. Restricted expensive models must not be used by this inner runner, which does not pass through Pi's Braid-session budget guard.

The addon includes the default Chromium only. Keep `web()` on that browser and use the prepared browser tree; do not trigger browser installation during a run.

## Isolate application check data

A database copy isolates the check service from delivery data, not one case from another. Fresh browser contexts and `workers: 1` do not reset server data, repository files, uploads or search indexes. For independent cases, create separate mutable business objects; use the runner's `beforeEach`, `afterEach` or `test.extend` fixtures when setup or cleanup is needed. In particular, do not merge a seeded PR into the same repository that later file/search cases assume is unchanged.

Keep an intentional stateful journey in one case, or an explicit serial scenario as described in `e2e guide writing-tests`. Do not reset its state between dependent steps. If a case needs an initial database snapshot, stop its owned service before restoring the isolated copy, include associated mutable files/indexes, then restart and check readiness; never overwrite a live database or delivery data. A whole-database reset is not the default.

When a failure may depend on prior cases, run the failing case alone from its documented initial fixture, then compare with the sequence. Retain the fixture and order with the report. A pass after earlier cases is not proof of independence, and a failure in the sequence alone is not proof of an application defect.

## Operate the browser

Use `mcporter call e2e.open_session --args '{"config":"<absolute-checkout>/.factory-e2e/e2e.config.ts"}'` and retain its session id. Each checkout's server connection is separate; agents sharing this checkout each open their own session. Pass that id on every `tools`, `call` and `close_session` invocation. Use `mcporter call e2e.tools --args '{"session":"<id>"}'` for the actual catalog, then `e2e.call` with `session`, `tool` and `args`. Observe before acting; node ids belong to the latest observation. A successful action or a closed session does not establish application acceptance.

For pixels, invoke `e2e.call` with tool `screenshot` and add `--save-images <owned-evidence-directory>`. Read the saved image with the native read tool, or pass its absolute path to the assigned vision/browser-operator. Do not print base64 into model context. Coordinate tools need a current screenshot. Preserve actual errors; mcporter reports MCP error results with exit 1. Trace files are saved under the config output's `artifacts/`; explicit start/stop_recording saves video. Video is not masked. Secret-filled sessions may withhold pixels; continue through semantic nodes when appropriate.

Close only your session with `e2e.close_session`. Read its cleanup text: exit 0 alone does not prove cleanup. The run owns the mcporter daemon; do not stop a shared daemon or another agent's session. Agent-browser remains available for its console/network diagnostics or a documented e2e capability gap.

## Application E2E results

Run `e2e run --config .factory-e2e/e2e.config.ts <application-check-file> --reporter list,markdown --ai-trace` through the existing durable command record; if that record omits full output or the real exit status, read the agent-browser skill and use its `with-service --check-only` wrapper. Record the frozen candidate commit, actual service and isolated data prerequisites. A report is valid only for the attempt that produced it; startup errors can leave old reports unchanged. Use a fresh output directory for each acceptance attempt.

Read `run.errors`, final attempts, steps and artifact paths in `report.json`. Exit 1 is an application failure; 2 is a config/dependency/policy failure; 3 is infrastructure/provider/cleanup failure; 4 is an internal failure; 130 is interruption. None is a verified pass. `--ai-trace` records model round trips but replaces image bytes with counts; retain screenshots separately. Do not send upstream feedback or enable a GitHub reporter. `E2E_TELEMETRY_DISABLED=1` is supplied by this run.

Inspect repaired `MODEL_OUTPUT_INVALID` responses and failed steps even when the run passes. This release can omit a rejected schema response from report usage; count all model round trips in `ai-trace.json` when recording consumption. An exploration can fall back from a failed planner and end at its step limit, so its exit 0 alone does not prove its original goal was covered.
