# 官方标准 Pi multi-agent Harness 设计

状态：Human 已批准。本页整合产品边界、HLD 和关键 LLD；支撑分析见 [Agent边界](agent-boundaries.md)、[范围与事实](scope.md)、[SVC接线](svc-wiring-design.md) 与 [Pi诊断](pi-diagnosis.md)。源码实施仍以单独的 impact handshake 为开工门槛。

## 产品结果与第一性约束

Harness每次接收一个Factory task及其完整requirement bundle，在无人中途介入的环境中调用平台模型、组织软件工作，并把可部署应用写入指定输出目录。一个task建立一个根Issue；根description保存Factory任务prompt、冻结bundle的身份/读取入口和总体完成义务，不要求复制全部长文本。bundle中的单条requirement不是独立Issue。最终价值由应用满足需求的程度、成本与完成时间决定；Agent数量、Issue数量、方法文档读取量和内部测试数量都不是目标。

LLM只有本次输入与可调用动作。需要跨采样保留、由多方共享或从失败恢复的状态必须由Harness或工作材料持有。增加一个Agent只有在能力匹配、上下文隔离或并行收益超过交接与整合成本时才合理。语义判断由LLM作出；Harness提供对象、工具、状态和约束，不从标签、评论文本或阶段名推断任务含义。

本轮保持以下不变量：

- Factory task的完整requirement bundle及其reference是产品输入权威；SVC提供工作方法，不改写需求。
- Agent使用GitHub式Issue、PR、comment、reply、assignee和worktree。运行时指引不出现Braid、agent-profile、preset、事件、group、turn或内部状态机概念。
- Issue承载需求理解、方案和最终验收设计；PR承载实施计划、执行和验收。它们可以反复讨论和修订，不是固定单向阶段机。
- 是否拆sub-issue、怎样拆、由谁承接由当前Agent根据完整子结果、独立验收、上下文与并行收益判断；Harness不自动拆分。
- SVC V&V的正文与演进归SVC Corpus；Factory只选择版本、提供导航和记录实际装配。
- 同一个冻结ZIP既用于官网也用于本地官方runner；来源不同的结果分别标识，不能把本地结果称作正式成绩。

## HLD

```text
official runner
  └── main.py(requirements_dir, output_dir)
             │ task = complete requirement bundle + reference assets
             │ platform model + visual env
             ▼
     Factory package adapter
       ├── frozen source/material manifest
       ├── SVC semantic navigation + Corpus
       ├── model/profile/native-role catalog
       └── GitHub-like object instructions
             │ create exactly one root Issue for this task
             ▼
       local issue / PR runtime
       ├── Issue/PR/comment: cross-Agent collaboration
       ├── worktree + task packet: one work-item Agent's external context
       ├── assignee: another configured Agent
       └── Pi session tree: bounded native sub-agents
             │
             ▼
       accepted delivery commit
             │
             ▼
       official output directory

one immutable ZIP ─┬─ hosted Competition adapter ─ hosted score/artifacts
                   └─ official local runner adapter ─ local score/artifacts
                              ▲
                        resumable controller
```

### 语义与状态所有权

| 信息或状态 | 唯一owner | 消费方式 |
| --- | --- | --- |
| Factory task、完整requirement bundle与参考资产 | 平台输入快照 | 每个task建立一个根Issue；description引用冻结bundle，Agent按入口读取；视觉Agent读取明确路径 |
| 工作项目标、description、讨论及关系 | GitHub式Issue/PR/comment对象 | 通过CLI查看、编辑、回复、关联和指派 |
| 当前工作项的设计材料、计划、脚本与证据 | 该work-item工作树中的task packet | 当前Agent及其原生sub-agent按索引读取 |
| 跨work-item消息 | comment/reply | 发给父项、关联项或明确消费者 |
| 跨work-item代码/文件结果 | ready PR commit及合入后的delivery commit | 通过PR关联、查看和合入，不读其它脏worktree |
| 软件工作方法 | 冻结的SVC Corpus | semantic index按压力路由到一个概念 |
| 可指派Agent及能力说明 | GitHub式assignee投影 | Agent按成员名指派Issue，不感知agent-profile |
| 模型、skills、MCP、原生sub-agent等能力配置 | 内部agent-profile | Harness按assignee映射启动或恢复会话，不暴露给运行时Agent |
| provider物理会话及停止/恢复 | Adapter + Pi RPC合同 | Harness管理，Agent不感知内部身份 |
| 实验定义与证据身份 | Factory controller manifest | package hash、venue、task、model和revision关联 |

task packet不需要成为跨worktree共享数据库。它服务一个work-item Agent及其Pi session tree；子Issue有自己的packet。跨Agent真正需要传递的是结论、问题、接受条件、commit与证据handle，通过comment/PR表达。若一个材料必须共享，先成为可引用的提交制品或把必要语义压缩到评论，不暴露其它Agent未提交的工作树。

