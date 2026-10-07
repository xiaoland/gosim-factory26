# 首轮 SVC / braid Harness 比较

本轮以相同比赛视觉模型、需求与官方 Keep 32 项评测比较四种组合。四组已完成 Keep 全部 32 项评测；Pi + SVC + braid 本次最高，为 14/32（43.75%）。这是一轮单任务探索性结果，尚不足以决定最终提交。只依据需求独立生成，没有外部评测反馈修复。

本报告保留旧适配器的历史结果。当前 braid 本地模式已改变工作记忆归属与会话组合边界；这些分数不代表当前实现，运行方式以 Deployment 为准。

## 条件

模型为 deepseek-v4-flash-vision-exp，网关为 https://api.arc-bench.com/v1，thinking/effort 为 high。Pi 0.85.1 和 Codex app-server 0.155.0 使用独立临时 HOME 与原生 user-scope AGENTS.md；SVC Corpus 固定 4fe4c66ac4deb35209069c00b1bbdc1b22aae3af。核心默认上下文行为没有强行统一，未设置额外生成 token 或总时限。

Codex 使用 LiteLLM 1.102.0 的 Responses → Chat Completions 适配。网关直接 Responses 请求返回 422、要求 messages；开启 use_chat_completions_api 后，再用原生 Codex reasoning 配置避免发送网关不支持的 summary 结构。适配器的实际图片读取、工具往返和正常终态已观察到；它是实验条件，不代表网关原生支持 Responses。[LiteLLM 文档](https://docs.litellm.ai/docs/response_api)

braid 基于 08c1c10d3b61b24119580ba8af14e2a393f7ea33，应用 [归档的本地入口补丁](../20260920-141339-6138c072/patches-source/braid/entry.patch) 和 [归档的 requirement 入口](../20260920-141339-6138c072/patches-source/braid/requirement.rs)，复用上游 provider/session。设计与实现会话串行，通过可编辑任务包和 action.json 交接。新会话重新读取当前任务包；不继承旧聊天历史。没有 GitHub、人类唤醒或动态并发子 Agent。

官方 ARC-bench 固定 1eb018367bedd618d3b9ced406ce07fb423d4956，未修改评测器。生成在本机 macOS，冻结后在 wsl.win-ws.localhost 的 Linux / Node 22.22.3 环境评测；单套评测仍是 worker=1、retries=0、test timeout=60s、expect timeout=10s。四组生成交错并行，所以 wall time 包含共享网关和机器竞争，不能视为独占性能基准。WSL 的 runner、node_modules 和 Chromium 跨运行复用。

## 接入证据

Pi 和 Codex 单会话分别观察到 user AGENTS 标记、真实图片工具、Corpus 查询、文件写入与读回。Pi + braid 观察到三个不同原生会话正常结束，第三个会话加载修改后的设计。Codex + braid 的文件烟测观察到两个不同会话正常结束及当前任务包重建，但外层清理 EPERM，不能视为完整执行器通过；第一次应用烟测卡在模型自写测试中，已中断保留，不算基准成绩。随后修正工作区独立子进程清理，回归检查覆盖该路径。

braid Pi provider 另修正了上游提前把 message_end 当终态的问题：现在等 agent_settled，允许原生错误重试/压缩完成，并拒绝最终 length。用量统计包含 Pi 压缩与分支摘要，缺失部分标为未知；Codex 归档只选择真实 sessions，排除插件夹具。

## 正式运行

| 组合 | 运行 | 状态 | Keep |
| --- | --- | --- | --- |
| Pi + SVC | [20260920-141147-e04e9b16](../20260920-141147-e04e9b16/run.json) | 完成 | [7/32（21.875%）](../20260920-141147-e04e9b16/evaluation/20260920-142310-7dc5c0/summary.json) |
| Codex + SVC | [20260920-141148-8e0331ca](../20260920-141148-8e0331ca/run.json) | 完成 | [9/32（28.125%）](../20260920-141148-8e0331ca/evaluation/20260920-151521-069546/summary.json) |
| Pi + SVC + braid | [20260920-141339-6138c072](../20260920-141339-6138c072/run.json) | 恢复后完成 | [14/32（43.75%）](../20260920-141339-6138c072/evaluation/20260920-143117-15f133/summary.json) |
| Codex + SVC + braid | [20260920-141340-5b605666](../20260920-141340-5b605666/run.json) | 完成 | [8/32（25%）](../20260920-141340-5b605666/evaluation/20260920-151759-f063a9/summary.json) |

每个 run 保存配置、Harness/Corpus 哈希、运行器源码、应用和需求快照、全部原生会话，以及每次评测的 JSON/HTML/trace。分析为每个原生会话分别生成 svc evidence-v4、overview 和 profile。四份评测均为 completed，无全局错误、跳过或重试；共 128 项已执行。单次 Keep 结果不能表述为完整 ARC-bench 或线上提交成绩。

Pi + SVC + braid 的两个阶段完成后，运行器 killpg 收尾返回 EPERM。原失败记录保存为 run-before-recovery.json，恢复记录为 recovery.json；核验两个原生会话最终 stop、阶段 completed、最终 action=complete、应用哈希未变及无剩余工作区进程后恢复送评。原进程退出码未被保存，仍记为未知；没有重新生成或修改应用。此记录不能算作无故障端到端完成。

并行生成仍共享主机网络和 /tmp，属于探索性比较。已观察到两个 Codex 写入同名 keep-server.log，但完整会话中未读取它；Pi 两组 h.json 的写入和读取不重叠，返回匹配各自服务。Codex + braid 使用宽泛 pkill 匹配 server/index.js，其他三组启动 server.js，未见跨组命中。最终还核对了同名 final.log，读写时段不重叠、读回匹配自身服务。四组归档会话中未发现实质交叉反馈或跨组终止迹象，故保留本轮结果；没有宿主机完整进程审计，不能宣称绝对无干扰或强隔离。

## 生成用量与耗时

| 组合 | 原生会话 | 生成耗时 | 总 token（含缓存） | 缓存读取 token | 输出 token |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pi + SVC | 1 | 702.3 秒 | 4,255,865 | 4,105,216 | 116,038 |
| Codex + SVC | 1 | 3,831.5 秒 | 9,994,049 | 9,593,344 | 297,039 |
| Pi + SVC + braid | 2 | 648.5 秒 | 3,332,839 | 3,165,056 | 108,141 |
| Codex + SVC + braid | 2 | 3,877.5 秒 | 11,800,327 | 11,385,856 | 248,635 |

统计来自各 run.json 的原生 usage；Codex 的 input_tokens 包含缓存读取，Pi 则分列 input/cacheRead，因此表中统一使用原生 total。两种客户端及协议适配的计量语义可能不同，不将该表当作账单。实际费用未知。braid 两组本轮均使用一个设计会话和一个实现会话；可编辑上下文的再次刷新能力在烟测中验证，本轮正式生成没有请求第三个会话。

两组 Codex 在首次冻结前持续运行、修订自写检查，生成耗时超过一小时；没有追加外部评测反馈。原始 Pi 的历史 6/32 来自另一轮 macOS 评测，与本轮 WSL 环境和并发条件不同，只作背景参考，不能从单次差异推出稳定的 SVC 或 braid 收益。

## 已确认的评测差异

两组 Pi 的 REQ-2.2 创建笔记均在定位 `getByRole('dialog', { name: /^Note editor$/i })` 内的 Title 输入框时超时。官方 helpers.ts 要求该精确对话框名称；Pi + braid 生成代码将创建对话框命名为 Create note、编辑对话框命名为笔记标题。其需求派生自检使用生成实现自己的定位方式，未覆盖这一差异。

在给定 requirements 文本资源中搜索未检出 Note editor 这一精确名称。因此不能把此处的定位失败直接等同于创建功能不存在，也不能据此把全部失败都归因于评测器。原始测试报告保留调用栈和 trace；本轮没有修改应用或评测器。若后续用这类外部信息修复，须另建 oracle/dev-only run。

## 收尾验证

四个冻结应用的哈希与送评前记录一致；四份 JSON/HTML 评测报告和六份 svc evidence-v4 已下载。Codex 三个原生会话的 analysis coverage 完整；Pi 三个会话的内容、工具关联、用量等覆盖完整，唯原生格式缺失执行终态，需结合运行器与 braid 终态记录。全部会话记录的模型均为 deepseek-v4-flash-vision-exp。

运行器 7 项 Python 检查通过；WSL 同组检查通过，macOS 隔离检查按平台跳过。braid Pi 终态回归及 Rust clippy 通过，评测器保持固定且干净。SVC 项目文档状态 healthy。没有 Git 提交或线上提交。

本轮 Pi + SVC + braid 的分数和反馈时间最好，适合作为下一轮候选；仍需更多独立生成和任务验证。Codex 两组自检耗时较长但未带来本轮最高分，下一轮应优先研究需求到可观察验证的覆盖和停止条件，而非仅增加自检数量。本报告的评测差异属于事后诊断，未回灌到本轮生成。
