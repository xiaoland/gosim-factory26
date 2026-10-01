# I12：连续工作、明确协作操作与人工语义诊断

2026-10-01 当前状态纠正：[WSL清理执行记录](../../runs/wsl-retained-20260930/README.md)在最终步骤明确记载，I12已被主动终止，随后WSL干净关闭、VHDX从480.62GiB压缩至71.17GiB，Debian保持停止。以下9月30日暂停/恢复记录属于历史阶段，不能继续当作当前仍存活的现场。项目内 `runs/wsl-retained-20260930/i12-current/` 保存约19:39捕获的文件快照及control在线一致DB备份、Git bundles、worktree映射和dirty patches；该采集点不等于最终终止点，也不是完整机器备份。现阶段以归档取证，不自动复活旧I12；WSL环境修复另按用户修正后的目标讨论。

2026-09-30。当前阶段：两题已按用户“可以暂停 I12 了，内容已经太多，我已经看到很多问题”整体暂停。15:59:13 CST确认两个容器Running=true、Paused=true，冻结全部容器内Agent会话与Braid定期检查，不取消、清理或自动恢复。代码、Git、对象及原生会话保留，暂停状态的数据库文件另存；部署身份与暂停回执以 [从零重启](restart.md) 为准。两题此前15:14:51/52 CST分别取得真实GLM响应及成功工具结果；原12:25:47 CST现场保留为退役证据。核心修复及新版Console已落地，Console整体暂停/恢复能力已登记到I13、尚未实现。
授权原话：“其它的各项处置我都同意，请你应用它们为 I12 并且从 I11 的运行状态中再次进行摘剪……另外 I12 还实现一个实时的可交互的 web console”。

## 目标与边界

减少上下文整理重新制造工作、冲突验收纪律与讨论操作范围歧义；让用户在本轮通过原生Issue/PR语义介入，发现更深语义问题，再从真实交互提炼指引。
I12是独立variant，不覆盖I11冻结输入与证据。模型及凭据沿用本地I11自有API配方。
人工介入是本轮实验条件，console属于开发工具，不进入无人值守参赛制品；本轮不得自动正式参赛。
最新修正：“Braid console建议重新制作……有独立的目录（不需要额外的git repo）……至少不是plain HTML/CSS/JS”；“计划让I12从0开始实现，而不是I11的裁剪结果”。两题不继承I11应用、Issue/PR、Git与原生会话；复用的是工具环境和冻结Harness。模型、两份官方需求及资源配方保持不变。
不新增或运行Factory/Braid/SVC/设施测试、模拟探针；通过编译、语法、真实对象操作及已授权生成观察取得反馈。

## 实施树与分工

```text
I12
├─ 1. Braid连续性与操作范围［i12_braid_continuity］
│  ├─ 区分上下文更新、未完成处理的接续与真实新输入
│  ├─ 自编辑/自然完成不重新制造处理请求；中断与新消息不丢
│  └─ resolve/unresolve说明thread根、范围、变化；局部整理用hide理由
├─ 2. 工作材料［主线］
│  ├─ 删除“新SHA本身不使证据失效”的专门规则，保留变化与证据的判断方法
│  ├─ 历史交付记录不镜像全局最新状态
│  └─ 清退摘剪对象中冲突的“head变化即全量重验”纪律
├─ 3. 从零生成［i12_runtime_deploy］
│  ├─ 原摘剪尝试cancelled，保留证据与前期CLI/消息核验
│  ├─ 同需求、自有API及4GiB/2CPU，标准入口初始化空应用/Git/Braid/会话
│  └─ 复用共享runtime，不重复安装runner和浏览器；真实空seed、新对象与模型响应已核实
├─ 4. 交互console［i12_console_rebuild］
│  ├─ 独立braid-console目录，React/TypeScript/Vite/Ant Design/TanStack Query
│  ├─ 实时查看Issue/PR/负责人/讨论，编辑、评论与thread回复
│  ├─ 写入复用Braid CLI外部对象事务及通知机制
│  └─ 记录人工介入来源；显式registry控制读写，旧摘剪只读
└─ 5. pi-minimal验收技能支线［pi_minimal_verification］
   ├─ 仅svc-verification及其references，不引入Braid/其它SVC技能或新角色
   └─ 原生接线已落地；后续单独授权的官网GitHub自费运行见pi-minimal packet，不接续I12
```

## I11 GitHub评分归因的新增消费

