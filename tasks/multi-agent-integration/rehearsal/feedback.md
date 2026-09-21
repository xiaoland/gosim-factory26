# 诊断与固定批次：实施接缝

主 Agent 已沿 `scripts/core.py::archive_sessions`、`factory.py::generate/analyze/run_experiment`、`run_feedback.py::_declared_native/collect` 和 `inspect_runs.py` 核对。capabilities 独立预演已复核本稿，要求仅从 runtime 的 physical roots 和真实关系发现 children；无新源码、模型或 bench 执行。Factory 起点 e229e6b。

## 已观察缺口与接口

- archive_sessions 只消费 Braid 声明的父会话，Codex 缺路径时仅搜单一 home；即使原生 child 已运行，也不会自然进入清单。须从已归档 physical 的 native_home/native_session_path 出发，按 Codex thread_spawn 和 Pi subagent tool result/status/artifacts 的真实关系发现 children；未关联的日志只能标未知。foreground 缺 background process-terminal 不意味着缺 sessionFile。
- 归档行已保留原 entry，扩展 profile_id、effective_profile_digest、work_item、assignment_generation、parent_native_session_id、native_role、身份来源即可；无需另一数据库。所有路径须留在隔离 work 内，以 provider/native_id 去重，重复 ID 内容冲突报错，缺失保留显式证据。
- Pi usage 当前按归档日志求和，Codex 按日志末次累计值求和；child 纳入后必须区分原生逐会话统计与父汇总。未证明计数口径时分开报告，不把父子两份相加称全量，也不把缺失字段当零。
- run_feedback 目前只返回 `(path, provider)`，错误分组丢失 profile/session 归属。保持短摘要，通过已验证 manifest 建映射，给相关错误及 show 提供 session/profile 入口。原日志继续按需下钻。
- analyze 已按 exporter、原生内容 hash 缓存并逐会话执行；可复用，provenance 补身份即可。缺失一个 child 应明确 analysis 不完整，不使真实 bench 分数失效。

## 线性实施切片

1. 在现有归档边界扩展身份与 child 发现；先用真实格式的小型受控日志检验父子、重建、重复/冲突、缺失和越界，保持旧 run 可读。要求 runtime 返回明确的每 physical home 与 profile 身份。
2. 更新 usage 的口径及 brief/show：能从同一受控失败定位其父 work-item/profile/native child，区分声明、加载、使用，不靠 role 名称证明活动。将此证据接到真实受控核心场景，不另开模型实验。
3. 新增一个薄 batch 模块，复用 generate/evaluate/analyze/save 和终态语义；父入口持有固定清单、run IDs、PID/进程启动身份与状态。生成、评测独立容量，不把等待评测算成占用生成槽。配置/源码/输入不一致时在启动前拒绝。
4. batch 先持久化条目身份再启动阶段进程，进程退出推进阶段并最终回传。控制进程重启后复用已有终态；没有终态又无法证明原进程状态则 unknown，禁止自动再次 generate。恢复冻结应用的评测也必须使用既定 evaluation ID 和当前阶段证据，不覆盖既有尝试。
5. 批次聚合报告 4×2 的实际覆盖、分数、失败阶段与证据，普通应用失败继续预排清单；系统性配置/隔离/协议错误暂停排队。相关设施问题归 owner 修复，不自动补跑。

原生发现可留在 core.py 或按实际格式复杂度独立 native_evidence.py；不为每字段拆模块。batch 的持久清单本身就是控制事实，不再加通用工作流模型。Factory 源码共享接缝由主 Agent 集成。

## 独立检查入口

扩展现有 test_braid_runtime/test_core 的原生归档行为，test_run_feedback/test_inspect_runs 的真实错误归属，以及 test_experiment 的终态后 analysis 不覆盖原结果。新 batch 的关键反例是中途崩溃/恢复仍只生成一次、unknown 不重复启动、单个应用失败不漏后续项、系统性错误不继续扩散。用受控子进程验证容量与实际退出，不用固定睡眠估并发。

仍需独立核对：Pi artifacts 与 Codex headers 的实际可用父子关系；Codex usage 是否含子调用；跨阶段失联与终态身份。实现不能以猜测补齐这些信息。
