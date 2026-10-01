# 本轮实施记录

本页是实现经过，保留当时状态与核对结果；当前工作和授权见[packet](packet.md)，方案取舍见[最终审查](repair-review/final/packet.md)。

2026-09-29追加：vision先辨认图片类型、用途及可读性，再按类型和委派问题分层提取，区分参考材料与运行证据；保留fresh/read-only/既有模型。pi-braid和Flash的五份vision角色同步，未修改归档variant。
开发工具要求已进入根Issue任务正文及共同运行条件：使用pnpm与portless，正式应用保持官方逐目录npm安装/build/start兼容性。锁定pnpm 10.34.5、portless 0.15.6，Linux运行时增加对应Node启动入口；portless使用现有Node24工具环境，应用仍兼容Node20.19.3。代理使用1355/HTTP、关闭hosts写入，状态按本run存放；各工作项/服务用独立名称，正式启动不依赖代理。依据：https://portless.sh/configuration 、https://portless.sh/commands 。依赖锁更新完成；尚未重建Linux制品或启动实验。
用户同时要求清退全部Braid测试。后续只用编译、实际操作和获授权实验反馈；本页原63/63等记录是清退前历史结果，不是继续维护测试的依据。

主线已修改 pi-braid 与 Flash 对照的根 prompt、成员 instructions：先形成跨项产品/技术/验收决定；根共享基础直接交关联 PR；子项自包含来源；实施计划与预演在 PR 承接；合并前消费当前候选的检查和未解除前提。
SVC product/check-design 补保真转换方法：原需求与派生决定的权威、并列范围/非单调条件、初始状态被检查 setup 绕过的范围及不确定解释。
原生指引与 executor 角色补工作所有权，observer 在真实 Unknown agent 工具结果追加目录与所有权纠偏，保留原始错误，不自动映射角色。
Braid CLI 补指派别名→具体成员、背景关联≠关闭意图、持久退订帮助与成功回执；Issue create JSON 在 id 之外返回 assignees/assignment_note。Braid 共用职责只说明对象责任，不加入 V&V 方法或题目语义。

上述均为源码落地，尚未进入统一 Linux 制品或新模型运行；实际采用待实验。

有效输入独立审查完成后，主线已修两处遗漏。运行共同约束从根Issue正文移到variant的单一RUN_CONDITIONS，由native_files传给每个Braid profile及advisor/explorer/executor/browser-operator的原生正文；保持独立上下文，约束不扩大各角色既有修改权限，vision仍只读委派材料。部署条件、保留端口与数据、外部修改和评测材料限制不再依赖父逐层转述。根prompt保留需求来源、根工作流程和交付目标。
整合PR负责人只负责验收、合并和交接，删除其“关闭根Issue”的重复责任；根负责人仍据完整交付判断关闭。PBB service字段说明只保留在实际追加的后台说明中，避免两处维护。pi-braid与独立Flash实现同步，未改变历史冻结包；静态沿native_files装配核对，不新建Factory/Corpus测试。

两题新增因果证据也已进入方法正文。SVC product把“派生内容不覆盖原需求”细化为实际原句对照、负责决策者处理、显式变更及受影响材料更新；原始输入内部矛盾仍允许有据裁决，不强求同时满足矛盾原文。technical把调用入口用途改变纳入契约变更，implementation补追踪旧豁免前提与从实际调用路径取证。入口导航同步指向这两类问题；没有写入赛题名、特定接口或评分规则。
Sheet最终视觉返回的父消费已核实：不是没收到，而是用另一检查边界的PASS把具体观察归为capture artifact。interpreting-results因此补“同一待证属性”要求：解释为什么观察不可靠，补缺失观察或缩小声明；不要求父重复整份委派，不把截图缺证直接判为产品失败。
check-design同时补齐相关规则重叠/转换和跨组件交接的判别条件；普通孤立parity或各模块分别PASS不能独立证明这些连接成立。

GitHub完整轨迹又确认了具体CLI误导：根把Braid检查评论的delivered消息回执当作基础负责人已交付。`cli/mod.rs::print_message_receipts`现作为create/edit/view共同展示入口，消息状态与正文分区，delivered解释为会话接受输入；JSON与原始reason保留。不靠根提示词解释运输层术语。
当前二进制已编译。只复制原GitHub attempt09的braid.sqlite3到临时目录，实际执行`braid --state <副本目录> comment view 4 --thread`，输出检查评论#4与催发布回复#5的原正文，再单独输出“消息投递回执 — 评论 #4（仅表示评论输入的接收状态）／收件人 @glm-1: 会话已接受评论输入 (delivered)”。未修改原运行；attempt03/04旧快照尚无#4，未据其查询失败判接口错误。

原生等待方案已收敛：PBB登记非service后台任务到pi-subagents已有background-work接口，Pi headless agent_end既有drain处理完成；常驻服务显式service:true，不按命令字符串猜。主指令与observer等待反馈同步采用该语义，依赖补丁与 Mac/Linux 构建接线已完成，Pi 主/子形态的实际 RPC 扩展加载通过；作业结束与 follow-up 时序还须真实运行观察。Braid不新增job知识。

Braid已编译并实际查看 issue create、pr create、pr link、issue unsubscribe帮助，三处语义展示符合当前约定。本批完整Braid检查63/63通过，覆盖暂时性恢复失败后的worker重试与静止保现场两条路径；不是仅引用前批59/59。原生Pi实际断连恢复和新方法采用仍待新运行。

监控已按实际新生成/冷恢复入口修正来源边界，并使用旧真实记录只读核对：能读取全新生成的native证据，也能识别旧Sheet当次22条持续429。历史错误、之后发生的共享工作区变化与当前运行分开；发现当前可执行会话连续未恢复错误时返回attention，不自动取消、换模型或把bench判为失败。