用户要求：“是否有i11 github的评测的分析结果，如果没有，请安排分析，找到的问题也纳入i12。”
已有独立定向报告确认最终应用正常送达和启动，并追出跨对象需求承接悬空、需求编号覆盖被误用为行为覆盖；它不能解释全部96项失败。
问题账已有I12-G01/G02/G03。用户补充的“最终审查沿用mapping”和“失败日志、旧成功标签与packet错配”经补齐的PR23原生过程确认，登记G04/G05；两题共有的重复核查及提交变化误判统一登记E01/E02。通用修复归属、实际投递与待验证边界以 [问题账](i11-github-score/findings.md) 为准。
主线完成方法/角色入口核对及独立材料调查后，用户明确要求“那么将G01/G04/G05纳入I13的范围内”。这三项连同 [具体方法方案](../iteration13/quality-methods.md) 转交 [I13 packet](../iteration13/packet.md)，保留原编号和证据。G04/G05现已融入SVC V&V元理论改写（`31906a5`），尚未部署到冻结I12；G01及角色接线继续由I13推进，不以E01/E02已经部署代替质量问题闭合。I12从零生成随后按用户要求暂停，保留既有修复与采用证据，不改变冻结制品或清理现场。
原Astra medium补充调查已按用户新指示中断并保留提取材料，改由GPT-6 Astra / xhigh接续整体低分及I12未闭合问题的根因分析。独立调查已返回 [综合报告](root-cause-review/report.md)，包含需求与验收共用错误前提、Pi配置根/session目录混用、watch结果消费缺口及I12连续性的实际行为证据。主线已按新从零授权部署Pi目录、成员指派及历史成果职责修正；质量方法按问题账继续区分待修与采用未证，不以报告返回或启动成功视为全部修复完成。范围、分工与证据边界见 [根因排查cell](root-cause-review/packet.md)，原 [评分调查断点](i11-github-score/investigation.md) 作为交接入口保留。

## 成员指派修正已完成并进入新从零运行

用户针对具体范围授权：“这点不需要分析了，直接修改”；进一步要求“按配方，委派一个后，按序号递增，虚拟下一个assignee”。
对象及CLI由 `assign_members_impl`（GPT-6.1 Sol / high）实现，主线同步provider与I12成员指引，并在真实归档副本核对候选查询和指派；不写或运行测试，不启动模型。
每配方独立提供下一位虚拟assignee，读取不占号，成功指派才认领并递增。编译及实际归档副本CLI操作通过：`glm-17 → glm-18 → glm-19`，`deepseek-24`不变；重复当前成员幂等，裸配方名与已认领名字明确拒绝。完整回执及未覆盖的运行行为见实施记录。
范围为下一位虚拟成员、事务内认领、输入/回执/负责人同名、帮助及指引；调度容量、原生子代理、工作区和旧writer交接边界保持。
此项最初仅获源码修改授权，没有更新暂停现场。随后按新的从零启动授权，连同Pi目录修正冻结为Linux binary `38c68450fa93399e7dabd3c4c912410a503e59152cb13f3d3c724ce7d9fc708d`，进入当前新运行；旧冻结binary保持不变。见 [方案](assignment-members.md)、[实施记录](assignment-implementation.md) 与 [部署](restart.md)。

## 推进与验收

先核实实际调用/API和分支，再并行实施；核心源码预演反馈已明确自然完成和reset结算竞态，不能只改消息措辞。
Console使用明确的当次binary/state身份；从零使用标准variant入口，不使用continue-in-place。保留已有runtime，避免重复复制安装工具。
验收包括Linux编译、真实CLI读取/写入回执、浏览器实际查看和操作指定I12对象、真实模型响应/消息消费。既有检查结果保持原始归属，不将复制/Running或模型自述当产品完成。
启动前检查模型路由、版本、恢复身份和人工介入标记；沿用3+8周期观察，不把每5秒页面刷新变为Agent调用。
原始I11两题已核实交付：GitHub main `442dc1cf776f144688d8ad667a76dd026f553e27`，Sheet main `10cba2ad888fd60f283382158c1bfb00b0fad240`；两者根Issue关闭，最终PR合入，生成出口成功。
按用户“既然交付……尽快上传到官网进行评测”的指示，冻结同一应用重放包，SHA256 `bc4cab139ed9cf3c282a1b3359ed1d6a8e5f552dcf13efda30144a44fb5076fc`。
官网 submission `87acf1919de7`，Sheet run `fe617f4f8526`（59/100），GitHub run `e68661975b53`（4/100）；均为 `self_funded`，部署、应用启动和评分阶段完成。重放不调用模型，不重新生成，不将隐藏评分反馈带入I12。原始journal见 `runs/iteration11/final-replay-20260930/official/`。

## 当前实施状态

最新启动授权覆盖GitHub/Sheet从零本地生成，两题各4GiB/2CPU，沿用自有API原配方与3+8观察，不运行本地评分；每題交付后独立self_funded官网重放。启动前带入新成员指派机制，修正已证Pi配置根/session目录冲突，补齐已经批准的历史成果与整合状态分工材料投递；为既有watch指定结果消费者。旧暂停现场保全后停止旧外层与容器，避免两批模型同时运行。新的质量方法结论仍按根因报告和问题账区分采用证据与未批准候选，不以此次启动视为全部发现已经修复。

