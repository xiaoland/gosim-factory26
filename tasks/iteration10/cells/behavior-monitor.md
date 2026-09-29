# 两题原生工作行为增量证据

人工语义观察基线见 [behavior.md](../observations/behavior.md)；本采集器仅提供下一次观察可核对的证据位置，不根据工具次数判断流程是否落实。

`scripts/monitor-behavior.py` 以 lab `run.json.labels.retained_generation` 定位两题原工作区，读取 Braid `sessions.json` 和 Pi `pi-timing.jsonl` 所列原生 JSONL。后者可补充不在 Braid 会话索引中的 Pi 子会话；嵌套在主会话文件同名目录下的子会话标为路径推断父会话。采集 `subagent` spawn/status/wait 的动作、角色、模型和任务摘要，工具结果的错误标记，skill 文件读取、workflowScript 调用、Braid issue/pr CLI 及文档操作的路径证据。每条事件带时间、会话、工作项、原文件路径、行号和字节偏移。原生输出正文、文档内容和凭据文件均不复制到采样文件。缺失 spawn 时，status 仍只是 status，不能算作本次委派。

采样还记录 `origin.git` 的 develop commit/tree、PR ref 摘要，以及 Braid SQLite 对象、assignee、assignment lifecycle 概况。Braid 状态是采样时点的共享现状；一次工具读取或写入不证明设计、计划和验收要求已被采用，须回到原始路径与人工基线核对。

在运行主机以只读方式启动：

```sh
python3 monitor-behavior.py --root /home/yyh/Development/factory26/runs/e20260928-03-check-receipts/hotfix-01/generation-02 --out /home/yyh/Development/factory26/runs/e20260928-03-check-receipts/behavior-monitor.jsonl
```

`--once` 只采一次。默认开始十分钟内每三分钟，此后每八分钟；有未读完的历史材料时立即继续下一批，两题都终态且材料已读完后采集最后一批并退出。每次每题最多约 160 条事件、每个原生文件最多读取 2 MB 完整新行。首批标 `sample_kind=backfill`，后续标 `incremental`；每条事件再按当前 continuation 的 `started_at` 标 `historical` 或 `current_attempt`。`<out>.cursor.json` 原子保存各文件字节偏移和行号、待匹配工具结果与已观察子会话模型；保留它可避免重复全读。采样文件和游标都只写在指定 `--out` 所在目录，不改变运行、Git ref 或 Braid 对象。

2026-09-29 已将脚本放到实验根目录并启动 PID `872164`，对 `hotfix-01/generation-02` 持续采样。输出为实验根目录的 `behavior-monitor.jsonl`，游标为 `behavior-monitor.jsonl.cursor.json`，进程日志为 `behavior-monitor.stdout.log`。首批回填 GitHub 和 Sheet 各 160 条；随后增量批次读完历史积压，两题 `backlog=false`。首次追平时 GitHub 索引 24 个 Braid 会话、20 个可读原生文件，Sheet 分别为 8 个和 7 个；多出的原生文件来自 Pi timing 索引。初版输出保留为 `behavior-monitor-pre-spawn-fix.jsonl`；当前输出已将 `agent` + `task` 和 `workflowScript` 两种原生调用格式均标为 spawn，历史记录中两条简写格式的 action/role 已依据原文件修正。脚本通过 Python 语法核对和真实运行只读采集，未运行测试或模拟探针。