### Agent、assignee与内部agent-profile

Braid级Agent由work-item及其持续上下文形成。运行时Agent只认识GitHub式assignee：把Issue指派给某个成员，就能与另一个Agent协作。Harness在内部把assignee映射到agent-profile，并据此装配模型、skills、MCP和原生sub-agents。一个内部profile可以支持多个并行会话；这些配置名与机制不进入Agent提示词。活动配置先提供少量能力配置，不预建UI/App/Coordinator组织图。

每个Issue或PR同时最多一个active assignee，它是当前work-item的执行owner，不是共享语义的唯一作者。公开Context提供当前assignee和一份短成员目录（login + 可观察能力/限制）；`list/view/context/status --json`不返回内部profile ID、model/provider、revision、digest、assignment generation或session身份，运行时也不能调用`profile list/view`。

CLI采用Agent已经熟悉的`gh`形状：create使用`--assignee LOGIN`；edit使用`--add-assignee LOGIN`和`--remove-assignee LOGIN`，允许同一命令原子替换。添加第二个active assignee或删除不匹配的login会给出明确错误，不制造同一work-item多个writer。成功指派会在旧writer fenced、旧native session取得停止证明后启动或恢复目标Agent，并以当前对象上下文产生一次新采样；不能只创建idle session后等待另一条消息。停止未知时保持blocked，不能激活竞争writer。

具体粗筛矩阵、profile字段与原生角色见[能力装配设计](recipes.md)。首批只保留两种可指派的通用能力，不把模型差异包装成岗位：

| 内部配置 | 适用说明 | 默认用途候选 |
| --- | --- | --- |
| `pi-glm-fast` | 低成本的通用需求理解、设计、实现与整合 | GLM或mixed组合的Issue默认，也可承接PR |
| `pi-deepseek-fast` | 快速、长上下文的需求理解、实现、探索与整合 | DeepSeek组合的默认；mixed组合的PR默认，也可承接Issue |

内部description写可观察能力、适用问题、工具与限制，并投影成指派者可读的成员能力说明；运行时不出现profile术语。login在一个variant中唯一；未知login在对象、revision、event或wake写入前失败。不要用岗位名暗示某个成员拥有某类Issue，也不要把供应商宣传当能力事实。Kimi只作为原生specialist提供昂贵咨询；Qwen只在精确的`qwen-3.8-flash`可调用且协议通过spike后加入，不以Max替代。

每个普通Pi profile提供相同的基础原生角色，使当前work-item能够有界委派：

| 原生角色 | 建议模型 | 局部责任 |
| --- | --- | --- |
| explorer | deepseek-v4-flash | 一个事实、约束或证据问题；只返回消费方需要的结论 |
| executor | deepseek-v4-flash | 一个已授权的局部实现与反馈循环 |
| browser-operator | deepseek-v4-flash-vision-exp | 操作应用、结合DOM与截图执行明确页面旅程 |
| vision | deepseek-v4-flash-vision-exp | 分析明确图片集合并返回带源路径的观察 |
| specialist | kimi-k3 | 结构性复杂且普通模型未收敛的问题；昂贵、非默认 |

原生角色必须各自显式配置model、实际支持的reasoning、tools、skills、MCP和context策略。父Agent决定是否调用；Harness不按失败次数或关键词自动升级到Kimi。browser-operator可直接看截图，不经vision重复中转；vision用于没有浏览器动作的图像分析。

## SVC接线

运行时入口应让Agent先得到足以行动的语义地图，而不是一份命令清单：

1. SVC提供task packet、探索/设计/实施方法、sub-agent委派、V&V、长期specification与taste判断。
2. 当前Factory task属于非简单工作时，Agent主动创建或接续当前work-item的packet；无人环境中不存在等待Human宣布任务或逐阶段批准。
3. `packet.md`是短控制面：结果、约束、完成依据、重要当前事实与下一步。设计、调查、计划、脚本和证据按真实检索/更新压力分开；并行主线或共同门槛出现时才增长Tracks/Cells。
4. 需要设计验收、选择证据、判断是否完成或解释残余时，读取SVC Verification。具体方法只在该压力出现时加载，不全量读取Corpus。
5. Issue/PR/comment是跨工作项协作界面；packet是当前工作项的文件材料。运行时文案只使用前者的GitHub式名称，不解释底层Harness。

公共team variant使用上述共同索引，可以按需发现Verification。`pi-team-vv`使用同一Corpus版本与团队能力，由variant额外引用并注入canonical `methods/design/test.md`和`verification/index.md`；基础组仍允许且应当按需自检。这样实验变量是方法加载/强调，不是另一份Factory V&V理论。

## 官方与本地混合实验

