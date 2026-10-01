# Braid Console 运行控制

2026-10-01。独立实验基础设施任务。前序运行控制和会话导航已有真实现场反馈；本轮完成稳定服务、归档只读和GC引用收敛，并在新制品中取得真实归档接口及浏览器反馈。旧WSL部署未启动或迁移。Console不属于I13或生成Harness迭代。


## 2026-10-01：生命周期收敛开工

用户明确授权：“你可以开始委派收敛braid console了”。本轮由GPT-6.1-Sol / extra-high独立实现与收尾，不属于I13，不阻塞生成主线；已有自主git commit授权适用于本批，提交仅限定Console及必要GC/文档增量，不push。

目标是稳定服务归属、现场与归档读取边界、持久配置的依赖保护、HTTP/转发/访问容器的独立所有权，以及访问日志轮转和人工journal保留。advisor已先独立判断：归档不能直接运行可写CLI或依赖原Git，应读保存字段与manifest；HTTP停止不解除恢复配置的引用。本次使用新输出目录、真实已保留归档及本地只读实例取得反馈；不启动Debian/旧Console/I12、模型或业务写入，不运行历史GC、apply或清理，不移除旧容器。

当前实现、前序dirty归属及实际结果归[生命周期实施回执](lifecycle-implementation.md)。前序控制与会话导航未提交源码在限定快照中保留，并作为本次完整Console制品的既有依赖有意收纳；不将其当成本轮新行为或新验收。

## 2026-10-01：运行位置与生命周期复核

用户新增查看Console运行位置与架构，并明确重点是避免重蹈存储生命周期问题。已只读核对：本机8765无监听，Windows侧WSL列表为Debian Stopped、docker-desktop Running；原Console部署随Debian停止。旧registry的四个容器ID在Windows当前desktop-linux daemon均查不到，未启动Debian确认其它Docker环境。没有启动服务、迁移文件或操作I12。

[生命周期核对](lifecycle-review.md)保存架构、真实路径、引用与清理缺口：registry/journal和host binary仍在实验目录，CLI访问容器依赖原挂载，原生正文依赖原绝对路径，HTTP退出不接管访问容器清理，当前GC不解析Console registry。存储整合者已收到这些事实并在现有显式protect边界中记录；Console后续独立收敛服务资产、现场/归档浏览及引用释放，不把它加入I13。当前回执在 `runs/braid-console-control/20261001-lifecycle/`。

## 授权与目标

用户本轮原话：“console 问题不纳入 iteration 问题；console 修正可以立即应用，应该让 braid 和 braid console 之间存在清晰的边界，让他们可以相对独立地迭代；braid console 属于实验基础设施的一部分。”
主线据此授权 Console 整体暂停/恢复控制及暂停后人工读写的必要修正，允许实施、部署和实际操作验收，由主线统一提交。用户随后明确：“braid console的修改方案不需要我复核，可以直接应用。”
不得为了验收解除暂停、发测试评论或改变生成内容。此授权最初要求两条I12都保持暂停；19:25:33 CST的Console journal曾记录GitHub被用户恢复，用户随后再次暂停。20:52 CST真实API读取确认两题均暂停，以[I12 packet](../iteration12/packet.md)及实际控制读取为准。本次接续与前端部署不改变现场控制状态。

目标是让用户能冻结当前运行的全部 Agent 会话及 Braid 定期检查，同时保留原代码、Git、对象和原生会话；人工查看、编辑及评论使用原现场，恢复只由用户明确操作。

## 职责与最小实现

Braid 负责对象、Git、事务和事件投递，接口仍是配套 CLI。Console 负责页面、人工草稿、操作回执；Docker 运行适配层负责固定容器身份下的物理暂停和恢复。Braid 不依赖 Console、实验名或 ARC，本次不修改 Braid 调度、数据表、事件语义或生成材料。

前一支线已将对象 CLI 改为每 run 一个独立、无网络的访问容器；根因、一次性容器的实际失败及稳定读取证据见 [暂停后访问历史记录](../iteration13/console-paused-access.md)。本次沿用两条既有访问容器，不创建或复制另一份 state。
新增明确的 Docker registry 配置，分别登记生成容器与访问容器的完整 ID、容器内 binary/state。对象基础命令由该配置生成；物理控制只使用登记的生成容器 ID，浏览器只提交 run ID 与 pause/resume。
页面独立查询生成状态、显示暂停/恢复按钮；恢复前说明会继续全部会话、定期检查和已入队人工输入。物理状态查询失败不阻断对象查看，也不把缓存状态当控制成功。

