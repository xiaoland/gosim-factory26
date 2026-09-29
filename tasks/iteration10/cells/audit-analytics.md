# 开发侧可观测性与跨链 analytics

## 当前状态

已完成用户授权的开发侧读取工具改进。范围只覆盖现有 `lab` 入口和已保存 run 的只读分析，不重新运行 Sheet/GitHub 审查，不启动 Factory/Braid/模型/评分，不修改原始证据，也没有新增 Collector、数据库或索引平台。

根因是旧 `lab evidence --session` 只能从 `native/manifest.json` 找到单个归档文件并按 UTF-8 字节分页；它不能从工作项导航成员、原生 session-tree、timing、PID、commit/ref 或工具原文。直接对原生 JSONL 做全文检索还会把超长单行输出淹没真正证据。

已交付：

- [`lab trace`](/Volumes/WorkSSD/Development/factory26/lab/__main__.py:276) 复用 manifest、session-tree、`pi-timing.jsonl` 和只读 `braid.sqlite3`。`--work-item issue:6` 列出成员、原生 session、context/instructions/turn 原文入口、父子记录、时间与工具事件；`--session <native_id>` 可反向定位工作项。
- `--pid`、`--commit`、`--tree` 只检索已保存的精确字段；结果显式区分 `exact`、`ambiguous`、`missing`，不从时间邻近、文本相似推断因果或补造关联。
- `--record <record_id>` 与 `--tool-call <tool_call_id>` 返回原始 JSONL 的 source、line、offset、record 边界和 bounded read。tool-call 只有一条同 ID 调用与一条同 ID 响应才标为 `exact_pair`；单 record 读取严格限制在该 JSONL 行内，超出 record 边界报错，续读使用 `next_record_offset`。
- `--text` 只返回有限 preview 和原始位置，标记为 `text_candidate`，不能当作身份关联。现有 `evidence --offset/--bytes` 仍用于文件级绝对字节续读。

## 真实材料反馈

只读材料：`tasks/iteration10/run-audit/sheet/evidence`。执行：

```sh
python3 -m lab trace <run> --work-item issue:6
python3 -m lab trace <run> --session <native_id> --text "公式计算"
python3 -m lab trace <run> --session <native_id> --tool-call <tool_call_id> --bytes 4096
```

真实样本 `issue:6` 返回 57 个成员、747 条 timing（结果上限 50 且标记截断）、4 条关联 merge。会话 `01a0e5f8-6ca9-7214-ac46-4c97f93b633f` 中，文本候选可定位到 record `06a95e96`/`84a553bd`；tool call `call_aefd2d6288c34594b97a9702` 返回 assistant 调用与 toolResult 响应的精确成对位置。读取 4096 字节时分别在 944 和 3099 字节的 record 边界完成，没有混入下一条记录。

旧 `evidence --session` 的 UTF-8 边界也保留：会话 `01a0e5f3-7f6c-7001-b229-04dc2a2d2d57` 的字节 680/685 续读跨中文字符时没有替换字符；旧 run `runs/20260920-225624-82074f1f` 同样可按 native ID 定位。

## 已知限制与下一步直达

当前 evidence run 的 session-tree 真实记录只有 self parent、children 为空，因此工具明确显示“无已归档父子关系”，不会虚构未归档子会话。真实材料中不存在的 PID、commit、tree 字段保持 `missing`。工具提供证据定位和 bounded 补读，不替审计者完成语义阅读或因果结论。

下一步直接使用 [`lab/README.md`](/Volumes/WorkSSD/Development/factory26/lab/README.md:15) 的 `trace` 示例，从目标 work-item 开始，再用精确 session、record 或 tool-call 续读；将 `missing`/`ambiguous` 作为审查缺口回传，不改用全文 grep 猜链。

验证仅为 Python 编译和上述既有 evidence run 只读命令；未运行 Factory/Braid/设施测试或探针。
