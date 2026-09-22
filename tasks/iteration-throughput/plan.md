# 线性实施计划

状态：设计、验收、独立预演及 [implementation impact handshake](implementation-impact.md) 均已批准。当前进入实现；按依赖顺序集成，独立文件族可并行实施。

## 已由预演收敛的结论

- 一个 Factory task invocation 对应一个根 Issue。Requirement bundle 是根 Issue description 引用的冻结输入；单条 requirement 不自动成为 Issue。是否创建 sub-issue 由 Agent 根据任务决定。
- Agent 只看 GitHub 式 Issue、PR、comment、reply、reaction 和 assignee。公开 assignee login 映射到内部 agent-profile；Agent 不知道 Braid、profile、preset、model、session 或调度状态。
- 当前 Braid 已能让同一 assignee 的多个 work-item 并发运行。无需增加 worker pool、event orchestration 或新的并发抽象，只需用真实重叠场景守住现有行为。
- Pi RPC 已提供 detached child 的 `processTerminal` 与 canonical-session lease 证据。当前缺陷是 Factory extension 忽略该证据并错误返回 ready；不重写 RPC，也不让 Braid 扫描进程。
- `preset` 只转抄 profile/default，删除该层。Variant 直接选择内部 profiles、默认公开 assignee 和 SVC preload；Braid 不读取 variant。
- SVC Corpus 本轮不改正文。`pi-team-vv` 只额外装配冻结的 canonical `methods/design/test.md` 与 `verification/index.md`；基础 variants 只通过语义索引按需发现。
- Competition 与 local simulation 使用同一冻结 ZIP bytes。Hosted 写接口需要独立 adapter 和逐写 journal；不把 Playground、包内 runtime、本地 controller 混成一个状态机。

## 冻结的公开合同

- assignee login 采用 GitHub 式小写形式：配置不带 `@`，CLI 接受可选 `@` 并规范化；长度 1–39，字母数字或单个连字符，不能以连字符开头/结尾。不同 profile 的 login 必须唯一。
- assignee description 是单行 UTF-8 文本，最多 240 bytes，只描述可观察能力和限制。Issue/PR system instructions 提供完整成员目录；canonical object 只显示当前 assignee。
- `create --assignee LOGIN` 指定初始 owner。`edit --add-assignee LOGIN`、`--remove-assignee LOGIN` 遵循单 owner 合同；同一命令可原子替换，第二个 add、不匹配 remove、多个 add/remove 都在任何写入前失败。
- remove 当前 owner 会停止并进入明确 unassigned；重新 add 才恢复。新指派/重指派必须在旧 writer fence 和 native teardown 证明完成后，让目标 Agent 恰好产生一次新采样。终态证明 unknown 时保持 blocked。
- 旧活动 request 缺公开 assignee 投影时不从 model/profile 猜身份，也不跨版本 resume；旧 DB 保持可读和可归档，活动运行须重新初始化。
- 运行时隐藏 `profile list/view` 及内部 profile/model/provider/digest/generation/session 字段；宿主诊断保留内部视图。

## 实施顺序

### 0. 冻结设计基线

批准 handshake 后先提交本 task packet，仅包含 `tasks/iteration-throughput/`。不纳入现有无关修改 `tasks/competition-p0/packet.md`。Factory、Braid、SVC revision 和验证命令写入提交说明，作为实施起点。

### 1. 修复 Pi lifecycle 证明边界

先把 `/tmp/factory26-pi-proof-probe.mjs` 的 unknown-terminal 反例移入 `tests/pi_lifecycle.test.mjs`，保留 observed+free 正例。随后只改 `harness/extensions/factory-subagent-lifecycle.ts`：background receipt 必须证明 process identity、terminal observed、canonical session free、lease released/not-held；stop ack 只作诊断。

再改 `sources/braid/src/provider/factory.rs`，按 foreground/background 校验 receipt。Foreground 仍由定向 control 加 Braid 所拥有 parent process tree 的终态证明；background 不能用 parent 终态升级。最后更新归档证据消费和联合场景，不增加进程扫描器。

通过条件：extension 红灯先出现再转绿；Braid fixture 拒绝 unknown/missing/mismatched proof；原生 Pi、extension、Braid 三层可对照；失败后不进入 assignee 旅程。

### 2. 建立 GitHub 式 assignee 投影

在 Braid 增加 forward-only `0007_assignee_projection.sql`，直接扩展现有 profile record，不建第二张 assignment/projection 表。依次接通 config/request identity、Store 的 login 映射、canonical Issue/PR、Context/system instructions、CLI create/edit 和 assignment wake。

复用现有 `desired_profile_id`、assignment revision、writer fence、native teardown、worktree reuse 和 scheduler。删除 runtime item/JSON/context 中的内部 profile 字段。重指派顺序固定为：校验全部输入 → 在同一事务中记录目标 owner 并 fence 旧 writer → 在事务外取得 teardown proof → 创建/恢复目标 generation → 恰一次 Wake。

通过条件：旧 DB 可读；新 request fresh/resume 一致；未知 login 与非法 add/remove 零写入；Issue/PR 投影对称；A→B→C、重启、teardown unknown 均无竞争 writer；同一 assignee 的两个 work-item 真实重叠。

### 3. 收敛 variant、profile、native role 与 SVC 装配