## 2026-09-29 本批落地结果

Vision 的分类读图方法已更新到两个活动 variant 的五份角色提示词，保留独立上下文、只读工具和原模型配置。
Braid 的内嵌测试、集成测试、测试专用脚本与支持代码、CI 测试调用已删除；维护入口不再要求测试。历史测试结果保留为历史证据。`cargo check --bin braid` 通过，现有 11 条 dead-code 警告尚在；本批未运行测试。
pnpm 10.34.5、portless 0.15.6 已加入 npm 锁、runtime 命令入口和两个活动 variant 的任务要求。开发自检通过 portless 分配端口，正式应用保留平台 npm 安装、构建与启动兼容性。旧镜像需更新依赖层，尚未将这些改动打包部署或启动实验。

用户追加技术栈要求已接入两个活动 variant 的 RUN_CONDITIONS：应用测试使用 Vitest，UI 使用成熟组件库、图标库和 UnoCSS，保留浏览器 E2E 验收工具。该选择归属 variant adapter，不进入 Braid/SVC 或通用 ARC 协议适配层；由运行中的 Agent 为生成应用选择兼容版本并安装，不由 Harness 预写应用依赖或源码。Vitest 要求仅针对生成应用，不改变禁止维护 Braid/Factory/设施测试的约束。

## 共用工程指引与预打包环境

用户批准：“除了针对两题分别提出的内容，都接受”，并要求称为预打包环境。两个活动 variant 已加入官方脚手架/兼容版本、SQLite 优先评估/事务/幂等初始化、同源 API、真实跨模块接口、Vitest 与 Playwright 分层反馈、组件语义和 UnoCSS 提取约定。未指定 TS/Vue，未加入两题专属新库建议，未预写应用源码。
预打包工具路径通过现有环境变量和 PATH 告知；新增同次运行共享 npm cache/pnpm store，接续沿用 work/cache。浏览器和现有结果保留工具继续复用，安装错误保留首轮日志。未重建统一制品、未启动实验；等待两位 Astra 全量分析完成并消费后再复核实验启动。

## 完整审查返回后的局部修复

GitHub审查完成42/42个可得原生会话；其四个新增窄边界已写入SVC implementation/debugging：前置执行成功终态再消费、原退出码/首错不被格式管道替代、临时文件/浏览器/服务归属及干扰通知、已受理或结果不明的外部写入先读回再重试。agent-browser入口明确named close而非close --all，修正上游通用例在共享运行中的适用范围。
Sheet发现HyperFormula技能例把getCellValue结果当CellError，已核官方3.4.0 CellValue.ts及index.ts，改为DetailedCellError；自定义函数仍返回CellError。属于现有技能API纠错，不引入用户排除的两题专属新增库建议。未运行测试或实验，尚未冻结新包；Sheet全审仍在推进。

## 独立修复复审 F1/F2 的消费

复审41个目录项已完成，未要求整树回退。F1已在两活动variant的observer修复：首次写入前读取当前native-home持久清单，核对schema/父身份/子项基本结构，再通过现有merge合并后续事件；同父resume不清空索引，无法识别的索引报具体错误而不覆写。原生transcript/artifact不改，Braid不接管子任务。尚无真实恢复采用证据，未运行测试。
F2仍在处理：旧run watcher仅在新父进程存活时转送，不能称无条件唤醒；需收敛所承诺的生命周期，不擅自把所有历史任务变成Braid的待完成责任。F3 PBB等待/取消顺序和F5 Node20正式兼容保留为获授权运行观察项，不任意加超时或第二套框架。

## Sheet全审完成后的收尾

Sheet263/263可得会话及24942条记录已审，9个provider原文缺失保持缺证。BodyArgs共用帮助已说明多行/特殊字符正文使用文件或stdin，既有能力不变、不新增转义器。
F2收敛为持久入口+存活期间转送：observer启动消息及运行说明明确通知适用条件，恢复时重读原生状态；不自动adopt旧任务或为历史任务无限保活、不让Braid接管原生生命周期。与F1保留同父索引共同提供接续材料，真实消费待运行观察。该取舍进入最后独立复审，不能声称保证关闭后自动唤醒。

## FF1：按父身份保留原生子任务索引

最后复审发现 Pi 正常启动会先产生 startup 父身份，再由 Braid RPC new_session 创建另一个父身份，二者复用 native-home。
两个活动 variant 的 observer 已区分同父恢复和不同父切换：同父先加载清单再合并；切换时将有子任务的旧清单保留在 `.factory/session-trees/<parent>.json`，只为当前父恢复它自己的清单。
历史发现同时读取当前 home 与其它 home 的清单，按父身份选最新记录，避免当前/归档副本重复；旧子任务不改挂到新父，不转移执行所有权。
正常启动的空索引不再触发父身份错误，也无需存档空历史。
使用已安装 esbuild 对两份 TypeScript 做编译转换成功；这不是行为验收，没有新增或运行测试、探针。
独立复审仅核对本次增量，真实 startup/new/resume 采用仍待获授权生成观察。

## FR1：被动历史结果不独立启动原生回合

用户授权后，两活动variant的factory-subagent-observer将历史子任务终态通知改为triggerTurn:false。
继续记录消息、保留索引及原生成果，不接管旧任务、不放宽Braid writer；handoff说明与运行文档同步反映结果通过合法后续输入消费。
两份TypeScript经现有esbuild编译转换成功，未执行测试/探针或实跑；自然时序与模型消费效果仍待验。
产品/架构的独立审计另见cells/lifecycle-architecture/，不以本次局部修补代替对结束/唤醒权的整体判断。
