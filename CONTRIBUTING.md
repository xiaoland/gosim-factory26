# 开发 Factory26

开发者是 Coding Agent，用户参与目标、设计与授权。常驻约定见 [AGENTS.md](AGENTS.md)，本页帮助定位改动；组件的本地 README 持有实际接线和操作方法。

## 修改对象与反馈来源

反馈来自编译、实际操作和获授权实验；不维护 Factory、Braid 或开发基础设施测试。完整反馈边界归 [AGENTS.md](AGENTS.md#工作知识与反馈)。

| 修改对象 | 源码入口 | 实际反馈来源 |
| --- | --- | --- |
| Harness 的指令、角色、协作或执行 | `variants/<name>/main.py`、`run.py`、`agents/` | 生成运行的原生配置、会话与应用，获授权的 bench 得分。 |
| 原生工具或打包 | `scripts/runtime.py`、variant 的 `build.py`、`scripts/package_agent.py` | 实际安装、构建与提交过程的输出。 |
| 实验命令、定义编译与环境解析 | `lab/exp/__main__.py`、`compiler.py`、`environment.py`；记录版本归 `core.py`。 | 公开 CLI、冻结定义及环境解析回执；合同见 [Lab](lab/README.md)。 |
| 准备条件、保存状态、阻塞与下一动作 | `lab/exp/readiness.py`、`projection.py`；可用动作由 `controller.py:available_actions` 判断。 | `doctor` 的实际只读观察，`status`/`monitor` 的保存事实与原件时间。 |
| 实验执行与控制 | `lab/exp/controller.py` 调用 `runner.py`、`backends.py` 或 `hosted.py`。 | 所属冻结执行器的回执、实际进程和平台错误；低层函数不是绕过控制门控的操作入口。 |
| 材料引用与 Harness 定义/state 布局 | `lab/exp/artifacts.py`、`scripts/harness_layout.py`。 | 实际制品、捕获和装配回执；不以目录存在证明完整可恢复。 |
| Pi 子代理观测 | variant 的 `extensions/` | 实际会话和原始观测记录。 |
| Braid | `sources/braid` 自身说明和公开 local 接口 | 自身构建和实际 Harness 调用结果。 |
| SVC skill 接线 | variant 的启动参数、角色 Markdown、`build.py` | 运行中实际读取的技能及上下文。 |

各团队 variant 是完整独立实现；不相互 import，也不从共同配方生成。当前活动、实验与历史状态见 [Variant 索引](variants/README.md)，新实验的 case 与运行名见 [实验导航](experiments/README.md)。
原生 models/settings/角色 Markdown 是 Pi 直接消费的材料，profile.json 是 Braid 的原生 profile 字段。
`run.py` 明确构造本次 Braid 请求。
共有支持模块只做文件、进程与证据操作。

## 从任务到实现，再回到文档

修改前从对应 packet 的当前摘要确认问题、已批准方案、授权与未完成事项；需要某阶段的依据时再沿其证据入口读取。实现导航由组件 README 持有，不必为了找函数、角色或材料入口整读任务历史，再按需读 [技术说明](docs/product-tdd/index.md) 中受影响的约定。
源码描述实际行为，设计描述意图；两者冲突时先记录差异，不能用文档里的承诺代替已实现能力。
临时调查、候选方案和计划留在 packet，决定变化时改写当前答案；不要要求接手者按日期猜哪段正文仍有效。

实现中，产品行为变化更新 PRD，跨组件责任或失败语义变化更新技术说明，运行方式变化更新本文件或 Deployment。
局部实现的非显然理由、外部接口特殊行为和维护约束写在代码旁；已有完整解释时引用其归属，不重复抄写。
注释使用完整句子，按句换行，不为行宽机械折行，也不逐行翻译代码。
仅影响一个局部实现的改动不要求更新全部文档。

收尾记录实际结果与限制，将持续有用的知识提升到长期说明，原始证据留在运行目录，历史结论归 reports。
完成或转交前保留未完成验收与恢复入口；旧阶段的授权、模型资格及平台状态不能作为新阶段的实时事实。

## 修改一个成员或内部角色

从 [Variant 索引](variants/README.md) 选择实现，再读该目录的 README。I13 的接线与 prepare-only 方法归 [I13 本地说明](variants/pi-braid-i13/README.md)；I14 的基线、Cleaner、Reviewer 和 E2E 各自持有本地导航，说明实际角色、材料入口和反馈位置。根成员、Braid assignee 与 Pi 内部角色是不同消费者，不能只改同名模型字段。

## 准备实际需要的依赖

工具安装、开发 SVC、换机器和外部源码交接统一归 [scripts 本地说明](scripts/README.md#准备原生工具)。`make` 与 `make help` 只显示入口，`make tools` 才准备原生工具。机器绝对路径保存在可选的 `AGENTS.local.md`，共享文档不维护另一份机器环境。

## 直接验证源码

不启动模型的原生材料装配见 [I13 源码操作](variants/pi-braid-i13/README.md#直接验证源码)；其它实现按自身入口解释。真实生成有模型费用，仍按对应实验范围执行。材料可读取、原生调用成功和完整生成收益是不同证据。

## 构建独立运行资源与制品

统一使用 [runtime 与打包方法](scripts/README.md#构建独立运行资源与制品)；Linux 装配责任见 [submission](submission/README.md)，技能来源与分发边界见 [harness](harness/README.md)。纯指令变化重新装配材料，依赖变化才重建资源。

## 运行证据与收尾

Braid 运行诊断以外层实验 run 为入口：`make braid-report RUN=<实验目录> OUTPUT=<新网站目录>`。
[诊断运行手册](docs/deployment/braid-diagnostics.md)说明 Backend 查询、补采、失败产物、组件修改位置及验收边界；`lab.analysis.run_viewer` 负责实验总览，Braid 网站负责 OTLP 内的会话和协作现场，两者不是同一数据视图。
修改导出语义时从 `sources/braid/src/telemetry.rs`、`evidence.rs` 开始，修改页面从 `lab/analysis/braid_telemetry_viewer.py`、同名 HTML 模板开始；构建本机 Braid 后用已归档真实 Backend 生成新目录核对，不以重新运行模型作为默认验证手段。

原始证据位于生成输出的 `.factory26/<id>`；外层 lab run 与官网 journal 分别记录其执行和采集边界。先按[记录生产者](docs/deployment/evidence.md#按记录生产者查询)选择查询入口，不用外层进程成功代替生成或评分完成。静态网站、SVC 原生分析与长运行观察同归[证据手册](docs/deployment/evidence.md)。

`lab.analysis.factory` 提供 list/show/watch/analyze；旧配置式 generate/run/bootstrap/eval/batch、concurrency 及 shared submission 已退役，官网客户端和历史查询不再 import 旧生成器。旧结果与 journal 保留原身份。新官网提交显式提供模型 JSON，矩阵消费冻结 manifest；完整操作见[平台手册](docs/deployment/competition.md)。

跨仓库改动记录实际依赖与反馈，更新受影响的操作说明。具体实施依据和授权归所属 packet；编译、材料组装、真实工具响应和完整生成收益是不同证据，不能互相替代。不要为文档一致改写历史报告。
