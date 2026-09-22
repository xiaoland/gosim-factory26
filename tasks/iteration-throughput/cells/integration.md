# Cell：Pi lifecycle 与整合顺序

状态：实施前判别与整合已完成；结论已进入 `plan.md` 和 `implementation-impact.md`。未修改产品源码。

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
