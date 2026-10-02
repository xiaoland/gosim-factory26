# 最新 GitHub / Sheet token review

> 已由[终态 token 复审](token-final-review.md)接续：09:20 是统计起点；终态修正了无头原生续写漏计、子代理与恢复副本口径。下文保留为历史截面。

审查截止：2026-09-28T12:15:09Z。最新实验身份为 `e20260928-02-deepseek-direct/attempt-09/continuation-03`：GH Braid run `pi-braid--hackathon--github-3d75045c72f1d6`（生成器对应归档目录 `pi-braid--hackathon--github-88884da4b94a0f`，monitor 已报 `ready/completed`）；Sheet run `pi-braid--hackathon--sheet-22730f82778f3a`（生成器目录 `pi-braid--hackathon--sheet-984a08e3155e3e`，monitor 截止时仍 `running`）。`execution.json` 的 `orchestration_status=stopped-before-local-scoring`，不能把它当成生成失败。

## 可重读的成本基线

原始证据在 WSL `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/` 下各自的 `workspace/official-generation/template/.factory26/**/work/home/.pi/pbb/sessions/**/instances/**/events.jsonl`。既有 `continuation03-token-profile.md` 的 GH 统计已按 `(file.name, record.id, timestamp)` 去除归档副本；`token-deep-03` 提供了更深的 session、Context 和工具分类证据。两份统计的 cutoff 不同，不能直接相加；下面采用同一 09:20 cutoff 的去重值作为跨题比较基线。

|题目 / model|有效 usage 请求|input（不含 cache）|output（含 reasoning）|cacheRead|cacheWrite|
|---|---:|---:|---:|---:|---:|
|GH / glm-5.3-flash|370|616,847|108,090|29,216,960|0|
|GH / deepseek-v4-flash|59|75,456|30,009|2,551,168|0|
|Sheet / deepseek-v4-flash|2,015|2,347,336|999,547|266,225,280|0|
|Sheet / glm-5.3-flash|614|1,603,360|183,004|55,024,192|0|

统计只在单条 message 自身含 `usage.input` 时计一次；GH 归档副本已去重。没有单价，因此不报费用。Sheet 仍在推进，数值是截面；不能把 session 数或 cacheRead 当成独立请求数。

## 根因和决策

1. **Context 注入修复已在当前 dirty 源码中实现，但尚未部署到本次冻结运行。** `sources/braid/src/provider/pi.rs:start_turn` 在 prompt 成功后 `state.context.clear()`，失败/Deferred 路径保留；`resume_session`/新 session 会清空并等待重新注入。`token-deep-03` 严格匹配到本次运行历史中 Sheet 69 份、GH 7 份重复前缀；Sheet Issue5 单会话有 14 次相同前缀，单次输入从 113,253 增至 141,017 token。约 67.1M 是基于这些重复证据的保守反事实情景估计，不是实测已节省量；本次运行仍使用修复前冻结制品，不能把它报告为已验证收益。

2. **批量化关闭成员通知，并在 Context revision 不变时复用原生 session。** `reactivate_work_item_agent` 会替换 sleeping/idle session；同一 revision 下 Sheet Issue6 三个代表样本各自只读后确认“无需动作”，合计 101,098 input、5,677 output、50,304 cache。先合并同一收件成员的通知，保留投递收据；只有身份、指令或 Context revision 变化才重建。该收益与 Context 去重重叠，不能相加；三样本仍需一次语义读取，不能宣称全部 token 可删。

3. **等待交给事件，不让模型循环 `sleep; grep/tail`。** `token-deep-03` 的保守候选为 Sheet 598 次（218,749 input / 125,436 output / 102,191,808 cache），GH 57 次（24,842 / 6,305 / 4,407,296）。这些是候选上限，不是确定浪费：保留首次检查、错误诊断和完成事件；同一后台作业已有完成通知时停止重复轮询。该项和前两项有重叠，不能叠加成总节省。

4. **压缩失败输出与全量状态输出。** 已见跨文件系统 `cp -al` 失败产生约 559KB 日志，以及为查 blocked 状态打印约 427KB `physical_sessions`。返回首个错误、设备边界和状态摘要即可，保留原始文件供取证；不要截断关键验收证据。

## 建议验收

先只实施第 1 项，在自然接续中核对同一原生 session 的第二个普通通知不再携带完整旧 Context，新 session 首次通知仍携带完整当前 Context；再评估第 2 项的批量投递和 session 复用。第 3、4 项随后按真实完成事件和失败证据验收。不要通过降低模型、删除必要验收或按 token 数推断质量收益。
