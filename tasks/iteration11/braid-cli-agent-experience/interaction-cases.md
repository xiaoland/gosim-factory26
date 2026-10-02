# Braid Issue/PR CLI：真实 Agent 交互案例

2026-09-30，只读诊断。复用既有 GitHub [方法论报告](../braid-context-methodology/report.md)、[历史语义](../braid-context-methodology/runtime-semantics.md)、[覆盖账](../braid-context-methodology/coverage.md)与 Sheet [完整 lineage](../sheet-effectiveness-analysis/full-lineage.md)，沿索引定向回读原生输入和返回。下列八例不是全量调查，也不推导净 token、运行成本或评分影响。结构化证据为 [case-evidence.json](case-evidence.json)，保存来源 hash、物理行、消息时间、message ID、toolCallId、必要原文及省略标记。

**最清楚的体验断点是操作单元不合预期、读取/截取顺序损坏目标与回执、以及以重复 mutation 获取上次结果。纠正也真实发生：回读状态、拆合法参数、保留替代入口和按精确 head 合并都有效。**

## 身份与退出码边界

GitHub 只取 inner `20260929-042409-1202e245`，不混入更早 `78b10c07`；Sheet 为 `20260929-042409-811f18d4`。GitHub 09-30 终态接续 binary 是 `d76d65f133979a9f310b39e73fc254f727b564734ee1513c4febe6fbecb083be`；Sheet 终态是 `3056feb7a599addeb82e0250d6a0cc1e055d9e8e78f0151ca12ea75582605bf4`。身份来源见 GitHub [runtime-semantics](../braid-context-methodology/runtime-semantics.md)、[build identity](../../../runs/iteration11/runtime-stalls/build/build-identity.json)及 Sheet [identity](../sheet-effectiveness-analysis/evidence/identity.json)。**C1、C2、C8 发生在 09-29；本分项没有把每次调用绑定到当时 binary hash，不能把终态 binary 倒填给它们。** C3–C7 位于 GitHub 09-30 终态接续。

本分项不读取当前实现来补写历史回执。父报告另核当前源码已有的 resolve 回执和 reset continuation 改动；C7 只能证明历史行为，不能据此断言当前仍必然发生。

除特别说明外，下面每个 CLI 的独立退出码均为**不知**。大部分原生 bash 返回 `details={}`、`isError=false`，但实际命令有 `head`/`tail`/后续命令，错误文本仍明确存在；不能把 wrapper 状态当成 Braid 成功码。C4 的 wrapper 明示 exit 1，失败点是 Python 解析。

## C1 — GitHub #318：想收束转呈，却折叠整串；恢复后仍误述局部状态

09-29 16:29–16:32，Issue10 owner 原意是在已保留裁决后折叠 #318→#322 的转呈交换。`resolve --help` 当时只有“评论 ID；可一次提供多个”，未展示线程影响范围（[G1:L104](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0edfd-2cfa-7dc3-a64c-77bbdfa02a56/2026-09-29T16-26-28-729Z_01a0edfd-31f9-746f-83ed-47b29491cd20.jsonl:104)）。