删除活动 `preset.json` 消费路径；新增每个 variant 的直接声明和两份 Braid profiles。Profile 拥有 core/model/reasoning/instructions/skills/MCP/context 与 native role refs；role 自己拥有 model/reasoning/tools/skills/MCP/instructions/context；model catalog 拥有协议、输入模态、context 与 reasoning 映射。父 profile 不猜子角色配置，native role 也不继承未声明能力。

活动 variants 固定为：

| variant | 可用 assignee | Issue 默认 | PR 默认 | SVC preload |
| --- | --- | --- | --- | --- |
| `pi-team-deepseek` | `deepseek` | `deepseek` | `deepseek` | 无，仅索引 |
| `pi-team-glm` | `glm` | `glm` | `glm` | 无，仅索引 |
| `pi-team-mixed` | `glm`, `deepseek` | `glm` | `deepseek` | 无，仅索引 |
| `pi-team-vv` | `glm`, `deepseek` | `glm` | `deepseek` | canonical test design + verification |

共同 native roles：`explorer`/`executor` 用 `deepseek-v4-flash`；`browser-operator`/`vision` 用 `deepseek-v4-flash-vision-exp`；昂贵 `specialist` 用 `kimi-k3`。MCP 默认为空，skills 只有在实际 runtime consumer 存在时进入 digest。`harness/AGENTS.md` 改为简洁的 SVC 语义索引，说明主要内容、何时读取、task packet 的意义/模式和 V&V 入口，不提 Braid/profile/variant。

`scripts/profiles.py` 成为唯一 resolver；`native_profiles.py` 只物化 effective contract；`factory.py` 只消费；`package_agent.py` 写入完整 material manifest 和 hashes。旧 generalist/verification preset 从活动矩阵删除，历史 runs 不改写。

通过条件：四 variant 可静态解析；mixed 与 vv 除 SVC preload/hash 外完全一致；runtime instructions 不泄露内部概念；canonical SVC path/revision/hash 可复现；同一输入只因真实 consumer material 改变才改变 digest。

### 4. 固定同一 ZIP 的官方资格

先用无模型 fixture 检查根 `main.py`、`requirements.txt`、manifest、package hash、source/material revisions 和标准 `frontend/package.json`/`backend/package.json` 合同。继续使用 fixed local simulation `cfbbc287ee1bbffcf1e936545e4803145693a8d8`；`deploy.sh` 永远不作为 Competition 资格证据。

Docker daemon 与官方 image 可得后，先跑一个标准无模型 deploy，再跑一个真实模型单题。若 image/digest 不能固定，本地资格停在 prepare-only，不把它报告为 runner 通过。

### 5. 增加 Competition adapter 与混合 controller

新增独立 `scripts/competition.py`，复用 Playground 的 Cookie HTTP、redaction 和日志 cursor 基础；它拥有 Competition schema、snapshot/run/start、状态/日志/traceability/artifact 收集和原子 journal。所有 POST 禁止自动重试，成功 identity 先持久化；传输结果 unknown 时先只读核查，无法唯一恢复就 blocked。

`scripts/batch.py` 保留本地 generation/evaluation owner；需要 local simulation 时使用小型 `scripts/local_runner.py` adapter，直接调用 fixed upstream runner，不复制 Docker/评分逻辑。Hosted controller 默认串行，真实 schema/spike 证明 slot 后才提高；local 以独立 workspace/container 并行，Playwright worker 保持 1。

通过条件：fake transport 覆盖 snapshot/create/start 的逐写恢复、unknown POST、unknown status、cursor replay、重启与重复拒绝；同一 package/task 恰一身份；两个本地无模型 workspace 真正重叠且证据隔离。

### 6. 资格、冻结与实验

先完成一次最小模型接口资格：DeepSeek/GLM 文本 tool call 和 reasoning wire shape，DeepSeek Vision 的图片与 browser screenshot。当前比赛 key 对三次最小调用都返回 429 `insufficient_quota`，因此此 gate 尚未通过；不以静态 catalog 或旧 GLM 声明替代。

随后执行一个 root Issue、可选 child Issue、一个 PR 的真实协作旅程，确认 assignee、comment/reply、packet、ready/merge/finalization 与生命周期合同。再用同一冻结 ZIP 完成一个 Competition smoke。任何设施修复导致 source/material 变化都使资格过期，重新资格后才 score。

最终冻结四个 ZIP，执行 `4 variants × 2 ARC-Bench-Lite tasks`。本地先并行提供快速反馈；Competition 按平台 slot 顺序取得全部八个 hosted task 结果。每项记录 venue、package hash、score/pass、cost attribution、generation/evaluation/queue time 和设施失败。低分是有效实验结果，不触发同轮重采样；八项完整后汇总并停止。

## 不实施的内容

- 不重写 SVC Corpus，不增加新的 reviewer/contract-reviewer，不实现 preset 兼容层。
- 不重写 Braid scheduler，不引入事件语义层、共享 packet 同步服务或多 owner assignment 表。
- 不让 runtime Agent 接触内部 profile/variant/model 状态，不用 labels 选择 Agent。
- 不把 Playground practice、Competition hosted、local simulation 和包内 runtime 合成 God controller。

## 开工后的停止条件

只有以下情况中止并请求 Human 注意：外部额度/服务使必要资格无法继续；官方合同与只读/单次 spike 证据冲突并改变产品前提；同一 work-item 无法维持单 writer；或所需行为必须让 Agent 理解内部 Braid/profile。普通实现缺陷在授权范围内继续修复和复验。
