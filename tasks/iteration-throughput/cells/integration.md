# Cell：Pi lifecycle 与整合顺序

状态：已获批实施。无模型代码、协议、Linux ZIP 入口、文本/视觉工具接口与四包冻结通过；真实协作资格进行中，尚无评分。下方 Observed 保留实施前反例，最新结果见末尾。

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

Factory 实现检查点已提交 `32f1e3c`。首包在浏览器依赖安装处失败：官方 `agent-browser install --with-deps` 调用 sudo，而精简 Python 构建镜像没有 sudo。Braid release 与 npm 安装已缓存；最小修复仅补充构建镜像的 sudo，继续使用浏览器维护的系统依赖清单，避免在 Factory 手抄该清单。此故障没有产生 ZIP 或模型调用。

首包入口与真实 Pi RPC 的 Linux 复验已通过：`runs/qualification/entry-recheck/`，network none、UID/GID 1000、1 CPU、2 GiB；真实工具启动与替身交付不再失败。Chrome 初次运行证明动态库、fonts 与 glib schemas 需要随便携 runtime 装配，由 capabilities owner 处理，仍在本轮打包范围内。首包压缩内容中，未使用 Codex native 占 133.2 MiB、其它平台 agent-browser native 占约 41.8 MiB，本轮 Pi/Linux 包定向移除它们，本机完整缓存和 npm lock 保留。

文本工具调用与视觉工具调用资格已通过，证据由 `runs/qualification/models/` 与 `models-vision-auto/` 组成；视觉400只来自测试强制函数选择，不是 Pi 默认消费者所需参数，未因此修改产品模型或降低 thinking。Luna 持有真实 native→Braid 场景执行；主 Agent 不轮询原始 rollout，失败或终态才收取最小证据。模型目录只保留稳定能力配置，临时 gateway_verified/429状态已移除，实时资格状态归本 cell/runs。

Linux 最终候选 `pi-team-mixed-chromium-candidate-3.zip` 已通过入口、真实 Pi RPC、Chrome loader 与 agent-browser 跨命令检查（打开data页、title、URL、snapshot、close）。SHA256 `a1cc6e660c0a9a3c05dfb59148ccb65deac55b2406c19f7be53661759315bab7`，369 MiB / 解包873 MiB；环境仍为UID1000、1CPU、2GiB、network none，证据 `runs/qualification/container-acceptance-final/`。Chrome私有动态库、字体与schemas随runtime打包，仅启动脚本设置其环境；SVC正文不变。Braid实现提交 `8b2c986`。最终四包用 `scripts/freeze-packages.py` 校验候选hash、source文件和构建输入，复用相同已验runtime。

最终126项Python检查（1项macOS不适用skip）及Node lifecycle通过，Factory提交 `57d0e90`。四包位于 `runs/packages/iteration-throughput/final-57d0e90/`，manifest为 `runs/competition/iteration-throughput/manifest.json`；离线装配106.79秒、manifest冻结1.23秒。最终mixed与已验候选3的SHA256完全相同，其余三包复用相同runtime bytes；尚未上传或启动Competition。

真实native场景 `20260922-212127-pi-native-844388` 在Mac上受控停止：vision已正确识别red/green/blue，executor断言通过；两browser重复CDP关闭，底层为嵌套sandbox初始化失败，还有GNU timeout缺失。它未产生完整资格，也未进入Braid/bench。另一个脚本错误是要求只读vision写image.json。修正归属是资格环境与夹具：父会话落盘视觉观察，native/Braid场景改为消费同一已验Linux ZIP，沿submission配置和隔离入口运行，不新增Mac兼容补丁。Linux无模型资格不能外推到Mac live浏览器，反之Mac设施失败也不否定已验Linux browser。

Linux live 容器 `factory26-live-linux-20260922` 已就绪，消费最终 mixed 包 a1cc6e66…；UID1000、1CPU、2GiB，bridge 仅为模型网络与本地页面服务。无模型 entry/RPC 再次通过。联合场景脚本新增 `--package/--output`，直接使用包内 manifest/config/runtime/isolation，不重建近似环境。官网 GET 确认 Lite 66 项与空提交历史，首 variant 状态已在 `runs/competition/iteration-throughput/matrix/hosted/pi-team-deepseek` 本地 prepare，尚无远端写入。
