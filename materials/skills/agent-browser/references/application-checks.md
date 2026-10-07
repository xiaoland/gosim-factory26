# Run an application check and retain its execution

Read this when a browser, API or build check needs a durable output/exit record or an owned temporary service. Use the existing runner and execution record when they already provide both. This helper records execution; it does not define application acceptance.

For Playwright checks, use the supplied `BROWSER_EXECUTABLE_PATH` and verify it is executable before a long run; do not guess a Chromium cache path. When copying an existing dependency tree into a temporary checkout, `cp -al` works only on the same filesystem. Across devices, use an ordinary copy or install; keep the first concrete failure in a log and return a short error summary.

Before the first application check, use the execution tool’s durable record if it already retains complete output and the check’s exit status; otherwise use `scripts/with-service.py` beside this skill to retain them and clean up its own process groups.
This also applies to API or build checks; using this wrapper does not require browser interaction or delegation to a browser operator.
Read `python3 <skill-directory>/scripts/with-service.py --help` for arguments. The helper creates its receipt directory under the process temporary directory; set `TMPDIR` to an existing, owned evidence directory allowed by the run before invoking it. Preserve that directory through cleanup and handoff.

If the application already has a check runner that starts its own services, keep that runner and wrap it with `--check-only`:

```sh
python3 <skill-directory>/scripts/with-service.py --check-only --cwd "$PWD" \
  --context "candidate=$(git rev-parse HEAD)" \
  --context "data=runner creates fresh per-spec directories" \
  -- bash checks/run.sh
```

Replace the command and context with the actual check entry and its prerequisites; the example does not require that filename or assert how your runner prepares data.
`--context` records supplied facts for review; it neither sets environment variables nor proves their truth.
Set required environment variables through the check's normal interface.
The runner still owns its service topology, readiness checks, test data and assertions.
Pass the actual check command after `--`, without a display pipeline such as `| grep` or `| tail`; summarize the saved `check.log` afterward.
The wrapper records the supplied process's exit status. If a runner hides a failed step behind a successful final command, that runner must propagate the failure; the wrapper does not parse or rewrite its shell.

If the check needs one foreground service, use the existing service mode:

```sh
python3 <skill-directory>/scripts/with-service.py --cwd "$PWD" --port 4317 \
  --start 'npm run dev -- --host 127.0.0.1 --port "$PORT"' \
  -- python3 checks/browser-check.py
```

The service receives `PORT`; the check receives the same `BASE_URL`.
Choose a readiness path that succeeds only when the needed service is ready; HTTP success does not establish application correctness.
The helper refuses an occupied port before starting and monitors its foreground service.
It does not create or reset data, choose assertions, rewrite the application or change the browser tool.

The completion output names `check.log` and `result.json` and reports `check_exit` separately from execution and cleanup status. The receipt retains the actual command, working directory, candidate information, supplied prerequisites and original check exit result.
Preserve it from the first execution and pass that directory to the next member.
Use svc-verification’s result interpretation to judge coverage and applicability to another candidate; the wrapper records execution facts and does not decide acceptance.
An unstarted check has no exit result; interruption and service failure must not be described as an application assertion failure.

For a long check, run the whole wrapper using the existing background Bash tool and retain its job ID; completion is delivered through that tool.
Prefer letting the wrapper finish normally. If abandoning the check, stop its specific background job, then inspect result.json cleanup_status and the owned processes or ports. A missing or pending receipt leaves cleanup unconfirmed; do not compensate with a global pkill.
Do not append global `pkill -f` by program name or port.
Other members can share the process space even when their Git checkouts are separate.
The helper cleans up only the process groups it started; it cannot prevent a wrapped command from killing unrelated processes or capture descendants that detach into another session.
Use runners whose own cleanup stays within their owned processes.
SIGKILL or host failure may prevent cleanup and the final receipt; missing evidence is not success.
