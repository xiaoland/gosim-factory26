# Factory / SVC / 诊断集成预演

这是 2026-09-20 的静态预演，依据 packet、design、verification、plan 和当前源码；没有构建、启动 native、调用模型或运行评测。当前 `sources/braid/src/local.rs:192` 仍是旧双正文/action 循环，不能作为已确认 Issue/PR 方案的完成证据。以下字段是待双方确认的最小语义，不指定新数据库或文件布局。

## 跨组件必须对齐的身份

| 字段集合 | 生产者 → 消费者 | 不可混淆的含义 |
| --- | --- | --- |
| `run_id`、输入哈希、组件源码/实际制品哈希 | Factory → Braid 启动、归档、评测、诊断 | 区分实验条件；源码归档已有 `scripts/sources.py:69` 的构建校验，运行制品仍须对应该记录。 |
| 工作项 kind/id/revision、`group_id`、上下文 revision、provider/session/turn ID、worktree 身份 | Braid → Factory 会话清单 → SVC/诊断 | group/worktree 可持续，物理 session 可替换；失效 turn 不能被展示为当前执行。每条关联须来自创建/投影记录。 |
| 根 Issue、关联 PR、收敛状态/原因、交付 ref/commit、交付目录 | Braid → Factory 冻结 | Braid 指定哪个已收敛交付树；Factory 校验路径归属并计算冻结内容哈希，不能按最后一个 session 或当前 cwd 选择。 |
| `evaluation_id`、冻结应用哈希、benchmark revision | Factory ↔ WSL runner → case 查询 | 一次执行只归属一个预先确定的评测 ID；不能以目录排序或最新成绩代替请求身份。 |
| 证据 ID/相对路径/内容哈希、生产者版本、源 session/应用身份 | Factory 归档、SVC exporter、官方 runner/SDK → 诊断 | 原始证据、analysis 派生证据和 Agent 显式关联分别保留来源；仅有路径相似或 REQ 文本相同不能构成因果。 |

## 五个需要先消除的接点

1. **启动契约与新产品行为冲突。** `scripts/factory.py:289` 只建空目录，`:296` 禁止 Git 提交；现有 `sources/braid/src/worktree.rs:46` 却要求 Git checkout、GitHub remote 并 fetch。必须明确本地仓库初始化/基线提交由谁完成、工作树都位于本次隔离目录。另有 CLI 差异：Pi 在 `provider/pi.rs:89` 补当前 Braid 目录到 PATH，Codex `provider/codex.rs:33` 只设 CODEX_HOME；Factory `:184` 未统一提供复制后二进制及本地配置入口，Codex 可能找不到或命中宿主版本。

2. **完成与冻结没有交付树契约。** `scripts/factory.py:320` 当前以旧 `braid local` 进程零退出继续，`:348` 写 generated，`:356` 永远复制最初 app。新 PR worktree 即使已完成，可能冻结空树/旧树。须等待 Braid 给出已收敛的交付 ref/commit，并在相关写入停止后冻结；`.git/.braid` 被排除的同时，应独立归档本地对象权威快照及会话清单，不能只保留旧 `braid-state` 阶段目录。

3. **物理会话替换会丢证据或误判失败。** Pi 把 session 写到每个 workspace 的 `.braid/pi-sessions`（`sources/braid/src/provider/pi.rs:64`），Factory `:323,359` 只收最初 app；`pi_usage(:129)` 又要求每份会话末尾为 stop，会把合理失效/中断的旧会话当整次生成失败。Braid 应提供全部物理 session 及终态/失效原因，Factory 按清单收集并分开计量与收敛判断；`inspect_runs.py:133` 的阶段目录映射仅用于历史兼容。

4. **评测与 analysis 仍有“最新/序号”歧义。** `scripts/factory.py:538,558` 从本次前后目录差集选最后评测，重入或同 run 并发可认错执行；`:587,594` 的 analysis 缓存键不含 native 内容哈希，已有目录直接复用。`:608` 虽保存 source_sha256，`inspect_runs.py:131,153` 只按文件名和 mtime 选择。应让请求携带评测 ID，并以 native 哈希和 exporter 来源验证派生证据；保留未建立/不一致关联，不悄悄回退。

5. **诊断已收集数据，但缺少定向消费与观测边界。** `scripts/playground.py:124` 从 steps 文本取进展；`:145` 保存有 heartbeat、timestamp、artifact_reference 的 runner_events，却未投影这些字段，`:164` 固定收全部 traceability。历史 `runs/playground/2041e4b58701/traceability.json:2` 为空，不能展示为已追溯实现。SDK 不需要进入 Braid 或 SVC，消费接口归 Factory；平台轮询时间与源事件时间必须分开记录。