为避免新的暂停冻结 SQLite 写事务，适配层在同一 Linux 访问容器、同一挂载数据库中取得 BEGIN IMMEDIATE 写者门闩；持锁调用 Docker pause 并确认实际 Paused 后，再 ROLLBACK 释放。门闩不修改任何行，也不读写 Braid 私有表。生成与访问容器的数据库挂载必须一致，当前库必须使用 WAL。
每 run 的 Console 操作锁串行化物理控制及对象修改的前置读取到执行结束。若写者门闩不能取得，不发新暂停命令；若 Docker 结果或门闩释放未确认，保留原错误及 journal，不自动 unpause、解锁、删 WAL/SHM 或重试。
已有的直接 Docker 暂停可能发生于写事务中；对已暂停运行重新请求 pause 只核对现存写者锁，不解除或重新施加暂停。该核对不等于业务修改已验，也不能倒推历史暂停经过了新顺序。

独立 advisor 已复核上述正常路径，无需新增 Braid 暂停协议；其要求是门闩共享 Linux WAL 锁域，并处理超时、EOF和异常释放。数据库写者门闩只保证暂停边界未冻结写事务，不代表全部文件或应用已经到达可恢复检查点。

## 实施与验收范围

改动在 braid-console/server.py、docker_runtime.py、web/src 的运行控制 UI/API，以及 README 和部署说明。物理控制与对象写入共享原 journal，采用 started、completed、failed 或 unconfirmed 回执；不另建控制数据库或调度状态机。

验收使用 Python/TypeScript 编译、现有真实 Console API与浏览器，以及当前两条暂停运行的 BEGIN IMMEDIATE→ROLLBACK。允许再次请求 pause 核对写者锁，保持原 Paused；不发送业务 POST，不恢复生成，不建立或运行设施测试、模拟测试、smoke或自检。
必须记录实际两题对象读取、写者锁回执、页面控制及人工输入入口、最终原容器暂停状态，并保留版本、registry及服务身份。
新运行状态下的暂停顺序、真实 resume 和实际评论/编辑提交，在本次保持 I12 暂停的范围内均不能实测；交付中明确区分这些边界，不声称已完全验收。

## 部署与实际结果

Python 源码编译、TypeScript 编译与 Vite 构建成功。构建仍提示现有主 bundle 超过 500 kB；本次没有引入依赖或扩大为构建优化。没有建立或运行设施测试。