| 证据链 | 原始调用与返回 |
|---|---|
| 16:29:19，[G1:L105](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0edfd-2cfa-7dc3-a64c-77bbdfa02a56/2026-09-29T16-26-28-729Z_01a0edfd-31f9-746f-83ed-47b29491cd20.jsonl:105) | `call_00_ET_g01DPaqVQInATtoxoRhi3443`：`comment resolve 318` 后读单条，返回 `Comment 318 … reply to #313 - resolved`。resolve 自身没有可见结果摘要。 |
| 16:29:21–24，[G1:L107](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0edfd-2cfa-7dc3-a64c-77bbdfa02a56/2026-09-29T16-26-28-729Z_01a0edfd-31f9-746f-83ed-47b29491cd20.jsonl:107) | `call_00_w3Z3B7e4fyqudNiluPVi9414`：逐条 view 发现 #313/#314/#317/#322 等也 `resolved`；`call_00_aCNKmDnsWYHdBalclzYA8491` 的全板标题确认 root308 同样 resolved。 |
| 16:29:32，[G1:L112](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0edfd-2cfa-7dc3-a64c-77bbdfa02a56/2026-09-29T16-26-28-729Z_01a0edfd-31f9-746f-83ed-47b29491cd20.jsonl:112) | `call_00_s9SfJ0Bzzt9Xl4eMVoHY2113`：`unresolve 308 311 313 314 317 322 323` 经 tail 只留下 `Usage: braid comment unresolve <ID>`，错误首行当时已被丢弃；线程仍 resolved。 |
| 16:29:33，[G1:L114](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0edfd-2cfa-7dc3-a64c-77bbdfa02a56/2026-09-29T16-26-28-729Z_01a0edfd-31f9-746f-83ed-47b29491cd20.jsonl:114) | `call_00_lssNzJui1HgIlXV7OqbE6666`：循环单 ID 调用，返回七个 `unresolved ID` 与无 resolved 标记的标题。`&& echo` 可证明每次该 unresolve 返回成功，但整个操作未提供影响范围回执。 |
| 16:31:16，[G2:L124](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0edf0-3050-72f0-8275-fc6ee38edf6f/2026-09-29T16-12-17-682Z_01a0edf0-3592-766f-9cb7-f9c533bce566.jsonl:124) | 根 `call_b762dabade884b768341081f` 读取 JSON，#308–#324 被查条目全 `resolved=False`；纠正 #325 所称“仍保留局部折叠”。 |
| 16:32:00–13，[G3:L22](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0ee00-f656-7640-a78b-9f84f1e40172/2026-09-29T16-30-36-947Z_01a0ee00-fb93-735a-8734-51274094f4e2.jsonl:22)、[G3:L35](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0ee00-f656-7640-a78b-9f84f1e40172/2026-09-29T16-30-36-947Z_01a0ee00-fb93-735a-8734-51274094f4e2.jsonl:35) | `call_00_0hbI6zyGNPrwGi6dB6XG1465` 回读318/324同根308；`call_00_VyA6WqyXzx84f9ott1858737` 发 #327：“不再重折叠，全部保持可见”，并更正文案。 |

这不是永久丢失证据；安全恢复和另一角色的状态复核都有效。还出现读取 schema 的试错：根曾把 `comment view --json` 当对象提取字段而得到 `{}`（G2:L120–123），随后处理数组并逐条核实。混合线程与工具实际操作单元不一致有实证，但没有下游产品缺失证据。

## C2 — Sheet #362/#370：同类粒度误解加 resolve/unresolve 参数不对称

09-29 11:29，E 想折叠已被后续决定取代的两条冻结请求。作者已经读了 resolve help，仍认为“individual comments can be resolved”（S1:L51）。

| 证据链 | 原始调用与返回 |
|---|---|
| 11:29:17，[S1:L53](../../../tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl:53) | `call_00_GfPKaJ84r28iHDNWfouM1150` 先发 #470，再 `comment resolve 362 370`；返回只有 #470 与 queued 投递回执，**没有 resolve 影响摘要**。 |
| 11:29:21、30，[S1:L55](../../../tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl:55)、[S1:L60](../../../tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl:60) | `call_00_qvZtdHnTit4V6XZf7GY46191` 读出 thread314/331 `[resolved]`；`call_00_hrhOG3GY86qJ28Ihe7Bs9742` 再读最新 #470，也属 `thread: 331 [resolved]`，这才促成明确识别。 |
| 11:29:40，[S1:L64](../../../tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl:64) | `call_00_buEXdBxuOWmgeCYOscqp6310`：`unresolve 370 362` 返回 `error: unexpected argument '362' found`，Usage 只允许 `<ID>`；原生 `isError=false`。 |
| 11:29:42–51，[S1:L66](../../../tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl:66)、[S1:L68](../../../tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl:68) | `call_00_8G5ra38FEhCMBluW6nMv3396` 拆为两次后读回 thread314/331 `[open]`；`call_00_ioNHANOdaKPIWpLQKXT95287` 编辑 #470，撤回“随本条折叠”，留下替代决定与恢复说明。 |

