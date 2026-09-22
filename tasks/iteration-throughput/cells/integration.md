# Cell：Pi lifecycle 与整合顺序

状态：已获批实施。无模型代码与协议检查通过，Linux ZIP 入口资格进行中；真实模型/协作与评分尚未通过。下方 Observed 保留实施前反例，最新结果见末尾。

## Observed

当前`harness/extensions/factory-subagent-lifecycle.ts`对background child的`proofComplete`只要求`childSessionId && controlRequested`，`childReceipt`也只保存`control_requested`。它虽然从pi-subagents status解析`processTerminal`，但没有把该证据带入receipt或完成判断。

独立无模型probe `/tmp/factory26-pi-proof-probe.mjs`构造：stop精确ack、child session存在、status为stopped，但`processTerminal.state=unknown`且canonical lease未证明释放。当前adapter仍返回：

```json
{
  "receipt_state": "ready",
  "receipt_error": null,
  "child_proof": { "control_requested": true }
}
```

probe以42退出表示错误接受；随后现有`node tests/pi_lifecycle.test.mjs`仍通过。这证明当前测试没有守住设计要求，而不是Pi RPC缺陷。

pi-subagents 0.56.0已经提供所需权威：`ProcessTerminalV1.state=observed`包含runner/writer process-tree终态；有canonical child session时，`canonicalSession.freeAtObservation=true`且`leaseDisposition=released|not-held`，否则上游产出明确`unknown`原因。无需在Braid重新扫描detached进程或发明另一套lease。

另行核对Braid当前`GroupDriver::drive`：它以`HashMap<provider_session_id, RunningAgentTurn>`同时跟踪多个运行中的work-item，并在每个调度周期继续claim下一项。一个`(kind, profile)` worker不是单turn容量槽；同一assignee的多个Issue/PR可以并发。实施无需重写并发架构，只需用两个同profile work-item的重叠执行证据守住这一行为。

Braid `sources/braid/src/provider/factory.rs::teardown`当前只校验extension receipt为`ready`，关闭parent native tree后给所有child proof追加`parent_process_group_terminal=true`。这对foreground可作为终态组合证据；detached background不属于parent tree，该字段不能替代processTerminal/lease。

## 最小修改合同

1. lifecycle extension把background的权威`processTerminal`压缩进receipt proof：至少包含`process_terminal_observed`、`canonical_session_free`和可归档的原始身份/来源；只有`state=observed`、run identity匹配、child session identity匹配、canonical session为free且lease released/not-held时才`ready`。
2. `pending`、`unknown`、缺canonical session、lease仍owned/unreadable或identity不匹配均返回`unknown`；stop acknowledgement只保留诊断意义。
3. foreground仍由定向interrupt/control + Braid关闭自己拥有的parent native process tree组合证明；不要求pi-subagents为其提供detached proof。
4. Braid在接受`ready`前按mode验证proof形状；关闭parent后只把parent-tree终态用于foreground完成判据。background可记录parent终态为旁证，但不得由此升级。
5. archive/diagnostics保持原始processTerminal handle或压缩字段，使后续能区分control失败、process未终止和lease未释放。

## 拟修改面与owner

| Owner | 文件族 | 责任 |
| --- | --- | --- |
| Factory lifecycle | `harness/extensions/factory-subagent-lifecycle.ts` | 解析、校验、序列化background终态proof |
| Factory检查 | `tests/pi_lifecycle.test.mjs` | 用独立oracle让unknown terminal保持unknown；observed+free才ready |
| Braid provider | `sources/braid/src/provider/factory.rs` | receipt模式校验、parent tree与background proof分离 |
| 联合场景 | `tasks/multi-agent-integration/scripts/braid-scene.py`及对应资格入口 | 用真实writer静止/PID消失/lease证据检查context replacement顺序 |
| 归档诊断 | `scripts/core.py`、相关archive tests | 保存并验证终态证据，不用`stopped`字符串代替 |

