# 诊断消费实现与验证

本模块只修改 `scripts/inspect_runs.py`、`scripts/playground.py` 及各自测试。没有修改官方评测器、旧 run 产物、SVC 或 Braid，没有调用模型或执行平台任务，也没有提交父仓库。真实核心、独立盲验及新 Keep 验收仍由集成阶段完成。

## 已实现行为

`factory.py show RUN --eval EVALUATION --case REQ-ID` 保留原接口，在用例错误后追加页面片段。读取范围限定为该次评测附件中的 `error-context`，只解析官方 `Page snapshot` 区段；按失败 Call log 中的 role/字面名称选择节点及相关祖先，显示原文件行号。后附测试源码里的其他定位器不参与选择；无法匹配时明确缺少片段，不展示完整 DOM 或推断故障原因。读取及片段长度有界，原错误/附件字段仍保留。

`show` 优先消费 `native/manifest.json` 的 schema_version=1 清单，保留 provider、group、工作项、context revision、turns、原始来源等字段。每份原生文件只做流式哈希校验，不解析全文；缺失、越界、重复路径保留身份与拒绝原因。历史阶段目录仍可导航，但缺少来源哈希的分析只能作为未核实候选。

清单的 `context_path`、`instructions_path` 与 `turns[].input_path` 在 `--json` 中转换为可直接打开的本地归档路径；只检查路径边界与文件存在，不读取正文。缺失或越界入口为 null 并产生警告，`source_*` 与生产者的 `evidence_error` 原样保留。这样输入归档缺失也不会丢失物理会话身份。

SVC 关联要求 provenance.source_session 与源文件名一致、source_sha256 与实际原生字节一致；清单自身哈希不符或已声明 provider 冲突时拒绝关联。多个核实结果保留在 `analysis_candidates`，单值 `analysis` 保持 null，不根据 mtime 或目录顺序选择。无源会话的分析也单独计数。

评测摘要声明的 evaluation_id、run_id、benchmark_revision、application_sha256 必须与所选目录、配置和冻结哈希清单一致。应用摘要哈希使用与 Factory 相同的排序、紧凑 JSON 编码。身份不符时不输出分数或关联 case，也不回退到其他评测。选择评测时优先读取 `remote-evaluations/<id>.json`，不会混入另一尝试的兼容摘要。

`playground.py status RUN --saved` 是新增的离线只读入口，重放已有 status、日志块和 traceability，不联网或补写旧文件。现有实时 status/watch/collect 命令继续使用官方接口。新采集用 `observation.json` 分开记录 status/logs/traceability 的本地观测时间和接口来源，官方原始响应格式不变。

状态摘要按官方 event_id 去重，分别呈现最近非心跳事件与心跳；保留源 timestamp、阶段、状态和产物引用。终态来自平台状态，运行中的计数不作为完整分数。status 与 logs 各自显示 observed_at、年龄及 fresh/stale/unknown，当前超过 60 秒标 stale 并显示该阈值；它只标识观测时效，不判断执行停滞。旧记录没有采集时间时为 unknown，不使用文件 mtime 或跨主机时钟推导。watch 不为单纯采集时钟和重复心跳变化反复打印。

traceability 区分 unavailable、empty、available，显示采集来源及已提供的 producer/version；缺失字段保持 null。其 kind 明示为显式关联，SDK 自报信息不转换成官方评测成功或生成因果证明。

## 可重复的真实样本

```sh
python3 scripts/factory.py show 20260920-141339-6138c072 --eval 20260920-163747-e5039d --case REQ-2.2
python3 scripts/playground.py status 2041e4b58701 --saved
```

第一个入口同时给出失败定位器 `dialog "Note editor" → textbox "Title"` 与官方附件的页面事实：

```text
335: - dialog "Create note" [ref=e421]:
338: - textbox "Title" [active] [ref=e426]
```

这足以区分“Title 不存在”和“父对话框限定不匹配”，但代码不替用户判断需求/实现/评测的责任。下一项定向检查仍是冻结 `application/public/app.js:763`、官方 `keep/tests/helpers.ts:233` 与输入 `requirements.md:36`，均有现成证据。

第二个入口显示平台 FAILED、135 个 timedOut、约 1526 秒，最近非心跳为评测阶段终态错误；最近心跳仍是 `Test progress 0/135`。traceability 为 empty，producer/version 与采集时间为未知。这些旧记录不能据此证明运行时卡死或已建立实现关联。

## 检查与未决事项

- `python3 -m unittest discover -s tests -p 'test_inspect_runs.py' -v`：10 项通过。覆盖页面实际父节点、后附源码干扰、跨评测附件拒读、清单身份与实际输入入口、缺失证据保留、哈希错配、多 exporter 不自动选择、错误评测身份和远程尝试隔离。
- `python3 -m unittest discover -s tests -p 'test_playground.py' -v`：8 项通过。覆盖心跳/进展/终态、分别过期及未知观测、显式关联来源、离线不联网不写文件、错误 run ID、凭据与日志游标既有边界。
- 两个真实历史入口已只读执行；`git diff --check` 通过。没有把行数或固定查询次数作为通过指标。
- 新清单与评测字段已按主 Agent 给出的契约接入，目前无等待中的字段定义。实际新 Braid 导出的完整会话、真实核心受控场景和新 bench 链仍须集成验证；本模块测试不是它们的替代。
- 等待未参与实现的 Agent 盲验诊断链；历史 traceability 为空且未记录生产者版本，保持缺失事实，不补造关联。

## 运行中的 Braid 状态入口

补充 `show` 的两行实时摘要，仅在 run.json 声明 `status=generating`、`workflow=braid` 且有 runtime 时读取当前 `runtime.braid_state/status.json`。解析后的路径必须位于同一 metadata 声明的 `runtime.work` 内，包含符号链接解析；缺失、解析错误或越界显示 unknown 与警告，不使用归档状态替代。Factory 也给纯核心运行预置 braid_state 路径，因此仅有该路径不能开启实时读取。

JSON 的 `live_braid` 只保留状态来源、同一打开文件的 mtime、本次观测时间、工作项 kind/id/state，以及 active_turns/pending_batches/pending_resets/blocked_groups。默认最多展示三个工作项，其他工作项通过 JSON 查看；不返回 physical_sessions 或整份原始状态。Braid 调度器每约 250 ms 写状态快照，两个时间只描述快照写入与本次读取，`model_progress` 保持 unknown，不作为模型实质进展证据。

本次在两个真实运行仍为 generating 时只读执行 `show 20260920-233128-6aae4ce3` 与 `show 20260920-233128-1ba8fed8`；2026-09-20 15:45:27 UTC 的两份摘要均为 `issue #1 OPEN；active turn=1，pending batch=0，reset=0，blocked=0；模型进展: 未知`，来源分别是各自 runtime.work 下的状态文件。未等待生成、执行模型或修改运行产物。

新增两个回归测试覆盖当前来源、不混入归档、时间/进展分离、无 raw 会话展开、完成后停止读取、纯核心隔离，以及缺失/无效 JSON/外部路径/符号链接越界。inspect 共 12 项通过，`git diff --check` 通过。真实纯核心 `20260920-225624-82074f1f` 复验无 Braid 实时摘要；本次只改诊断脚本、对应测试和本报告。

主流程集成时进一步收束默认输出：仅保留一行工作项/调度计数与“模型进展未知”；确切 source、written_at、observed_at 归 --json，避免每次 show 都重复长临时路径和时间戳。它们描述快照，不描述模型进展。12 项定向检查再次通过。
