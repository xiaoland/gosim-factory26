# 逐项覆盖与证据限制

`方向成立` 指已读观测/产品约定与当前机制的因果关系成立，不是实跑通过；`有限核查` 指本轮未独立取得该项全部原证据或读取全部相关实现；`需修` 与 `待定` 详见 findings.md。P1 为进入效果结论前的重要证据缺口，P2 为局部缺陷/风险，P3 为非阻断维护项。无缺陷严重度写“—”，不把原历史问题的严重度冒充当前修复的缺陷严重度。

证据简写均为仓库根相对路径：G=`tasks/iteration10/run-audit/github/report.md`及`evidence/session-*.txt`；S=`tasks/iteration10/run-audit/sheet/report.md`及其定向单元；I=`tasks/iteration10/instruction-audit/report.md`；L=`tasks/braid-github-minimal-review/cells/iteration10-lifecycle.md`；T=`tasks/braid-github-minimal-review/cells/iteration10-tools.md`；N=`tasks/iteration10/native-idle-spike.md`；O=`tasks/factory-subagents/cells/iteration10-role-audit.md`；B=`tasks/braid-product-reaudit/cells/termination-contact.md`。原账本中的历史测试只当时点证据，本轮未运行。

## 原账本 29 项

| ID | 观测、竞争解释与原证据 | 当前机制、根因及边界判断 | 状态、严重度与最小补证/改进 |
|---|---|---|---|
| R01 | G session04 L25–32：评论只催进度，父却把 delivered 归成完成；后来同父正确识别同样回执，故不是固定无能力。该段的旧 Context/工作区与根行为已定向阅读；原生完整链由 G 覆盖。 | CLI 将评论正文与投递回执分区，是能在工具边界消除的真实歧义；不擅自判业务完成。R22 的接管判断仍必要。 | 方向成立，—。旧 DB 实际读回是已有反馈，本轮未重跑；下次观察根是否仍以运输状态断言交付。 |
| R02 | I 的冻结/现行输入装配显示根独占共同条件；缺输入不证明已经越界污染。 | 已直接读 native_files：profile 与四个 bash 角色拼同一 RUN_CONDITIONS；fresh 与角色范围仍保留，vision 除外合理。 | 方向成立，P3 重复负担。下一实际制品核对消费材料，非仅磁盘模板；不必为角色定制再建生成层。 |
| R03 | I 记录根与整合 PR 都被告知关闭根。 | 当前 profile 明写整合 PR 交接、根判断关闭；Braid Closes 仍是显式普通能力，没把权限集中成硬锁。 | 方向成立，—。实际交接待观察；不要求禁用所有 Closes。 |
| R04 | G 原/派生/种子与 S 初始状态：旧样例覆盖窄于原条件；S 原输入内部确有互斥种子，不能要求机械同时满足。 | run.py 保留来源与跨项方案，SVC product/check-design 要求并列、例外、起始状态与 setup 绕过的范围；方法层合适。 | 方向成立，—。观察实际判据是否保持原场景，不把方法出现当采用。 |
| R05 | G session03 L23、session15 L41 明知冲突仍选择派生正文；中央 seed 最终修回是终态反证。 | 已读 product.md：原句对照、交决策者、有据变更并更新材料；允许原输入内部冲突，未封死根裁决。 | 方向成立，—。观察冲突是否形成消费者可用决定；不归因隐藏具体失败数。 |
| R06 | S PR15 用途扩大而 PR19 仍按 undo 豁免；最终 FE/BE 双规则差异由 Sheet 独立审查取得，本轮不重审整个应用。 | 已读 technical、workflow、check-design：用途也是契约、追消费者至写入、交叠/跨组件观察；是语义方法非 Harness 业务修补。 | 有限核查、方向成立，—。本轮消费 S 的定向源链而未重跑应用；真实调用守卫须下次生成自行验收。 |
| R07 | S 两个 vision transcript 与已提取图确认父收到了疑点；截图不支持标题不等于功能失败。 | interpreting-results 明确同属性反证不能被其它 PASS 替代。 | 方向成立，—。本轮未重新看全部图片；遵守已有视觉审查限制，下一结果需补同状态观察或收窄声明。 |
| R08 | G 根旧指令曾允许基础独立子项，后补 PR 也受工具/职责口径影响；不能把旧合法策略本身称 bug。 | 当前用户批准根基础独立 PR；run.py 持有业务分批策略，provider 介绍 Issue/PR 分工，未混入比赛业务答案。 | 方向成立，—。属于流程选择而非已证全部失分根因；看实际 PR 前置交接是否形成可消费契约。 |
| R09 | O 六组零调用、目录可发现；零调用不是工具阻断，迟到咨询也未必造成每个错误。 | 当前 profile 已把重大假设前咨询与普通 ROI 分开；SVC 保持方法、原生 role 提供能力。 | 有限核查、方向成立，—。本轮读父指令、advisor 正文与 O；快照中五份角色正文摘要一致。需实际调用/返回/父采用链。 |
| R10 | O 错 agent 名后换 executor 仍重复已指派工作，说明只纠正名称不够。 | 已读 observer Unknown agent 保留错误并提示 list/所有权；profile 区分 Braid 指派和内部子任务，不自动重映射。 | 方向成立，—。已读 executor 的重叠核对/返回切口条款，下一自然误用看是否重新审视归属而非只 spawn 成功。 |
| R11 | O 有 fresh 交接正例，真实在途终态父消费未证。旧父恢复确有重复派写。 | observer 的同-home 覆写与跳过组合破坏索引持久性；旧 watcher 没有覆盖新父关闭后的寿命。 | 需修，P2，见 F1/F2。保留当前父清单并明确通知存活条件；不要把生命周期挪给 Braid。 |
| R12 | O/S 纯读 vision 被 guard 错拒，PBB bg ID 误投 wait；已有 vision 成功反证能力本身缺失。 | 当前 vision completionGuard=false，observer 仅在对应原生错误后附提示，保留原始错误；aggregate wait 与 ID wait 区别准确。 | 方向成立，—；A01 时序待验。提示不能被当作结果已经送达的证据。 |
| R13 | O/I 工具方法原先分散；explorer 零调用没有阻断证据。 | 角色直接含探索入口、MCP 归 variant，领域知识仍留技能，职责放置合理。 | 有限核查，P3。已读 explorer 全文及 mcporter 三服务配置；是否远端可用尚未调用确认，不建议按调用配额扩展。 |
| R14 | S PR24 L159 附旧 OPEN Context，父误疑重开；除 token 重复，还有真实状态干扰中介。 | 已读 Pi prompt 接受后 clear context、resume/start 清暂存；不以同回合最终失败倒推输入没接受。 | 方向成立，—。协议旧验证与当前源码一致，真实净消耗/不再误读待观察。 |
| R15 | L 暂时 start/timeout/断连被当永久不可达；部分是定位期间历史验证，非比赛真实失败实例。 | session Deferred、dispatch sleeping/context/profile/instruction/worktree 严格匹配与 store 退回 pending；身份改变 fresh 合理。 | 方向成立但与 R11 有组合缺口，P2。同身份真实恢复、保留 queued 与消费一次仍待原生观察。 |
| R16 | G 重复完成响应存在；新评论影响 canonical revision，不能假定所有终态通知都可原生复用。 | 同身份/revision 批量和严格 sleeping resume 避免技术重复；不靠系统理解“这条评论没意义”来丢输入。 | 有限核查、方向成立，—。本轮检查 dispatch 与 store 条件，未全读所有 SQL 分支；收益不能从旧 cacheRead 直接兑现。 |
| R17 | I/G 描述短期反复改写与旧决定可见；行为可能源于整理习惯，不能只认工具缺陷。 | provider 介绍稳定正文、增量评论、更正/hide/resolve 及重建时效，不自动判废消息。 | 方向成立，—。自然整理是否减少错误仍待运行；无需额外 packet 模板。 |
| R18 | L/原账本的 Closes 无效与背景关联混淆；关联本身并非自动关闭意图。 | 已读 closing_issues_in/default branch、冻结 closing_issues、apply/recovery 共用结算；保留明确语义。 | 方向成立，—。本轮未重新实操全部 merge 恢复点；不把 develop 子 PR 文本追溯成 main 关闭。 |
| R19 | 显式退订仍被历史参与者集合纳入，行为与用户选择冲突。 | 已读 discussion_changed SQL：历史参与排除 explicit inactive；当前负责人和当次 @ 仍保留；订阅恢复须显式。 | 方向成立，—。与责任不能退订一致；自然采用待验。 |
| R20 | G session02 真实 create JSON 仅 id，不兑现新成员说明，父推测只有两个 worker；后续实际多人并发是容量反证。 | CLI 返回 assignees/assignment_note 与 provider 说明相配，能力名与具体身份分开，不增加创建成员步骤。 | 方向成立，—。本轮定向读 G、provider 与 CLI print_issue_created；看下一指派后是否还重复启动。 |
| R21 | 手工 Git 整合已发生但对象仍 OPEN；旧双编号有歧义。 | 已读 merge 以 created base、observed unique head 和祖先正证记录整合，无 Git 修改且回执说明观测；新对象共用序列旧号保留。 | 方向成立，—。迁移及全部编号路径仅有限核查；不能把观测 base 称新造 merge commit。 |
| R22 | G 错误接管与 S 同候选未消费前提说明：未发布不等于停止，head 相同不等于判据已满足。 | profile 要联系/明确失败证据，合并前消费结果及未解除前提；没有新锁或机器 V&V 裁决。 | 方向成立，—。真实候选/base 变更仍需行为观察，不再叠自动审批。 |
| R23 | B 实际 DB 副本：27 pending direct_contact 指向 retired，queued 25→0，身份不变；根关闭而开放项仍在。 | 已读统一 local_delivery_closed 与生命周期入口：全对象/未决 merge；终态地址结清，sleeping 与改派不同。 | 方向成立，—。本轮未重开 B 的 DB；全范围关闭保留迟到 queued 的行为必须如实输出，不能宣称所有通知已消费。 |
| R24 | L/B 及既有 Sheet 无模型恢复：无 provider materializing 阻塞；原应用不变是关键反证/隔离。 | 已读 prepare_offline_resume：仅无 provider 的孤儿、校验现责任/版本，开放项重排，结束项收尾，原工作区保持。 | 方向成立，—。调用前必须确证旧执行停止；本轮不重复恢复。 |
| R25 | S 22 条429与余额/原生错误是具体故障，不是语义无进展推测。 | Pi 保留 stopReason/errorMessage；monitor 同路径连续错误与恢复边界，不自动换模型/取消。 | 方向成立，—。当前错误有原文；A03 负责来源隔离，不能把所有非 error assistant 响应称业务成功。 |
| R26 | S PR23 缺 shell exit 后18.7/17.2分钟重跑；不能把所有独立检查都算浪费。 | 完整读 with-service：check-only、首次退出保存、候选/context/log、信号和自有组清理；SVC 用内容/条件复用。 | 方向成立，—。既有实际操作反馈仅对当时 helper/应用；dirty 标记不是内容快照，调用者仍须给足候选前提。 |
| R27 | G/S 全局 pkill 影响邻居；个别损害仅时间相关，不能都归进程清理。 | helper start_new_session + killpg 自己的组，skill 要按所有者清理；不引入用户否决的沙箱。 | 方向成立，—。脱离组的应用自管服务不由外壳保证，SIGKILL 无最终回执是明确限制。 |
| R28 | T 跨设备硬链接4499行、浏览器路径猜测、socket 长度失败均为具体环境事实。 | 运行时浏览器路径和 skill 普通 copy/install/短 TMPDIR 解决相关假设，不创建新应用框架。 | 方向成立，—。下一制品路径存在与实际消费者使用分开确认；无净分钟收益证据。 |
| R29 | T status 427KB 与 collector 重建丢发送集合；SDK flush 并非逐条持久化。 | CLI Agent 只投影工作项，宿主仍诊断全集；evidence flush_succeeded/retry_since_flush 保留进度，telemetry 复用 collector。 | 有限核查、方向成立，—。本轮查相关函数接线未重审全部 OTLP；错误窗口重复/丢失需原始批次证明。 |

