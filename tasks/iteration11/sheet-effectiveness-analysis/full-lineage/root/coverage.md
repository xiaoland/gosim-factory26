# root 后段阅读与证据覆盖账

## 原始范围

- 原始 B：`tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4`
- 全局索引：`tasks/iteration11/sheet-effectiveness-analysis/full-lineage/inventory/inventory.json`、`records.jsonl`、`read-gaps.json`
- 早期复用：`tasks/iteration11/run-audit/sheet/`，截止 `2026-09-29T08:24:25.679855+00:00`；只复用有明确 read-range 的全文，不把索引存在当作已读。
- 阶段切割校正：Issue 1 的 final-source `work/native-homes/pi-glm-fast-01a0ec2e-f964-77b1-a16f-2da0f3f4e202/2026-09-29T08-01-37-411Z_01a0ec2e-fc83-71b9-9bd1-16ee3da2ee43.jsonl` 为 28 行；旧 early 对应载体只有 17 行，`lineage-comparison.json` 标为 `appended`，故新增 final lines 18–28 已单独语义阅读。新增 line/msgID 为 `18/1fa6d264`, `19/36ad3de9`, `20/25017017`, `21/5561dbd4`, `22/aa81aeb6`, `23/880e41e6`, `24/ddc81439`, `25/12e2179e`, `26/1d867cf4`, `27/87f98efd`, `28/5366b8db`；内容包括 root 处理 PR #9 #171、Issue #1 #172/PR #10 #174、D-C14、resolve/reopen 事件。
- 同一时期的 `work/native-homes/pi-glm-fast-01a0ec18-dd01-7710-8628-056a21a12e7a/2026-09-29T07-37-31-051Z_01a0ec18-eaab-742f-beef-c670a8c6bc1c.jsonl` 是 Issue 4/B，不是 Issue 1；final 78 行、early 36 行，`lineage-comparison.json` 为 `content_diff` 且前缀不相等。它不能从旧 early audit 继承“完整已读”状态，也没有被本报告当作 root Issue 1 证据。若综合报告需要跨 issue 的 root 维护背景，应引用该 final path 的独立 coverage，而不要从本账推断其全文已读。
- 目标工作项：Issue 1（后段 root 主线）、PR #13（整合）、PR #14（D stability）。Issue 6/7、PR #11/#12 的成员主链只作为 root 的直接输入/验收证据引用，完整成员演变由其他分工负责。

## 记录和文件覆盖

| 工作项 | inventory 记录 | 本段新增/后段 | 主要时间范围 | 处理方式 |
|---|---:|---:|---|---|
| Issue 1 | 2,411 | 1,083 needs_new_read | 09:26→02:11 | 逐 record 导航原生 message/tool 语义；关键 assistant 决策、命令、结果和评论回到原行核读；早期 08:24 前引用既有审计 |
| PR #13 | 415 | 415 needs_new_read | 11:55→02:10 | 415 条记录进入语义导航范围；长重复 payload 不逐字重展开，gap 设计、候选变更、四道门、merge 和 post-merge 关键证据回到原行核读 |
| PR #14 | 52 | 52 needs_new_read | 17:25→01:52 | 52 条记录进入语义导航范围；长重复 payload 不逐字重展开，flake 根因、wait helper、spec-only diff、68 passed 和 head/merge 关键证据回到原行核读 |

源目录总计 565 个 JSONL、38,414 行、188,251,949 bytes、解析错误 0。完整机器账在 inventory；本文件不复制 188MB 正文。

## 物理文件和关键锚点

### Issue 1 root 主线

以下是后段主要 native 载体；同一 lineage 的 continuation、无头记录和重复载体仍按原路径保留在 `records.jsonl`，未按 basename 合并。

