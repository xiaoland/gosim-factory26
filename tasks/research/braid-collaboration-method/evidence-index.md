# 证据索引与版本边界

本研究区分三类证据：历史运行事实、当前 dirty 工作树的静态语义、外部一手事实/研究。方法规则是三者综合后的设计结论，不冒充任何单一来源的原话。

## 1. 当前 Braid 工作树

- Git HEAD：`0712a58d0e5f7af225473d6c48c4aa740c20dfbf`；工作树 dirty，19 个 Braid 文件有既有修改。
- 当前整合 binary：`sources/braid/target/debug/braid`，SHA-256 `e2f58d6342f5c74be91dbbbf2c45511148e00fb5d76d1cb05ec6510956279d81`。
- `src/context.rs`：SHA-256 `7d092b54855be71bbd7780a82e93b3e54bb63b7f362ed76e394aa7ffadc0db15`。
- `src/objects.rs`：SHA-256 `60e7e8542c43c6b4a3c17a050987570bee8ac272601a7ea54362cafff7f0810c`。
- `src/store/mod.rs`：SHA-256 `e273e4721022cc9d5a10c1e5c96b4dfc010a2f7b764e8ed3720d530dc55d6059`。
- 当前实施记录：
  - `tasks/iteration13/context-implementation.md`
  - `tasks/iteration13/cli-implementation.md`
  - `tasks/iteration13/session-continuity-implementation.md`
  - `tasks/iteration13/context-update-policy.md`
  - `tasks/iteration13/context-reset-catalog.md`

静态定位：

- 投影和预算：`sources/braid/src/context.rs:233-360`
- Issue/PR 展开：`sources/braid/src/context.rs:377-440`
- description Invalidate：`sources/braid/src/objects.rs:770-790,873-949`
- comment 通知：`sources/braid/src/objects.rs:1062-1133`
- hide/delete：`sources/braid/src/objects.rs:1171-1238`
- resolve root/cutoff：`sources/braid/src/objects.rs:1243-1298`
- 当前根提醒：`sources/braid/src/objects.rs:368-426`
- Issue/PR 本地 snapshot：`sources/braid/src/objects.rs:1413-1474`
- close/ready/merge：`sources/braid/src/objects.rs:1805-2055`

当前源码只经过编译和归档只读 CLI 核对，没有真实写操作、模型运行、并发送达、休眠 resume 或预算降档的运行验收。因此“当前语义”是源码与文档静态结论，不写成已部署/已观察保证。

## 2. 历史运行与冻结实现

- GitHub 终态 DB：`runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/braid-state/braid.sqlite3`，SHA-256 `98a503029161ce12a6a4d9f6c2be5193b3f2fab0a3ed41871a9a498e32b3399d`。
- Sheet 终态 DB：`tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/braid-state/braid.sqlite3`，SHA-256 `15dec2a9b7697395fd25ba81037cc4ec2487ec7b7a88d56b343bac129e65643d`。
- I11 冻结源码：`runs/iteration11/20260930-completed-turn-resume/build/braid-source.tar.gz`，已有材料记录 SHA-256 `fa7e91a0…675fc28`。
- 冻结 `objects.rs` 证据副本：`tasks/iteration11/braid-context-methodology/evidence/frozen-src-objects.rs.txt`，SHA-256 `db5d79c17810ea08b61d6ccfd90daa4f7db102c44c6a769ec700fd252ca0f751`。
- 历史机制与版本：`tasks/iteration11/braid-context-methodology/runtime-semantics.md`。
- 完整 lineage：
  - `tasks/iteration11/braid-context-methodology/report.md`
  - `tasks/iteration11/braid-context-methodology/root-causes-deepening.md`
  - `tasks/iteration11/braid-context-methodology/maintenance-activity-timeline.md`
  - `tasks/iteration11/sheet-effectiveness-analysis/full-lineage.md`
- CLI 真实交互：
  - `tasks/iteration11/braid-cli-agent-experience/interaction-cases.md`
  - `tasks/iteration11/braid-cli-agent-experience/semantics.md`
  - `tasks/iteration11/braid-cli-agent-experience/report.md`
- 需求树协作边界：
  - `tasks/iteration11/requirements-tree-collaboration-plan/plan.md`
  - `tasks/iteration11/requirements-tree-collaboration-plan/context-boundary-review.md`

历史实际 binary 和当前工作树的关键差异见 `report.md`；不能用当前 reply-ID 拒绝、description-only reset 或精确回执倒填 I11 行为。

## 3. 本研究采用的真实案例

