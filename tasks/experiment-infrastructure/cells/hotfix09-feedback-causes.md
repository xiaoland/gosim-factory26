# 09 前置诊断：Sheet 08 检查成本的上游机制

本页是只读诊断，不是修改方案已实施或纯 Harness 实验结论。证据窗口为2026-09-28 06:44:20–约07:22 UTC；原生文件读取时运行继续，引用均给明确消息时间。没有启动任何应用、检查、探针或模型，没有修改运行、源码或工作树。前置事实及退出码修复见 [Sheet08进展](../../braid-product-reaudit/cells/attempt08-sheet-progress.md)，成本口径见 [token截面](token-economics.md)。

根目录 `R` 为 WSL `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/workspace/official-generation/template/.factory26/20260928-025746-66feadac/`。提交从 `braid-state/origin.git` 只读查询；会话按下列UUID定位 `work/native-homes/*/2026*.jsonl`。不把旧提交、评论自称通过或PBB外壳exit0单独当作08产品验收。

## 关键判断

成本不是一个“Agent太爱写检查”原因。两条链显示：独立工作树保护了改动边界，却各自承担构建和服务；共享启动脚本、契约及候选连续变化，令旧证据失效；自建多服务watchdog又引入清理竞态和退出码错误；长TMPDIR使绕开检查入口的浏览器调用启动失败。与此同时，存在真实产品修改和检查前提纠正，不能把安装、重跑和诊断一概删去。

08已带 `agent-browser/SKILL.md` 与5119字节 `scripts/with-service.py`。本次对06:44:20后可见原生toolCall参数定向搜索，未见 `with-service` 调用；约07:22截面只找到一次读取该SKILL（REQ2，07:20:58），随后实际调用agent-browser。故“已安装”不等于“已发现并采用”；没有证据认定两条代表链已经读过工具却拒绝使用。反过来，这不是新增同名工具即可解决的缺口。

## 链一：moveCells 的候选推进与重复干净构建

父session `01a0e6c2-187b-710b-bf5b-71187eb36207`，工作树 `braid-state/worktrees/issue-5/pi-deepseek-fast-g1`。这是继承的工作树，本次没有定位最初创建记录，不能把08恢复视为新建一套任务。

| 环节 | 实际证据 | 成本解释 |
| --- | --- | --- |
| 接续工作树 | 06:44:40 fetch并读origin/develop；06:44:58 merge新基线；06:45:14检查backend/frontend/checks/shared的node_modules及run.sh | 并非一直不知道共享基线已更新；有主动消费。单纯“再提醒fetch”不是完整解 |
| 本地构建/服务/浏览器 | 既有 `checks/run.sh` 执行；06:57:56读取真实日志为31passed、1skip、10.0m，原job exitCode0。skip是REQ2结构undo依赖 | 这轮覆盖moveCells和validation写入，具有真实用途，但不证明尚未集成的结构undo |
| 合入共享变更 | 06:57:58再次merge，06:57:59提交 `21b627b` 消费PR12 bootstrap及当时develop | 旧PASS对应此前候选；共享build/dist变化使“从干净环境能构建”成为有根据的新问题 |
| 第一次干净clone | 06:58:13 clone到 `/tmp/issue5-clean`；返回证实frontend node_modules和shared dist均不存在；06:58:22 frontend install/build，06:59:28 backend install，06:59:56 checks install，随后全套检查 | 重装是刻意核对干净交付，不是工具莫名丢依赖。安装隔离与产品初态隔离不必永远绑定，但此次bootstrap刚改，有真实必要 |
| 新产品/契约变化 | 07:12:45父说明补dropdown seeder和blank-field回归；`77df566`按共享裁决使空/纯空白输入不被规则拒绝；07:17:58 merge含PR16的新develop，07:18:09显示 `4950509` | 第二次复验不只是“又看到检查修复就全跑”；产品validation也改了。不能把整轮判为可避免 |
| 第二次干净clone与反馈 | 07:18:41 clone `/tmp/issue5-final`；07:19:37 frontend install/build；07:21:05 backend install、随机端口及独立DATA_DIR启动；07:21:33清理服务再安装checks；07:21:40启动全套 | 每个新候选都重做干净安装的边际收益应按bootstrap/依赖是否改变判断。这里最明显的优化机会是分开安装自举证据、validation行为证据及最终集成证据，不是省掉后两者 |

