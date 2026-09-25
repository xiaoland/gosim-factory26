# 实验基础设施目录架构审查

## 当前范围与授权

2026-09-25 用户要求：“接下来我们对实验基础设施的架构（主要是文件目录架构）进行审查（集中在可维护性、可读性上）”。随后确认：“我同意这个方案，你可以做实现计划以及计划预演、排障了（别开始落地）”。计划和预演完成后，用户明确说“好的，开始落地”。当前授权范围是按已认可的目录职责和实施计划修改源码、操作文档，在 WSL 利用已有真实记录验收；不包含新模型调用、benchmark、官网提交、停止现有服务或 Git commit。

审查与实现针对当前工作树，包括其他任务尚未提交的改动。当前唯一活动 variant 为 pi-team-mixed；raw/Hackathon 源码已归位但仍归档。实现后在 WSL 使用现有真实记录和 runtime 做查询与制品核对，没有运行模型、基础设施测试或 benchmark。

问题是工程师能否从目录直接找到某个职责、判断其生命周期，并在不理解全部 Harness 历史的情况下修改实验设施。职责布局已获认可并实施。[实施计划](plan.md)记录文件去向、接口、兼容和验收安排；[预演与排障](rehearsal.md)记录静态断点、现场证据及已采纳的收窄。

## 实施前观察与判断

### 通用执行与专用分析的边界在查询入口处混合

`scripts/local_experiment.py` 的执行部分只调用外部 argv，使用 `experiment-result.json`，导入的 OTLP backend 不解释 Harness 语义。这一边界应保留。但该文件第 291–293 行的 `status` 调用 `inspect_runs.show_run`，后者 `experiment_summary`（第 107 行起）识别 `official-generation`、`.factory26`、`.arc/raw`，解析官方 Runner 事件并重新解释完整评分。Factory、Pi、Braid 的历史查询也在同一 778 行文件中。

这已经产生可见的维护成本：原生 Hackathon 把过程证据放在 `.arc/hackathon`，该摘要只有 `.arc/raw` 的专用会话遍历，没有对等的 Hackathon 分支。此判断来自路径和调用关系的静态检查，不是新运行的行为验收。执行器仍然独立，不能将查询层耦合说成生成流程依赖 Braid。

建议通用状态入口读取通用 run/result/OTLP 元数据；ARC 结果解释归 ARC 消费者，Harness 过程重建归明确命名的分析消费者。分析可由实验用户提供；不增加强制事件语义、插件注册系统或统一 Agent 轨迹 schema。现有 Braid 网站通过原始 OTLP 和 Braid CLI 解码，本身符合这个方向。

### 实验定义与机器执行现场缺少清楚的归属

仓库 `experiments/` 只有旧 `multi-agent-lite.json`，其 `generation_workers/evaluation_workers` 等字段属于已移除的旧执行入口。当前运行说明第 400 行已说明不能用它启动新矩阵，但从目录本身看不出。

本轮四配置八任务的实际清单在 WSL `/home/yyh/Development/factory26-official-local/hackathon-generation-matrix.json`，恢复清单同样在这个根目录。文件使用机器绝对路径；Runner 指向另一场历史实验的 `raw-baseline-20260923-wsl/runner`，网关 env 指向根目录的服务实例。单个 run 的输入已有快照和哈希，事后证据并非没有保存；缺的是源码仓库内可发现的实验定义，以及定义、解析后的执行清单、结果之间的稳定目录关系。

建议 `experiments/<name>/` 保存非敏感、可复用的矩阵定义或现有命令配方；机器解析后的清单留在对应实验输出目录。无需设计新配置语言。历史清单明确归档，不作为默认新实验样例。

### 文件位置掩盖职责和生命周期

`scripts/` 将通用执行、OTLP backend、ARC adapter、官网客户端、制品打包、模型网关、Factory 历史查询和 Braid 网站平铺。目录名不能回答“我要修改实验调度，还是改某个 Harness 的证据解释”。

`submission/` 同时持有公共 Linux runtime 构建，以及 raw/Hackathon 两组实际 Harness 的入口、模型配置和角色正文。`package_hackathon.py` 第 30、38–43 行从这些位置组装运行材料；`hackathon_main.py` 又导入 raw 入口与 raw OTLP。一个独立基线的修改散布在 scripts/submission/harness 三处。`variants/README.md` 已标记这两组历史状态，但物理目录仍把它们与共用交付设施放在一起。

建议按职责聚合实验核心、ARC 集成、分析消费者；将独立基线的入口和角色材料归其 variant，公共工具构建继续独立。归档状态不代表应删除仍用于读取历史结果的代码，也不要求立刻搬动所有参赛实现。

### 数据目录的导航仍停留在退役流程

