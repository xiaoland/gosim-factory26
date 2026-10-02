# 迭代 10：既有证据的消费对账

本轮从 [packet](packet.md)、[闭合账本](closure.md)、[实施记录](implementation.md)、[实验计划](experiments.md) 回查既有 09/10 报告，定向确认被声称已修的入口。只写本页，未改源码、其它 packet 或运行，未执行测试或实验。原生 idle/休眠边界和旧 objects 检查由既有 Sol 负责；Collector/status 的当前修复按工具 cell 已证事实接受，不重复深挖。

**有界结论：未发现需要从头另立方案的已证根因；有四组修复漏登、一组状态冲突及一个具体监控接续缺口。** 主要风险是源码已有改动被控制表漏掉，或缺少新冻结/真实采用证据却被写成“完成”。以下按最小处置列出，不把缺乏根因的现象强行转成改动。

## 必须补到控制链的事项

| 遗漏 | 既有证据与本次定向核实 | 最小处置与完成含义 |
| --- | --- | --- |
| **额度/供应商错误可见性修复未进入 closure，新监控接线缺具体要求** | [provider 错误调查](../braid-product-reaudit/cells/provider-error-observability.md) 已定位：原生持续 429/余额不足，Braid 只报泛化错误，监控仍以 running/文件活动判断。当前 `sources/braid/src/provider/pi.rs:577` 保存 `errorMessage`，`:596` 在 settled 失败时回退 reason，成功 stop 清中途错误；旧修复及验证有记录。closure 没有此行，experiments 也未明确保留连续失败识别。 | 主线把该源码修复列入统一构建；新监控保留“最近原生错误、首末时间、连续 failed turn、最近成功是否已恢复”，按本次 run/恢复边界排除旧错误。不要把 running 当请求成功，也不要把一次可恢复 error 当永久停机。具体新监控接线未证，属于启动前需落地的既有观察缺口；无需另加 DB 字段或重做错误分类。 |
| **外部 Git 整合的可证识别、Issue/PR 共同编号未登记** | [09 对象层实施](../braid-product-reaudit/cells/hotfix09-object-identity.md) 已给根因和修法。当前 `objects.rs:470` 按仓库全体工作项最大 number 分配；`:1671–1706` 使用 created base/observed unique head 正证识别已进入目标分支，明确不改 Git ref、不冒称原始 merge commit。`store/mod.rs:80` 注册迁移 0013。 | closure 登两项“当前源码存在，旧数据不重编号/无正证不推断”。统一包须包含代码和迁移。沿用本支线已有定向证据，较宽旧检查由 Sol 处理；这里不追加测试或自动同步语义。遗漏的是控制表，不是需要再次实现。 |
| **原生角色接线修复漏成一行 advisor 提示优化** | [三角色审计](../factory-subagents/cells/iteration10-role-audit.md)、[08 采用边界](../factory-subagents/cells/attempt08-validation.md) 分别定位 Braid/Pi 生命周期混淆、父重建旧 UUID 丢失、vision 语义 guard 误拒、PBB wait 误用。当前父 `instructions.md:19` 已说明已指派成员独立推进；observer `:360` 有 Unknown agent 调用处纠偏，`:305/:351` 有旧 UUID 索引/注入，`:322` 有终态转送；四个非实施角色均有 `completionGuard:false`。 | closure 至少分别登记“所有权/错误名反馈”“跨父旧任务身份交接”“非实施角色 guard”。08 已证明交接注入，未证明在途终态转送和父消费；下一次自然事件观察，不为证明而重复派同一写任务。PBB 与原生空闲机制归现有 Sol，不将纠错文字当机制已修。 |
| **explorer 工具知识归属调整漏登，运行资源迁移容易随旧包遗漏** | [exploration-tools 调整](../braid-product-reaudit/cells/exploration-tools-review.md) 已决定删除独立技能，把通用工具知识直接放 explorer。当前 explorer 正文含 rg/ast-grep/Context7/Exa；`run.py:193` 使用 variant `tools/mcporter.json`；技能目录说明已记迁移。 | 纳入统一材料清单：explorer 直接正文、领域技能、variant MCP 资源及正常/恢复入口保持同版。这里是已实施的归属修正，不是运行调用或外部服务收益证明；不重复安装旧 skill 或再注入 advisor/executor。 |
| **closure 的“尚未应用”与已实施记录冲突** | closure 仍把三处 CLI 帮助、根共享基础/设计预演、跨设备/browser/status 列为未应用；[implementation](implementation.md) 已记前两类落地，[tools cell](../braid-github-minimal-review/cells/iteration10-tools.md) 已记后者。定向读取当前 `run.py:159–161`、成员 instructions、SVC product/check-design，确认跨项方案、根基础 PR、场景保真和候选前提消费已存在。CLI 编译行为仍待主线核对。 | 主线把这些状态改成“源码/指引已应用，行为验证或统一冻结待完成”，保留真正未完的 idle/休眠项。不要为了让旧待办归零再做一遍已完成修改；也不要仅因源码存在改写成自然采用已证。 |
| **控制目录迁移后的证据入口失效** | closure 末尾 `../implementation.md`、`svc-cli-integration.md` 均不存在；正文裸 `workflow-entry-audit.md` 在本目录也不存在。 | 分别指向 `../braid-github-minimal-review/implementation.md`（历史协作实施）、`../braid-github-minimal-review/cells/svc-cli-integration.md`、`../braid-github-minimal-review/cells/workflow-entry-audit.md`；本轮实施单独指 `implementation.md`。这是任务控制入口问题，修链接即可，无需搬写历史报告。 |