原生命令还出现 `git merge ... | tail -N; echo EXIT=$?`。若未启用pipefail，该EXIT描述过滤器而非merge；同样PBB显示外壳exit0不证明内部套件通过。此前已实际出现 `29 passed`、内部 `RUN_EXIT=1`、外壳exitCode0并存。因此收窄回显必须保留原命令状态，不能为了小输出牺牲失败语义。

**基线为何没有瞬时扩散：** PR16于07:14:22才合入；moveCells在07:17:58主动消费，约数分钟后进入新验证。同期个人树/克隆有既有长检查在跑，它们应保持被检查对象稳定，不能中途改脚本。07:18旧tree仍旧helper只证明该候选旧，不证明成员未读通知或调度故障。REQ2和PR15具体为何尚未同步，现存截面不足以区分在跑检查、分支整合负担或消息延迟。

## 链二：CSV 回归与自建服务生命周期的连锁修补

父session `01a0e6c2-0361-7254-b391-9b84cfe2a710`，工作树 `issue-3/pi-deepseek-fast-g1`。该成员承担CSV，后来承接共享检查清理的窄回归；不是在08从零建立检查设施。

1. **已有设施背景。** `266f0e4:checks/run.sh` 明确每个spec一个独立DATA_DIR、backend及端口，避免种子/运行日志互相覆盖。SUFFIXES含CREATE、EDITOR、HOME、CSV、REQ3_CORE、REQ3_INTEGRATION，共6个服务；Playwright配置workers1、retries0、单测timeout180秒、expect30秒。顺序浏览器worker并没有消除各检查运行之间的并行。
2. **为何写watchdog。** 脚本注释写明应对外部脚本杀掉服务，按同端口和DATA_DIR重启并记日志。原始watchdog写入前的首次杀进程证据本轮未追溯，不能把注释当根因实证。已证的是它后来成为实际代码和新的清理竞态来源：旧 `fcbb114` 修成先停止并等待watchdog，再清理本run服务。
3. **08的检查自身问题。** 06:45创建PR14只加cleanup-race-check，不改业务；初版根据公告行单次找victim会遇到尚无live pid的窗口。06:50:18读取PBB真实日志，两次修后均 `RACE_CHECK_PASS` 且RUN1/2 EXIT0。提交 `6b34914` 增115行脚本与README，06:51:53合入develop。额外 `/proc` fallback 未继续加入；该问题已有收敛，不宜再因理论场景扩展工具。
4. **绕开共享runner做CSV定向复验。** 06:53:31调用临时 `/tmp/csv-reverify.sh`，使用独立seeded server和浏览器CSV项目；Chrome实际06:54:09 FATAL `Socket path too long`，父06:54:49读到日志。此前套件runner设短TMPDIR，这条直接调用没有继承该约定。改短TMPDIR后06:56:12观察CSV3passed、52.5秒、CSV_PROJECT_EXIT0，服务仍活着并收尾。这是环境条件造成的重试，不是CSV业务修复。
5. **消费不应只看表面PASS。** 另一个PR8父发现原run.sh cleanup中lsof无监听退出1，在set-e/pipefail下覆盖套件成功；修复 `1be21ec`经PR16合入 `1d7eca7`，窄回归修前FAIL/修后PASS、合并候选再次PASS已由原生证明。修公共helper同时覆盖启动等待、watchdog和cleanup调用，优于各分支继续手写小补丁。

这条链表现为“为了稳住隔离检查而构建运行管理，再修运行管理”的成本。隔离DATA_DIR有产品前提依据；把全部服务预先常驻、遇服务消失就自动复活，则是可重新讨论的生命周期选择。若检查不要求服务自动恢复，服务死亡本应作为清晰环境/应用失败被保留，而非默认重启后继续宣称同一条观察。是否替换既有runner仍须看其真实消费者，不建议在09恢复时未经评估全换。

## agent-browser / with-service 的能力与采用边界

08冻结 `work/skills/agent-browser/SKILL.md` 已明确可选with-service：指定cwd、服务命令、HTTP就绪、执行检查、保留日志和退出码。它不是业务验收skill。现有实现为一个受管服务加一个检查进程，检查期间服务退出即报service_error，按进程组收尾；没有自动重启、没有一次组织六服务的接口。

因此它能减少**新的一次性单服务检查**的nohup/PID/日志/退出码手工代码，不能直接承诺替掉现有每spec一服务的整套runner，也不能自动修复Chromium长TMPDIR。实际安装事实与方法覆盖可以核实；这两条链没有with-service调用证据，故分类是“可发现入口尚未观察到读取/采用”，不是“正文已采用但仍无效”。

