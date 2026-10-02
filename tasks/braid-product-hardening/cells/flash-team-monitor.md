# Flash team local generation monitor

## 2026-09-28 initial check

- Remote run root: `/home/yyh/Development/factory26/runs/e20260928-01-flash-team` on `wsl.win-ws.localhost`.
- `execution.json` is `phase=generating`, controller PID `122373`; controller `active.json` is `phase=running`.
- Both expected runs exist and are `phase=running`: GitHub `pi-braid-flash-team--hackathon--github-8585fe9975271a`, Sheet `pi-braid-flash-team--hackathon--sheet-d7d79571498155`.
- Frozen agent SHA matches the authorized value `ca994e13be524e8a2ffc6cda03c1c26d6c88e44a5df97cb11b887b91b2b5f5af`.
- Runner launch is confirmed: both runs have `local_submit.py run` children (PIDs 122694 and 122695) using the pinned image digest `sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d`; each emitted `stage-started` in `events/arc-bench.jsonl` at ~10:27. These facts do not by themselves prove native model execution.
- No terminal result or collector failure is present yet. Continue scheduled observation; do not restart, cancel, or poll model APIs.

## 10:33 terminal observation

- GitHub run has a confirmed generation harness failure in `workspace/official-generation/template/.arc/runner-events.jsonl`: `status=error`, command `/workspace/submission/main.py ...` exited 1. `execution.debug.log` gives the root error: `FileNotFoundError: 后台任务 CLI 缺失：.../runtime/node_modules/pi-background-bash/bin/pbb.js 或 .../pi-lane/bin/pil.js`.
- This is an actual runner/agent failure, not a token-progress inference. Sheet remains `phase=running` with heartbeat events through 10:33 and must be observed until its own terminal state; no cancellation or restart performed.

## Old experiment stopped

- After the authorized lab stop, GitHub is `phase=finished` with `error: Agent generation did not produce a complete application`; Sheet is `phase=cancelled` with missing `experiment-result.json`.
- No `arc_bench_adapter`, `local_submit`, controller, or `run-experiment` process remains (the matching `pgrep` output only reported its inspection shell).
- These are preserved as old-attempt outcomes; no restart was performed.

## attempt-02 monitoring start

- `e20260928-01-flash-team/attempt-02` controller PID 124602 is generating, but its `generation/runs` directory had no assigned run at the first check.
- `e20260928-02-deepseek-direct/attempt-02` controller PID 124546 is generating; GitHub run `pi-braid--hackathon--github-87616ca3ee80f1` and Sheet run `pi-braid--hackathon--sheet-6533a6edafdd94` are `running` and have `stage-started` events.
- At this check no native Pi session transcript/tool evidence or collector result was present yet for the DeepSeek runs; runner presence alone is not treated as model execution. Continue scheduled monitoring.
