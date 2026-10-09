# I15 Pi 与运行时接入

本轮用户要求核对 pi-minimal-vv 已定位的 Pi 和运行时缺陷是否进入 I15，并明确授权落地上下文界限及根负责人跟进。此处记录实际源码和交付材料；不改在途运行，不启动模型或官网评测，不执行 Factory/Braid 测试或包 smoke，不提交或推送。

## 原材料与接入缺口

I15 的 standalone 完整底包固定为 `runs/deadline-20261003/i14-baseline/agent.zip`，SHA256 `e9f7b7d2a7ad88728dcf5c589db552dd1dde1731055d10563d161baf7b8733f5`。旧 builder 只覆盖四个 Pi 协议模块、launcher、native-managed 和 PBB CLI，未走公共 Pi retry gate。此前的 pbb-e2e overlay 已含跨会话 printKill 修复，但不能因此认为 PBB extension、原生子角色与嵌套 SDK 都已更新。

逐个读取旧底包与 pbb-e2e overlay 的实际成员，再与当前补丁目标比对。完整记录在 `runs/iteration15/materials/runtime-integration-20261007/patch-audit.json`。结果如下：

| 修复 | 原交付 | 本轮处理 |
| --- | --- | --- |
| pi-ai 连接重置的原生有限重试 | 旧通用 overlay 未含；Evo GitHub 执行者另行叠加 SDK，exact-runtime-readback 确认 d92542… | 统一补丁目标与 retry SHA 门控进入 builder。 |
| PBB 跨原生会话停止 | pbb-e2e overlay 的 CLI 已含 | 保留相同 CLI 字节 SHA 30b4bc…；从受 lock integrity 验证的 npm 原包应用当前补丁。 |
| PBB 同一推理期间后台回执合并、失败/中断后的后台收口 | 旧 extension 遗漏最新行为 | 当前 extension 进入 overlay，保留每个 job 原始结果，仅合并通知。 |
| pi-subagents 原生错误后保留工作和已保存结果 | 旧 index.ts 遗漏 | 当前 extension/index.ts 进入 overlay。 |
| pi-subagents foreground 生命周期初始化时序 | 旧 execution.ts 未采用当前初始化顺序 | 当前执行模块进入 overlay。 |
| 既有模型排除、开放工具、acceptance-off、Pi Braid 工具边界、context7、FFF、managed 接线 | 对应已审核目标字节相同，部分目标与上述后续修改重合 | 完整统一目标集进入 builder，避免未来手选遗漏。 |

builder 现在复用 `tooling/scripts/runtime.py::native_patch_specs` 的有序补丁目标集合，核对当前 patch 哈希及原生 retry SDK，再覆盖其实际成员。runtime_source 仍明确区分底包和窄 protocol 输入；窄输入不是完整可执行 runtime。模型路由、角色配方和 standalone gateway 继续来自原冻结底包。Lab observer/status、正式比赛上传和 vv 单 session main 的退出/接续控制属于各自生产者，未复制到 I15；它们不自动成为 Braid 的运行合同。

Mac 原生 `patch --fuzz=0` 重建暴露两处补丁上下文不足：printKill hunk 缺尾上下文，managed spawn hunk 的变化末尾缺上下文。已仅补上下文，不改变目标改动。原错误保留 `pbb-patch-failure.txt` 与 reject 原件；完整重建通过 `pbb-patch-output.json`。CLI 与上一轮显式修复逐字节一致；extension 与已有 managed 来源的差异仅为本轮共享 batch 通知、批量 job ID 回读及 aborted 终态处理，见 `pbb-previous-source-diff.patch`。

## 原生压缩与 Braid reset

Pi 原本只有 reserveTokens 配置，同时控制压缩阈值和摘要输出预算。对于真实 1M 模型，把 reserve 设为 755000 虽可提前到 245k，却会放大摘要请求输出预算；原生子角色继承同一个 agentDir/settings，128k visual 模型还会得到负阈值。因此采用 advisor 独立核对后的最小扩展：可选 `compaction.thresholdTokens` 只参与原生 shouldCompact 判定。

I15 原生设置为 enabled=true、thresholdTokens=245000；reserveTokens 默认 16384、keepRecentTokens 默认 20000 保持。实际触发为 `min(thresholdTokens 或 Infinity, max(0, 真实 contextWindow - reserveTokens))`。1M 模型约 245k 触发；128k 模型受真实容量限制，在 111616 以上触发；未配置该字段的正常容量模型沿用原行为。配置输入须为正安全整数，错误保留具体原因。摘要生成的 maxTokens 仍按 reserveTokens 计算，不使用 thresholdTokens。

新增原生 patch 已登记到 host/Linux 的共同生产输入与 Linux Dockerfile 实际应用顺序；包含 settings-manager 与 compaction 的 JS 和类型声明。Pi 两处已有 shouldCompact 调用共同消费该设置，不增加自定义双阈值、交接器或强制重启。完整 Python/JS/TS 语法检查通过，原生材料生成读回确认 fast/reviewer 的真实容量仍为 1000000、settings 为 245000。证据归 `native-readback-delivery/readback.json`，这是材料消费反馈，未实测模型压缩、摘要质量或费用收益。

Braid reset 继续是协作状态变化后重建原生会话的独立生命周期。profile.context_hard_bytes 约束渲染后的协作输入字节，context_soft_ratio 参与协作上下文选择；它们不代表原生累计 token，不由本轮改作 245k。新任务和 reset 仍遵守 Braid 已有停止、notice 与来源核对。

## 根负责人跟进

run.py 的现有 root_check_messages 现在要求核对当前负责 Issue/PR 实际讨论和实现进展，按需查看已发布 diff、工作区未发布改动和首次失败原件，对照原需求、责任边界及共享前提判断纠偏。已有充分进展可等待；无行动价值不发重复回执。沿用原五分钟 idle 检查机制。root/fast 的职责正文由主负责人更新，并在原生材料中读回；这些职责不内联技能正文。

当前交付为 `runs/iteration15/materials/runtime-integration-20261007/overlay.tar`，SHA256 `7fbf2347a2b235e81c7e2cee45da816171dc1188e9aa13a59b2441880c2225a3`，22,466,560 bytes、46 overlay 成员；99 个声明材料成员与实际底包/overlay/manifest逐字节SHA一致。新Braid SHA256 `8540ea7a07df53ff9a84d6e2c2532e5811c28e1ead9895243750217f74931c2d`，其编译与CLI反馈由reviewer负责人保存于 `runs/iteration15/reviewer-session/`。材料身份和实际归档读取分别归 `package-identity.json` 与 `overlay-readback.json`。旧 overlay、底包和运行现场均保留；交付材料形成不称为热部署。
