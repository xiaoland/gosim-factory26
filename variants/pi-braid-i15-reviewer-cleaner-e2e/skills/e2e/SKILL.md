---
name: e2e
description: Operate the current application through local e2e MCP; write and run TypeScript application E2E checks with the frozen e2e runner, retaining screenshots, traces and actual errors; establish bounded visible business outcomes before dependent actions.
---

Read `e2e guide mcp` before browser operation, and the applicable `e2e guide setup`, `writing-tests`, `agent` or `running` before writing or running application checks. These version-matched instructions are independent files in the installed package. Use `--help` for unfamiliar flags.

## Prepare the owned environment

Before opening a session or running application checks, read [Runtime setup](references/runtime-setup.md) for this package's configuration path, service, browser, model connection and output ownership. Keep those values with the work item and provide them in every shell invocation; an export in an earlier tool call does not persist into another. Do not substitute another run's configuration or evidence. Manual MCP does not call the inner model; model-backed steps consume the run's authorized budget. Use exact locator assertions when the contract is exact.

## Isolate application check data

A database copy isolates the check service from delivery data, not one case from another. Fresh browser contexts and `workers: 1` do not reset server data, repository files, uploads or search indexes. For independent cases, create separate mutable business objects; use the runner's `beforeEach`, `afterEach` or `test.extend` fixtures when setup or cleanup is needed. In particular, do not merge a seeded PR into the same repository that later file/search cases assume is unchanged.

Keep an intentional stateful journey in one case, or an explicit serial scenario as described in `e2e guide writing-tests`. Do not reset its state between dependent steps. If a case needs an initial database snapshot, stop its owned service before restoring the isolated copy, include associated mutable files/indexes, then restart and check readiness; never overwrite a live database or delivery data. A whole-database reset is not the default.

When a failure may depend on prior cases, run the failing case alone from its documented initial fixture, then compare with the sequence. Retain the fixture and order with the report. A pass after earlier cases is not proof of independence, and a failure in the sequence alone is not proof of an application defect.

## Operate the browser

With `E2E_CONFIG` exported to the absolute config path from Runtime setup and `E2E_APP_URL` set to the owned service URL in this invocation, open a session and retain its id:

```sh
mcporter call e2e.open_session --args "$(node -e 'process.stdout.write(JSON.stringify({config: process.env.E2E_CONFIG}))')"
```

The JSON serialization preserves the actual path, including spaces and quotes. Each checkout's server connection is separate; agents sharing this checkout each open their own session. Pass that id on every `tools`, `call` and `close_session` invocation. Use `mcporter call e2e.tools --args '{"session":"<id>"}'` for the actual catalog, then `e2e.call` with `session`, `tool` and `args`. Observe before acting; node ids belong to the latest observation. A successful action or a closed session does not establish application acceptance.

For pixels, invoke `e2e.call` with tool `screenshot` and add `--save-images <owned-evidence-directory>`. Read the saved image with the native read tool, or pass its absolute path to the assigned vision/browser-operator. Do not print base64 into model context. Coordinate tools need a current screenshot. Preserve actual errors; mcporter reports MCP error results with exit 1. Trace files are saved under the config output's `artifacts/`; explicit start/stop_recording saves video. Video is not masked. Secret-filled sessions may withhold pixels; continue through semantic nodes when appropriate.

Close only your session with `e2e.close_session`. Read its cleanup text: exit 0 alone does not prove cleanup. The run owns the mcporter daemon; do not stop a shared daemon or another agent's session. Agent-browser remains available for its console/network diagnostics or a documented e2e capability gap.

## Dependent business transitions

Before the next action depends on a submit, login, logout or save, use the visible success/failure states and bounded assertions described in [Business state transitions](references/business-state-transitions.md). Action completion, URL changes and HTTP200 do not establish the required page outcome. Keep the first failure and its response latency; a narrower passing rerun does not erase a full-journey failure. Read the frozen `e2e guide writing-tests` complete example for fixtures and supported APIs before constructing the acceptance suite.

## Application E2E results

Run `e2e run --config "$E2E_CONFIG" <application-check-file> --reporter list,markdown --ai-trace` through the existing durable command record; export the config and owned service URL in this invocation. If that record omits full output or the real exit status, use the application-check execution reference in the installed agent-browser skill for its `with-service --check-only` wrapper. Record the frozen candidate commit, actual service and isolated data prerequisites. A report is valid only for the attempt that produced it; startup errors can leave old reports unchanged. Use a fresh output directory for each acceptance attempt.

Read `run.errors`, final attempts, steps and artifact paths in `report.json`. A verified pass requires the applicable observations and successful execution, rather than an exit code alone. `--ai-trace` records model round trips but replaces image bytes with counts; retain screenshots separately. Keep reporters within the run's authorized local evidence destinations.

When interpreting nonzero exits, repaired model responses, exploration limits or usage totals, read [Frozen runner result interpretation](references/runner-results.md). Check the installed runner identity first; version-specific report omissions are diagnostic conditions, not common acceptance rules.
