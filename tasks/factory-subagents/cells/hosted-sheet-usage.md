# 官网 Sheet 的 Pi 子代理使用证据

本次仅分析已有归档，不运行模型、应用、测试或探针，不修改运行或源码。时间均为 UTC。**生成来源 `bd7ac1b232ba` 与评分回放 `1efffb84ae1b` 不是两次生成。** 回放沿用交付 `main=402336217ef1329f71b8f15560cfbf19d514e82f`，没有重新调用模型；58/100、8/24 的分数不能归因于之后的子代理指引改动。

证据入口是 `runs/official-collaboration-review/data.json` 的 `sheet` 索引、同目录 `sheet.sqlite3`，以及 `runs/e20260928-completed-replay/sheet/source-workspace.zip`。下文归档相对路径均以 `template/.factory26/20260927-082825-d9c4f6ea/` 为根。回放边界另见 [既有诊断](../../sheet-score-diagnosis/packet.md) 与 [迭代记录](../../braid-product-reaudit/iteration-report.md)。

## 覆盖与计数

| run | 原生可见范围 | Pi 执行尝试、结果及父消费 | 耗时与 token |
| --- | --- | --- | --- |
| 来源 `bd7ac1b232ba` | `work/native-homes/` 的 682 个 JSONL，全部可解析；另有 `native/` 的 94 份同 session 快照，按 session ID/消息 ID 去重 | 可见记录中 `subagent` 和 `subagent_status` 均为 0；有 38 次 `subagent_wait`，全部返回无活动 run。未发现 Pi 子会话 transcript 或子报告消费链。不能说模型生成了 38 个失败子任务 | 38 次 wait 的消息落盘时间到工具返回合计 0.386 秒，单次 0.001–0.227 秒。这是记录间隔，不含此前模型推理。没有可归属的 child token 或 child 执行时长 |
| 回放 `1efffb84ae1b` | 已完成应用快照的官方评分 | 没有新生成，不能把复制来的 native 记录再计一次调用 | 不追加模型或 child token |

SQLite 有 686 个 `provider_sessions`，其中 4 个路径没有对应归档 JSONL。因此这里的零是**已保留轨迹的观察值**，不是对缺失文件断言零调用。缺失文件分别为 `01a0e25e-9a5b-7200-a648-4f6a0668bd29`（10:17:25，replaced）、`01a0e32b-4e36-7267-91b8-21ceaddb839c`（14:01:01，idle）、`01a0e32b-5d6c-726e-afda-749d01724088`（14:01:05，idle）、`01a0e3cd-bc3a-75df-8396-d0a72ca0999e`（16:58:26，running）。不能由数据库 lifecycle 推断这些文件中有无调用。

SQLite 的 `agent_instances` 实际是 7 个 Braid 成员：6 个 issue_agent、1 个 pr_implementation_agent。682 个 Pi session 是这些协作成员的原生会话/重建，并非 682 个 Pi 子代理。原生 `model_change` 显示 551 个 session 使用 `factory26/glm-5.3-flash`，131 个使用 `factory26/deepseek-v4-flash`；这些是 Braid 成员实际模型，不是子代理模型。全工具名扫描也没有子代理执行别名；Bash 参数中没有发现 `subagent` 或 `pi --`/`pi -p`/`pi -e` 的旁路启动，不过这不构成对任意间接脚本的穷尽证明。

## 38 次 wait 实际在等什么

20 次显式指定 Bash/PBB 作业 ID：`bg001` 11 次，`bg002`、`bg004` 各 2 次，`bg003`、`bg009`、`bg010`、`bg019`、`bg030` 各 1 次；另有 18 次无特定 ID 的泛等。前者返回 `No active run matched`，后者返回 `No active async runs or registered provider work in this session`，并非启动 guard 拒绝，也没有 child lifecycle。

| Braid 父工作项 | 实际父模型 | wait 次数 |
| --- | --- | ---: |
| issue #1 | glm-5.3-flash | 9 |
| issue #2 | deepseek-v4-flash | 6 |
| issue #3 | glm-5.3-flash | 7 |
| issue #4 | deepseek-v4-flash | 3 |
| issue #5 | glm-5.3-flash | 3 |
| issue #6 | glm-5.3-flash | 4 |
| PR #1 实施成员 | glm-5.3-flash | 6 |

可复查例：`work/native-homes/pi-deepseek-fast-01a0e244-5283-72d2-a653-e757fa43a1d9/2026-09-27T09-48-44-652Z_01a0e244-56ec-7212-8367-589f955520a5.jsonl` 第 67 行先返回“Bash job bg002 moved to background after 30s”，第 72 行父明确说等待 bg002，并于 09:52:08.153 调用 `subagent_wait`；第 73 行 09:52:08.155 返回没有匹配 run。随后第 75 行 PBB 列表显示 bg002 已 exited。这里能定位接口混用，不能把 600000ms 请求超时记为等待了十分钟。

归档 `native-config/*/native-template/agents/` 的角色配置已有 advisor（kimi-k3）、executor/explorer（deepseek-v4-flash）、browser-operator/vision（deepseek-v4-flash-vision-exp），均声明 `defaultContext: fresh`、不继承项目上下文/skills。**这是可用角色与 fresh 配置证据，不是实际执行或 fresh 子会话证据。** 没有子会话时，实际角色模型、启动错误、完成状态、父消费和 child token 均不可虚构。

## 直接读图与后续本地 vision 的区别

在同一原生索引中定向检查 `read` 图片路径及对应工具结果：13 次调用均有 image 类型返回，其中 12 次读取需求参考图（7 个唯一文件），1 次读取实现验收失败截图。不是 vision 子代理。

| 父会话/工作项 | 时间 | 直接读取内容 |
| --- | --- | --- |
| GLM issue #1，`native/000-…jsonl` 第 15、18 行 | 08:29:13、08:29:38 | workbook-home、worksheet-overview、sort-range |
| DeepSeek issue #2，`native/002-…jsonl` 第 27 行 | 08:34:32 | workbook-home、create-workbook |
| 同上第 191 行 | 09:22:19 | checks/results 下 formula-bar/inline-editor 的 test-failed-1.png |
| GLM issue #1 重建会话，`native/010-…jsonl` 第 22、25 行 | 08:55:48、08:55:55 | workbook-home、create-workbook、worksheet-overview |
| DeepSeek issue #4，`native/028-…jsonl` 第 34 行 | 10:02:01 | worksheet-lifecycle、manage-rows、manage-columns |
| GLM issue #6，`native/030-…jsonl` 第 33 行 | 10:03:23 | sort-range |

这些记录证明图片工具返回进入了父会话，不能单凭返回证明模型正确理解或完整落实图片约束，也不宜把整段父会话 token 全算视觉成本。之后本地 DeepSeek Sheet issue #5 曾实际委派一次 vision，子模型为 `factory26-visual/deepseek-v4-flash-vision-exp`，父于 03:07:49 读取报告；但初始设计评论早于视觉报告完成。详见 [本地视觉取证](../../braid-product-reaudit/vision-requirements-evidence.md)。可确认的变化是“官网父直接读图”到“本地出现独立视觉分析并回传父会话”，尚无控制变量支持分数或净收益的因果比较。