- GitHub Issue #6：DB `local_items.node_id='issue:6'`。
- GitHub comment #89：DB `local_comments.comment_id=89`。
- GitHub thread #308：`tasks/iteration11/braid-context-methodology/evidence/continuation-comments.json` 与 `comments-324-327.json`。
- GitHub #256/#257：`tasks/iteration11/braid-cli-agent-experience/interaction-cases.md` C8。
- GitHub PR #23：`tasks/iteration11/braid-context-methodology/final-pr23-flow.md`，comments #341/#345/#347/#348/#349。
- Sheet PR #9：Sheet DB `local_items.node_id='pr:9'`。
- Sheet thread #1 与 167,672 字符输入：`tasks/iteration11/sheet-effectiveness-analysis/full-lineage.md:87-101` 和 `full-lineage/primary-reading.md:8`。

计数来自 DB 的只读 SQL。它们描述维护面，未计算实际模型 token，也不建立得分因果。

## 4. 外部官方资料

- GitHub：[About issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/about-issues)
- GitHub：[Creating issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)
- GitHub：[Assigning issues and pull requests](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users)
- GitHub：[Managing labels](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)
- GitHub：[Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)
- GitHub：[Pull request reviews](https://docs.github.com/en/pull-requests/reference/pull-request-reviews)
- GitHub：[Commenting on a pull request](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/commenting-on-a-pull-request)
- GitHub：[Incorporating feedback](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/incorporating-feedback-in-your-pull-request)
- GitHub：[About notifications](https://docs.github.com/en/subscriptions-and-notifications/concepts/about-notifications)
- GitHub：[Managing disruptive comments](https://docs.github.com/en/communities/moderating-comments-and-conversations/managing-disruptive-comments)
- GitHub：[Using issue and PR templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- Google Engineering Practices：[Writing good CL descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html)
- Google Engineering Practices：[How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html)
- Google Engineering Practices：[The standard of code review](https://google.github.io/eng-practices/review/reviewer/standard.html)

GitHub/Google 是成熟实践参照，不是 Braid 已实现能力或天然最优制度。尤其 typed dependencies、labels、review decisions 和批量 review 当前不在 Braid 本地对象模型中。

## 5. 外部一手研究

- Sadowski et al. (2018), [Modern Code Review: A Case Study at Google](https://research.google/pubs/modern-code-review-a-case-study-at-google/)；[论文 PDF](https://storage.googleapis.com/gweb-research2023-media/pubtools/4476.pdf)。12 次访谈、44 份问卷、约 900 万 reviewed changes、约 1300 万评论；单一大公司外部适用性有限。
- Bosu, Greiler & Bird (2015), [Characteristics of Useful Code Reviews](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bosu2015useful.pdf)。五个 Microsoft 项目约 150 万评论；usefulness 含作者感知和分类器扩展，不等于 Braid token 或最终质量。
- Gousios, Storey & Bacchelli (2016), [Contributor Perspective](https://doi.org/10.1145/2884781.2884826)。645 名活跃 OSS contributor 及 GitHub traces；志愿者生态与封闭 Agent 团队不同。
- Gousios et al. (2015), [Integrator Perspective](https://repository.tudelft.nl/record/uuid%3A757f9888-abf4-4dd5-a734-d5280e189a67)。749 名 integrator 及项目数据。
- Bacchelli & Bird (2013), [Expectations, Outcomes, and Challenges of Modern Code Review](https://doi.org/10.5281/zenodo.1401198)。Microsoft 多团队观察、访谈、问卷与评论分类。
- Bjarnason et al. (2014), [Aligning Requirements with Verification and Validation](https://arxiv.org/abs/2307.12489)。六家公司 30 名从业者；支持需求变化、VV 与共同理解需要对齐，不规定某个 Braid 模板。
- Tian et al. (2021), [Impact of Traceability on Software Maintenance and Evolution](https://arxiv.org/abs/2108.02133)。63 篇研究的 mapping study；同时报告变更管理收益与维护 trace link 成本。
- Liu et al. (2023), [Lost in the Middle](https://arxiv.org/abs/2307.03172)。支持相关信息在长上下文中位置会影响使用，不支持统一字符上限或“长上下文必然无用”。
- Yang et al. (2024), [SWE-agent](https://arxiv.org/abs/2405.15793)。支持 Agent–Computer Interface 和按需仓库导航的重要性；不是多 Agent Braid 协作实验。
- Jimenez et al. (2024), [SWE-bench](https://arxiv.org/abs/2310.06770)。真实修复联合 issue description 与代码库；不证明任一 description 格式最优。
- Packer et al. (2024), [MemGPT](https://arxiv.org/abs/2310.08560)；Park et al. (2023), [Generative Agents](https://arxiv.org/abs/2304.03442)。只用于“工作集 + 按需慢层”的研究启发，不把其实验架构当成 Braid 保证。