读回状态使纠正成立；不能写成 resolve 操作本身已经给了清晰回执。两条 lineage 都能观察到同类误解，但样本不足以计算发生率，也未证明折叠窗口造成产品损害。

## C3 — GitHub #347：展开 thread 再 head，最新目标消失；纠错中又猜错命令

09-30 02:36:48，PR23 owner 要读根的新 #347，执行 `comment view 347 --thread | head -60`（[G4:L27](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0f02b-2742-7ce3-9fd4-f681396d7c15/2026-09-30T02-35-56-168Z_01a0f02b-2b86-75e8-81b5-2ae38e9a3abc.jsonl:27)，`call_00_SoxYWhMncTWxLrl0QeRp0290`）。原始回包从 root #341 开始，经过 #343/#344，只到 #345 标题；**没有 #347 正文**。这次截断是 Agent 自己的 shell 管道，不是模型窗口降档。

02:36:49，作者识别“output was truncated at 60 lines”，但尝试 `braid comment 347`，返回 `error: unrecognized subcommand '347'`（[G4:L30](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0f02b-2742-7ce3-9fd4-f681396d7c15/2026-09-30T02-35-56-168Z_01a0f02b-2b86-75e8-81b5-2ae38e9a3abc.jsonl:30)，`call_00_afl1FCVMSVlSwpFj9nxK3440`）。同轮 `comment create --help` 也报未识别 create（G4:L27/L29）。02:36:50 改为 `comment view 347 | head -60` 后，完整目标和 delivered 回执出现（[G4:L32](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0f02b-2742-7ce3-9fd4-f681396d7c15/2026-09-30T02-35-56-168Z_01a0f02b-2b86-75e8-81b5-2ae38e9a3abc.jsonl:32)，`call_00_YriCGj4fy62N7rVOKu820472`）。

单条读取是有效恢复。证据只支持这次检索顺序有问题，不支持“thread 默认不可用”或应一律禁止上下文展开。

## C4 — GitHub 正文 JSON：先按显示行截取，再解析，破坏了机器输出

09-30 02:36:40，根准备改 Issue1 正文：`issue view 1 --json body | head -3 | tail -1 > /tmp/issue1-body.json`，再 `json.load`（[G5:L31](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl:31)，`call_0ba1bc3a3fd1475f97821c5b`）。返回 `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`，并明确 `Command exited with code 1`、`isError=true`。

02:36:42 改为把完整 `--json body` 保存后再解析，成功写出正文并打印 `2817`（[G5:L33](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl:33)，`call_ba5c53616500409c88062da3`）。本例没有正文丢失：第一步是读取失败；后续恢复读取后才执行编辑。不能将 Python 失败码归给 Braid CLI。

## C5 — GitHub PR23：精确 head 合并与实际落地核对有效

09-30 02:35:34–02:36:06，根收到最终候选后，先 fetch 并核 `origin/develop=f628045a17dced69c453cbc3f3fb225dd68aa713`，回读 diff 确认新增主要是日志/packet，再核通过数量及证据中的退出码（[G5:L13](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl:13)，`call_caaef210c2eb4055907728ce`；G5:L18–22）。

随后执行 `braid pr merge 23 --match-head-commit f628045a17dced69c453cbc3f3fb225dd68aa713`（[G5:L23](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl:23)，`call_f466fb11e30a4f0d85f619ab`）。返回 JSON `{"merge_commit":"442dc1cf776f144688d8ad667a76dd026f553e27"}`，同调用 fetch/rev-parse 也返回同一 main SHA。PR owner 后续执行 `git diff --stat origin/develop origin/main | tail -3`，diff 输出为空；它打印的 `DIFF_EXIT=0` 实际取自 tail 管道终态，不能充当 Git diff 的独立退出码（[G9:L13](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0f02c-b44b-7e62-9784-89ec2591541d/2026-09-30T02-37-37-782Z_01a0f02c-b875-75b6-8799-f89f99846e80.jsonl:13)，`call_01_J2V3N4foG7RfN0ONvg0L2481`）。

