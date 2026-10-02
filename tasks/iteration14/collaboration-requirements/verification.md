# 材料验收与主线交接

2026-10-02。此文件持有材料身份、完成依据和待回传的实际效果。职责与入口方案归 [design.md](design.md)，整体状态从 [packet.md](packet.md) 恢复。

## 已完成范围

| 提交 | 结果 |
| --- | --- |
| `ed9a97bb` | 首轮把协作原则绑定到接手、行为裁决及采用/完成决定。 |
| `60ba2e01` | 撤回 root 重复 description 的建议，收敛独立技能换版入口。 |
| `a31eb888` | 两技能 What／Why 改写与中性例子调整，共8个材料文件；平台合同未动。 |
| `b13f4290`（主线） | cleaner fast/root 成员入口取消固定读技能及对象重读开场，已只读核对源码；不代表热部署。 |

逐文件阅读、独立地址及交叉引用核对、`git diff --check` 已完成。没有运行 Factory/Braid/SVC 测试、smoke、prepare、打包或新模型实验。

独立 advisor 从原证据审视方案，再用中性反例检查改后条件：责任接手不解除完整结果；修检查输入与新行为合法性分别成立；用户调用缺少接口条件时，后端通过不足以支持该入口。What／Why 复核另区分了可取得的私有 packet、同格式但不同读取时机的新消费者，以及局部合并与整体关闭。复核支持材料判断自洽，不证明真实采用或收益。

## 分发与恢复路径的证据

四 I14 variant 的 build 明确选择两技能，run 的 MAIN_SKILLS 对全部 Braid 成员显式提供 Pi `--skill` 入口。`scripts/agent_support.py:copy_skill` 复制整个 references，package assemble 使用同一路径。内部原生角色未自动选择这两技能，按具体委派取得独立入口；文件存在不能代替实际读取。

已冻结 I14 runtime 的 `dist/core/skills.js:275` 只生成 name、description、location，`system-prompt.js:111` 加入系统输入，`resource-loader.js:332` 在 `--no-skills` 下仍加载显式技能。Braid Pi 恢复保留原会话并重启进程；`submission/recover_completed.py` 的显式刷新备份旧材料，重建 launcher 并记录新哈希；packager 从完整冻结 base 取得材料。这些是源码及冻结 runtime 的读取证据，未取得本次实际恢复 payload。

## 主线剩余回传

主线或对应 owner 持有最终制品、恢复通知、实际 run/容器及 Console。本任务不重复运行台账或操作现场。交接条件如下：

- 冻结和恢复包含完整独立技能目录，逐文件读回下表的新 hash，保留旧材料、原需求及同一恢复时点的 Git/Braid/native 身份。
- 换版通知到达当前实际实施、整合与检查的消费者；只通知 root 未必涵盖其它保留会话。通知不注入技能正文、历史题目答案或隐藏反馈，不统一强制复读或要求全员 ACK。
- 实际系统发现绑定新文件；相关消费者在当前决定中取得并采用适用方法。部署、送达、读取及决定改变各自留证，不用读取计数或角色身份冒充效果。

当前本任务尚未取得这些完成回执；这不宣称其它 owner 没有进展。整体运行状态以 [I14 packet](../packet.md) 与 [恢复 packet](../cleaner-hidden-context/packet.md) 为准。

## 实际效果的判别

已有投影足够且无新协作决定时，负责人直接推进工作，可以减少机械开场和重复查询；存在折叠、索引、新交接、责任冲突或候选缺口时，仍能定向取得必要信息。cleaner 面对未证实主张或冲突不会制造已解决事实，完整延期义务、新行为判断与真实调用的闭环仍保留。

效果取决于重复获取与整理成本是否下降，以及原承诺是否仍被兑现；少一句开场、少一次 view 或 cleaner completed 均不足以证明。首次错误形成、交付前发现修正、最终残留分开记录；本次不能给出成功率或评分增益。Hook 暂缓，baseline 的主动暂停不由本任务恢复。

## 最新材料身份

下面比较首轮改进提交 `ed9a97bbb8415633dcf1628738ab37e9a035ca7f` 与What／Why 提交 `a31eb8889dbaa8843a55377594354a6462a8c37d` 的材料；首轮旧新身份表仍在该提交的 packet 中保留。`60ba2e01` 只修改入口判断，不修改技能。实际冻结/恢复以本表的新值读回，platform 行未变。

| 文件（相对 harness/skills） | 首轮 SHA256 | 当前 SHA256 |
| --- | --- | --- |
| `arc-bench/SKILL.md` | `b92b281913728c54234baed1ceb64518b603a44f246cda58846966eb0a52f2dc` | `f68e56dc12d7b4093ed76a0a8dcb1db73b73142c1287e2fc0494b71966553f4b` |
| `arc-bench/references/platform-delivery.md` | `d042032f153e5346dee6913e972c02c322ade51231c6a32aafa172d26423a1dc` | `d042032f153e5346dee6913e972c02c322ade51231c6a32aafa172d26423a1dc` |
| `arc-bench/references/reading-requirements.md` | `363686fcf65f95ec0855b92c2cdf6e009f5731e2cfc6fffd65124c51c3537d54` | `d63e2d01b39e78471ac1fcb3c39175bc9000ada612d71c14b649ead904cf272c` |
| `arc-bench/references/tracing-and-reviewing-coverage.md` | `73844a8858351d62036d9b51bac0bedd9ed6f8efdc8e8275eaac6a7580ac3fc5` | `31dc1e18d9705ddad7fed5c3341e796f657beda6e7409ebae9cbf0c033c66a2d` |
| `braid-collaboration/SKILL.md` | `a30cfb7128690b1ef66653bb7e53cd315b4e32845d5c62dd15663b6620dea08a` | `b5008d92d6aa9b687597d21fb7db0ad2fac07fe59880559e7150dc4f6e1da5c4` |
| `braid-collaboration/references/accepting-and-closing.md` | `33043321cc8a971f27ca2dcb780eee62aeee72e5a2337d8a910a5d5194d2bc1a` | `ce894fc7c513cff1f98a75c8855402a4eb07a096d9a393ec6a8de1f584470112` |
| `braid-collaboration/references/handoffs-and-changes.md` | `c2e2d2d1071687c8310fa8597f3ed21d29d9e5e339ec788b47cf2bf9d16991a2` | `4ff3e297ac5c9ce0944cf486d15fab559a3d4a161b656dfe97110e4f5fd6e348` |
| `braid-collaboration/references/organizing-work.md` | `7f785f4e29837ec43457692f3140c7e33f8e78ebded997c3527518090b024a8b` | `6608a81d8a3ba1089020f44e49da7cf48addc015257edad649a0868272312c28` |
| `braid-collaboration/references/worked-example.md` | `f6f30f293f1f3eaa4e923bd9036a56fa3f84b3594aa516d0872f2bc25ddf4aa9` | `7f943770117622391ff6831e1df98e74a47d5b5eb83a36f7e2ecf740d91e74f1` |