07:20:58 REQ2实际读skill，07:21:01执行 `agent-browser skills get core`，随后命名session、open/snapshot/click用于探索。它证明该入口能够被找到；这不代表CSV/moveCells早先已读，也不代表最终Playwright脚本应改成Agent操作。探索与可重复检查的分工是合理的，工具名称不同不是成本根因。

## 并行和资源竞争：证据及竞争解释

真实07:02:50进程查询见多个lane的Playwright/run.sh，server进程计数22；run.sh本身每次启动6个backend，浏览器配置单worker。09前置环境已知4GiB/2CPU。由此可以确定**同时存在多份服务与检查资源需求**；多工作树独立不意味着计算资源独立。

但本轮没有同期CPU使用率、CPU throttling、内存压力/OOM、浏览器调度延迟或相同候选串行对照。不能断言10分钟全套是CPU争用造成，不能给资源损耗比例。已证的CSV失败是socket路径，退出码假失败是shell语义；两者不依赖CPU饱和。服务消失可能由其他清理命令、应用退出或资源压力造成，未得到区分。

优先决策不是再次增加timeout/watchdog，也不是无证据加全局调度器。先让检查需要的服务随真实寿命存在，服务退出保持原始原因；同时将完整集成验收归明确候选，局部改动用能区分问题的反馈。在仍有不明慢/消失时，才由既有可观测数据判别资源条件；本页不要求造负载或新增探针。

## Corpus、入口和工具的归因

| 现象 | 当前证据支持的分类 | 对应决策 |
| --- | --- | --- |
| 宽进程回显、重复sleep查job | investigation已有决策导向、notification/wait原则，但具体执行仍出现宽查与轮询；未逐会话证明读过正文 | 窄化现有方法到范围/字段/完成信号，保留原错误；不新造等待SOP。按真实调用确认改善 |
| 已合入基线在个人tree未同步 | 候选隔离、持续合并与运行中的长检查可解释一部分；不足以确诊通知bug | 交接“已合入哪一候选、哪些消费者受影响”，消费者在安全边界同步；不把同一时刻所有树强制更新 |
| 全套PASS与退出码矛盾 | 工具反馈冲突已有确定shell根因，并由Agent修复 | 保留PR16，消费新基线；不要把“读更多verification”当修复 |
| 浏览器长TMPDIR崩溃 | 环境公共配置真实缺陷，应用runner局部绕过 | 由09环境热修处理，别在所有角色重复贴TMPDIR特例 |
| 私有runner重启/清理越做越多 | 服务所有权与生命周期设计复杂度；with-service已可用但未见采用，且非整套替代品 | 在单服务临时检查可复用既有工具；多服务需求保留必要隔离，审查自动重启是否掩盖失败，不再多写一套wrapper |
| 两次干净clone、安装、复验 | bootstrap/产品validation/候选都曾改变，部分必要；每个变化都全量重建仍有优化空间 | 安装可复现性、行为反馈、最终候选集成分别拥有证据；按改变的依赖与行为复验，不能以省token跳最终验收 |

## 能减少成本的共享边界

共享契约、bootstrap、检查生命周期helper适合有明确唯一维护入口；功能成员消费其版本和已知范围，避免在各分支复制实现。当前PR12/16已朝此方向收敛。功能工作树和可变数据保持隔离，以免一个lane污染另一个；工具和方法知识可共享，安装/构建结果只有在版本与输入仍适用时才能复用，不盲目共享可变node_modules或运行中dist。

最小方法改进是明确“这次改变使哪些旧结论失效”：bootstrap刚改需要一次真实干净安装；validation变更需要受影响行为检查；最终集成还缺用户旅程则必须补。别人已提供同一候选同一条件的有效结果时，消费者先判断适用性，不默认重装重跑；缺实际结果、出现矛盾或候选变化则保留必要复验。这属于当前V&V/委派消费方法，不应扩成统一验证控制面。

本页的建议不含直接改运行：09仅应集成已确认的环境修复和已有Agent检查修复，再用真实接续看结果消费是否改善。未知仍包括watchdog最初触发现场、缺失的工具阅读历史、REQ2旧基线未及时消费的准确原因、资源竞争因果、各次重装中可省的净时间。没有证据就不把这些写成已定位的Harness根因。
