# 文档系统的具体断点

调查阶段只读开发侧 Corpus 15.0.1、当前工作树的长期文档、17 个任务入口及所列代码边界。
调查阶段没有修改长期文档、源码或 Corpus，没有运行 Factory 测试、模型或 benchmark。后续获批实施的结果归 plan.md。
工作区有并行变化：official_matrix 的旧 freeze 入口已被移除，原有调查描述不能直接充当当前事实。
下列结论是文件与调用路径核对，不是运行能力验收。

## 场景一：修改 mixed 的执行角色或技能

实际入口为 variants/pi-team-mixed/run.py 的 native_files、agents/<id>/profile.json、instructions.md、agents/*.md，以及 build.py。
profile.json 供 Braid 使用；内部角色 Markdown 供 Pi 扩展使用；主会话 skill 参数由 native_files 显式选择，角色 skill 由 Markdown 指定，build.py 决定哪些文件进入包。
CONTRIBUTING 只写了入口位置，没有解释这几种选择的关系。
只改 build.py 不会自动给会话启用技能，只改角色模型也不会改变 Braid assignee 的主模型。
模型具体值应继续以各 variant 原生文件为准；长期说明应解释选择发生在哪里，而不是复制四份模型表。

## 场景二：修改交付或 Runner 接入

scripts/braid_runtime.py 的 load_delivery/export_delivery 读取 Braid 的交付结果并从 accepted commit 导出；variants/*/run.py 将交付与诊断归档分开记录。
scripts/arc_bench_adapter.py 的 instrument_entry 在副本外添加标准入口，run 的两阶段分支用入口状态判断生成完成，再冻结应用并评测。
Runner 容器还会部署应用，所以 generation_code 不直接代表 Agent 生成是否完成；这一原因主要保存在 DX 调查/实施记录中。
scripts/local_experiment.py 的 execute 消费适配器 result.status；telemetry.received 只表示收到了批次，不说明会话覆盖完整或载荷可以被标准工具读取。
这些是多个组件共同依赖的约定，已经满足开发侧 Corpus 对 Product TDD 的准入条件。
当前 PRD/Deployment 分别包含部分内容，但没有一个清楚解释组件责任、交付链与不同终态含义的技术入口。

注释并非全面缺失：agent_support 对 macOS zombie 和 ZIP 权限的原因已有说明；braid_runtime.export_delivery 已说明导出 accepted commit 而非工作树。
应保留这些注释，只补实际信息缺口。
core.archive_sessions 会保存可归档内容并以 unknown/partial/complete 标记诊断覆盖；这一返回语义不能被消费者当成应用交付状态。

## 场景三：诊断一次当前实验

local_experiment.status 读取外层 run.json；Factory 的 show/analyze 读取内部 .factory26/<id>；raw 的过程归 .arc/raw；官网有独立 journal。
AGENTS 和 Deployment 的诊断起手命令仍无条件推荐旧 run_feedback brief，而其 _outcome 主要识别旧 status/outcome。
这造成两种问题：文档没有按证据生产者指路，读取设施本身也有尚未接通的格式。
本轮文档应写清当前可用路径和限制，不能声称已有统一诊断入口；格式接通属于另一次实现。
Viewer 通过 inspect_runs.list_runs 和特定官网/Playground 布局发现记录；不能把未被发现的嵌套运行说成未执行。

## 场景四：接续任务与处理需求纠正

AGENTS 的规则有信息归属意识，但仍残留“源码、配置和测试维护事实”；docs/index 仍提“回归检查”，与禁止 Factory/基础设施测试冲突。
PRD 的持续验收基线仍指某轮四 variants × 两题的 task 验收，长期产品要求因此依赖临时实验计划。
DX design 顶部宣布测试要求已删除，正文却继续推荐 make test 和 smoke；packet 同时保留“正在实施第一轮”和“第二轮未授权”的叙述。
这证明本任务自身也在追加纠正而非维护一份当前答案，应先修复自身 task packet。

17 个 packet 不代表 17 项正在执行的工作。
agent-profile-presets 已明确转到 multi-agent-integration，independent-variants 已由 DX 承接，svc-cli-simplification 已转到 skill 接线。
svc-corpus-review 与 svc-skill-integration 均明确还有未完成验收，不能关闭。
local-run-analysis 已声明完成盘点与报告，可列为历史结果导航候选。
dual-bench-hosted/raw-core-local-baseline 含远端状态和运行恢复信息，本轮没有查询平台或进程；不能根据文件时间宣布它们结束，也不能改其操作恢复点。
competition-p0/local-official-bench 等旧 packet 有“生产 Runner 未提供”等阶段事实，与当前公开 Runner 路径并存；应标清历史阶段与后继任务，不将旧前提继续用作当前操作指令。

## 场景五：在另一机器继续开发

runtime.py 的资源准备已经独立；开发 .venv/bin/svc 和被忽略的 sources/ 仍依赖机器已有状态。
文档应区分开发侧完整 SVC 15.0.1 与参赛侧已改写 Corpus 的来源和用途，并说明未经发布的本地源码修改不会随父仓库 clone 自动出现。
本轮可以明确现有来源、调用位置与恢复缺口，不能用“clone 上游 main”冒充精确恢复，也不能未经授权替上游工作树提交或发布。

## 使用的 Corpus 内容

开发 .venv/bin/svc lookup：specs/、specs/product-tdd/index.md、task-packet/information.md、taste/implementation/index.md。
这里借用其信息归属、消费者及注释理由的原则，不照搬模板；用户禁止 Factory/基础设施测试的要求优先。
参赛 Corpus 的裁减规则不直接用于长期迭代的开发仓库，本轮不改任何 Corpus 正文。