## 线性实施与检查

1. 先把独立probe转成一个会失败的extension行为检查，确认它因错误`ready`而红；同时保留observed+free正例。
2. 收紧extension receipt，运行`tests/pi_lifecycle.test.mjs`；不改Braid时先证明extension边界。
3. 给Braid provider增加fixture：background缺process/lease proof拒绝；foreground在parent tree terminal后通过；运行其定向Rust tests。
4. 更新archive与联合场景判据，再执行无模型三层spike。只有A原生Pi、B扩展、C Braid顺序通过，才允许进入模型/协作资格。
5. 后续真实协作资格只跑一个foreground、一个background context replacement，不扩成模型矩阵；完整benchmark不承担生命周期诊断。

## 失败归属与残余

- 上游status不给observed processTerminal或canonical lease时，B层明确unknown，形成pi-subagents接缝证据；不由Braid猜测。
- extension正例通过而Braid拒绝，归Braid receipt validator/close顺序。
- 两层通过但archive丢身份，归Factory证据消费，不重跑模型。
- 仍需在实现预演中确认workflow background的每个nested child是否各有独立processTerminal，不能只用父run proof覆盖所有child。

## 实施进展（2026-09-22）

开工基线 `7d3b1e6` 已提交。Factory extension 的 unknown-terminal 反例首先失败（ready != unknown），修复后 Node lifecycle 检查通过；独立 `/tmp/factory26-pi-proof-probe.mjs` 现在返回 unknown/control_deadline，保留原始 processTerminal。Braid 按 mode 校验 ready receipt，只给 foreground 附加 parent-process-tree 终态；7 项 provider::factory 测试通过。Native archive 保留 lifecycle_proof，7 项 archive 测试通过。

上游 canonicalSessionId 实际是 canonical realpath 的 SHA256，不是 native session UUID；extension 按该协议绑定 lease 证据，并独立核对 session header identity。Background workflow 没有逐 child canonical proof 时维持 unknown，不能把父 run 证据冒充 child 证明。该边界在真实分层资格中继续验证。

本轮分工：assignee_impl 拥有 Braid 配置、store、objects、CLI、context、scheduler 接线（不含 provider/factory.rs）；capabilities_impl 拥有 Factory profiles/native materialization/package/活动配置；主 Agent 拥有 lifecycle provider/extension、archive、local runner 与集成；环境 cell 完成后转 Competition adapter。相邻接缝通过明确字段和命令合同协作，不由多个 Agent 同时改同一文件。

实际 Pi 0.85.1 RPC（get_state、abort）与安装的 pi-subagents 0.56.0 + `/factory-subagent-stop` 已通过无模型进程检查。该证据只覆盖真实协议装载与空子树控制，不能替代有 writer 的真实协作资格。可重跑脚本在 `scripts/pi-rpc-smoke.py`，输出 `runs/qualification/pi-rpc-smoke/`。

另外修复包内 platform_config 视觉配置覆盖主模型的问题，文本与视觉 key 各自仅传给消费 provider。新检查覆盖冻结模型不匹配拒绝；submission 10 项检查通过（macOS 跳过 Linux Landlock 1 项）。local 官方 wrapper prepare-only 实际通过；官方矩阵用 barrier 验证独立本地 workspace 并行、hosted snapshot 严格顺序和已完成不重复运行。上述仍不是模型/评分验收。

主线最终无模型检查：`make test` 共 125 项 Python 检查通过（macOS 跳过 1 项 Linux 检查），Pi lifecycle 通过；Braid 32 unit + 1 CLI integration 通过，fmt/diff 检查通过。22 份本轮文档的相对链接无缺失，SVC status 为 healthy。原始日志：`runs/qualification/implementation-tests.log`。首个混合 variant ZIP 为资格候选；真实入口/浏览器检查后提交源码，再用缓存构建四份最终 ZIP。
