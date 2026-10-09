# 开发 Factory26

开发者是 Coding Agent，用户参与目标、设计与授权。常驻约定见 [AGENTS.md](AGENTS.md)，本页帮助定位改动；组件的本地 README 持有实际接线和操作方法。

## 修改对象与反馈来源

反馈来自编译、实际操作和获授权实验；不维护 Factory、Braid 或开发基础设施测试。完整反馈边界归 [AGENTS.md](AGENTS.md#工作知识与反馈)。

| 修改对象 | 源码入口 | 实际反馈来源 |
| --- | --- | --- |
| Harness 的指令、角色、协作或执行 | `variants/<name>/main.py`、`run.py`、`agents/` | 生成运行的原生配置、会话与应用，获授权的 bench 得分。 |
| 原生工具或打包 | `tooling/scripts/runtime.py`、variant 的 `build.py`、`tooling/scripts/package_agent.py` | 实际安装、构建与提交过程的输出。 |
| run 命令与 Python 策略 | `lab/__main__.py`、`run.py`、`automation.py` | 公开 CLI、实际 dispatch/control、保存 status 与结果；合同见 [Lab](lab/README.md)。 |
| ARC 执行、路径与 restart | `lab/arc_bench/execution.py`、`run_layout.py`、`restart.py`、`tooling/scripts/harness_layout.py` | 实际 Docker/平台句柄、原生恢复与完整 data 回收，不以目录存在证明保存完成。 |
| 状态与活动解释 | `variants/<name>/status.py`、run observer | 执行事实与脚本 activity 分开；原生来源、时间与缺项来自实际采集。 |
| Collector、Backend 与 Console | `lab/otlp.py`、`backend.py`、`serve.py`、`consoles/lab/web`、`consoles/braid/web` | 实际 OTLP 接收、持久查询及页面；历史现场写桥不进入新链路。 |
| 独立应用评测 | `lab/arc_bench/evaluate.py`、`package_arc_replay.py`、`arc_replay.py` | 不可变应用副本的 simulate/task/official 原件、费用与真实评分。 |
| Pi 子代理观测 | variant 的 `extensions/` | 实际会话和原始观测记录。 |
| Braid | `sources/braid` 自身说明和公开 local 接口 | 自身构建和实际 Harness 调用结果。 |
| SVC skill 接线 | variant 的启动参数、角色 Markdown、I14 的 `materials.json`/`run.py` | 运行中实际读取的技能及上下文。 |

各团队 variant 是完整独立实现；不相互 import，也不从共同配方生成。当前活动、实验与历史状态见 [Variant 索引](variants/README.md)，新实验的 case 与运行名见 [实验导航](experiments/README.md)。
原生 models/settings/角色 Markdown 是 Pi 直接消费的材料，profile.json 是 Braid 的原生 profile 字段。
`run.py` 明确构造本次 Braid 请求。
共有支持模块持有文件、进程、证据与公共装配服务；variant 持有生成和原生协作语义。

现行 Harness 的新建应用 UI 默认使用 Tailwind CSS。各 variant 的生成指令要求按所选版本的官方方式配置构建集成及 CSS 导入，确认应用入口加载 CSS，并在正式构建的实际页面核对代表性布局、颜色和字体的计算样式，不能只以构建成功验收样式。接续既有应用时沿用其基线技术栈和数据语义，不为工具偏好迁移；历史 variant、冻结制品及在途应用保留原身份。

## 修改与文档

从组件 README 定位实现，按需读取受影响的[架构约定](docs/product-tdd/index.md)和任务记录。源码描述实际行为，设计描述意图；两者不一致时记录差异和未验边界。

产品行为变化更新 PRD，跨组件合同变化更新技术说明，操作变化更新组件 README 或运行手册。局部的非显然理由靠近代码；调查、计划和授权留在 packet，实际结果及限制归任务记录或报告。入口变化时同步撤回下游的旧推荐，避免维护重复配置与状态清单。

## 修改一个成员或内部角色

从 [Variant 索引](variants/README.md) 选择实现，再读该目录的 README。I13 的接线与 prepare-only 方法归 [I13 本地说明](variants/pi-braid-i13/README.md)；I14 的基线、Cleaner、Reviewer 和 E2E 各自持有本地导航，说明实际角色、材料入口和反馈位置。根成员、Braid assignee 与 Pi 内部角色是不同消费者，不能只改同名模型字段。

## 准备实际需要的依赖

工具安装、开发 SVC、换机器和外部源码交接统一归 [公共工具说明](tooling/scripts/README.md#准备原生工具)。`make` 与 `make help` 只显示入口，`make tools` 才准备原生工具。机器绝对路径保存在可选的 `AGENTS.local.md`，共享文档不维护另一份机器环境。

## 直接验证源码

I14 不启动模型的原生材料装配从[公共源码入口](tooling/scripts/README.md#i14-源码装配)开始；[I13 源码操作](variants/pi-braid-i13/README.md#直接验证源码)保留历史入口，不能用它推断新 context 能力。真实生成有模型费用，仍按对应实验范围执行。材料可读取、原生调用成功和完整生成收益是不同证据。

## 构建独立运行资源与制品

统一使用 [runtime 与打包方法](tooling/scripts/README.md#构建独立运行资源与制品)；Linux 装配责任见 [Linux 支持](tooling/linux/README.md)，技能来源与分发边界见 [共享材料](materials/README.md)。纯指令变化重新装配材料，依赖变化才重建资源。

## 运行证据与收尾

Braid 运行诊断以外层实验 run 为入口：`make braid-report RUN=<实验目录> OUTPUT=<新网站目录>`。
[诊断运行手册](docs/deployment/braid-diagnostics.md)说明 Backend 查询、补采、失败产物、组件修改位置及验收边界；`lab.analysis.run_viewer` 负责实验总览，Braid 网站负责 OTLP 内的会话和协作现场，两者不是同一数据视图。
修改导出语义从 `sources/braid/src/telemetry.rs`、`evidence.rs` 开始，Braid 自有 reader 与页面位于 `sources/braid/viewer/`；`lab/analysis/braid_telemetry_viewer.py` 只承担离线兼容入口。构建后可消费已归档真实数据核对，跨组件运行合同由独立真实使用验收，不以源码阅读或页面可打开冒充。

原始证据位于生成输出的 `.factory26/<id>`；外层 lab run 与官网 journal 分别记录其执行和采集边界。先按[记录生产者](docs/deployment/evidence.md#按记录生产者查询)选择查询入口，不用外层进程成功代替生成或评分完成。静态网站、SVC 原生分析与长运行观察同归[证据手册](docs/deployment/evidence.md)。

`lab.analysis.factory` 提供 list/show/watch/analyze；旧配置式 generate/run/bootstrap/eval/batch、concurrency 及 shared submission 已退役，官网客户端和历史查询不再 import 旧生成器。旧结果与 journal 保留原身份。新官网提交显式提供模型 JSON，矩阵消费冻结 manifest；完整操作见[平台手册](docs/deployment/competition.md)。

跨仓库改动记录实际依赖与反馈，更新受影响的操作说明。具体实施依据和授权归所属 packet；编译、材料组装、真实工具响应和完整生成收益是不同证据，不能互相替代。不要为文档一致改写历史报告。