这是工具状态、Git 身份及树一致性的有效闭环；不证明所有需求的语义覆盖。该次实际匹配成功，也不能单靠本例证明 mismatched-head 分支如何失败。旁边一个读取错误应保留：PR owner 请求 `--json state,mergeCommit` 收到 `error: unknown view field "mergeCommit"`（G9:L11–12），之后用 timeline/Git 核对，而非得到该字段。

## C6 — GitHub close：文字先宣布完成，状态随后落地；跨工作项 reply 被拒后恢复

| 时间与来源 | 观察 |
|---|---|
| 02:36:32，[G5:L29](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl:29) | 根发 #347，正文已经写“Issue #1 以 completed 关闭”（`call_9957b3bb7ad1436f9672a373`）。 |
| 02:36:53，[G4:L35](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0f02b-2742-7ce3-9fd4-f681396d7c15/2026-09-30T02-35-56-168Z_01a0f02b-2b86-75e8-81b5-2ae38e9a3abc.jsonl:35) | PR owner `call_00_8aMEQoV4EZ97UtCr38yC3914` 真实读到 Issue OPEN、PR MERGED。后续 timeline 也只到 associated_pr_merged；所以当时观察本身成立。 |
| 02:37:12，[G5:L37](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl:37) | 根 `call_eedb253c64ff48f89be3109c` 执行 `issue close 1 --reason completed --comment …`，返回 `issue #1: closed / comment #349`。02:37:17 view 已是 CLOSED（G5:L40–41）。 |
| 02:37:21，[G4:L52](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0f02b-2742-7ce3-9fd4-f681396d7c15/2026-09-30T02-35-56-168Z_01a0f02b-2b86-75e8-81b5-2ae38e9a3abc.jsonl:52) | PR owner仍基于先前 OPEN 读数发 #350，称状态未落地（`call_00_qUXWn3RMt3lWOQKemqwm4724`）。此时关闭返回已经出现。 |
| 02:37:44，[G5:L47](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl:47) | 根已再次读回 CLOSED，尝试在 Issue1 `--reply-to 348`；#348 属 PR23，返回 `error: reply belongs to a different work item`（`call_e2661829daea4381bdbd805b`）。 |
| 02:37:49，[G5:L49](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl:49) | 去掉跨项 reply-to，正文保留#348导航和@目标，成功产生#351与 queued 回执（`call_670a588f4aa546ae9863a5a1`）。PR owner也独立查到 CLOSED 并发#352确认（G9:L5–6、L22–23）。 |

最终状态成功关闭，不能将其描述为“关闭工具故障被提醒修复”，也不能证明提醒触发了根的关闭。Agent 所写“Closes #1 在本平台不自动关闭”只是当时解释，本案例不将该句升级成一般语义；自动关闭识别条件归主报告源码核查。`queued`/`delivered` 只代表输入投递状态，不等于理解与行动。

## C7 — GitHub 自己整理后继续读：历史通知与冗余刷新有直接链

09-30 02:03:32–42，根已知道 PR23 正在验收，连续 `pr list`、`pr view`、`pr view --comments`，读到同样候选与无新讨论（G6:L6–10）。02:09:25再次读取，02:09:56明确写“Nothing new”，仍为保持整洁 hide306/328/329、resolve337（[G6:L20](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f00d-4b0e-7cf3-8418-0c9d7c75b0d8/2026-09-30T02-03-19-230Z_01a0f00d-4f3d-73c1-8bbc-7295d6b93d8f.jsonl:20)，`call_ccaee1fcf58d4dd1831b61b1`）。mutation 回包为空，于是另读337确认 resolved（`call_6ad41bf679de4b4cbf6f5201`）。

