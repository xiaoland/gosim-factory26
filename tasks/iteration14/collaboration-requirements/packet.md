# I14 协作与 ARC 需求方法改进

2026-10-02。两项独立技能的改进由本会话实施，主会话持有集成、冻结与实际热恢复。任务保持一个紧凑计划；独立 advisor 只返回方法判断，不另建实施分支。

## 目标与授权

让组织、接手、新产品行为裁决、PR 采用/合并和完成判断消费原承诺与适用结果，避免把发布、局部检查或错误共同约定视为完整兑现。委派消息确认用户已复核树并授权继续两技能改进、热修到 I14 系列；主 packet 记录用户明确要求集中于 braid-collaboration 与 ARC 需求方法。本会话允许当前任务 commit，不 push，不启动模型实验或操作现场。

源码所有权限于 `harness/skills/braid-collaboration/`、`harness/skills/arc-bench/`，及本 packet。四个 I14 root/run 入口只给主会话建议，不编辑。共享仓库其它修改不覆盖、不纳入提交。技能正文保留独立文件，不内联进 prompt。禁止 Factory/Braid/SVC 测试、smoke、probe；不向生成材料注入历史应用缺陷答案、分数、隐藏反馈或 rollout。

## 当前事实与方案

证据为 [官网 Flash/Sheet 分析](../../iteration13/i13-2/flash-sheet-score-analysis/findings.md)及 [I14 对账](../evidence.md)。对象和 packet 实际被使用，错误约定也成功接续；首次遗漏与最后放行应分开。ARC 主技能与部分 reference 已读且早期有采用，覆盖 reference 无读取记录；补读不是充分修复。

现有技能已有正确原则，缺的是把原则绑定到下一项决定：接手时找回尚欠完整消费者结果，公开新增语义时对照原承诺，接口条件改变时检查真实调用方，PR 采用/合并及最终关闭时按声明范围消费证据。拟在现有文件重写相应动作及按问题加载 reference 的入口，保留合理局部接受与证据复用，不增加模板、固定三层检查或全节点同步表。通用协作与 ARC 格式保持分离。

先核对现有分发/发现与各 reference，再独立 advisor 审视最小路径，完成材料并按真实调用路径读回。旧源码路径显示四 I14 build 均选择两技能，run 的 MAIN_SKILLS 明确启用；根 issue 当前只提示 ARC 主文件及泛泛适用 reference。实际材料目录由 run 显式复制，完整参考目录随技能取得。

## 验收与效果边界

材料验收核对独立文件及相对链接可达、四 variant 的分发/发现入口、旧规则不矛盾、相关决定能从主文件到达问题 reference。独立方法复核从中性场景判断下一动作，不用阅读次数或角色身份冒充效果。不运行设施测试或模型实验。

能判别的方法采用是：接手任务含原延期承诺的完整结果，新增语义冲突被裁决，真实请求与新接口条件一致，局部证据只支持其范围，未证实义务保持开放。错误首次产生、交付前检出和最终残留分开记录；本次材料改进不能证明这些效果已在 I14 运行发生，也不能给成功率增益。

材料实现与独立方法复核已完成。下一步由主会话集成 root 发现入口、冻结材料并按已授权范围热恢复；本会话只提交这两项材料与 packet。主会话需为每个新/恢复 run 保留旧新技能身份及采用时点；暂停的 baseline 不由本会话恢复。

## 实现与独立复核

改动仅为两个 SKILL 的 description/问题入口及现有 references，共 8 个材料文件；平台 reference 不改。协作方法在组织时保留完整消费者结果、接手时恢复前序延期、传播新约定前比较原承诺、接口改变时核对真实调用、采用/合并时限制结论范围。ARC 方法从原树与适用父层找回义务，在接手、行为变化、审阅采用和完成决定时进入覆盖回查。中性编辑器/导入器例子说明不同判断；没有写入历史题目的具体业务修复。

独立 advisor 先基于指定原证据提出三项决定动作，再对改后材料作中性反例复核：仅错误提示的接手范围须恢复状态保持与重开持久化；后端含版本的请求通过不能证明遗漏版本的 UI 调用正确；检查输入修正与违背原承诺的新保存语义须分别判断。它同时指出有效编辑器结果可先合并，整体不能因此关闭；若漏接线的正是编辑器，旧结果也不可继续视为有效。这是方法决策自洽性复核，不是实际运行采用或收益验证。

逐文件阅读及 `git diff --check` 未发现冲突或格式问题。沿用 SVC 对原要求/派生设计、判据/结果适用性、文档归属与 packet 的现有方法，不复制通用教程。两主文件按问题进入已有 reference；reference 之间的相对地址及所引用四 SVC SKILL 均实际存在。

