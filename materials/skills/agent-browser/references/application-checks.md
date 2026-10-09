# Run an application check and retain its execution

Read this when a browser, API or build check needs a durable output/exit record or an owned temporary service. Use the existing runner and execution record when they already provide both. This helper records execution; it does not define application acceptance.

For Playwright checks, use the supplied `BROWSER_EXECUTABLE_PATH` and verify it is executable before a long run; do not guess a Chromium cache path. When copying an existing dependency tree into a temporary checkout, `cp -al` works only on the same filesystem. Across devices, use an ordinary copy or install; keep the first concrete failure in a log and return a short error summary.

Before the first application check, use the execution tool’s durable record if it already retains complete output and the check’s exit status; otherwise use `scripts/with-service.py` beside this skill to retain them and clean up its own process groups.
This also applies to API or build checks; using this wrapper does not require browser interaction or delegation to a browser operator.
Read `python3 <skill-directory>/scripts/with-service.py --help` for arguments. The helper creates a new attempt directory under `--evidence-root` when supplied, otherwise the process temporary directory. Choose an owned evidence directory allowed by the run. Preserve that directory through cleanup and handoff.

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
It does not choose assertions, rewrite the application or change the browser tool. For a check that modifies data, bind a fresh attempt copy to the application's existing data-path option:

```sh
python3 <skill-directory>/scripts/with-service.py --cwd "$PWD" --port 4317 \
  --evidence-root "$RUN_EVIDENCE" \
  --fresh-data "$SOURCE_DATABASE" --data-mode sqlite --data-env ARC_DB_FILE \
  --start 'exec node backend/src/index.js' -- npm run application-check
```

Replace `ARC_DB_FILE`, the commands and source path with the application's actual documented interface. SQLite mode opens the source read-only and uses SQLite online backup into a new path; file and directory modes copy into a new path, and directory sources must be quiescent. The chosen environment variable is set identically for service and check. The wrapper does not interpret schemas, invent seeds or make the check runner honor that variable. The receipt records the source, fresh path and variable; inspect application logs/configuration to confirm consumption. It never deletes or replaces source data, and retains the attempt copy for diagnosis. Use a new invocation for each reset rather than replacing an open database.

Readiness requires a previously vacant port and the owned process alive before and after HTTP. This reduces stale-service confusion but does not independently prove which PID owns the socket; retain the recorded limitation rather than treating health success as absolute ownership proof. Cleanup signals only its own process groups, confirms group disappearance after KILL, and reports incomplete cleanup as an error.

The completion output names `check.log` and `result.json` and reports `check_exit` separately from execution and cleanup status. The receipt retains the actual command, working directory, candidate information, supplied prerequisites and original check exit result.
Preserve it from the first execution and pass that directory to the next member.
Use svc-verification’s result interpretation to judge coverage and applicability to another candidate; the wrapper records execution facts and does not decide acceptance.
An unstarted check has no exit result; interruption and service failure must not be described as an application assertion failure.

For a long check, run the whole wrapper using background Bash and retain the returned `pbb:instance:bgNNN` handle. Use `background_job` with `operation: "wait"` or `"result"` and that handle to obtain the retained exit/body while other jobs remain active. `subagent_wait` is for subagents; aggregate waiting is not the way to wait for one suite. `operation: "stop"` requests owned process-group shutdown and confirms it; a timeout is not proof that the service stopped. Automatic completion notifications remain available, but terminal results do not require waiting for a notification. Never infer suite success from a final grep/tail exit; pass the real command to the wrapper and summarize its retained logs afterward.
Prefer letting the wrapper finish normally. If abandoning the check, stop its specific background job, then inspect result.json cleanup_status and the owned processes or ports. A missing or pending receipt leaves cleanup unconfirmed; do not compensate with a global pkill.
Do not append global `pkill -f` by program name or port.
Other members can share the process space even when their Git checkouts are separate.
The helper cleans up only the process groups it started; it cannot prevent a wrapped command from killing unrelated processes or capture descendants that detach into another session.
Use runners whose own cleanup stays within their owned processes.
SIGKILL or host failure may prevent cleanup and the final receipt; missing evidence is not success.