## 官方证据的最小消费接口

以下是三个只读查询语义，可复用现有 show/status/collect，不要求另造命令体系。

| 查询输入 | 最小返回 | 直接证据与边界 |
| --- | --- | --- |
| run + 明确 evaluation + case | 失败层、错误与定位器、相关页面快照片段、附件入口、来源应用哈希 | `scripts/inspect_runs.py:176` 已解析报告；官方 `third_party/arc-bench/playwright.config.ts:22` 保留失败 trace/截图/视频。优先读 error-context，再按需要打开 trace，不默认输出整个 DOM。 |
| run + event cursor | 最近非心跳事件、最近心跳、源 timestamp、本地 observed_at、终态、产物引用 | 使用官方 runner_events 的 heartbeat 标记及事件 ID去重；时钟未校准时不跨主机相减。无有效进展、通信正常与观测过期分别表达，不由 0/N 或心跳推断生成/评测已前进。 |
| run + requirement ID | 显式接口/测试关联、文件/行号/commit、生产者与版本；无记录则 unavailable | 用 `/traceability?node_id=…`，有明确记录才接 source/commit-history；只在解释生成过程时接 Braid session 清单 → SVC match/trace。SDK 自报 passed 不能替代外部评测。 |

SDK 精确依据为已有 `runs/development-loop-research/starter.zip` 内 `arcbench-agent-runtime/src/arcbench_agent_runtime/events.py:22,75` 与 `traceability.py:85,98`；它已提供事件和显式接口/测试字段，消费者无需另建关联图。平台不提供的 observed_at、归档哈希由 Factory 在采集边界补充。

REQ-2.2 的最短静态链已可成立：指定评测 → error-context 的 locator 与 `Create note`/`Title` 快照 → 冻结 `public/app.js:763` → 官方 `keep/tests/helpers.ts:233` 和输入 `requirements.md:36`。结论是父 dialog 名称不匹配；输入并未规定 `Note editor`，仍需区分评测契约和实现责任。无需把模型 score 或 REQ 文本映射成生成因果。

## 可先做与必须等待

- **可独立实施：** 历史 case 的页面片段定向读取；官方事件游标/观测时间/心跳投影；显式 traceability 的空值与来源表达；SVC 缓存内容校验；WSL 评测请求 ID。都可用现有真实产物重放验证，不依赖新的 Braid 对象存储。
- **可先准备检查：** 两核心在隔离 HOME 中能调用同一 Braid 二进制和本地配置、svc 开关不改变 Braid CLI 可用性、实际源码与执行制品一致。`sources.py:69` 已有基础，不另造构建系统。
- **必须等待：** 本地根 Issue 初始化接口、对象/上下文/物理会话清单、无人值守收敛与合并、最终交付树及权威快照出口。确认后再接 Factory freeze/usage/archive/show；不能暂用递归 glob、最后会话或旧 action complete 充当接口。

## 对 verification 的修订建议

1. `verification.md:7` 四组均开启 SVC，不能证明 `:21` 的纯核心及 SVC-off Braid 独立性。首批真实 bench 结论应限定这四组；若宣布完整独立组合已验收，需给缺失组合补真实 native/Keep 证据，不能只靠确定性 provider。
2. 为 `:11,27` 增加交付树判据：真实 Braid run 经过本地 Issue/PR CLI 与实际交付分支收敛；冻结目录内容哈希等于所选交付树导出，WSL 实际评测副本、回传报告、应用快照保持相同身份。保留“不要求零失败”，明确 32 项终态齐全，跳过/缺失不能冒充已验证。
3. 为 `:23,26,35` 增加替换会话判据：至少一个真实核心的受控场景观察旧/新 session、同 group/worktree、实际新输入与旧 turn 拒绝；若自然 bench 未触发，应标未覆盖并另做受控真实核心验证，不能让静态记录或假 provider 代替。计量包含已消耗的失效会话，终态判断以工作项收敛为准。
4. 为 `:31,33` 明确可盲验输出：三次定向查询内说清失败层、预期/实际、支持假说的代码、竞争解释和下一检查；事件重放可区分心跳、有效进展、观测过期及终态，并能回到准确产物。不得以输出行数或日志条数作为通过条件。
5. 为 `:35` 增加负例：另一评测尝试、错误 native 哈希、缺失 traceability、陈旧组件制品必须显式拒绝关联或标未知；新 run 的一条查询链应贯通自身源码/交付树/评测及正确 session，旧成绩不得充作新版本证据。

以上均为静态预演发现与建议，没有将任何新 Braid 行为或新 bench 标记为通过。
