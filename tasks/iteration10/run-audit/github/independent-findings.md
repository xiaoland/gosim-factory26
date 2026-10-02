# 独立发现快照（对账前）

截至本快照，未读取 iteration10/review.md、closure.md 或既有 GitHub 因果报告。本文件锁定先由原始运行证据得到的方向，后续证据可推翻。

1. 初始根会话从完整 YAML 改读 description-only（原始场景主要未读）；47 ATOMIC 被写成约 40。它意识到 PR milestone 依赖，但拆分 #7 仅写 Issue，#8/#9 没有补接。这是潜在跨模块漏项，而不是“少 7 个功能”的直接证明。
2. 共享基础 03:09:57 已识别原需求 acme-docs 与父 Issue web-app 冲突，却在内部思考选择服从父 Issue，未将这个冲突发布到工作项。这支持派生契约权威倒置的因果链；最终整合 bb9bbe6 修复了错名，因此错名不是最终代码遗留违约。
3. 原需求 explicitly non-cumulative operation roles；基础建立全序角色，#7 将 Triage/Maintain/Admin 压缩为 Triage+。冻结代码前后端均允许 Write 修改 Issue milestone，违反 REQ-5-3-3；PR 页面/API 没有 milestone 支持。尚未运行应用，无隐藏评测归因。
4. 共享基础接管发布了未修完的 mutable worktree；只验 login 响应未验 login→me。该缺陷使至少 REQ1/2/3/4/5 各支线重复处理 sessions.expires_at；最终 PR3 已修，影响是返工与验收注意力而非最终登录缺陷。
5. 多轮“独立复验”主要复跑作者套件，最终整合却首次发现中央仓命名/种子关系错误。REQ2/5 浏览器走查没有进入最后五套 E2E，全量声明的证据范围偏窄；#12 reviewer 的额外 DB 验证是有价值反证，不能笼统说所有复核没有增量。
6. Braid 确实提供依赖分批、共享契约、分支整合与上下游交接；但基础 owner 03:16 计划实现大量未来模块 UI/API，基础边界膨胀造成依赖和复写；#8 开工额外等 #2/4/7 全合，并非每段等待都由真实依赖造成。
7. 原始根会话可见 pbb/subagent_wait 混用，反复声明要等但继续开 sleep。后续闭项通知引发多个空转原生会话，完整 native usage 与 timing 合计完全一致（2,707 条 message_end），证明能用去重证据而非摘要估计成本。模型 token 总和不是金额，reasoning 是 output 子集。

覆盖事实：全工作项最终正文/可见评论已语义阅读，活动元数据已核对；约 42 个存在原生会话的完整全文尚未全量语义阅读，仍需按 coverage.md 逐段继续，不能称“全量审完”。
