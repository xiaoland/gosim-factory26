# Hackathon Evolution 资料归档与复盘指南

> 赛事已于 2026-10-08 结束。本页只用于读取历史规则、官方输入、基线和结果证据，不授权注册、提交、启动、重放或恢复比赛运行；旧文中的“后续”均指当时的赛中计划。

本页供赛后复盘查找规则和读取官方输入。本资料准备会话没有选择 variant、修改 Harness 或应用，也没有注册、上传、运行模型或评测。候选 variant 及改进方向当时须依据实验数据决定；基线生成者身份、静态兼容性和修改行数都不是效果排序。

## 历史规则与截止

本轮规则依据是用户转述的[决赛通知原文](../references/hackathon-evolution-notice-20261006.md)，未变更部分沿用[初赛参赛须知](competition.md#赛事规则与提交模式)。[官网入口](https://arc-bench.com/competitions/hackathon-evolution)仅队长白名单账号可访问。正式题目标识为 `hackathon-evolution--github`、`hackathon-evolution--sheet`。运行记录简称 `evo-github`、`evo-sheet`；它们与初赛普通 `github`、`sheet` 或 GitHub stages 是不同任务身份，输入、基线、运行和分数须分别记录。临时自费评分快照对 latest-saved 门控的影响及删除恢复流程见[运行说明](competition.md#决赛保存快照与多题执行的顺序)。

截止为 **2026-10-08 18:00，北京时间**。届时平台停止全部仍在执行的容器，单次容器最长 24 小时。官网卡片的 2036 年日期不是本轮截止；不把截止停止当作可保留进度并恢复的承诺。

用户明确要求尽快至少取得一次成绩，不再卡点提交。后续执行首先取得完整评分回执，再依据数据开展比较或改进；不能用已上传、已启动、生成完成或本地验证代替官网已评分。用于上榜的成绩须来自正式评测额度提交，自费结果不等于上榜成绩。具体首次执行、模型、费用和候选范围仍由后续会话取得授权，本页不设运行矩阵或承诺完成时长。

最新有效正式提交上榜，“有效”只要求至少一题已有运行记录，并不保证两题已完成。创建较新的正式提交可能替换已有成绩的提交，因此后续比较必须保存每次评分和提交顺序；截止前核对当前最新有效提交是否已有期望结果。通知允许选手在截止后决定是否删除最后一次未完成提交，但本页不授权自动删除。已经取得过一次成绩并不自动保证最后采用这次成绩。

## 本地材料入口

原始数据集中在仓库内 `runs/hackathon-evolution/inquiry-20261006/`，实际磁盘为 WorkSSD；目录由 Git 忽略，不能只靠 Git clone 恢复。文档保存在本仓库，原始下载和哈希清单需一并交接。

| 材料 | 本地入口 | 用途 |
| --- | --- | --- |
| 官方需求原包 | [requirements.zip](../../runs/hackathon-evolution/inquiry-20261006/requirements.zip) | 保留官方下载字节、两题 YAML 和参考图。 |
| GitHub 需求 | [requirements.yaml](../../runs/hackathon-evolution/inquiry-20261006/requirements/hackathon-evolution--github/requirements.yaml) | 52 个 atomic，包括本轮 5 修改、5 新增；同目录 reference 提供图像。 |
| Sheet 需求 | [requirements.yaml](../../runs/hackathon-evolution/inquiry-20261006/requirements/hackathon-evolution--sheet/requirements.yaml) | 仅展开本轮 10 个 atomic，不能替代保留旧功能的要求。 |
| 本队官方基线原包 | [initial-projects.zip](../../runs/hackathon-evolution/inquiry-20261006/initial-projects.zip) | 下载包含 github/、sheet/，保留应用、业务数据和原运行材料。 |
| 离线基线目录与逐文件身份 | [material-manifest.json](../../runs/hackathon-evolution/inquiry-20261006/material-manifest.json) | 定位 baseline/github、baseline/sheet，并读取提取方式、逐成员哈希与限制。 |
| 官网规则与账户观测 | [competition.json](../../runs/hackathon-evolution/inquiry-20261006/competition.json)、[registration.json](../../runs/hackathon-evolution/inquiry-20261006/registration.json) | 2026-10-06 快照，不代表后续实时状态。 |
| 基线来源核对 | [GitHub 对照](../../runs/hackathon-evolution/inquiry-20261006/github-source-comparison.json)、[Sheet 对照](../../runs/hackathon-evolution/inquiry-20261006/sheet-source-comparison.json) | 明确比较文件范围与未覆盖数据，不把目录名当来源凭证。 |
| 静态调查 | [需求与基线](../../tasks/hackathon-evolution/requirements-baseline-inquiry.md)、[Harness 生命周期](../../tasks/hackathon-evolution/harness-inquiry.md) | 已观察的边界、差距与未知，不代表实际运行结果。 |

需求 ZIP SHA256 为 `7d4b7414c2ef00b4bace62ce3747581cf91077ca8ab0985dcb8602f69989b500`；基线 ZIP SHA256 为 `38c0457d9df5871d69604a53763b2514b9d6e1abde918364af2bc6a97fad8ba0`。后续若官网材料变化，保存新的快照和身份，不覆盖本次原件。

本队初赛最终排行榜 submission 为 `aea08b61772c`，GitHub 采用 stages 路线。下载 GitHub 基线与 Stage 3 `d86b43e8c891` 已归档的 51 个 frontend/backend 文件一致，另含旧归档没有的 `backend/database.db`；该数据库未由这份旧归档证明。Sheet 基线与 `e53e7ab5ec79` 当前官方工作区的 128 个 frontend/backend 文件全部一致。本地后来生成或修复的应用不是这份决赛基线。

## 阅读需求与使用基线

每题本轮均有 5 项修改和 5 项新增，官方列出每题 30 个评测用例，评测实现未公开。GitHub 变化涉及账号、组织、搜索、分支及会话管理、审计、归档、releases、reactions；Sheet 涉及命名、清除矩形、过滤视图、validation 文案及冻结、查找替换、named ranges、条件格式、notes。概要用于定位，完整行为、可访问名称、错误文本和初始数据以官方 YAML 为准。

正式运行的基线由平台在 Agent 启动前注入 output；参赛包不需要下载或粘贴应用。智能体应先理解现有项目，再增量完成需求，保留已支持的功能与业务数据。不能清空、重置或整体覆盖 output。初始化、数据库迁移和多工作树交付都须服从该约定。

本地调试应从完整官方基线的独立工作副本开始，原始 ZIP 和 baseline 目录仅作参考材料，禁止在原件上修改。不要用“只复制源码”漏掉 GitHub 数据库或 Sheet JSON 数据，也不要把两个项目的业务数据混在同一 output。具体副本装配遵守所选执行器的真实合同，不在本页写一个未经运行验证的启动命令。

官方基线还携带旧 `.factory26`、原生会话、工具状态和应用自验材料。保留这些来源证据，但新任务不能误用旧 session 或覆盖旧 evidence，也不能把旧评分/评测反馈喂给生成 Agent。公开需求说明预置业务记录的契约；平台注入应用不等于已替应用创建新增 EVO 记录。应用应满足公开初始数据要求，并保留原有数据库、workbook 和未知字段。

## 后续比较与收尾

后续比较记录同一题目的需求哈希、基线哈希、variant 源码/制品身份、模型及供应商、费用模式、执行环境、来源提交和结果回执。不同候选从同一官方基线开始，各自隔离应用副本、原生任务状态和证据；不能将前一候选的改进应用悄悄作为后一候选输入。条件不同时记录差异，不能把它们归因于 variant 效果。

输出目录读取、应用交付、会话隔离、工具输出路径和数据保留是所有候选要满足的接入要求。现有调查已发现部分入口从空应用启动、拒绝更新同名文件或复用固定会话等问题；这些是具体入口的兼容性事实，不能用于预先淘汰或推荐某个架构。实际实现和验证由后续已授权工作完成。

取得首次成绩后保存评分、费用、耗时、提交/run 身份和应用产物；比较或改进不得消耗全部收尾时间。后续会话依据实际运行时长为两题生成、评测、失败处置及最终提交顺序留出余量，不把 24 小时容器上限当作完成预测。截止前确认最终希望采用的提交和结果已落盘，不能依赖截止后继续运行。

2026-10-06 只读报名快照显示队长资格有效、尚未注册；注册确认会关闭当前未注册队伍并创建正式比赛队伍。接口初始预算为 ¥200，页面正文为 ¥0，剩余额度为 null；初始数字不能当可用余额。后续正式操作前应重新核对注册、余额及费用模式，并取得相应授权。当前资料准备没有执行注册、提交、删除或决赛运行。
