# e20261001-01：I13 首轮实验

2026-10-01 用户在审阅最终检查结果后明确：“好的，可以启动 I13 了。”本轮承接两组根配方各生成 GitHub、Sheet 一次，共四次新生成的建议，授权必要的根对照实现、最终材料冻结、独立干净宿主建立、本地生成、Console 人工介入与逐题官网应用重放。I12 已结束，仅保留其归档；当时无法挂载的旧 Debian VHDX 和冷备不进入恢复范围。

## 配方与判断目标

| case | variant | 根 Issue | 原生 advisor | 子 Issue / PR 与其余原生角色 |
| --- | --- | --- | --- | --- |
| flash-root | pi-braid-i13 | glm-5.3-flash / high | kimi-k2.7-code | 两个 Flash 可指派成员及其余已核定 I13 配方 |
| glm-root | pi-braid-i13-glm-root | glm-5.3 / high，root-only | kimi-k3 | 同上 |

用户最新修正为：“有一个变化，使用 K2.7 code 替代 K3”；“抱歉，GLM-5.3 组继续使用 K3”。ARC 同时提供 kimi-k2.7-code 和 highspeed 变体，本轮采用精确的 kimi-k2.7-code。这一决定同时改变根模型和 advisor，结果不能归因为单一根模型差异。其余工具、技能、共同提示词、Flash 子 Issue/PR 成员与视觉 glm-5.3-flash 保持一致；所有模型走 https://api.arc-bench.com/v1，使用用户已恢复授权的 ARC 额度。

本轮回答整体需求理解、责任交接、最终覆盖、上下文连续性与运行成本是否改善；description 重建、普通评论增量送达、深层委派、executor采用与归档恢复承诺来自真实工作证据。技能读取、对象关闭、token增长不单独证明有效行为。人工介入保留 journal，若两组介入不同，明确分析限制。

## 输入、次数与运行安排

允许输入来自项目已保存的官方需求：`runs/wsl-retained-20260930/official-local/platform-inputs/hackathon/`。GitHub 28 个文件、Sheet 10 个文件，均已与各自 source.json 校验一致。无官方本地 tests-source；生成不接触外部测试、参考应用或历史运行产物，本地采用 requirements-only，不报告本地分数。

四次可读生成名称为 `e20261001-01--<flash-root|glm-root>--<github|sheet>--g01`。每题两组使用独立干净起点，不互相导入代码、Git或会话。并发上限2，先 GitHub 的两组，再 Sheet 的两组；每个容器 4 GiB/2 CPU。若实际容量不支持并发2，则全轮统一串行并记录原因，不扩大资源。无自动增加重复次数。

新宿主采用[独立 Debian 方案](../debian-disk-recovery/packet.md)：Debian-Factory26、独立 Docker Engine 与稳定 host-lab Python资产。只准备实际运行依赖，不安装整套开发环境。先核实新 ext4 与承载它的 Windows 卷空间、真实 bind mount、容器网络和 OTLP，随后冻结 schema v3 的空间/inode预算。当前24 GiB workspace、4 GiB telemetry、8 GiB finalization scratch是待宿主实测校准的准备值，不是已完成容量验收；host reserve至少为文件系统容量10%与最大scratch的较大值。保存所有原始错误，不自动清理历史数据。

本机 `runs/iteration13/start-20261001/` 保存准备和回执；最终 ZIP、源码、Braid、SVC、依赖及补丁身份由 `artifacts/` 的实际材料记录。根对照与Kimi替换实施归[root-comparison.md](root-comparison.md)。当前尚无模型请求；最终包和运行ID在取得后追加。

## 完成、反馈与后续边界

每题生成完成即从准确交付版本发布应用重放包，并独立提交官网，不等待其余任务。本地生成使用 ARC 模型额度；应用重放不调用生成模型，采用既有非榜单 `self_funded` artifact-replay 入口及 no-model 凭据占位，明确记录平台实际 billing_mode。重放不是新的Harness生成，耗时和模型消耗分开记录。评分只用于开发侧结果，隐藏反馈不送给仍在生成的Agent。

lab程序保存终态和容量观测；远端无事件接口时，采集按启动后前10分钟每3分钟、此后每8分钟执行。需要语义审查时使用 agents/run-monitor.md 的 GPT-5.6-Luna / low，读取定向证据而不铺开全量rollout；程序等待不每分钟唤醒主模型。明确设施缺陷在已授权范围内保留现场、修复和接续；预算停止后另用reconcile核对外部容器。新题目、增加重复次数、改模型配方或不可逆宿主变更不由本记录默认授权。

最终每条结果关联实际lab/Braid/原生身份、包/需求/应用摘要、官网run与分数、原始错误和证据缺口。四次完成后无论分数高低先汇报，由用户决定下一轮。
