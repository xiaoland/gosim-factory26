# I13 根对照实施收据

2026-10-01。用户已明确“好的，可以启动 I13 了”，随后指定基线用 K2.7 Code 替代 K3，又更正“GLM-5.3 组继续使用 K3”。本页记录本轮独立制品及模型配置；实验启动、题目与宿主归主 packet。当前进一步取消 DeepSeek Braid 成员，已有运行的实际切换回执归 experiments.md；下方最初冻结哈希保持为历史来源。

| 制品 | 根 Issue | advisor | 可指派成员 |
| --- | --- | --- | --- |
| `pi-braid-i13` | GLM-5.3-Flash / high | `kimi-k2.7-code`，开启推理，不发送 effort | GLM-5.3-Flash / high |
| `pi-braid-i13-glm-root` | GLM-5.3 / high，root-only | `kimi-k3` / high | 同上 |

对照同时改变根模型和 advisor 模型，结果不能解释为仅根模型的消融。新增 `pi-glm-root` 的 instruction、原生角色、工具和技能模板沿用原 `pi-glm-fast`；保留成员的原生角色配方不变，其中仍允许 DeepSeek sub-agent。root-only 标签使新增根不进入可指派成员清单。根与子 Issue、PR 之间不自动传播模型选择。

## 最初 ARC Descriptor 与证据

最新运行已分流为官网Flash使用ARC、本地GLM使用自有API，实际通道以 experiments.md 新冻结输入为准。以下保留最初ARC制品的descriptor依据。

最初 ARC endpoint 采用 `https://api.arc-bench.com/v1`，凭据由实际启动环境提供；模板仍经原生生成函数将本次 endpoint 写入 models.json。当前精确 ID 来自 `runs/iteration13/final-readiness-20261001/arc-models.json`，该发现响应只证明存在，不证明能力。

GLM-5.3 采用文本输入、1,000,000 context、131,072 maxTokens，支持工具，推理仅开启；档位映射为 low/high/max，根保持与基线相同 high。依据 [Z.ai 官方文档](https://docs.z.ai/guides/llm/glm-5.3)，不沿用 Flash 的 image 声明。Pi 的 zai 兼容路径发送 thinking.enabled、clear_thinking=false、reasoning_effort=high，并沿用已有工具流兼容；当前 ARC 参数可用性留给首次真实 I13 请求反馈，没有增加 Chat 测试任务。

K2.7 Code context 为 262,144、支持 image、工具以及强制保留推理，依据 [Moonshot 官方模型卡](https://huggingface.co/moonshotai/Kimi-K2.7-Code)。运行输出上限保留旧独立 `pi-braid-kimi-root/agents/pi-kimi-k27-code/models.json` 的 131,072；它是本轮运行上限，不声称等于模型理论最大输出。2026-09-23 ARC 原件已记录该 ID 两轮工具往返及 max_tokens=262144 接受，见同级 `factory26-official-local/runs/raw-baseline-20260923/replacement-api-qualification/qualification/kimi-k2.7-code/`；这不证明实际曾生成对应长度。旧 reasoning 实测还明确拒绝关闭推理，见 [历史报告](../../reports/2026-09-23-model-reasoning-probe.md)。采用既有 deepseek thinking 兼容、不发送 effort，并显式保留 assistant reasoning_content；不复制 K3 的 effort 和 deferredToolsMode。

## 装配与反馈

打包使用 `.env.i13-tools`，凭据只进入 Git 忽略目录下 `.private/tool-env.json` 及私有 ZIP，不写入文档。`scripts/package_agent.py` 的既有 OTLP 装配和 tool-env 许可名单加入根对照，未新增打包框架。

复用 `runs/iteration13/final-readiness-20261001/linux-runtime`，Braid 源 hash 为 `105e42ad20018531b7e47ce739a8df4f107b457bd1e1bb9f462b817111b8a260`。本批变动不改变 runtime 构建输入，不重复构建 Linux。Python 编译及两组源码入口实际 prepare-only 为本批反馈；不运行测试、smoke、fixtures 或模型探针。私有 ZIP、stage、源码身份及摘要保留在 `runs/iteration13/start-20261001/artifacts/`，冻结回执见 `artifacts/freeze-receipt.json`，配方、源码清单一致性和装配读回见 `artifacts/material-readback.json`。两组源码与 package manifest 一致，OTLP 与私有工具配置已装入。

Mac 的包入口首次 prepare-only 被现有平台检查拒绝（需要 Linux x86_64、CPython 3.12），原错误保留在 `pi-braid-i13-prepare.json`。随后源码入口使用同一包内 runtime/skills、ARC endpoint，两组 prepare-only 成功；这只验证材料生成，不替代 Linux 包入口验收。宿主侧真实包入口及模型反馈由主线启动取得。

当前父仓库 HEAD 为 `3b79a2e512be136d24118ea58a68e86e8dfad3d0`。Braid 源码纳入父仓库后，实际构建输入仍为上述 hash；npm lock 与八份原生补丁均匹配 runtime-source.json。仅 Git 归属变化未触发重构。

基线冻结为 `pi-braid-i13-k27.zip`，SHA256 `afca9654b10544851885c748060d7d283b2d40b0890363f6acfb9a2dfe677877`；根对照冻结为 `pi-braid-i13-glm-root-k3.zip`，SHA256 `6bcabc7d5e48a2f78574ee7651b5fa072a00761d80d8d3194df7f12f08d93404`。stage 保留供实际材料核对；没有 push。