已部署到 WSL `/home/yyh/Development/factory26/braid-console/`，服务 PID 从 111070 替换为 **204242**，仍监听 `127.0.0.1:8765`。Mac 的既有 SSH 转发入口是 [Console](http://127.0.0.1:8765/)。部署使用 `runs/iteration12/restart-20260930/console-runs.json` 与原 `console-actions.jsonl`；registry 从自由 CLI 参数改为固定 Docker 配置，原 state、binary、run ID、权限及访问容器保持。前端实际资源为 `index-YblaaaWX.js` 与 `index-D_SK0Cwi.css`；源码及资源 SHA-256、部署命令、旧服务备份和新服务日志见原始证据。

两条真实 `POST /api/control` 的 `pause` 均返回 HTTP 200、`changed=false`、`writer_lock=available`，journal 分别记录 started→completed。这证明在原容器保持暂停时，同一现存库可取得 `BEGIN IMMEDIATE` 并完成 `ROLLBACK`；没有执行 unpause，也没有执行新的 Docker pause 命令。

| 实际读取 | GitHub | Sheet |
| --- | --- | --- |
| 列表 | 9 个 Issue、1 个 PR | 6 个 Issue、2 个 PR |
| 根 Issue #1 | revision 3、6 条评论 | revision 5、2 条评论 |
| 已有 PR | #2：revision 1、0 条评论 | #8：revision 1、4 条评论 |
| 原生成 PID | 5217 | 5181 |
| 最终原生成状态 | Running=true、Paused=true | Running=true、Paused=true |

实际 HTTP 记录包括 registry、两题物理状态、两次幂等暂停、列表、根 Issue 与已有 PR，共 13 条全部 HTTP 200，耗时 0.345–1.529 秒。暂停后的对象 revision 与评论数和此前读取一致。最终 Docker 核对确认原容器完整 ID、PID 和 StartedAt 未变；两访问容器均只有 `sleep infinity`，网络为 none、无自动重启，临时写者门闩已退出。

使用新的 Chrome 临时标签实际打开两题根 Issue，页面均显示“生成已暂停”“恢复生成”，列表和正文已加载，编辑按钮、external 评论输入仍在。Sheet 可见错误列表为空、评论输入未禁用；未点击恢复、保存或评论提交。两题截图及可访问状态保留在本次工具记录，临时核验标签已关闭，用户原页面未操作。

原始证据在 Mac 和 WSL 的同一相对路径 `runs/braid-console-control/20260930-control/`：`deployment.json`、`source-manifest.json`、`console-runs.deployed.json`、`http-operations.json`、`control-journal.json`、`final-container-states.json`、`browser-observation.json` 与 `server.log`。HTTP 文件保留具体路由、输入、状态、原始正文及耗时；浏览器 observation 是实际界面观察摘要，不能替代业务提交回执。

可重复的实际读取入口如下，恢复和业务写入需由用户决定。对于本次两条已暂停运行，可先读取 `/api/runtime` 确认 `paused=true`，再按 README 的 `/api/control` 请求 `pause` 取得幂等写者锁回执；不能将其改为 `resume` 用作验收。

```sh
curl --fail-with-body 'http://127.0.0.1:8765/api/runtime?run=i12-restart-github'
curl --fail-with-body 'http://127.0.0.1:8765/api/items?run=i12-restart-sheet'
curl --fail-with-body 'http://127.0.0.1:8765/api/item?run=i12-restart-sheet&kind=issue&id=1'
```

新运行状态下的“持写者锁→Docker pause→确认→释放”、真实 resume、实际评论/编辑及之后 Agent 消费仍未实测。当前证据只确认暂停后的读取、写锁可取得和 UI 入口；不能声称业务写入或全生命周期已验。已有直接 Docker pause 若冻结了写事务，本实现报告具体锁错误并保留暂停，需要用户决定是否恢复；本次两题未遇到此锁障碍。

当前无源码或部署阻塞。后续按用户明确的恢复或人工业务操作取得相应真实反馈；本支线不恢复生成，也不改 Braid 调度或 I13 内容更新策略。

## 后续新 CLI 接入边界

I13 已将 Braid `resolve/unresolve` 收窄为只接受讨论根 ID，见[CLI实施](../iteration13/cli-implementation.md)。
当前 Console 绑定的仍是 I12 冻结 binary，保持原运行与读取能力。`Discussion.tsx` 的整串 resolve/unresolve 已集中到根讨论入口并明确范围，回复保留单条hide，不在服务端隐式转换编号。源码、前端构建与20:21 CST部署完成，实际页面读取已核对，真实写操作仍未验，见[实际实施记录](cli-root-actions.md)。未来切换新binary时复用此入口。
这项接口适配属于 Console 自身，不能为适配而恢复 Braid 的隐式扩大作用范围，也不改冻结 I12。

## 会话关系导航

用户新需求：“Braid Console 有新需求：我希望看到 issue/pr 相应的 agent session 以及 agent session 相应的 provider sessions（包括历史的）（可能需要引入页面路由管理框架）（仍然交给 sub-agent GPT-6.1 extra-high 去实现；不阻塞主线）”。沿用“braid console的修改方案不需要我复核，可以直接应用”的授权，本轮独立实现、部署并只读验收；未授权 commit/push。

用户随后要求“还要能阅读原生对话和工具调用内容”，已纳入原生历史文件按需分页读取。21:14 CST源码与前后端部署完成，服务PID **483894**，新资源 `index-BROGd5Gi.js` / `index-PdJYewCM.css`，原registry/journal、冻结binary、state和生成容器保持。两题前后均暂停，未业务写入、跑模型、commit/push。

冻结 I12 的 `status --json.physical_sessions` 给出工作项、`group_id`、assignment generation、provider/native 身份及生命周期、turn历史。`group_id` 经CLI源码SQL核对对应持久 `agent_instances.agent_id`；同一Braid agent下保留多次provider替换历史。该接口从physical目录枚举，再补充数据库映射；不证明缺失physical材料的数据库记录也已列出。本次独立只读诊断确认当前两题数据库provider/agent身份与inventory逐项一致，但GitHub1条、Sheet2条原生日志已缺失，接口明确返回FileNotFoundError并保留元数据。

Python/TS编译与Vite build通过；历史Pi原生正文真实GET、第二页、稳定offset与刷新、工具call/result ID对应以及资源hash均完成。浏览器Chrome初始化报 `codex app-server exited before returning initialize`；IAB管理策略安全检查不可用并拒绝访问，未绕过控制。直链重载、后退/前进及取消离开后的草稿保留尚未实际UI验收；当前两题全部provider为Pi，Codex未实测，非文本工具block只呈原生JSON。实现、部署与具体边界见[会话导航](session-navigation.md)，原始证据在Mac `runs/braid-console-control/20260930-session-navigation/`。

主Agent独立部署后GET也确认两题暂停、原PID未变，列表26/13及历史正文首页各50条无错误，证据 `primary-readonly.json`。当前源码与部署可行范围已收尾；剩余浏览器交互验收由工具可用性阻断，3份原生日志缺失保持原现场、Codex真实验收等待相应运行材料，不扩展Braid接口或启动模型。
