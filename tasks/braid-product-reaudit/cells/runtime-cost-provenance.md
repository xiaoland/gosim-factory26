# 耗时证据与工具归属复核

2026-09-28，用户质疑调查是否混入 Codex 开发过程；本次直接复读 WSL 原始 Pi JSONL、Braid SQLite 和实际 helper 源码。

## 统计对象

本报告的两次清理、17.2/19.0 分钟检查均来自本地 Sheet 比赛生成运行中的 Braid/Pi Agent，不是 Codex 开发 Factory 的操作，也不是实验控制器执行。
完整 WSL 来源前缀 `S` 沿用 [耗时报告](runtime-cost-followup.md)。

|行为|直接来源|角色与归因|
|---|---|---|
|09:33 `pkill -f dist/server.js`|`S/work/native-homes/pi-glm-fast-01a0e751-0825-7df3-b100-b41d5619f714/2026-09-28T09-20-45-676Z_01a0e751-146c-7111-8394-c1592615f521.jsonl:100`|文件首行 cwd 为容器内 `braid-state/worktrees/issue-4/pi-glm-fast-g1`；message.role=assistant、model=glm-5.3-flash，bash toolCall 包含清理命令。不是开发侧exec。|
|09:42 全局pkill|`S/work/native-homes/pi-deepseek-fast-01a0e75f-95dc-7f00-a80e-035d33f4e0c7/2026-09-28T09-36-39-049Z_01a0e75f-a089-7593-a867-60e4c60e8c7c.jsonl:113–117`|首行 cwd=pr-8工作树；DeepSeek bash调用。114为PBB已停止回执及其它lane PID；115模型发现误杀；117新PID显示watchdog重启。行为已证，逐个退出信号仍无内核审计。|
|同tree补退出码17.2分钟|`S/braid-state/braid.sqlite3:local_comments` #328、#330、#346，work_item=pr:23|生成Agent先报告18.7分钟已过，再为退出码重跑；根在330将回执列为合并条件；346报告49 passed/17.2m、RUN_SH_EXIT=0。这是运行内检查时长，不是开发侧诊断用时。|
|合并后19.0分钟|同表#354，work_item=issue:7|生成Agent在db23b1f上回贴47 passed/1 skipped/EXIT=0（19.0m）。与其它检查并行，不可累加为净墙钟损失。tree等价也不独立证明运行前提完全相同。|

## with-service 是什么

实际文件是父仓库未提交的 `harness/skills/agent-browser/scripts/with-service.py`，不是SVC CLI、Braid命令或agent-browser上游工具。
它是本项目开发Agent在之前“工具放入Skill”的授权下新增的可选辅助脚本；历史记录见 [工具实施记录](../../experiment-infrastructure/cells/live-observability-followup.md)、[技能清单](skill-inventory.md) 和 packet 的 attempt-07记录。
没有Git提交历史可据以精确归属某个开发子Agent，不能凭空指定作者。
WSL本次冻结code同路径确实存在（5119 bytes）；“已放入包”不等于生成Agent调用过，当前没有其参与上述慢检查的证据。

直接读源码确认：`Popen(...start_new_session=True)`分别启动服务与调用方检查；`stop`仅对持有的process.pid调用killpg；等HTTP成功后执行检查；finally保留service.log/check.log/result.json，其中check_exit来自真实进程returncode，status可区分服务错误与检查失败。
它只包装一个遵守前台和端口约定的服务；不是当前六服务run.sh的直接替代，不负责产品判据或数据准备。

历史记录中的Sheet临时副本HTTP200、exit0是**开发侧对该工具的隔离验证**，不能计入比赛Agent耗时或采用率。
本轮方案仅保留进程归属和首次结果回执的通用方法，不强制将已有多服务检查迁移到此脚本。
新增SVC CLI/dev接入已另行获授权，由独立6-Sol核实实际接口和最小接线；不能预先声称SVC dev具有所有上述能力。