四 variant 的 `build.py` 明确选择这两技能，`run.py:MAIN_SKILLS` 将主文件加入全部 Braid 成员的 Pi `--skill` 发现入口，并通过 `scripts/agent_support.py:copy_skill` 复制整个 references。`scripts/package_agent.py:assemble` 使用同一复制入口。成员 instructions 已要求开始/接续时读取 braid-collaboration。原生内部角色的自动 skills 选择未包括这两项，局部委派需按本次问题传独立文件入口；不据文件存在宣称自动读取。本次没有运行打包、prepare、测试、smoke 或模型；上述分发事实是源码路径与文件读取的验收，不代表新冻结包或现场已取得它们。

## 主会话的最小接口与热部署前提

四个 `run.py` 的 root prompt 当前只有 ARC 主文件和泛泛 reference 提示。建议保持本次需求路径与最终交付约定，使用 arc-bench 当前 frontmatter 的名称、description 和实际 `SKILL.md` 路径作发现信息；不用在 root prompt 再复制行为裁决或覆盖方法正文。braid-collaboration 已有 native discovery 与成员读取入口，不需扩角色正文、工具接口或通用 Harness 的 ARC 耦合。两项 SKILL 现在会把相关决定引向适用 reference。

恢复现场不能靠源码更新自动获得材料，也不能假定旧会话因技能换版就已采用。主会话须在实际恢复输入中交付完整技能目录，读回逐文件 SHA256；保留旧材料、原需求、Git/Braid/native 身份与恢复来源。在恢复后的本次工作入口，只提供技能名称、当前 description、实际独立文件路径和版本变化身份，由成员根据当前决定读取；不要把本报告、隐藏反馈或历史具体修复送入生成会话。各 run 保留部署与实际采用时点，未取得采用证据时如实记未观察；暂停 baseline 不因此自动接续。这里不要求额外 ACK 或全部工作重读历史。

四个 variant 的机制差异保持原样；实际容器、Console、冻结/新启动与恢复一致性由主会话负责，本会话不操作。不新增实验矩阵，效果取证仍消费已授权运行。

## 材料身份

旧材料按提交 `23fd80acbe5ef31d0228c3e1bbc3e330b12b7fe5` 读取；本任务 commit 包含以下新材料，platform 行未变。实际热恢复须读回独立文件，不能只比较打包目录名。

| 文件（相对 harness/skills） | 旧 SHA256 | 新 SHA256 |
| --- | --- | --- |
| `arc-bench/SKILL.md` | `acde79cd630725a0fe7db3d31044db26cb6e1f939789eda07a44badc29667e63` | `b92b281913728c54234baed1ceb64518b603a44f246cda58846966eb0a52f2dc` |
| `arc-bench/references/platform-delivery.md` | `d042032f153e5346dee6913e972c02c322ade51231c6a32aafa172d26423a1dc` | `d042032f153e5346dee6913e972c02c322ade51231c6a32aafa172d26423a1dc` |
| `arc-bench/references/reading-requirements.md` | `81adef409562e0cd1e7b1fb4f684993e7f5eb430be609df25483e27a8e881cb4` | `363686fcf65f95ec0855b92c2cdf6e009f5731e2cfc6fffd65124c51c3537d54` |
| `arc-bench/references/tracing-and-reviewing-coverage.md` | `7f2948601deb3bce8f7a195a7bc7bb04dbc394fc19413eb520bfa3c0fa0fdad8` | `73844a8858351d62036d9b51bac0bedd9ed6f8efdc8e8275eaac6a7580ac3fc5` |
| `braid-collaboration/SKILL.md` | `4a362dbaee96f7fbf5417cecbf496a8e0c4f1d5524a2a18b158ee8cd85fd5049` | `a30cfb7128690b1ef66653bb7e53cd315b4e32845d5c62dd15663b6620dea08a` |
| `braid-collaboration/references/accepting-and-closing.md` | `353e03a6688b43f1b088dcdfaf0a1b1317497d5f8251323f0f4485352ae2a9ca` | `33043321cc8a971f27ca2dcb780eee62aeee72e5a2337d8a910a5d5194d2bc1a` |
| `braid-collaboration/references/handoffs-and-changes.md` | `4f9c12a17cefa7ea7475e2bcd646ddfb7281325c7d164c45b6315d3e0fb9e726` | `c2e2d2d1071687c8310fa8597f3ed21d29d9e5e339ec788b47cf2bf9d16991a2` |
| `braid-collaboration/references/organizing-work.md` | `96c666e9b71334dc9d5aeee742c2223461f66247ffcd49aaf52db2f6f5cf8195` | `7f785f4e29837ec43457692f3140c7e33f8e78ebded997c3527518090b024a8b` |
| `braid-collaboration/references/worked-example.md` | `6ba754936ffb40ee725150cc3ae9eb012daa6af599b2111b6a7370f8fc683d4b` | `f6f30f293f1f3eaa4e923bd9036a56fa3f84b3594aa516d0872f2bc25ddf4aa9` |