| 时段 | 物理文件（相对 B） | 本报告使用的证据 |
|---|---|---|
| 09:26 | `work/native-homes/pi-glm-fast-01a0ec7c-532c-7cb3-8b89-f580a8ee0c64/2026-09-29T09-26-06-713Z_01a0ec7c-5679-76bb-8f0c-16ee96829f11.jsonl` | #212→#217 接手、advisor 结果、#214 EOF 修正、回执不重复回复 |
| 09:45 | `work/native-homes/pi-glm-fast-01a0ec9d-.../2026-09-29T09-45-...jsonl` | root 对 #232/#238/#242 及 Issue 正文更新的 assistant/tool turns；完整路径和原行见 inventory records |
| 09:55 | `work/native-homes/pi-glm-fast-.../2026-09-55-...jsonl` | #247/#259 关联核查、README/body 窄改、候选门禁义务 |
| 10:02 | `work/native-homes/pi-glm-fast-01a0ec9d-9f09-7e02-a3c7-839bcd784e30/2026-09-29T10-02-28-840Z_01a0ec9d-a268-771a-8193-b6a47af56470.jsonl` | `b3ced6be`、`1b14462a`、`e17117b7`、`05b44806`、`88e2cca6`、`b9d09e13`、`48f5dcfe`、`3bdc5bc2` 等 root 输入/检查/总结 |
| 10:47 | `work/native-homes/pi-glm-fast-01a0ecc6-e48e-77f2-835c-5d0d25dea18a/2026-09-29T10-47-33-486Z_01a0ecc6-e76e-7774-8701-b0cc8b4a9fa7.jsonl` | `63728dce`、`48b4e251`、`985619ce`、`fe3d9370`、`d87ba464`；#363→#397 pivot 更正 |
| 11:10 | `work/native-homes/pi-glm-fast-01a0ecc6-.../2026-09-29T11-10-...jsonl` | `eea2a5c7`、`d2492b5b`、`6bc2845f`、`87020d11`、`03c90826`；#406→#428 display-value 更正 |
| 11:20 | `work/native-homes/pi-glm-fast-01a0ece5-.../2026-09-29T11-20-52-...jsonl` | #462 缺陷识别、旧 sha 阻断、修复等待 |
| 11:28 | `work/native-homes/pi-glm-fast-01a0ecec-.../2026-09-29T11-28-48-...jsonl` | `4882c2e4`、`3d47077b`、`7070551c`、`ae568b81`、`1e4b677b`、`6ffd5e35`；#462/#476 |
| 11:32 | `work/native-homes/pi-glm-fast-01a0ecef-.../2026-09-29T11-32-14-...jsonl` | `6b937b4f`、`ab13ea46`、`40cd4716`、`5d8d907e`、`79ce6097`、`0410f7a2`、`d678d2c7`、`4686f4e5`；监测链和 hash 更正 |
| 11:44 | `work/native-homes/pi-glm-fast-01a0ecfa-.../2026-09-29T11-44-28-...jsonl` | `71355bc3`、`dbd26493`、`553cc0e5`、`d48c3576`；PR #12 合并与 PR #13 分配 |
| 02:00/02:11 | `work/native-homes/pi-glm-fast-01a0f00a-.../2026-09-30T02-00-14-000Z_...jsonl`、`work/native-homes/pi-glm-fast-01a0f014-.../2026-09-30T02-11-...jsonl` | PR #13 回交、root 最终 mapping/tree/dirty/12-of-12/24-atomic 验收 |

缩略路径中的 `...` 仅为本表可读性；完整物理相对路径和每条 record 的 line/msg_id 在 `inventory/records.jsonl`。报告引用的 comment 证据来自 `evidence/comments.md`：#232、#238、#242、#247、#259、#304、#319、#363、#397、#406、#428、#462、#476、#509、#553、#570、#571、#572、#574、#576、#577、#578、#580、#582、#583、#588、#589。这里只使用稳定 comment number，不把当前 `comments.md` 的近似行号写成物理锚点；每条评论的原 path/line/msgID 仍可由 `inventory/records.jsonl` 和 source JSONL 复核。

### PR #13

四个原始文件全部纳入：

1. `work/native-homes/pi-deepseek-fast-01a0ed04-b48e-7a90-a107-ba96166ae98a/2026-09-29T11-55-07-417Z_01a0ed04-c319-77f5-b538-3caf47830695.jsonl`（整合起始）。
2. `work/native-homes/pi-deepseek-fast-01a0efff-7173-7ff0-967a-9e619f01d259/2026-09-30T01-48-34-507Z_01a0efff-cf4b-7018-9b07-4dae29085d1b.jsonl`（root #578 后恢复/收尾）。
3. `work/native-homes/pi-deepseek-fast-01a0f011-fa89-7783-8ef6-0e8d4fc9e49e/2026-09-30T02-08-26-581Z_01a0f011-ffd5-7020-9be1-45874510d1fa.jsonl`。
4. `work/native-homes/pi-deepseek-fast-01a0f012-db7f-7552-ab10-e8f7491d2b2a/2026-09-30T02-09-24-375Z_01a0f012-e197-7712-961c-4c0a5fa99854.jsonl`。