## 新增 12 项

| ID | 观测、竞争解释与原证据 | 当前机制、根因及边界判断 | 状态、严重度与最小补证/改进 |
|---|---|---|---|
| A01 | N 证明旧接口没有 pending provider，settled 可早于作业；L 明确尚无某次 job 遗失的完整收据。 | PBB 自持 provider/service/完成队列，层次正确；child 无 subagents 用自身 await 填缺口，但等待无上限。 | 待真实时序补证，P1，F3。不能以加载成功宣称完成消息闭环，先观察取消传播与 service 排除。 |
| A02 | L 原保留 DB：Assign consumed、新 session 无 turn；PR/reopen 有同形路径。 | objects 同事务补 Wake 且不继承旧 writer 防 OriginEcho；旧 owner stop 栅栏仍在。业务内容仍由已有工作项提供。 | 方向成立，—。本轮定向读 replace/create/reopen 入口及 L，不重跑旧验证；下一真实负责人首轮输入/旧退出可观察。 |
| A03 | monitor.md/T 描述旧共享目录误选、fresh 原生漏读；路径同名不能证明本次来源。 | 已读 monitor native()：sessions 索引、路径约束、cutoff/until、每路径 streak；来源选择代码有 current attempt/recovery 区分。 | 有限核查，—。本轮未重新消费完整真实监控样本；不把后续成功跨路径抹旧错误。与 R25 合并评价，不重复计收益。 |
| A04 | 用户批准视觉方法增强，不是对所有读图失败的单因诊断。 | 已读 vision 全文：类型/用途→事实/推断/未知，只读显式材料；不从参考图强推新需求。 | 方向成立，—。新角色效果待真实图像提取/父消费，不要求每张图全清单。 |
| A05 | 用户明确删除测试，不能再拿测试存在作为产品要求。 | git diff 显示测试模块/fixtures/入口删除；L 记录编译成功及只供旧测试函数清理。 | 有限核查，—。本轮未逐行核全部删除，不能独立保证零误删；没有重建测试或以探针替代。 |
| A06 | toolchain-proposal 有明确技术选择授权；并非证明不用这些库就必然低分。 | run.py 工程默认、runtime 固定命令/版本、正式逐目录 npm/Node20 协议；无 TS/Vue 强制。 | 方向成立，P2兼容性观察，F5。Node24 自检不足以证明 Node20 正式运行；不先构建第二套框架。 |
| A07 | T 路径猜测/重复安装真实存在，预打包只解决资源取得。 | runtime/Docker/build 提供命令/browser/cache；run 内 npm/pnpm 缓存，不改需求初始种子，不强制离线。 | 方向成立，—。新 Linux 制品未建，旧 ZIP 不能承接新源码能力。与 R28 合并计因果。 |
| A08 | G 安装未终态即依赖测试、重叠 rebuild/reset；并行本身不是问题。 | 已读 workflow 精确区分依赖先成功、独立并行与竞争写，没有禁止所有并行或增加系统语义调度。 | 方向成立，—。观察实际安装退出与后继调用顺序；预打包不会自动修这个问题。 |
| A09 | G 格式过滤无匹配误当没评论/管道吞首错；工具成功与观察成功不同。 | debugging 方法要求保留原动作状态，属于观察方法；R01 CLI 已另修已知直接歧义。 | 有限核查，—。已读 debugging 保留首错/退出码与结构化回读的正文；没有证据表明新 CLI 全部歧义已消除。 |
| A10 | G 同名/tmp与全局close、S邻居服务受影响；需要区分已证破坏和相关性。 | workflow 资源归属/影响通知、agent-browser 命名关闭与 helper 自有进程组互补。 | 方向成立，—。与 R27 重叠；shell 任意路径写入仍由调用者判断，不建议用户否决的隔离层。 |
| A11 | G queued 被当失败再写重复评论；已受理消息不能靠预想字符串匹配断言失败。 | workflow 要先读回；CLI 回执明确业务正文/消息状态，objects 保留 queued/delivered/reason，未加入语义去重。 | 方向成立，—。应观察同写入回执后是否读回原对象；无法只靠方法断言 exactly-once。 |
| A12 | 目录给出 getCellValue 的 DetailedCellError 与自定义函数 CellError 区别。 | 示例改 public return type 是窄文档修复，职责在 HyperFormula 技能，不改应用业务。 | 方向成立，—。已独立读取官方3.4.0 HyperFormula.getCellValue 返回 CellValue、CellValue.ts 的联合类型和 index.ts 的类导出；未运行示例，不归因最终失分。 |

