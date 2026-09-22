# 协作运行时 × 接入就绪

Track：runtime。Phase：ready。状态：active。01 独立预演完成，见 [runtime.md](../rehearsal/runtime.md)；实现由 braid_profiles_impl 持有 Braid 源码，主 Agent 集成。实施起点提交后进入 02。

本 Cell 使 Braid Agent 能按问题使用多个 work-item 和异步讨论，并在明确 profile 下启动、重建、重新指派和恢复。profiles 是能力选择，不是 multi-agent 协作本身；不增加 preset 概念、强制拆 Issue、角色链或父 Agent 让位规则。

## 出口与依据

必须交付普通 profile registry/CLI 指派到实际 provider 的完整消费链，且错误 ID、并发 claim、重指派与恢复不串配置。旧 writer 及其原生子树停止后才能启动新写者，保留 work-item、讨论、工作树和未提交内容。返回实际身份、版本和相应行为证据，不以字段存在或原先单 profile 的探针代替新能力。

设计归 [直接指派与恢复](../technical.md#braid-的直接指派与恢复)及 [原生装配](../technical.md#原生装配与子代理)，判据归 [verification.md](../verification.md)。已有 comment/thread、自编辑与同类并发基础见 [上一轮执行记录](../../multi-agent/execution.md)；其中真实 Codex 和多个同类 Agent 协作的证据仍不充分，不能在迁移任务包时被标成完成。

## 局部计划

1. **01：返回可实施的运行链与预演结论。** 沿 config/local/objects/store/group/provider 的真实消费者核对 profile、assignment generation、binding 与 native session 身份；用独立 Agent 预演重指派、reset、失联和 native children 收尾。明确修改 owner、原有检查入口和实际未知，不重复抄写设计。
2. **02：返回可运行的指派与生命周期。** 在实施前共同门槛通过后，接 registry/CLI/claim/默认值和 provider 唯一参数源，解除现有 PiConfig/模型双重权威；再沿已有 fencing/reset 恢复边界处理子树。扩展现有真实行为检查，保持一条可运行的集成路径。
3. **03：返回与装配、诊断的联合证据。** 消费 capabilities 的 02 返回的真实配置，不等待其完整 Cell 满足 ready；向 feedback 返回 Braid work-item/profile 与原生父子关系、重建/终态证据。与已计划的 Pi/Codex 场景合并核验，真实协作残余按证据回填，不自行扩大模型探针范围。

01 后若原生接口不能满足既定语义，计划停在该未知处并返回方案影响；普通实现分支本地修复。当前调查不算正式预演，也不授予跳过实现前提交的权限。

返回给 capabilities：普通 profiles/运行绑定合同与隔离会话入口。返回给 feedback：可关联的实际身份和生命周期证据。源码所有权主要为 sources/braid；共享 store 由一个 writer 整合，Factory 消费接缝由主 Agent 协调。

## 02 集成记录（2026-09-21）

普通 profile 注册、直接指派、按 profile claim、独立 native home 与身份归档已实现。独立集成沿实际路径发现并修正了：Pi teardown 被误作可执行文件、Codex cold resume 定位错误、父子停止失败被吞、create/edit 指派跨事务留下半写、重指派事件被提前消费，以及新 generation 未复用原有工作树。受控子进程检查证明 Codex adapter 可停止其拥有的进程组；真实核心另组 PG 的工具进程仍须联合场景验明。

当前 Braid 主体提交为 `e9b3471`，后续原生 Pi 身份与 profile 指派竞争修复提交为 `9770e65`；24 项单元检查与 1 项 CLI 集成通过。新增 Issue/PR 重指派检查证明旧 writer 失效、停止前 assignment 保持 pending、停止后使用原路径且保留未提交文件。resume 已新增对 profiles/defaults/bindings 的一致性校验。停止失败通过明确的 fatal 通道返回 incomplete，再收尾其他会话；独立 execute 集成检查覆盖了此前因活动 turn 不归零而永久等待的风险。Pi start/resume 直接采用 RPC `sessionId`，不再从尚未写 header 的 JSONL 反推 UUID；多个 profile 读取同一 pending event 后，事务竞争失败为预期 no-op。以上是代码边界证据，真实 Braid 多 profile 协作、活动原生子树收尾仍未满足 03。

真实联合验收的 Braid 阶段已准备为 `../scripts/braid-scene.py`，并由独立 Agent 对照原生接口预演。受控 child 写入后由宿主触发 description 重建，以真实停止收据、写入静止、writer 拒绝和同工作树复用作为证据，再完成两个不同 profile 的 Issue/PR 小交付。Pi 覆盖 foreground/background，Codex 覆盖原生线程。尚未执行该阶段，不能由脚本存在推定通过。

## 03 真实联合结果（2026-09-22）

Braid `0c68c75` 将 teardown 提升为完整后代进程树的终态边界：在 lifecycle hook 前锁定 Pi 后代，hook 只确认精确控制请求，Braid 关闭并验证树后写入 stopped receipt。受控 Pi 场景实际通过 foreground/background 两种 replacement，旧 writer 被 fenced、heartbeat 静止、原工作树和未提交文件保留；随后两个不同 profile 的子 Issue/PR 完成交付。归档器使用终态 `subagent-stop.json` 并按 Pi UUID 唯一定位规范 session 文件，对该真实场景保留输入重放得到 21 个原生会话、0 个证据错误。

Codex 场景 `20260922-103554-codex-braid-533f50` 完整通过：原生 executor 在 description replacement 后终止，两个子 Issue、两个 PR 和根 Issue 均收敛，delivery commit 为 `df831aad3a6e7a6fa196bbfa74b08de7b4d91bb4`。前一轮曾因子 Issue 只关闭自身、未向根 Issue comment 而正确停在 incomplete；共同 profile 指令现明确 comment/reply 是跨 work-item 唯一推进通道，关闭或等待前必须向父/消费者报告并确认成功。Braid 没有增加隐式完成事件。

固定批次暴露了 provider 失败合同缺口：Pi 在内部重试耗尽后返回明确 `Failed`，Braid 将 batch 消费并让仍开放的 Issue 静默进入“无后续工作”；重新启动批次又从空会话开始，无法利用仍存在的 work-item 状态。Braid `690522e` 在 store 调度边界对开放 work-item 的同一输入精确重放一次，第二次 `Failed` 后返回 incomplete；`Unknown` 的既有 at-least-once 路径不变。该边界不识别模型错误文案、不增加 provider 分支或可变重试配置。store 回归检查覆盖首次重放、第二次停止及相同正文的独立新输入；全部 Braid 测试通过。旧批次的五个评分继续保留旧 revision，未评分项使用明确的新 recovery run 和新 revision，不能伪装成单一冻结源码。