打包器对每个variant生成一个不可变ZIP及manifest，至少记录ZIP hash、Braid/SVC/core版本、内部profile与原生角色effective digest、方法装配、入口语言及构建时间。variant直接引用这些配置与方法；删除一对一的preset空壳，Braid仍不接收variant语义。

controller消费显式run matrix，每项为 `{variant, package_sha256, venue, competition/task, model_config_id}`。Hosted adapter为一个variant的冻结ZIP保存一次submission snapshot，再为该Competition的每个task分别create run并start；同一task调用仍独立建立自己的根Issue。当前官网没有已观察到的原子bulk-run，controller逐项编排。Local adapter调用主办方固定版本的local simulation runner，在独立workspace、容器、端口和输出目录运行同一ZIP。两者汇总为共同状态但保留venue字段：

```text
planned → prepared → snapshot-saved → run-created → started → terminal → collected
                       \→ blocked/unknown
```

prepared证明ZIP、配置和输入身份冻结。Hosted的每个成功写响应必须先持久化`submission_id`或`run_id`再发下一次写；传输结果不确定时先通过历史/GET核查，不能盲目重复POST。远端未知status保留为`unknown`，不能把所有非`PASSED`值归为失败。terminal只表示明确终态；collected另行证明status、增量日志游标/events、traceability、commit/source、可下载archive或本地结果已经持久化，日志中的“collected”字样不算下载证明。

官网同时运行能力不足时，controller让其它独立矩阵项进入本地队列。hosted slot、同一submission的task并发与Meter限制仍需真实spike，不能从Playground或本地worker外推；不能用多账号绕过官网限制。本地并发单位是独立Docker run，不提高同一Playwright的单worker。共用一个Meter key并行时，前后usage差值不能准确归因到单项；在主办方没有request级归因前，将逐项成本标为不可分配或为成本测量单独串行，不编造估值。

Competition资格只接受标准`frontend/package.json`与`backend/package.json`交付路径；local simulation特有的`deploy.sh`只能作为本地便利，不能证明官网可运行。公开Lite/Web、local单任务score与正式初赛是不同venue/评分身份；controller保存逐task原文和平台聚合原文，只有官网明确返回完整Competition聚合时才标记正式complete。

controller是确定性进程，负责队列、恢复、状态采集和终态退出。主Agent不充当scheduler。内部远端采集从三分钟开始并使用游标；只有设施故障需要设计判断或完整矩阵终态才返回主会话。原始日志交低成本sub-agent做有界降噪，不把心跳或token增长报告成语义进展。

## Pi Adapter边界

现有证据不支持“Pi原生RPC反复teardown失败”。RPC的`abort`只保证当前operation idle；extension资源由幂等`session_shutdown`清理，独立bash另有自己的中止合同。上一轮真实缺口位于`pi-subagents`、自有lifecycle扩展和Braid Adapter的接缝：控制请求成功或`control_inactive`都不能证明detached child已经终止。

Adapter只翻译Braid所需的start/resume/turn/interrupt/teardown与身份，不重新实现Pi会话树语义。Braid负责在context replacement前fence旧writer，并证明自己拥有的native process tree已终止；lifecycle hook负责自己创建的detached background child，只有同时观察到实际process terminal和canonical session lease释放，才能返回`stopped`。stop acknowledgement保留为诊断字段，不能升级为终态证据；证据不足返回`unknown`并阻止replacement。

session UUID是唯一身份，`sessionFile`只是可重新定位的材料。归档与恢复只按UUID关联；路径变化时必须以JSONL header唯一匹配canonical file，找不到或多匹配都返回`unknown`，不得按mtime或basename猜测。明确`Failed`后的单次重放、`Unknown`的at-least-once恢复以及blocked worktree接管由Braid store持有，不下沉给Pi Adapter。

实施前的最小无付费三层spike保持同一writer与进程oracle：原生Pi RPC先证明自身bash中止和UUID恢复；Pi+subagent/lifecycle再证明foreground/background真实停止；最后经Braid验证context reset两个crash切点、单一replacement和Failed/Unknown恢复。最早失败层承担修正，不通过完整benchmark定位生命周期合同。

## 尚未冻结的LLD

- DeepSeek Flash、DeepSeek Vision、GLM Flash对Pi工具调用、图片输入、reasoning字段和1M context的真实网关协议。
- `qwen-3.8-flash`是否存在于比赛Meter及精确模型ID。
- Competition写接口的幂等/写后核查字段、hosted slot、同submission task并发、完整终态枚举、重跑计费/聚合规则和正式产物下载权限；已观察到的route仍需adapter版本化。
- 官方local simulation基础镜像真实来源/digest与平台最终镜像差异。
- assignee公开login的命名/大小写规则、description的context字节预算，以及PR是否需要展示完整成员目录。

这些未知在技术方案批准后以只读文档核验或最小无评分spike收敛，再形成线性实施计划；不会留到完整矩阵第一次发现。
