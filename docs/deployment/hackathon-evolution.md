# Hackathon Evolution 归档

Agentic Software Factory Hackathon Evolution 已于 2026-10-08 结束。平台拒绝新的 submission 和 run 启动，赛中 packet 和命令不能作为当前执行授权。

## 规则与输入

规则原文保存在[决赛通知](../references/hackathon-evolution-notice-20261006.md)与[初赛须知](../references/competition-notice-20261001.pdf)。决赛要求 Agent 在本队初赛应用上增量实现需求，保留已有功能和业务数据；平台在启动前注入基线。正式题目标识为 `hackathon-evolution--github` 和 `hackathon-evolution--sheet`，不得与初赛题目或 GitHub stages 混用。

原通知截止为 2026-10-08 18:00（北京时间），单次容器最长 24 小时；后续执行按用户更新的 20:00 截止安排，详见[正式运行记录](../../tasks/pi-minimal/evolution-20261006/packet.md)。官网曾显示占位日期，不能用它反推实际停止时间。最新有效正式提交至少有一题运行记录即可成立，不保证两题已经完成；自费评分不计排行榜。

原始资料集中在被 Git 忽略的 `runs/hackathon-evolution/inquiry-20261006/`，不会随 clone 分发：

| 材料 | 文件或目录 |
| --- | --- |
| 官方需求、YAML 和参考图 | `requirements.zip`、`requirements/` |
| 本队官方完整基线及业务数据 | `initial-projects.zip`、`baseline/{github,sheet}/` |
| 逐文件身份和提取说明 | `material-manifest.json` |
| 当时官网规则与账户观测 | `competition.json`、`registration.json` |
| 初赛应用与基线来源核对 | `github-source-comparison.json`、`sheet-source-comparison.json` |

需求 ZIP SHA256 为 `7d4b7414c2ef00b4bace62ce3747581cf91077ca8ab0985dcb8602f69989b500`；基线 ZIP SHA256 为 `38c0457d9df5871d69604a53763b2514b9d6e1abde918364af2bc6a97fad8ba0`。材料可用性以本地保存和清理记录为准，旧清单不证明所有原件当前仍在。

## 复盘边界

本队初赛最终排行榜 submission 为 `aea08b61772c`。GitHub 基线与 Stage 3 `d86b43e8c891` 已归档的 51 个源码文件一致，另有旧归档未证明的数据库；Sheet 基线与 `e53e7ab5ec79` 工作区的 128 个源码文件一致。本地后续修复不能冒充官方下载基线。

两题本轮各有 5 项修改、5 项新增与 30 个官方评测用例。行为、名称、错误文本和初始数据以官方 YAML 为准，评测实现未公开。源码比较、官方评分、业务数据保存和原生会话覆盖分别说明，不能从行数或架构推断效果。

原件与基线只作读取；若需分析副本，保留来源哈希和提取范围。旧 `.factory26`、原生会话和工具材料属于原运行，新任务不能误用其会话身份或覆盖旧证据。历次具体操作与调查可从 Git 历史查阅。