先前指示：“不，请先暂停I12”。当时已核对容器身份并执行Docker pause，GitHub与Sheet均确认 `Paused=true`、无OOM；未取消、清理、重建或改动应用/Braid/原生会话，不影响pi-minimal。回执为 `runs/iteration12/fresh/pause-receipt.json`，Mac与WSL各保留一份。后续从零重启不是恢复这些旧模型；退役处理见restart记录。

Braid Linux编译完成；自编辑及自然完成后的reset只更新Context，真实中断保留接续，讨论resolve回执明确范围。
SVC专门的SHA规则已移除，保留按相关变化与实际条件判断证据的方法，I12角色的交接指引已收敛。摘剪正文改动仅属于退役现场，不会带入从零生成。
Console新版位于独立braid-console目录，React生产构建通过，旧plain页面及执行路径已移除。当前只登记两个从零现场并允许人工介入；暂停后的CLI桥已改为每题独立访问容器，保持原数据库、Git路径和冻结binary身份。两题列表、根Issue与已有PR详情的真实HTTP读取成功；此次没有发表测试评论，写入效果尚未实测。入口是 http://127.0.0.1:8765/；部署及旧评论证据归console记录。
原I12摘剪尝试：GitHub run `pi-braid-i12--hackathon--github-690b8b3f871be2`，Sheet run `pi-braid-i12--hackathon--sheet-6c9d2806b4fac4`，已按最新决定cancelled/exit-15，容器不存在、cleanup完成、gateway绑定撤销，workspace及全部原生证据保留。停止前两根已有真实模型响应并成功读取#333/#567，wake为consumed；说明前期console消息接线可用，不是完整生成验收。证据见 `runs/iteration12/deployment/stopped/receipt.json`。
先前从零GitHub run `pi-braid-i12--hackathon--github-715fa714f396de`、Sheet run `pi-braid-i12--hackathon--sheet-8559b80ecb7f15` 已退役保留；其自然完成reset及真实评论消费是E01的历史行为证据。当前运行为GitHub `pi-braid-i12--hackathon--github-4ad2b95fc11c89`、Sheet `pi-braid-i12--hackathon--sheet-ab453a24432a17`，分别于15:14:51/52 CST取得首个真实模型响应与成功工具结果。每题新空Git seed、新DB和独立原生目录，各4GiB/2CPU，自有API模型配方不变，3+8 watcher持续采集。评分仍使用冻结应用官网self_funded重放；尚未交付或评分。完整身份见restart.md，不再将退役run写作当前执行。
pi-minimal支线已显式接入完整svc-verification与references，主会话及独立advisor可按问题读取；保留agent-browser快速反馈和主会话自动化最终验收。源码及材料路径核对完成，没有更新现有冻结官网制品或启动支线实验。
父仓库I12实现、console及导航提交 `86ec49e`。Braid/SVC本次改动叠加在之前已批准但尚未提交的I11材料上；没有可靠开工前基线用于分离时，不猜测暂存或夹带提交。运行身份来自完整dirty源码冻结及材料清单，而非声称HEAD等于制品。

## 产物入口

- [Braid修复](braid.md)：实际边界、代码与编译/行为证据。
- [恢复摘剪（已退役）](recovery.md)：来源、取舍、变更账和限制。
- [Console](console.md)：接口、部署与实际操作证据。
- [WSL部署](deployment.md)：材料刷新、资源、真实响应与监控回执。
- [pi-minimal验收接线](../pi-minimal/verification.md)：支线范围、实际采用方式及未验证项。
- 原因原始材料：[I11补充归因](../iteration11/runtime-stalls/packet.md)。
- [I11 GitHub评分问题账](i11-github-score/findings.md)：已有定向报告、已证问题、补充分析与I12消费状态。
- [I13需求责任与验收方法修正](../iteration13/packet.md)：G01/G04/G05已转交；后续V&V元理论、内容与导航改写获单独开工授权，角色接线及其余单元仍按I13状态推进。
- [I12未闭合问题根因排查](root-cause-review/packet.md)：Astra xhigh报告已返回，区分已证根因、待验证与证据不足，修复尚待消费。
- [指派直接选择成员名](assignment-members.md)：源码及实际CLI核对完成，每配方独立递增的下一位虚拟assignee，已进入新从零运行；旧现场不改动。
- [原生目录修正](native-directory.md)：配置根与活动session存放目录分离，历史记录不迁移；真实子Pi启动后的文件连续性待新运行验证。
- [从零重启](restart.md)：本次启动授权、旧现场保全、新冻结材料、两题身份与监控回传。