重点 comment 锚点为 #578、#580、#582、#583、#584、#586；其中 #582 的当前候选四道门与 #583 的 merge/post-merge 是最终直接证据。

### PR #14

三份物理载体全部纳入：

1. `work/native-homes/pi-glm-fast-01a0ee33-33cc-71c3-930e-8fcabdb592ec/2026-09-29T17-25-54-187Z_01a0ee33-998b-7726-bab5-046059220625.jsonl`。
2. `work/native-homes/pi-glm-fast-01a0ee36-8c27-7073-a754-4e5eec50accd/sessions/--workspace-template-.factory26-20260929-042409-811f18d4-braid-state-worktrees-pr-14-pi-glm-fast-g1--/2026-09-29T17-29-08-681Z_01a0ee36-9149-7107-8f5a-9184ef7fb294.jsonl`。
3. `work/native-homes/pi-glm-fast-01a0ee36-8c27-7073-a754-4e5eec50accd/2026-09-29T17-29-08-681Z_01a0ee36-9149-7107-8f5a-9184ef7fb294.jsonl`。

重点 comment 锚点为 #553（flake 原因）、#570/#571（helper 设计）、#572（spec-only 实现）、#574（68 passed/hash/match-head）、#576/#577（关闭与指针）。

## 阅读、去重和省略规则

- inventory 的 `needs_new_read` 是机器覆盖状态，不是“人工已经全文读完”的声明。人工语义 pass 以 record 为单位穿过目标文件；因果结论所用 assistant 解释、选择、命令结果、评论正文和生命周期事件均回到原 JSONL 行或 comments.md 行核对。长 user context、重复代码、重复回包和纯 delivery receipt 只保留位置/指纹及必要摘要；它们没有被逐字复制或反复展开。
- 每个原始 JSONL path、原行、timestamp、msgID 都以 `records.jsonl` 为准；不因相同 session basename、相同 payload 或 sibling 副本合并记录。
- 语义阅读优先顺序是 user context → assistant explanation/choice → tool command/result → comment/body mutation → 后续 consequence。巨量重复上下文、代码和工具回包只在叙述中折叠，并保留原 path/line/fingerprint 入口。
- inventory 报告有 39 个重复 payload fingerprint group、1,597 个额外重复记录；这些只作为候选重复，不能替代原始行。源行没有 exact duplicate line。
- 对 #218–#268 等长 thread，报告只把有因果改变的 #232/#238/#242/#247/#259 展开；其余 receipt/no-action 记录仍在覆盖账中，且在结论中明确“重复维护”而非假设不存在。
- SQLite 只读索引用于当前 item/comment、activity、event 位置核对；没有把当前 `resolved`/`hidden` 状态倒推成完整历史。hide/resolve 演变只在有 native event/comment 证据处引用。
- 本任务没有运行测试、模型、评测、应用或 variant 修改；也没有写原始 B、SQLite、inventory。新增物仅本目录的 `report.md` 和 `coverage.md`。

因此，本账对 root 的实质决策链、PR #13/#14 的完整状态转移和最终验收提供直接证据；对长重复 payload 的逐字覆盖不作额外声称。若后续需要审计某个被折叠的回包，应按 `records.jsonl` 的 exact/payload fingerprint 回到原始 path，而不能引用本报告摘要代替正文。

## 尚存边界

1. 这是 root 输入—动作—后果的 lineage，不是 ABCDE 全 DB 的重复全文审计；成员内部未传入 root 的思考不能由 root native 推断。
2. root 的最终 #588 证据支持候选/合并树一致和门禁已回交，不支持由记录单独推导隐藏评分或真实用户影响。
3. comments.md 是持续增量产物；本账保留当前物理行和稳定 comment number，后续增量若改变行号，应以 `records.jsonl` 的 path/line/msgID 与 comment number 复核。
