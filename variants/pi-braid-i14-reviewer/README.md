# I14 Reviewer 变体导航

Reviewer 的入口是 [`main.py`](main.py) → [`run.py`](run.py)，并有两条明确路径：普通公开需求生成，以及可消费已发布 application seed 的 `seed-audit`。配方提供独立 `pi-glm-reviewer` 成员的 reviewer 能力和指令；`native_files()` 按配方装配可用成员材料，生成流程选择启动成员，Braid 执行实际 Review 指派。不能仅由角色存在推断每次 seed-audit 都自动由该成员执行。seed-audit 对需求和候选提交做有界审阅，不是普通 I14 生成流程中自动注入的评测器。

## 改什么看哪里

- reviewer-only 成员能力和职责：[`agents/pi-glm-reviewer/instructions.md`](agents/pi-glm-reviewer/instructions.md)；根/快速成员的 seed-audit 与完整生成分流说明在 [`agents/pi-glm-root/instructions.md`](agents/pi-glm-root/instructions.md) 和 [`agents/pi-glm-fast/instructions.md`](agents/pi-glm-fast/instructions.md)。材料装配见 `run.py:native_files()`，启动选择见 `generate()` 中的 `root_profile_id`；角色存在不证明实际 Review 指派。
- seed 输入与 manifest v2 校验：[`build.py`](build.py) 的 `--application-seed`，以及 [`run.py`](run.py) 的 `load_application_seed()`、`seed_snapshot()`。
- 审阅报告合同与身份绑定：`read_audit_report()` 和 `run.py` 中写入 `audit-report.json` 的提示。报告必须绑定 seed manifest、需求 hash、candidate commit，并声明授权范围；程序只校验身份、范围和字段，不替审阅者判断语义。
- 供应商/网关材料：[`build.py`](build.py) 的 `--provider-env`、`--gateway-routes`；它们与 seed 是两类输入。
- 反馈：先看 `application-seed.json`、`audit-report.json`、candidate commit 和 run evidence，再决定机械项是否有合格修复；未完成或身份不符的报告保持失败/阻塞，不改写成交付成功。

Reviewer 的 seed 会在运行前形成非空 Git 快照；完整生成路径仍从公开需求开始，seed-audit 路径才消费已发布 seed。两者都不能从工作树未提交内容冒充候选来源，也不能把审阅报告变成正式评测结果。源码核对：[`main.py`](main.py)、[`run.py`](run.py)、[`build.py`](build.py)、[`agents/pi-glm-reviewer/instructions.md`](agents/pi-glm-reviewer/instructions.md)。

实验状态、启动/控制、监控和恢复仍由 [Lab execution 合同](../../lab/exp/execution.md) 与 [恢复手册](../../docs/deployment/recovery.md) 负责；它们不替代本页的 Reviewer seed/report 反馈，也不把审阅报告提升为实验终态。

入口要求设施已装配的 context；源码操作见[公共源码入口](../../tooling/scripts/README.md#i14-源码装配)。技能与额外角色需求由 [materials.json](materials.json) 声明，controller/SDK/Hosted 交付与实际服务不由本 variant 另行实现。