02:10:04 收到明确“你的修改…本次工作结束后将重建上下文”通知（[G6:L24](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f00d-4b0e-7cf3-8418-0c9d7c75b0d8/2026-09-30T02-03-19-230Z_01a0f00d-4f3d-73c1-8bbc-7295d6b93d8f.jsonl:24)）。作者说“Nothing new to process”，仍 `pr view` 两次再 fetch/head（[G6:L25](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f00d-4b0e-7cf3-8418-0c9d7c75b0d8/2026-09-30T02-03-19-230Z_01a0f00d-4f3d-73c1-8bbc-7295d6b93d8f.jsonl:25)，`call_1ade06e94eb842118bdbfa78`）。新 session 02:10:31再次 `pr view --json`、fetch/head、`pr view --comments`及单条337（[G7:L6](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f013-b40c-76c2-87f4-a0cdc333226b/2026-09-30T02-10-19-134Z_01a0f013-b77e-7065-8043-2a7c6d805f95.jsonl:6)，`call_a543a78035524076afd740e7` / `call_7812be4102b6449cb091474e`）。同样 head、仍无新证据。

02:21:55 的自述更明确：“repeatedly hiding every routine reminder adds churn”，仍 hide339（[G7:L23](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f013-b40c-76c2-87f4-a0cdc333226b/2026-09-30T02-10-19-134Z_01a0f013-b77e-7065-8043-2a7c6d805f95.jsonl:23)，`call_7d510fff81054c06b5b24d4c`），随后又收到自己的修改通知。可以判定这一小段有重复读取与维护产生新输入；不能把全部轮询都判为冗余，候选后续变化确需核实。**当前 continuation 实现已被父报告发现与历史冻结代码不同；这里不推断当前仍会同样续转。**

## C8 — GitHub #256/#257：为拿回被截断的 ID，重复提交同一评论

09-29 11:44:27，M4a owner 用文件发布对 #245 的回复：`issue comment 1 --reply-to 245 --body-file /tmp/issue6-reply-245b.md --json | head -c 300`（[G8:L96](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0ecf4-7c6a-7d51-82ba-5082c7528f91/2026-09-29T11-37-41-997Z_01a0ecf4-cf6d-76f9-9785-0db506ac13b4.jsonl:96)，`call_00_ET_EVvt1jM517T5Fx0JQvut2423`）。原生输出恰好截在 `"id`；前面已经有三名接收者的 queued 回执。

11:44:31，Agent再执行**同一条创建评论**，仅把尾部换成 Python 提取除 deliveries 外的字段，得到 `id? {'id': 257}`（[G8:L98](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0ecf4-7c6a-7d51-82ba-5082c7528f91/2026-09-29T11-37-41-997Z_01a0ecf4-cf6d-76f9-9785-0db506ac13b4.jsonl:98)，`call_00_ET_V1id6mQcuMAbjcrnUx828300`）。11:44:33随即承认“Oops — I posted the comment twice!”，后续读取确认 #256 与 #257 均由自己发出、都 reply-to245（G8:L100–103，`call_00_iLHDQ7MT0PiXCnfqShC58268`）。

11:44:54，`call_00_14BpR6ygAWx4MTaWscWM3516` hide257，理由为“同一次回复被提交两次。保留 #256，此条仅作追溯”；11:44:57用单条 view 与 `--include-hidden` 读回 #256 visible / #257 hidden 及该理由（[G8:L106](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0ecf4-7c6a-7d51-82ba-5082c7528f91/2026-09-29T11-37-41-997Z_01a0ecf4-cf6d-76f9-9785-0db506ac13b4.jsonl:106)、[G8:L108](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0ecf4-7c6a-7d51-82ba-5082c7528f91/2026-09-29T11-37-41-997Z_01a0ecf4-cf6d-76f9-9785-0db506ac13b4.jsonl:108)，`call_00_ET_vV66WBF7Hlr3PJC5xXzc6841`）。