## 已有合理处置，不应再次开工的部分

| 旧发现 | 当前消费位置与边界 |
| --- | --- |
| 同一 native session 重复 Context、联系逐条唤醒 | closure 已分别登记 Context 接受后清副本、通知合批；[token 终态](../braid-product-reaudit/cells/token-final-review.md) 给了真实重复证据与不可叠加的条件估计。后续自然运行还需测实际消息与用量，不能把旧 109.25M 情景当已省。休眠复用归现有 Sol，不重复设计。 |
| PR Closes 与背景关联、持久退订、配置别名与具体成员不同 | closure 已登记行为修复；implementation 记 CLI 明示。GitHub 最小协作复审的取舍是清楚履行现有动作，不补全 GitHub 产品。default branch、普通关联不自动 close、@ 不永久重订的边界应随新包保留。 |
| PR25 head 更新后未等所承诺的检查就合并 | 当前成员 instructions 明确合并前消费当前候选结果与未解除前提，head 匹配不代表前提满足。这是已落地的方法修正；不新增审批状态机。原始行为见 [GitHub 二审](../braid-github-minimal-review/cells/github-minimum-second-review.md)。 |
| PR24/25 接管竞态重复创建 | 当前 instructions 要求改派前联系负责人或依据明确阻塞；二审已给“不因单个样本新增自动去重锁/retarget”的理由。保留明确决定，不把缺少自动锁记成尚未修。 |
| 短期进展写入 description 触发重建 | 当前 `group/provider.rs:69` 明确 description 稳定依据、comment 增量、不要日常复制正文，并提供更正/hide/resolve。closure 已有工作记忆指引行。该行标题“工具存在但失效判断持续混在上下文”过于含糊，可改成具体根因，内容无需重复实施。 |
| 首轮退出码缺失、跨设备 cp -al、猜浏览器路径、危险清进程 | with-service 及真实应用验证、agent-browser 两句操作指引已有工具 cell 负责。当前 closure 不应把这些仍写成源码未修；它们尚未进入统一包/自然采用与是否已修是两回事。 |
| Collector 重建引起全量重发、巨大 status 回显 | tools cell 已说明当前源码修复及 SDK/持久化边界。接受该证据，不重复追源码、不要求无损保证、不新建查询接口。 |
| 需求摘要损失并列范围/初态，检查自己造数据掩盖初始状态 | implementation 与当前 SVC product/check-design 已覆盖原始场景权威、并列对象、setup 绕过范围；当前 root prompt 要求子项自包含来源/前提。Sheet 具体失分映射仍缺证，不必为未知因果追加题目专用提示。 |

## 应明确保留的否决或观察条件

1. **frontend-design 未装入并不自动是未修根因。** 旧 workflow-entry-audit 将其列为接线事实；本轮已用根级共用视觉/交互约定和现有视觉技能覆盖对应责任。尚无证据证明必须增加这一特定 skill 才能解决已定位问题。最小处置是在 closure 记“不扩技能清单，先观察当前职责与现有材料采用”，而非把目录存在当生效或未经比较直接加包。
2. **explorer/advisor 零调用不构成角色阻断。** 已明确实际机会、发现与零调用范围；advisor 前置方法已修，explorer 没有工具拒绝的实证。保留普通调查/实施委派的收益判断，不定调用配额。K2.7 根候选暂缓理由已经写明，不需要删除源码来证明取舍。
3. **K3 advisor 路由和父消费仍是观察条件。** 当前 `kimi-k3→KIMI` 是静态路由，旧 K2.7 简单 Chat 200 不证明它。首次真实有意义咨询记录请求模型、上游、子实际模型、工具往返/返回与父决定；若模型不可用，保留精确错误并显式调整配方，不能暗换还标 K3。本项未知不要求本 worker 另发探针。
4. **“少 token”不是独立质量指标。** Headerless PR26、归档副本、cache/output/reasoning 口径已在终态对账修正；不需要修改生产业务来补报告口径。下一轮继续分清含缓存输入处理量、未缓存 input 和实际账单；缺价不报费用，重叠优化不相加。

## 统一冻结前的最小闭合动作

主线只需把上表漏登修复和状态冲突写回 closure，修复证据链接，并把 provider 持续失败识别明确纳入新监控。已有实验计划要求同版源码/runtime/skills；补到材料核对项时应同时覆盖 0013/0014、Pi 错误原文、原生 observer/guard、explorer MCP 资源，以及本轮方法/工具正文。WSL 旧 lock/runtime 不等于当前源码，这一版本风险已有 tools cell 明确，不能从 collaboration-v2 名称推断含后加改动。

真正仍在实现的 idle/休眠与既有 objects 检查继续由原负责人完成。完成代码和适用验证后才能冻结；自然角色采用、净节省和应用评分在真实实验中确认，不能要求在实验前先证明尚未发生的收益。这样既满足“已定位根因有合理落地”，也避免把有限缺证扩成无止境调查。
