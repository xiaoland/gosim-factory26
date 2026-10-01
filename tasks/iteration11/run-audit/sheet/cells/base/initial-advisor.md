# 初始 root advisor 与 timeline 补充阅读

## 阅读范围与身份

本补充只读了初始 root 的 advisor 原生子会话、其 artifact 镜像、无头续段中遗漏的两条 custom message，以及后期两个 `01a0ec23*` 源指定的原始行。root 初始主会话和 vision 源不在本补充范围内，未重复读取。真实范围和未读项见同目录 `initial-advisor-read-ranges.json`。

advisor 原生任务是 `01a0eb6b-072e-746a-8fc8-3f1feedc15e8`（25 行、cwd issue-1），artifact 是 `afffce3b-c20f-445f-89f0-131659d04249_advisor_transcript.jsonl`（42 行）。原生子会话的用户问题要求评审四项前提：损坏 requirements 的权威层级、A1:C6 种子空行、公式引擎/网格自研与库方案、稳定 URL 和持久化面。artifact 第 42 行是完整 advisor 结论；无头续段 artifact 第 20 行重复投递完整结论，第 23 行是完成订阅工具回执。两处 advisor 正文逐字一致，后者不是新的判断。

## advisor 判断及其证据边界

### 1. requirements 损坏

advisor 抽取场景名/GIVEN 中存活的 `Escape`、`3`、`B`、`A1:B2`→`D1:E2`、`Sheet2`、`SheetN`、`Pivot1`、`COUNT`、`AVERAGE`、`ISO`、`Sales`、`Region`，逐一映射到相应 ATOMIC 描述；没有找到只存在于场景的反例。因此支持 ATOMIC 作为权威层，建议再做机械 orphan 交叉表，并先确认是否有完整需求副本。它同时指出 308 处相同的 “the requested workflow with concrete values East/1200/North/800” 是模板填充物，不是逐场景输入证据。

这支持根侧 D1，但只能降低“场景独有行为遗漏”的风险，不能恢复被替换的步骤时序或多错误优先级。报告不能把 advisor 的 token 映射当作验收工具证据；它是独立判断，实际验收仍需 ATOMIC 与真实操作结果。

### 2. 种子与跨 GIVEN 冲突

advisor 支持 A1:C4 写入三行列出的内容，A5:C6 保持空白：重复填充没有文字依据，空行能支撑 Is empty/Is not empty 与聚合忽略空值，B3=800 与 North 行一致。但它发现更大的矛盾：REQ-1/2/5 可组成 `Q3 Sales` 的 Region 表 + 空 Sheet2，REQ-3 又要求 A1:B2 为 Item/Qty，REQ-4 要求 A1=2、B1=3；单一静态 Sheet1 种子不能满足全部。

它给出的竞争解释是 harness 按场景族重置种子，或通过 UI 录入 GIVEN；缺失事实是重置机制。最大一致子集种子、幂等迁移和不覆盖用户数据仍是稳妥实现路径。这里“harness 必然具备其中一种能力”是推理，不是原生工具观察，应在总报告中标为假设。

### 3. 自研公式引擎/网格的成本与边界

advisor 认为自研方向合理，补充两个具体冲突：虚拟化网格无法保证视口外每个 gridcell 的 `aria-selected=false`，HyperFormula 的循环错误与需求 `#REF!` 不同。它把公式引擎实际规模上调到约 800–1500 行，原因包括解析、依赖图、直接/间接环、复制和结构操作引用重写、原始公式往返；拖选、键盘导航、TSV 剪贴板、ARIA 焦点和跨结构撤销仍是两种路线共有成本。它提出 MIT parser 作为中间选项。

这些是设计咨询，不是 PR2 运行结果；可用于解释为何共享契约要先冻结引用重写和错误语义，不能证明库方案运行时一定失败，也不能把 400–600 行变成已测量工时。

### 4. 持久化清单

advisor 列出显式 row/col dimensions、验证规则 range 的事务迁移、filter spec（而非隐藏状态）、pivot 配置+最近成功快照+失效标记、物理排序、每 worksheet 的已确认矩形选择、统一 updatedAt、从现有名字推导 SheetN/PivotN、公式原文并在加载时重算、会话内撤销，以及 `/workbook/:id`。它还指出筛选区内插行是否扩张需要定语义。

这些条目与后续 v1.3/v1.4 共享契约形成链条；advisor 的“建议内部插入扩张”属于选择，不是源需求已经裁定的事实。

## timeline 工具核对：分页缺口与模型截断要分开

### 原始会话表现

在 `01a0ec23-e455-7300-83d8-d8e632701b47`（issue-1）中：

- L8 的命令是 `braid issue view 1 --timeline | tail -20`，工具结果只显示 ordinal 23–44 的 20 行；这是模型 shell 的 `tail` 展示截断。
- L13 的命令是 `braid issue view 1 --timeline | wc -l; ... | head -30`，结果先给 `30` 再给 ordinal 1–44 的前 30 行；这是模型用 `head` 限制显示。L14 原始 `--help` 明示 `--after` 默认 0、`--limit` 默认 30。
- L16 使用 `braid issue view 1 --timeline --after 44 --limit 100`，未再加 `tail/head`，返回 ordinal 45–289 共 81 行。输出仍只有文本行，没有 `has_more`、`next`、`cursor`、总数或明确顺序字段。

在 `01a0ec23-2dc1-7504-b8ea-645445ad51a9`（pr-10）中，L8 的 `braid pr view 10 --comments 2>&1 | tail -120` 同样是模型对评论输出的 tail 截断；L13/L16 分别是 issue body 和 platform script 的完整工具结果，缺少分页元数据并非由模型 tail 造成。

### 实现核对

只读 `sources/braid/src/objects.rs:287-293`：`timeline` 强制 `limit` 在 1–100，SQL 为 `ordinal > after ORDER BY ordinal LIMIT ?3`，返回 `Vec<Value>`，没有总数或下一页计算。只读 `sources/braid/src/cli/mod.rs:548-554`：文本模式逐行打印 `#ordinal at author action detail`；JSON 模式直接输出 rows。只读 `sources/braid/src/cli/mod.rs:141-152`：`--after` 默认 0、`--limit` 默认 30。

因此结论是：**工具本身确实缺少 has_more/next/cursor/order/total 提示**；它只提供调用者手工维护 `after` 的接口，SQL 实际按 ordinal 升序。与此同时，样本中还存在模型显式 `tail/head` 造成的二次截断。不能把后者误报为工具分页 bug，也不能因为 `ORDER BY ordinal` 就说 CLI 向用户展示了完整边界信息。

## 对总审查的影响

advisor 补充强化了根侧 D1/D2/D3 和持久化清单，但没有新增 PR2 源码缺陷确证。timeline 证据则是审计方法风险：读取完整过程时必须记录命令级 `tail/head`，并把工具的无分页提示作为证据完整性限制。后续主审引用 timeline 时，应同时记录 `after/limit`、实际首尾 ordinal 和是否由 shell 截断。

## 主审补齐

原生advisor其余message/content已与本片已读artifact逐项比对；L7的artifact在32758字符处截断，原生多出的需求文本已由主审分两段补读。details.truncation.content与已读text前缀完全相同。见`../root/advisor-mirror-validation.json`；本片局部未读标记保留用于说明责任边界，全局总账已闭合。