这里的因果范围较清楚：Agent 先自行截掉创建结果，随后通过重发 mutation 获取 ID，造成两次发布；没有网络失败证据，也不是服务端重复投递一个请求。hide保留替代入口的恢复有效，但不能追回在途已发出的两组通知。应保留结果再解析、遇不确定结果先读状态，而不是为读取 ID 重放创建操作；是否需要 CLI 幂等键是另一个设计决定，本例本身不要求引入它。

## 原件导航与未读范围

`L` 为 JSONL 物理行。下列每个文件只回读上述相关区间与必要相邻输入；未重读全会话、全部 lineage、所有工具源码或应用内容。case-evidence 的摘录省略不表示原件也截断；C3/C8 明确标注的是当时真实 shell 截断。

| 代号 | 原始 native 文件 |
|---|---|
| G1 | [2026-09-29T16-26-28-729Z_01a0edfd-31f9-746f-83ed-47b29491cd20.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0edfd-2cfa-7dc3-a64c-77bbdfa02a56/2026-09-29T16-26-28-729Z_01a0edfd-31f9-746f-83ed-47b29491cd20.jsonl) |
| G2 | [2026-09-29T16-12-17-682Z_01a0edf0-3592-766f-9cb7-f9c533bce566.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0edf0-3050-72f0-8275-fc6ee38edf6f/2026-09-29T16-12-17-682Z_01a0edf0-3592-766f-9cb7-f9c533bce566.jsonl) |
| G3 | [2026-09-29T16-30-36-947Z_01a0ee00-fb93-735a-8734-51274094f4e2.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0ee00-f656-7640-a78b-9f84f1e40172/2026-09-29T16-30-36-947Z_01a0ee00-fb93-735a-8734-51274094f4e2.jsonl) |
| S1 | [2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl](../../../tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl) |
| G4 | [2026-09-30T02-35-56-168Z_01a0f02b-2b86-75e8-81b5-2ae38e9a3abc.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0f02b-2742-7ce3-9fd4-f681396d7c15/2026-09-30T02-35-56-168Z_01a0f02b-2b86-75e8-81b5-2ae38e9a3abc.jsonl) |
| G5 | [2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f028-5b31-72f3-a8a9-801b3ec467d8/2026-09-30T02-32-54-672Z_01a0f028-668f-71a0-927f-af1e093fe10e.jsonl) |
| G6 | [2026-09-30T02-03-19-230Z_01a0f00d-4f3d-73c1-8bbc-7295d6b93d8f.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f00d-4b0e-7cf3-8418-0c9d7c75b0d8/2026-09-30T02-03-19-230Z_01a0f00d-4f3d-73c1-8bbc-7295d6b93d8f.jsonl) |
| G7 | [2026-09-30T02-10-19-134Z_01a0f013-b77e-7065-8043-2a7c6d805f95.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-glm-fast-01a0f013-b40c-76c2-87f4-a0cdc333226b/2026-09-30T02-10-19-134Z_01a0f013-b77e-7065-8043-2a7c6d805f95.jsonl) |
| G8 | [2026-09-29T11-37-41-997Z_01a0ecf4-cf6d-76f9-9785-0db506ac13b4.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0ecf4-7c6a-7d51-82ba-5082c7528f91/2026-09-29T11-37-41-997Z_01a0ecf4-cf6d-76f9-9785-0db506ac13b4.jsonl) |
| G9 | [2026-09-30T02-37-37-782Z_01a0f02c-b875-75b6-8799-f89f99846e80.jsonl](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/work/native-homes/pi-deepseek-fast-01a0f02c-b44b-7e62-9784-89ec2591541d/2026-09-30T02-37-37-782Z_01a0f02c-b875-75b6-8799-f89f99846e80.jsonl) |

本次只写本报告和相邻 case-evidence.json；未修改任何实现、执行原生记录中的命令、操作真实 Issue/PR、运行测试/编译/安装/模型，未提交。
