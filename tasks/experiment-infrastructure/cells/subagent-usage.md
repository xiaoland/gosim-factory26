# 原生子代理使用：DeepSeek 恢复窗与 Flash 对照

只读截面至 2026-09-28 05:17 UTC；后续恢复窗和跨实验去重见[完整使用视图](../../factory-subagents/cells/usage-map.md)。DeepSeek attempt-06 两题路径为 WSL `runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/`；Flash 对照为 `runs/e20260928-01-flash-team/attempt-02/generation/runs/`。先用 `braid-state/braid.sqlite3` 辨认 Braid 成员/Issue，再以 `work/native-homes/**.jsonl` 的 `subagent` 工具调用和 `.factory/session-tree.json` 辨认 Pi 子代理。这里的 `subagent_wait({id:"bg001"})` **是模型误用 Pi 子代理等待工具来等待 PBB 的 bash 后台作业**；`custom_message source=pi-background-bash` 佐证该 `bg*` 作业属于 PBB，`subagent_wait` 不是 PBB 工具，也不代表曾启动原生子代理。未读取凭据、改源码或启动任务。

## 结论与可改动作

**新恢复窗两题没有发现原生 Pi 子代理 spawn；这是委派使用的空白，不是 Braid 成员数为零。** GitHub 从根/基础 GLM 两成员恢复，05:07 起 Braid #3 DeepSeek、#4 GLM、#5 DeepSeek 被分配并实际发起 Pi 请求；Sheet 既有七个 Braid 工作成员继续编写、检查、评审，另有 PR 成员。它们是 Braid 协作身份，不是同一父会话启动的 Pi 子代理。两题根/成员主会话直接做了需求阅读、设计交接、代码编写、API/Playwright 检查及合并。是否值得委派要看具体可分离任务，不能从子代理数为零直接推出效率损失。

**实际可核实的历史正例是 DeepSeek Sheet #5 的一次视觉委派，收益边界窄。** 03:06:04 的 `subagent` workflow 给 fresh `vision` 子角色三张明确图片（`copy-paste-range.png`、`worksheet-overview.png`、`basic-formulas.png`），限定只读图，要求可见英文标签、工具栏/公式栏、网格/选区及不可见细节不得猜；角色定义使用 `factory26-visual/deepseek-v4-flash-vision-exp`、`read` 工具。03:07:47 `status` 显示 vision completed/exit 0、带来源报告；03:07:49 父会话 `read` 该报告，并把中文图示与英文 accessible names 的取舍纳入判断。前述消费细节已由 [视觉证据专项](../../braid-product-reaudit/vision-requirements-evidence.md) 核实，此处不重新判图。#5 的方案评论约 03:06:36 已先于视觉返回，不能说视觉帮助了该方案的初始拆分；目前也没有隔离证据证明它提高实现/验收质量。新 attempt-06 接续后的同一 #5 主会话直接完成编辑域、接口、Playwright 检查等工作，没有新的 `vision` / `explorer` / `advisor` / `executor` / `browser-operator` spawn。

**最清楚的反例是 Flash Sheet 把协作成员名误作工具角色名，并重复分配共享基础。** Qwen 所属 Braid #3 在 03:04:34 的 Pi `subagent` workflow 指定 `agent:"qwen"` 承担整套后端与种子，立即得到 `Unknown agent: qwen`，没有子会话/输出；其主会话后续自己实现并提 OPEN PR #1，故失败不是 #3 完全停工。Flash 根 GLM 于 03:09:38 把已分配给 Braid `minimax-2` 的 Issue #2 再委 `agent:"minimax"`，立即 `Unknown agent: minimax`；03:09:56 `list` 已显示可用的只是 `advisor/explorer/executor/browser-operator/vision` 五个角色，遂 03:10:22 改用 `executor`。该 executor 按既有角色配置实际是 `deepseek-v4-flash`、fresh context，任务包给了 Issue #2、需求路径、工作树/分支指令、完整前后端骨架/种子/ARIA 范围；输入足够具体，但写入根 Issue #1 工作树，和 Braid `minimax-2` 对 #2 的持有重叠。03:16、03:23、03:31 三次状态仍为 running；Flash 被取消前没有这条子代理完成回执、可审阅 PR 或合并，不能把其在途代码计为交付。不能把 executor 使用 DeepSeek 说成配方缺陷：Flash 当时的原生角色模型本来就是该配置。真正应修的是“`subagent.agent` 从角色目录选角色，`braid assignee` 是协作成员，二者名字不可互换”，并要求已有 Braid 工作项先有明确唯一产物归属，需额外 executor 时限定不重叠的文件/结果。

