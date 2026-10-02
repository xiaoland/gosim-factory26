# I11 advisor provider 路由核对

## 当前结论

已确认的事实是：advisor 的角色声明、原生子任务 descriptor 和 native home 的模型 registry 都指向 `factory26/kimi-k3`，但两个实际 advisor 子会话的首条 `model_change` 都是 `openai/gpt-5.5`，随后以 OpenAI 401 结束。explorer 在同一父会话通道中实际选中了 Factory26 DeepSeek，因此不能把问题归因于 Factory26 registry 整体缺失，也不能把 Kimi 401 当作上游可用性结论。

根因已由真实材料与运行时代码共同确认：恢复包的 `work/tmp/pi-subagents-uid-1000/model-exclusions.json` 仍有未过期的 `factory26/kimi-k3` 排除项，原因是此前 Kimi 429。`pi-subagents` 的 `buildModelCandidates()` 将显式 primary 也交给 `filterFallbackCandidates()`；排除项使 `modelCandidates` 变成空数组。`subagent-runner.ts` 对“已提供但为空”的 candidates 采用 `[undefined]`，`buildPiArgs()` 因此不传 `--model`，Pi 继而选择 ambient `gpt-5.5/medium`。这条链解释了 descriptor 正确、显式 model 仍回落以及 explorer 正常的差异。

持久化材料没有保存最终 argv 本身，但代码路径和排除文件足以确定其效果：advisor 子进程实际没有有效 model candidate，故最终 argv 不含 `--model`。此前关于“环境变量优先级已确认是根因”的结论已撤回。

此前在 `variants/pi-braid-i11/run.py` 中尝试的 Factory26 环境优先级改动与上述排除链无关，现已撤回；它不能作为 advisor 修复，也不应进入本次接续包。

## 真实记录

取证来源是 WSL 冷接续 run：

`/home/yyh/Development/factory26/runs/iteration11/20260929-cold-resume/generation/runs/pi-braid-i11--hackathon--github-f402061b5bc88f`

Issue10 原生父会话为 `pi-deepseek-fast-01a0eded-85a1-7891-aa22-4da1a93d31fc`，子会话如下：

- `c47212f3-0cb7-465f-a18e-f55115701672`：descriptor 为 `factory26/kimi-k3:high`；实际首条模型记录为 `provider=openai, modelId=gpt-5.5`，随后 401。
- `78bd6c1a-3b7f-49d6-92dc-dbe0db5686db`：descriptor 同样为 `factory26/kimi-k3:high`；实际同样为 `openai/gpt-5.5`，随后 401。
- explorer：descriptor 为 `factory26/deepseek-v4-flash:high`，实际记录为 Factory26 DeepSeek。

父 native home 的 `agents/advisor.md` 保持 `model: "factory26/kimi-k3"`；`models.json` 也包含 `factory26/kimi-k3`。读取过程中没有输出凭据内容。advisor 实际 session 的第一条模型事件显示 thinking 为 `medium`，与 descriptor 的 `high` 不一致，和空 candidate 后走 Pi 默认模型的代码路径相符。

本次恢复包中的排除文件只摘录非敏感字段如下：`factory26/kimi-k3` 的 `recordedAt` 为 `1790681800857`，`expiresAt` 为 `1790768200857`，原因为 Kimi 账户余额告警导致的 429；advisor 启动时间为 `1790698315399` 与 `1790698341566`，所以该排除项在两次尝试时都有效。文件还记录了 OpenAI 模型的 401 排除项，但它们不是 advisor 回落的起因。

## 恢复入口边界

本次冷接续由 `submission/recover_completed.py` 启动，绕过变体 `run.py` 的 `generate()`。它只在 `refresh_native_materials` 为真时动态导入包内的 `run.py`，而当前冷接续材料为 `refresh_native_materials=false`；因此工作区中的变体尝试没有作用于已发生的 advisor 子进程。

即使刷新材料，`recover_completed.py` 使用的是恢复包内的 `run.py`，而不是自动读取仓库当前文件。已核对冷接续所用 base/agent 包中的 `run.py` 仍为旧版本（sha256 `cdc34db5...`），所以不能把源码工作区的改动视为已进入运行包。

## 接续决定

Sheet 可按现有已批准材料继续封包/启动；本报告不再把环境优先级改动作为阻塞条件或完成声明。若后续要修 advisor，应在 Pi runner 边界阻止“显式 primary 被排除后以空 candidates 静默回落到 ambient 默认”的行为：要么保留显式 primary 并让真实 Kimi 错误可见，要么在空 candidates 时硬失败；不能让它无提示地改用 OpenAI。仅清除环境变量优先级或只重写 `models.json` 不修复这条链。本项授权只覆盖共享补丁准备；不重放失败 advisor、不做模型 probe，补丁尚未部署到运行材料。

修复后的验收证据应来自新的真实运行记录：descriptor、子 session 首条 `model_change`、thinking level 和首个 provider 响应彼此一致。descriptor 单独不足以证明修复。

## 已准备的修复（未部署）

最新授权已将上述候选耗尽回退修复纳入 I11 的 `pi-subagents` 接线。补丁
`harness/npm/patches/pi-subagents-0.56.0-model-exclusion-boundary.patch` 做两层保护：

- `buildModelCandidates()` 在显式候选全部被活动排除时抛出诊断错误，包含排除类别和 ISO 到期时间；仍有可用配置 fallback 时保留既有 fallback。
- `subagent-runner.ts` 在单步、dynamic fanout 预检以及恢复或持久化路径对空 `modelCandidates` 直接失败，不再把它转成 `[undefined]`；因此不会省略 `--model` 让 Pi 选择 ambient provider。

`submission/Dockerfile` 已在既有 completion patch 后应用该补丁，`scripts/runtime.py` 已将三个目标文件纳入缓存校验，并把补丁哈希写入 `runtime-source.json`。对 I10 冻结的真实 `pi-subagents` 源码副本执行了 `patch --dry-run --fuzz=0` 和一次临时副本应用核对；未重建 runtime、未部署到正在运行或未冻结的 I11 材料，也未进行模型调用。新的真实运行仍需核对 descriptor、首条 `model_change`、thinking 和首个 provider 响应的一致性。