## 去重与本轮范围

R11/R15/R16 共用恢复边界；R12/A01 共用等待但区分命名空间与存活事实；R25/A03 共用原生故障采集；R27/A10 共用资源归属；R28/A07 共用预打包；R04/R05/A08/A09/A11 的方法不同，不能只因都改提示词就混成一个根因。A04/A05/A06 是显式产品选择，不伪装成原分数的经验证因果。

本轮主要独立深读了 observer、PBB补丁、run.py、provider 指引、Pi/session恢复及 prompt 路径、dispatch恢复、store 的关闭/离线恢复、objects 的评论收件人/merge闭环、with-service、核心 SVC 方法与 vision/profile。其它相关源面按表标注有限核查。完整读过“所有 ID 的主张”不等于读过每个文件每行，也不等于完整行为验证；此差别保留在交付结论中。

A12 官方来源：[HyperFormula.ts](https://github.com/handsontable/hyperformula/blob/3.4.0/src/HyperFormula.ts#L779)、[CellValue.ts](https://github.com/handsontable/hyperformula/blob/3.4.0/src/CellValue.ts#L8)、[index.ts](https://github.com/handsontable/hyperformula/blob/3.4.0/src/index.ts#L150)。本轮只读取这三个固定版本官方文件，未执行代码。