## 直接承担与合适的委派边界

| 现场实例 | 父任务与实际方式 | 可委派切口及边界 | 已见结果 |
| --- | --- | --- | --- |
| DeepSeek GitHub #2 → #3/#4/#5 | 根 GLM 先核对 `glm-2` 两次“delivered”无 commit/远端分支/PR，再接管验证、合并共享基础并发后续开工通知。 | 合并裁决和唯一归属留根成员；若要独立复核，可给 `explorer` 一个只读“origin 是否有提交/PR、与声明差异”问题。此次根会话自己几条 Git 检查即确认，额外委派不一定划算。 | 05:06 PR #1 合入 develop；非子代理产出。 |
| DeepSeek GitHub #3 身份需求 | DeepSeek 成员主会话直接读取长需求、检查代码和 `agent-browser` 技能/CLI，并编写方案；未见 `browser-operator` spawn。 | 待有可运行 UI 和明确旅程时，可把一条复现交 fresh `browser-operator`（URL、初始账号/数据、原需求判据、只读反馈）；最终仍要主会话落实可重复脚本。当前只是查工具入口，不构成漏掉的浏览器验收。 | 05:07 后请求开始，截面尚无该功能交付。 |
| DeepSeek Sheet #2 / #4 | #2 共享基础被 DeepSeek Braid 成员交付；#4 GLM 在主会话跑浏览器脚本，合并后找到 Shift+click 选区实现缺陷并提跟进 PR。 | 探索式页面复现适合 `browser-operator`；#4 此次已有可重复 Playwright 检查并直接复现，不应为了子代理利用率重复操作。重要的共享 API/状态取舍才是 `advisor` 候选，须给争议点与区分证据。 | PR #2 已合并，跟进 PR #3 当时 OPEN；缺陷被真实检查发现。 |
| DeepSeek Sheet #5 旧窗视觉 | DeepSeek Braid 成员把三张需求图作为单个、有界视觉问题交 `vision`，父会话读取结果。 | 这才是参考图的职责边界；模型主会话自行读图不能替代子角色分工。后续若需要页面交互则换 `browser-operator`，不能让 `vision` 猜未展示的行为。 | 只证明视觉事实进入后续判断，未证明初始方案和产品质量收益。 |
| Flash Sheet 根 #2 | Braid `minimax-2` 已有共享基础职责，根又尝试 Pi `minimax`，失败后改 Pi `executor` 在根工作树做同一大任务。 | 有效委派须是角色名、fresh 输入、单一代码所有者及具体返回产物；这次失败不支持“把 Braid 成员全部改成 Pi 子代理”。 | `Unknown agent: minimax`；executor 运行约 20 分钟仍无可消费结束结果。 |

角色配置的实际能力：`advisor` 是 fresh `kimi-k3`、只读独立判断；`explorer` 是 fresh `deepseek-v4-flash`、只读事实调查；`executor` 是 fresh `deepseek-v4-flash`、可写局部实现；`browser-operator` 与 `vision` 是 fresh 视觉 DeepSeek，前者可操作浏览器、后者只读图。配置存在不表示角色实际被调用。Flash GitHub 在停止前未见 Pi `subagent` spawn，且无最终 PR/合并；两事实不能推出其停滞是“少用子代理”造成的。

## 证据与不确定性

- DeepSeek：attempt-06 两题各 `.factory26/<run-id>/work/native-homes/` 的主会话 JSONL 与 `.factory/session-tree.json`；Sheet 旧窗 #5 的 `subagent-artifacts/9af6153d-e030-4eca-8237-ca26493a4e1e_vision_0_transcript.jsonl`、父会话 03:06:04/03:07:47–49 记录。Pi 根会话轮换与归档文件可能让仅靠 `work/native-homes/*/*.jsonl` 漏旧活动，所以上述旧窗正例另查递归会话、`native/` 与 session tree；新窗判断限定实际读取的 attempt-06 现场。
- Flash：attempt-02 Sheet 原生根 GLM 和 Qwen #3 JSONL 中的 `subagent` 调用/错误/状态、`braid-state/braid.sqlite3` 的 #2/#3 归属；Flash GitHub 同路径的主会话工具记录。旧 Flash 已按用户要求取消，不能用本次运行的后续结果反推 Flash 子代理完成。
- 本报告评估的是角色边界、任务包和父会话消费。未以调用次数/token 数推算 ROI；对未结束/未留回执的运行保留“结果未知”，对读入视觉报告保留“进入判断、收益未证实”。
