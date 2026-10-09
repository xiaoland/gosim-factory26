---
name: agent-browser
description: Operate applications through a browser; run existing application checks with retained exit results and owned-process cleanup, with or without a temporary service.
---

Read `agent-browser skills get core` for the version-matched interface and workflows. Use `--help` or a specific bundled reference for unfamiliar commands.

Before the first browser interaction, choose a named session as described by the bundled core skill: `export AGENT_BROWSER_SESSION="$(agent-browser session id --scope worktree --prefix task)"`. Reuse that name on every command, explicitly with `--session <name>` when the environment is not preserved between shell calls. Parallel browser tasks in the same worktree need distinct names or prefixes. Pass the name when handing off the same journey so the next agent can continue with the same page and login state. Sessions belong to browser tasks, independently of agent identities; use native profile or CDP options when the task needs them.

Observe the current page, perform the requested interaction, then inspect the state that answers the question. DOM references expire after page changes. Use screenshots when appearance matters and the accessibility tree for controls and content. Preserve evidence paths and return only observations relevant to the delegated question. A successful click is not proof that the application persisted or applied the change. Use normal UI interactions for the behavior being checked; direct API or JavaScript state mutation is only an explicitly identified precondition or diagnostic action.

For Playwright checks, use the supplied `BROWSER_EXECUTABLE_PATH` and verify it is executable before a long run; do not guess a Chromium cache path. When copying an existing dependency tree into a temporary checkout, `cp -al` works only on the same filesystem. Across devices, use an ordinary copy or install; keep the first concrete failure in a log and return a short error summary.

Before the first application check, use the execution tool’s durable record if it already retains complete output and the check’s exit status; otherwise use `scripts/with-service.py` beside this skill to retain them and clean up its own process groups.
This also applies to API or build checks; using this wrapper does not require browser interaction or delegation to a browser operator.
Read `python3 <skill-directory>/scripts/with-service.py --help` for arguments.

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
  -- python3 /tmp/my_check.py
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
