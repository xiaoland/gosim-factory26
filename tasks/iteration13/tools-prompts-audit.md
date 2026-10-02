# I13：工具接线与提示词审计

2026-10-01。用户已复核本页并明确同意工具接线与提示词实施，后续进展归对应实施记录。本页保留授权前的审计快照：当时工具源码未开工，提示词线已开始修改；下述“已改/拟改/未核”表示该次审计状态，不是持续镜像的实施状态。凭据当时由用户准备，随后确认实际已填文件为 `.env.i13-tools`；角色加载分配已随本页复核接受。

## 实际输入路径

主成员的两份 profile 均由 `variants/pi-braid-i13/run.py::native_files` 读取。起点实现把 profile 正文、`RUN_CONDITIONS` 和 `BACKGROUND_COMPLETION_RULE` 连在一起；Braid `src/group/provider.rs` 再将 Issue/PR 角色、通用协作指引和这份用户指引组合，由 Pi adapter 通过 append-system 输入。Pi 基础 system、工具 description、扩展的 `promptSnippet`/`promptGuidelines` 也进入同一模型输入，因此只比较 Braid 和 profile 会漏掉工具层的重复。

child 的共用前台/后台入口将角色 body 与技能发现信息写入独立 system，采用 fresh、append、关闭父项目指引和技能自动发现。父层 list 返回的角色 description 与 child 实际收到的 body 属于不同消费者，不能仅因内容相似就删掉一方。当前已查路径没有重新内联技能正文或父 profile。

审计起点保存在 `runs/iteration13/prompt-dedup-20260930/`：Factory HEAD 为 `93202ea`，Braid HEAD 为 `0712a58`，两边均有此前工作区修改。必须相对保存的起点快照归属本批改动，不能把当前相对 HEAD 的全部 diff 记为本批成果。

## 已证重复与归属

| 消费者与重复来源 | 审计结论及保留位置 | 本轮状态 |
| --- | --- | --- |
| 主 Issue/PR：profile 首两段与 Braid `local_instructions`、Issue/PR role | CLI、成员指派身份、回复通知、设计/实施角色边界有重复。通用产品语义归 Braid；profile 保留 develop→main、advisor/vision 及本配方整合政策。 | 两 profile 已改；Braid 通用段落整理中。 |
| 主 Issue/PR：profile 末段与原生 subagent/background-bash | list、等待任务 ID、后台进度、完成通知等教程被再次追加。调用契约归工具 description，profile 仅保留 Braid 成员与原生角色不同这一跨层区别及必要的接续入口。 | profile 已收敛；原生生产者修正中。 |
| 主成员：`RUN_CONDITIONS`、根任务、`BACKGROUND_COMPLETION_RULE`、定时根提醒 | service 停止、HOST/PORT、初态及种子存在内部重复；根任务再写 pnpm/portless 和 origin；提醒重复完整整理方法。环境要求保留一次，根任务保任务事实和职责，提醒只提出本次请求，后台行为归工具。 | `run.py` 已改，最终材料尚待重新生成。 |
| 使用 subagent 的 Agent：默认工具 description 与 promptGuidelines | workflow 单顶层/async、`runs.all` 有序结果、list、guide 等重复。完整调用契约保留在 description，独有有效条件合并进去；不能只留 guidelines，因为 Pi replace 模式跳过其 system 组装。 | 来源及取舍已核，生产者补丁修正中。 |
| 使用后台 bash 的 Agent：description、snippet、guidelines 三层 | background/service/自动后台在三处说明；其中恢复后 globalJobId、完成消息和交互 stdin 等独有语义仍需保留。完整工具说明集中在 description，其他 metadata 只承担必要发现信息。 | 来源已核，生产者补丁修正中。 |
| 配置 output 的 child：system 和 task | `single-output.ts` 两 helper 生成相同输出文件义务；前台、后台以及动态并行路径各自调用两种 helper。保留 system 来源并删除 task 副本；动态并行仍在最终 namespace 路径确定后注入。 | 调用者及独立判断已核，补丁修正中。 |
| 主成员接续与错误返回：`factory-subagent-observer.ts` 恢复消息、逐行 handoff、tool_result | 每个恢复条目重复 status 命令；恢复消息及错误补充又讲角色分工、等待、接续查询。消息应提供本次身份、状态、结果入口和具体错误解释，稳定操作说明归已有 profile/工具。 | 来源已核，拟窄改消息文本；观察、watch、调度保持原行为。 |

