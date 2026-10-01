# I12 未闭合问题调查断点

2026-09-30，主审 `/root/i12_open_roots`，GPT-6 Astra / xhigh。仅调查及本 cell 文档整理；不恢复、启动、取消任何运行，不触及暂停容器，不改源码、应用、DB、原生记录或冻结制品，不运行设施测试、模型或评分。另一条 pi-minimal 运行不在范围内。主线持有 packet.md 与评分总账，本 cell 只写 investigation.md、report.md 和有界证据摘录。

## 当前计划与决策问题

1. 复用 I11 最终身份及已证 PR 里程碑承接/覆盖缺口，不重做下载和哈希核对。补查能够共同阻断大量用户路径的认证、入口、数据前提：先核公开需求与最终成品，再回查决定和自验收是否绕开同一前提。有实际冻结应用运行环境才进行隔离操作，不为取证重装环境。无法取得官网逐例错误时，不能分配96项失败原因。
2. 以 I11 已观察到的自编辑/自然完成重复唤醒和讨论误折叠为反例，核 I12 冻结实现、实际事件和原生链。区分机制变更正确性与行为采用；无触发样本不宣称解决或新增缺陷。
3. 核实际 provider 材料和工作项，判别专门 SHA 规则删去后，证据适用性与历史正文职责是否仍冲突。
4. 定向核首次 native 缺头、终态回传断链和暂停 Console 边界的生产者/依赖链。宿主只读取证；不 docker exec 暂停容器，不发表评论。
5. 形成综合因果报告：已证未修、修过待行为验证、证据不足分开；说明同根因、优先级、最小合理归属与下一轮判别证据。

## 已复用与读取

- 已读 AGENTS.md（无 AGENTS.local.md）、agents/run-analysis.md、root-cause-review/packet.md、iteration12/packet.md、Ponytail skill。
- 已读 tasks/pi-minimal/github-score-analysis/i11-e68661975b53.md、causality.md；后者只作既有历史分析，不触及其它在跑 pi-minimal。
- 已读 I12 braid.md、console.md 及 deployment.md 前段；runtime-stalls 与广义审查输出部分截断，后续须按具体问题重读，不计完整覆盖。
- 评分证据根 E=`runs/analysis/i11-github-e68661975b53/20260930T033923Z/`；生成归档 G=`runs/iteration11/20260930-completed-turn-resume/github/source/template.tar`。
- I11 旧补查摘录位于 `tasks/iteration12/i11-github-score/`，只当线索，尚未裁决；不修改其 findings.md。

## 断点

正在沿公开需求与最终应用的公共入口核验补查线索，同时准备只读抽取 I12 暂停现场的事件、物理指令和原生文件元信息。没有进行任何源码或运行状态变更。

## 中段断点（13:18 CST）

- I12 暂停现场已只读保存 `i12-paused-evidence.json`、`i12-native-selected.json`；四次根自编辑 reset 均 continuation=0/applied，各两次真实外部评论的后续 turn 完成。旧说明“无行为样本”需要收窄。PR2仍在原turn且reset interrupting，暂停不当成失败。
- 首次 native 缺头已找到生产路径根因：Braid `--session-dir=PI_CODING_AGENT_DIR`，Pi 0.85.1 启动 migrateSessionsFromAgentRoot 将活动文件挪至 sessions/encoded-cwd，继承配置根的子 Pi 启动是四组共同断点；父进程 append 按旧路径重建无头后段。两段 parentId/ID 全部连通，无重复ID与未解析parent；不能说内容已丢，但单文件归档/冷恢复身份有真实隐患。部署源代码保存在 `deployed-materials-and-runtime.json`，对应结构统计 `native-split-correspondence.json`。
- 实际技能含证据复用及并列对象检查方法；历史成果不镜像全局状态只落在Braid技术文档，未进入此次 provider 指令。尚无 I12 完成交付后的镜像/重验触发样本。
- I11 冻结应用已在 WSL `/tmp/factory26-i11-root-review` 隔离副本实际运行。未改原应用、DB或冻结包；依赖复用旧摘剪现存node_modules（三个package.json逐字匹配），构建只写临时副本；Node24初试因已安装better-sqlite3为Node20 ABI失败，随后只读docker cp现有已知暂停容器的Node20二进制到临时目录（没有docker exec、unpause或状态变更），Node20.19.3启动成功。浏览器实际从首页选可见Sign in登录、刷新会话、搜索并进入acme-docs成功；严格不加范围的Sign in locator真实匹配两个控件。原始结果 `i11-entry-operation.json`。重复入口没有公开唯一性要求，暂为官网共同setup失败候选，不列已证产品缺陷。
- 补查发现组织场景指定Acme Demo/acme-docs，最终应用把acme-docs放个人名下、组织改为org-handbook；原始#73裁决、最终自验收与实际UI都采用后者。正在复核需求前提替换及证据边界；组织操作首轮错误等待一个并不存在的网络过滤请求，保留attempt1并改为观察真实No results。此为调查脚本观测假设错误，不归咎应用。
- Console只GET不触发CLI的/api/runs，读取既有log确认暂停期对象端点400。Watch最新仍running/clear，原启动方式为detach+文件重定向，没有终态返回消费者。`console-watch-observation.json`。
- 主线后续另获assign直接成员名改动授权，本cell移出该主题；分析一律以冻结190c74…，不读源码修改中间态。

## 完成与交接（2026-09-30）

综合结论已写入 [report.md](report.md)，本 cell 不再保留未完成调查步骤。此次没有实施或恢复授权，不存在等待执行的修复。主线应据报告完成用户复核和总账归并；本 cell 未修改主线 packet、评分 findings 或顶层 packet。assign 已按主线要求完全移出分析。

新增结论：组织 seed 原场景被内部约定替换，真实 UI 取证成立；双 Sign in 仅保留共同 setup 失败假设。I12 四次根自编辑自然完成的 reset 均 applied / continuation=0，四次后续真实外部评论完成处理；Sheet PR #2 在 interrupting 期间仍读取新的根评论，因此不能继续概括为全无连续性行为证据。真正中断、失败及重建提交瞬间交错无完整样本，保持未验证。native 目录冲突、watch 回传消费者缺失、资料职责未投递和 Console 暂停依赖分别判定，没有合并成 Braid 语义故障。

报告证据目录内保留 JSON 原文与路径/哈希；独立应用副本在 WSL `/tmp/factory26-i11-root-review`，临时服务器已由操作脚本 finally 关闭。没有运行设施测试、模型、官网评分，也没有触碰另一条 pi-minimal 官网上运行。
