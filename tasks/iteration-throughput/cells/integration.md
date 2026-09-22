# Cell：Pi lifecycle 与整合顺序

状态：本页保留前一实现与资格的历史证据，原生子代理停止证明方案已被用户撤回。当前实施以[Pi边界修正](pi-boundary.md)为准，不再执行本页的三层spike或receipt放行合同。

## Observed（实施前事实）

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

Linux native 首轮受控停止（`runs/qualification/live-linux/native`）：父会话两次把 `runs.run` Promise 传入 `runs.all`，后者要求 `{key,agent,task}` descriptor，工作流错误使刚启动 child 被SIGTERM。第三批已自行纠正并有真实vision read与executor响应，但停止指令先于恢复消息被执行；本次重复由诊断/运行消息交错造成，不是provider失败。`extensions: []` 警告无因果关系，实际effective runtime extension与factory26/visual模型选择均有证据（`live-linux-health/provider-resolution.json`）。只修资格输入为上游明确recipe，native-v2复验；runtime/四ZIP不变。运行owner必须先发启动回执再阻塞等待，停止判断核对最新事件，不能把历史错误当当前故障。

Native-v2 的 vision/executor 均 exitCode=0，application 已有 image.json 与 calc.py；当前两个 browser child 并行，父前台 subagent 正在等待。父日志静止不能推断无进展，应沿子会话查当前工具/产物。该轮未改模型、包、runtime；仅资格prompt固定已知API调用形状。

Native-v2 的浏览器真实child持续CDP断开，主线在14:30左右受控停止。collector又因临时`.brdiag`文件消失遮蔽终态，原check残留running；原始记录保留，资格明确未通过。fixture已改为先持久化终态，再收集可选文件，collection error单列，不遮蔽原始失败。

真正的浏览器根因已在同一materialized wrapper、submission environment与Landlock前缀上无模型复现：Chrome不能读取/proc/self/maps、/proc/self/fd并fatal退出。仅加readonly /proc后open/eval/close约12秒通过。官方Landlock的ptrace-domain边界仍限制宿主敏感proc；独立无密钥marker probe证实self maps/env可读，而parent env/fd/mem、hostmarker与input写均被拒绝。该边界加入既有test_submission真实Linux测试，原包实际红灯于self/maps。修复只改linux_sandbox系统读取规则，未扩大工作区或需求写权限，不增加browser broker。资料：https://docs.kernel.org/6.6/userspace-api/landlock.html#ptrace-restrictions 。

资格按变更依赖复用：native-v2已证明真实vision/executor正常及browser子会话使用既定wrapper；新的无模型两身份browser旅程覆盖修复后的页面、截图和存储隔离，再直接进入真实Braid场景，不让LLM重采已通过的视觉/加法步骤。source变更使旧ZIP退役，重新组合相同runtime并冻结四包后才上传；当前仍未发生任何Competition写入。

NSS动态模块是第二个同一打包边界缺陷：普通ldd不会列出softokn/freebl等dlopen模块。build.py现按构建镜像libnss3包manifest收集完整共享库族并递归ldd依赖，保持SONAME别名；不靠逐个fatal补库。proc修复+该库overlay的实际HTTP/storage/screenshot/close旅程25秒通过（browser-boundary-fixed7）；最终包会重新验证，并补充两会话同时存活后的交叉读取oracle。当前126项Python+Node lifecycle通过，真实Linux的self/parent proc及输入边界检查也通过，证据proc-source-test.log。

最终无overlay资格包 `pi-team-mixed-browser-boundary.zip` SHA256 e73fcbb64aac780a50a61519e015aa7f996ce54017958ce759479ede813d3fa1，388230732 bytes，已通过双浏览器同时存活/交叉读取/真实identity/screenshot/close及真实Linux拒绝检查。证据 `runs/qualification/live-linux/package-fixed-browser/`；外部package-identity.json绑定ZIP与manifest，不从manifest虚构自身ZIP hash。四包复用该runtime冻结在final-a102aa2，mixed完全同hash。Braid实际包场景已于15:01 UTC启动，独立detached wrapper持久化 `evidence/braid-process.json`（scene PID10389），观察Agent不拥有启动/终止权；主线接收终态后进入新manifest官方实验。

Braid首次foreground replacement失败（约166秒）：`capture_native_descendants`调用外部ps，而最小运行镜像不存在ps/kill，导致ENOENT，尚未执行extension stop。修复归打包边界：显式procps依赖、包装两个binary及其动态库。真实同隔离域无模型probe证明ps可枚举自身、kill可探测并停止probe自建group；证据runtime-tools-overlay。此前浏览器四包均未上传，重新构建一个候选后再冻结。另保留会话JSONL的实际source与记录path不同，独立核对，暂不据此改provider。

会话路径专项无模型probe在实际Linux包与真实pi-subagents/lifecycle两扩展下通过：get_state→new_session→get_state的路径等于extension读取路径，synthetic assistant落盘于自定义session-dir。可重跑入口为 `node tasks/iteration-throughput/scripts/pi-session-path-spike.mjs <runtime> <lifecycle.ts>`，证据session-path-spike/linux-actual-extensions.json。此前真实场景的路径差异仍未解释，不能据此推定Pi协议故障或修改provider；后续场景继续保留身份/归档证据。

5bee93dd实际Braid复验在首次foreground reset失败，writer PID10718已Z态、PPID1、PGID10718，错误为native descendant remained alive after SIGKILL。原始证据braid-procps/writer-terminal.json与foreground.jsonl绑定同PID。共享kill-0检查将已退出但未reap当活进程，修复应区分执行终止与PID槽位释放，不加subreaper、延长timeout或重采模型；Codex/Pi共享检查均需覆盖，未知检查结果保持fail closed。process_terminal_fix拥有源码与真实zombie回归，主Agent集成。