output 路径核对覆盖前台 `subagent-executor.ts`、后台 `async-execution.ts`、动态并行 `subagent-runner.ts`；preflight 已使用同一 system helper。新恢复 descriptor 分别保存基础角色 system 与 outputPath，恢复后重新走后台组装。无写工具时由 Agent 返回完整内容再由 runtime 保存的分支仍应保留。以上是源码路径判断，尚不是每条路径的实际新产物验收；历史会话已有的 task 副本不会被这次生产者修改追溯清除。

两 profile 原本同时要求文档/packet 机制和宣称技能方法均可选，属于义务表述冲突，并非纯重复。当前改稿明确非简单工作开始/接续时读取和使用适用方法，复用现有资料；explorer/executor 的独立输入补足对应读取入口。它们与父 profile 分属不同消费者，不恢复父 profile 继承，也不内联技能正文。

## 工具接线的补审结果

审查对象是 2026-09-30 下载的固定发布包，不表示已经安装或验证服务：`@upstash/context7-pi 0.1.2`、`@ff-labs/pi-fff 0.11.0`，原件在 `runs/iteration13/tools-prompts-plan-20260930/`。

**Context7。** 官方扩展已经直接读取 `CONTEXT7_API_KEY` 并访问 API，无需 mcporter。工具说明两次规定先 resolve、每问题最多调用三次，参数说明又重复 ID 来源；会使已获得有效 ID 的 Agent 被要求重复解析。建议集中为有效 library ID 的调用前提，删除次数上限和固定选择/回答流程。保留版本、来源及参数含义。`lib/api.ts::parseErrorResponse` 在 JSON 有 message 时直接返回 message，没有同时保留状态；其他分支丢掉原响应。建议窄改为保留 HTTP 状态和可诊断原响应。包内技能独立提供，prompt 模板不加载。

**pi-fff。** `before_agent_start` 只准备工具，不直接改 system，但不能因此断言插件没有 system 指令：工具在 `src/index.ts` 注册了 snippet/guidelines。已发现“grep 一两次后就 read”、“概念探索先使用本工具”、“只有指定情况才使用 ls/read”等额外流程限制，以及路径/case 参数与指南的重复。建议保留搜索语义、参数和索引行为，删去固定次数和工具优先级流程，并按同一输入去重。

这里更正前一版方案：该版本默认提供 `fffind`、`ffgrep`；`fff-multi-grep` 受 `PI_FFF_MULTIGREP=1` 控制，不是默认第三项工具。建议先沿用默认两工具与 `tools-only`，保留 Pi 自有 find/grep。本批没有额外多模式检索需求，不为增加工具数打开可选项。

**Exa。** 所需能力是检索与获取正文。已审候选中，轻量包缺正文且沿用旧 Pi peer，较宽包附带仓库克隆、存储和可选模型提取；建议仍为两个直接 HTTP 操作的薄原生扩展。其实际实现、schema、诊断与服务结果尚不存在，不能标为审计通过的已接线能力。

**父子接线。** 主 launcher 关闭自动扩展发现后显式加载；child 的 `extensions` 目前只写 background-bash，声明后也关闭环境扩展发现。所以只安装包或只改父 launcher 无法给选定 child 提供工具。Context7/Exa 分配仍待用户复核，之前提出的是主 Agent、explorer、executor，其他三角色不默认加载；不将该建议当成已选决定。fff 建议覆盖主/子本地搜索。

**凭据。** 根目录 `.env.i13-tools` 已建立，权限 0600，Git 忽略规则已确认；初建时两个变量留空，由用户填写。未复制其他个人配置中的 key。打包读取、私有制品注入和运行环境覆盖仍属拟实施接线，服务鉴权未验证。I13 的 mcporter 仅计划移除迁出的 Context7/Exa，其他服务保留。

## 尚未闭合的范围

- 原生 Pi edit 等基础工具与其 system guideline 的重复核对尚在继续；已有独有的实际行为要求不能因文案相近被删。
- 最终补丁链、实际 Pi system 组装、两 profile 的 prepare-only 材料尚未完成本轮反馈；前台、后台、并行和恢复须分别说明实际观察与源码判断。
- Context7/fff 尚未安装，Linux 原生依赖、headless 主/子装载、索引生命周期及两个服务鉴权没有实际结果。
- 未运行模型，未验证实际采用或上下文成本收益，也未修改 I12 运行状态、冻结制品或开展实验。

本次审计返回后，用户明确表示本页没有问题，授权两组开工，并要求进入Braid协作方法与Requirements树的讨论。工具线与提示词线现并行实施；下一组仍仅讨论方案，没有源码实施授权。

方案入口：[工具与提示词](tools-prompts-plan.md)。提示词实施进展由该支线后续记录；本页当前结论不得被理解为最终整合验收。