WSL 资产根目录混放多个版本的 Pi/Codex ZIP、runtime、网关实例、控制器日志、恢复脚本、需求包、诊断输出和 runs。根 `README.md` 仍声称生产 Runner 未公开并推荐 `platform_public_run.py`，与仓库当前 `docs/deployment/index.md` 第 62–63 行的退役说明相反。该旧脚本及 AppleDouble 文件仍在资产根目录。这里只确认导航残留，未尝试运行旧脚本，也未据此判定它干扰了过去评分。

仓库 `tasks/local-official-bench/packet.md` 的“当前状态”同样停留在缺镜像阶段；它是历史证据，但正文没有在入口指出后继。当前操作文档已有明确的历史章节和若干归档声明，这些应保留；需要修正的是仍冒充当前入口的材料。

建议新产物按共享输入、Runner/runtime、制品、服务实例、每次实验组织；旧目录先保留身份和显式入口。原始 run 中有绝对命令路径，不能为了目录整齐就搬动或重写冻结记录。

## 已认可的职责布局

源码的最小方向是增加一个有明确职责的 `lab/`：直接保存通用执行、状态、等待与 OTLP 模块；`lab/arc_bench/` 保存矩阵、官方 Runner 适配、冻结应用评测/回放和官网客户端；`lab/analysis/` 保存可选的 Factory/Braid/原生过程分析。现有 scripts 中不属于实验设施的开发和打包工具继续按各自职责维护，不为了统一目录制造空壳 CLI。

`experiments/` 保存具体实验定义，`variants/` 保存 Harness 实现，`submission/` 保留共用交付和 runtime 构建材料。目录名仍可讨论；主要约束是基础设施不反向导入 Harness 分析或实现。

WSL 数据根目录的新写入可收敛到 `platform-inputs/`、`runners/`、`runtimes/`、`packages/`、`services/` 与 `experiments/<id>/`。一次实验目录包含执行清单、控制器日志、runs 和后续 analysis；共享服务可以被多次实验显式引用。

单个 run 内已有 `inputs/`、`workspace/`、`artifacts/`、`run.json`、stdout/stderr 和 `telemetry.sqlite`，职责足够清楚，建议保留。官方 Runner 在 workspace 内的结构也继续原样保存。主要整理单个 run 外层的组织，以及源码的依赖方向。

## 交接

实施计划与两项独立预演已完成。explorer 追踪冻结脚本、包内布局及官网 import；QA 复核状态拆分、查询消费者和部署边界。主 Agent 结合真实元数据修订计划，QA 最终建议接受、进入待开工，未发现剩余静态计划阻断。

预演后明确保留 adapter/noop 的单文件执行与 ZIP 内布局；网关源码完全不改，Factory analyze 的 run/analysis 缓存约定不改；新版设施在 WSL 独立源码快照验收，不覆盖两端已有不同部署。已列出现存 Lite、requirements-only、旧中断、OTLP 和官网 journal 的证据入口，不需要为查询验收重新消耗模型额度。

用户开工授权后，源码迁移到 `lab/` 和历史 `variants/`，新增当前 Lite 配方，更新当前文档及 WSL 资产根导航；网关与既有服务未动。WSL 独立源码快照位于 `/home/yyh/Development/factory26-official-local/experiments/layout-acceptance-20260925/source`，生成的清单、网站、导出的 OTLP 和验收包均保存在该实验目录。抽查核心源码和专用打包器 SHA256 与 Mac 当前工作树一致；Braid 二进制是 0.3.2，SHA256 `76cb677435f13c897ab85bf0a7c5f42b18df847045c7356cdc14203f42919e3f`。

已有 Lite Keep/BookStack 分别读出 27/32、27/34，Hackathon Sheet 保持 skipped/null；`factory show` 与 `run_feedback brief` 均读到 8 份 session JSONL，主 events.jsonl 单独列为证据。旧 raw 失败记录仍显示 failed/退出码 1，未改写。OTLP 导出 214 批（8 traces、146 logs、60 metrics），Braid 网站重建 4 个会话并报告 complete，Viewer 发现 32 个 run、0 个发现警告。归档 Playground 的 `--saved` 在 WSL 离线读取两条保存状态，保持 FAILED；源文件分别保留 100 条和 0 条逐例记录，第二条不凭总计补造逐例结果。

真实 Pi 原生包、raw Pi、raw Codex 和 Lite 双题回放 ZIP 已实际打包，检查了平铺入口、角色、callback 和 manifest 文件名；当前 Lite 配方只生成含 Keep/BookStack、两阶段模式和 4 workers 的机器清单，没有执行该清单。`git diff --check` 无格式问题；未运行基础设施测试、模型、bench、官网写请求或停止服务。完整生成/部署效果等待下一次单独获授权的真实实验确认。

用户随后明确允许提交。本次只提交目录整理及其必要文档；工作树中其它任务的既有修改留待各自任务处理。
