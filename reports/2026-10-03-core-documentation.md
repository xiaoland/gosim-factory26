# 2026-10-03 核心文档与导航整理

本轮接续开发体验调查，按用户要求把范围转向核心文档、组件本地说明和目录导航，没有整理任务 packet，也没有启动实验或改动运行控制。整理基于当时工作树及实际 CLI/源码；它不证明运行耗时或模型 token 已经下降。

原先的主要成本不是缺少总索引，而是同一长页同时承担当前协议、历史操作、组件接口和瞬态状态。典型问题包括实验首页把九月底登记标成“当前”、Console 手册与 README 循环指路、旧暂停门闩与新控制门控混用、系统盘部署路径、失效启动方式，以及监控消费者说明沿用过期的模型禁令。

| 内容 | 整理后的归属 |
| --- | --- |
| 读者按主题找方法 | [文档入口](../docs/index.md)，工作与报告目录独立导航。 |
| 定义、执行、制品合同 | [Lab](../lab/README.md)及 `lab/exp/` 本地主题文档；技术说明维护跨组件责任。 |
| 工具准备、材料、Linux 装配、I13 接线 | `scripts/`、`harness/`、`submission/`、`variants/pi-braid-i13/` 的本地 README。 |
| Console 服务操作与界面读取 | [运行手册](../docs/deployment/console.md)和[组件合同](../braid-console/docs/contracts.md)，旧部署与暂停规则单独归档。 |
| 旧运行协议、实验登记、初始输入 | [历史协议](../docs/deployment/history/README.md)、[历史实验](../experiments/archive/README.md)、`docs/archive/initial-handoff.md`。 |
| 本机路径与发现方法 | 根 `AGENTS.local.md`，Git 忽略，不保存运行状态或授权。 |

还清理了根目录只剩空目录的 `skills/`、`patches/` 树；有效技能仍在 `harness/skills/`，npm 补丁仍在 `harness/npm/patches/`。独立 variant 与冻结执行器的代码路径和身份没有为文档整理而迁移。

重组时九个主要入口的正文合计从约 222 KB 降至 56 KB，减少约 75%；这是阅读载荷的度量，迁出的必要内容仍在对应权威页或历史协议中。原始 handoff 按字节保留。当时检查覆盖 59 份核心文档、517 个相对链接及 67 个外部指入链接，文件和锚点均可达；实际 CLI 帮助、schema 与来源导入分支已定向核对，diff 格式检查通过。

基线、迁移回执和检查明细位于 `runs/developer-experience/core-docs-20261003/`，由 Git 忽略。验证没有运行 Factory/Braid 测试、包 smoke、模型或 benchmark；现行能力中尚缺受管理 Console accessor 创建 CLI，手册明确使用已有合法 accessor、原容器只读或归档接入，没有杜撰创建步骤。

## 独立会话验收

按用户随后要求，新建「核心文档独立验收」（`01a0ff80-9844-71e1-a1d9-3dacf487db9b`），实际模型与推理配置核实为 `gpt-6.1-sol / medium`。它从普通入口独立选场景，不继承优化会话历史；主会话提供结果要求及隔离操作授权，没有提供首轮导航路径或标准答案。按仓库约定使用一个 advisor 处理迭代判断。核心整理已提交为 `d6e282d4`，首次导航补充为 `fcc87221`；验收针对变化中的真实工作区，未启动生成模型、评测或运行控制。

| 阶段 | 实际操作与判断 | 验收范围 |
| --- | --- | --- |
| 协作迭代 | 找到 I14 reviewer 的独立候选、责任与原生接口，建议先验证完整用户旅程的发现及采用能力。 | 开发边界可定位；没有启动应用或证明 reviewer 的质量收益。 |
| 实验准备 | 从真实 A2 材料创建显式演练 intent，compile 退出 0，execution_permission=false；doctor 保留 runtime 与私有引用缺失。 | 离线编译通过；build/start 未执行，不将材料准备当作执行就绪。 |
| 监控 | 实际读取 status/monitor、三个连续 liveness 样本及六条有界原始事件，辨别 active、语义 unknown 和 resource_deferred。 | 保存事实消费通过；未重开采集器，未把工具活动、内存压力或 token 增长当成交付或 OOM kill。 |
| 热恢复 | 核对旧 A 的 HTTP 404、来源停止及两个相同 ZIP；真实 partial payload 的 recover 退出 1，缺 checkpoint manifest。 | 正确拒绝无依据的保留进度恢复；没有可确认的完整 checkpoint，正向热恢复仍未验收。 |

首轮耗时约 14 分 22 秒，其中只读 ps 从申请到返回花费 7 分 07 秒，占约一半；这不是四阶段演练必需的进程核实。其余约 7 分 15 秒包括入口阅读、材料判断、离线操作及报告，不等于纯命令执行时间。主会话有 20 次工具编排、0 次上下文压缩，本地累计记录约 200 万输入 token，其中约 186 万来自缓存，非缓存输入 137,384、输出 11,748；reasoning 已包含在输出中，不另加。这不含 advisor，也不是一次上下文大小或账单。

演练暴露了一次约 581 KB 的递归路径列表、zsh 空通配符，以及首轮报告把 recover 后续写成再次 build 的错误。现已让普通查询先使用已有文本 status，沿 projection 的证据路径定向读原件；核心手册明确 checkpoint 目录、recover 内含 compile/build，以及 runtime 换版的兼容约束。缺 manifest 时，公共 recover 入口保留 FileNotFoundError、errno、路径与 traceback，并补充明确操作说明，不改变恢复门控。

两处历史断链不能合并处理。Sheet 的展开 application 副本已清理，但终态 ZIP 仍在；独立会话实际重取最终 Git 提交 `4812a40400b55f593c061ae180c6a609e9a72400` 的五份业务源码，SHA256 与旧分析索引全部吻合。入口是 `runs/iteration13/i13-2-20261001/flash-sheet-score-analysis/evidence-index.json` 所绑定的终态 workspace ZIP，来源 member 为 `template/.factory26/20261001-074506-6e7af22b/braid-state/origin.git/`；冻结 agent.zip 不能代替最终应用。旧 Console reviewer 的原始 CLI/HTTP/UI 回执和现场已按清理记录删除，仅剩历史完成记述，不能独立复证，也不能用新运行的同名 PR 追认它。核心证据说明新增了派生副本清理后的导航原则，本轮未整理 tasks。

功能演练中开发导航、离线准备和监控消费有条件通过；**首轮开发体验效率未通过验收**。它有搜索爆量、空通配符、非必要审批、失效证据入口和恢复步骤返工。校正轮耗时 5 分钟，最后回验约 99 秒，但二者已知道路径，不能作为冷启动提速证明。按用户补充，后续验收要分别观察定位、阅读/判断、实际操作、外部等待和返工，记录无收益绕路、截断与主会话提示，不能以流程结束、工具次数或单一总时长代替判断。

完整 build/start、模型实际路由、评分、reviewer 质量收益和成功保留进度热恢复没有取得本轮实证。首轮、校正与最终回执分别保存在[独立演练目录](../runs/developer-experience/fresh-session-acceptance-20261003/)，原始缺口和失败不改写为成功。没有增加测试、探针、模拟设施或新索引系统。
