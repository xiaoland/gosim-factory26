# 实施预演与排障

本轮用户授权“完成实现计划以及排障”。主 Agent 负责 OTLP、模型网关、报告与整体接线，两个独立只读 Agent 分别预演控制器生命周期和 ARC 发布/复评。检查基于当前工作树、固定官方 Runner 源码、WSL 已安装 LiteLLM 1.102.0 的源码和 metadata；没有运行模型、benchmark、Collector、网关或设施测试，也未修改运行代码。

以下“已收敛”表示实施路径已经明确，不表示现有缺陷已修复。结论已同步进 [技术约束](technical.md) 与 [实施计划](plan.md)，不留下互相矛盾的备选方案。

## 1. 历史目录和 v2 读取会同时破坏哪些调用者

`lab/run.py:240` 允许向已有 runs-root 追加，每次生成随机 run ID，记录不含实验身份。`benchmarks/hackathon/report.py:122` 只扫描该根的直接子目录。因此不能覆盖其父 manifest，不能把所有旧记录归到一个实验，也不能悄悄改变 --runs-root 的含义。

决定保留 `R/<run-id>`，新元数据位于 `R/.experiments/<id>`；原生入口使用标准 experiment-root。显式引用跨两种布局读取，同根旧无身份数据保留为历史集合。

另一条调用链由 `result_path` 兼任类型识别：`inspect_runs.py:138/192`、`run_feedback.py:342`、ARC `results.py:44` 都依赖它，`status.py:10` 又只接受 v1。v2 无结果文件的通用 job 会被遗漏或送进 ARC 解释器。决定增加明确记录类型，v1 规范化保留旧默认结果路径，v2 不声明才是进程型任务；这些消费者必须同批接线。

## 2. 准备和控制器失联的未完成窗口

`run.py:250` 顺序 prepare 全部 job 后一次提交 futures。输入失败会打断整批，部分目录可能尚无 run.json；取消未开始 future 也不会写 queued 终态。`run.py:221–228` 在收集/SQLite 查询后才保存退出事实，任何收尾异常都可能留下 running。

决定先记录计划请求和 job 身份，再临时冻结、原子发布，按受影响输入标记准备失败。调度改为 ready/active/slot_limit 和每个在途尝试一个线程；控制器集中处理状态写入。Popen 之前保存尝试分配，之后立即保存身份，wait 返回后先保存退出；辅助收集单独处理。

进程已启动但身份未写入的窗口不能凭一个操作 ID 达成恰好一次。恢复时查询原分配并保留未知，不自动补启动。CLI 请求与回执分文件，避免两方抢写；SIGTERM/SIGINT/socket stop 共用禁止派发和停止路径。通知游标带控制器世代，socket 用短私有路径，旧裸 PID 不成为归属证明。

## 3. 应用不能等整个 Runner 结束再冻结

现有 `arc_bench_adapter.py:176–207` 等 Runner 返回才计算应用身份。独立 Agent 核对本机固定生产源码 `../factory26-official-local/runs/runner-source-20260923/run_submission.py`：1266–1268 同步调用入口，1290 才部署；1173–1205 的部署操作限定在 template 的前后端。

固定 `raw-baseline-20260923-wsl/runner/local_submit.py:417–434` 会复制完整 submission 树，523–524 只挂载 `/workspace`。决定在容器的 `/workspace/.lab-artifacts/application` 发布快照，宿主直接引用已知 bind 对应的冻结目录。发布临时目录不算可用；原子发布完成后 receipt 即可恢复索引，无需宿主复制/确认握手。

生产 `run_submission.py:370–372` 在包装器退出后才清理生成进程组，不能把它当成包装器冻结时已经静止的证据。包装器对原入口建立自己的组，沿用同一组清理顺序后冻结。只记录能确认的组状态，不声称包含主动 setsid 的所有后代。入口、组清理和发布结果各自保存。

## 4. 资源清理存在登记窗口与名称复用窗口

固定 `local_submit.py:554–557` 先 flush workspace/容器名再调用 Docker。当前 adapter:98 只在 finally 从 stdout 找名称，inspect bind 后仍按名称删除；inspect 与删除之间若名称复用，可能作用于另一个容器。adapter:139 虽然查询镜像 ID，实际命令仍用 tag。

决定调用前记录 workspace/image ID/资源意图，实时登记名称并取得完整 ID，停止时先收回本次启动进程，再按完整 ID 和 bind 清理。新 inspect/cleanup 子命令由冻结计划声明，正常路径与 reconcile 共用。刚创建请求仍未确定时，单次 absent 只能是本次观察；不能提前宣布资源已清理。数据不足时保存未确认，不批量扫描名称前缀。

## 5. 新 helper 与应用执行位会在冻结/打包边界丢失

两个 matrix 当前只冻结 adapter 单文件；`run.py:88–90` 只复制被声明输入。如果共享身份逻辑改成 sibling import，却不改输入声明，开发目录可导入而真实 run 会缺模块。决定新配方冻结 ARC adapter 目录；容器包装器、noop、replay 包显式包含同一 stdlib helper。

官方 `local_submit.py:264–266` 解压 ZIP 仅写 bytes，不恢复 mode。新身份包含执行位，因此新 replay 必须按 manifest 恢复后再核验；旧包没有权限事实则不补造。应用快照不能用源树硬链接，避免后续部署改变所谓冻结内容。

本地 evaluate 直接用 `--template` 和核验型 noop。当前 noop 只写摘要，新路径必须比较预期值与实际加载值。回放入口当前只复述 case，新路径也需独立消费见证。场景终态需匹配稳定 ID 和数目，不能只有 expected_tests=1。

## 6. OTLP 读取和依赖也需要明确边界

现有 `lab/otlp.py:connect` 用普通 sqlite3.connect；查询一个不存在的文件可能先创建空库。读取改为 `mode=ro`，升级只在明确写入/补采时发生。旧 Braid viewer 直接使用 list_batches/read_batch，不能通过给旧函数新增默认条数上限，让原先全量分析悄悄少读。

gzip、signal-specific 配置和错误码问题已在前轮确认。此次进一步核实 WSL `hackathon-runtime-codex/python` 的 dist-info：LiteLLM 1.102.0 存在，未找到 opentelemetry-proto、googleapis-common-protos 或 protobuf 的安装 metadata。它不能充当 lab 协议依赖已准备好的证明。决定 lab 声明自己的最小宿主依赖，纯读取按需导入，不让缺协议包阻断历史查询。

后补会话与新批次元数据用附加表关联旧 batch ID。原 payload 不重编码、不去重。HTTP 请求体接收需要网络空闲超时和有界解压；这是防止半截上传卡住正常收尾，不向模型请求加时长限制。关闭服务先停止接收，再等待在途保存；硬中断后的缺口保持可见。

## 7. 网关接口确实覆盖 Chat 与 Responses，但还不能当作实测

在 WSL 现用 LiteLLM 源码进一步追到调用点：

- `proxy/auth/user_api_key_auth.py:1346–1357` 基本 custom_auth 直接验证 UserAPIKeyAuth。
- `proxy/litellm_pre_call_utils.py:2306` 将可信认证 metadata 带入请求上下文；本项目应从认证对象建立 run/request 归属，不相信请求正文自报。
- `proxy/response_api_endpoints/endpoints.py:349–358` 的 Responses 路由进入共同处理并传入 select_data_generator。
- `proxy/proxy_server.py:9253–9263` 选择 async_data_generator，9057–9062 在 callback 覆盖 iterator hook 时包裹实际流；`proxy/utils.py:2518` 用具体类的覆盖检测能力。因此 hook 要实际定义在注册的 GatewayCompat 类上。
- `integrations/custom_logger.py:451/472/503` 分别提供 failure、success 和 streaming iterator 接口；pre-api hook 继续可用。

决定采用这些现有扩展，不修改 LiteLLM。每请求固定认证上下文，单独保留 ingress/LiteLLM/provider ID。流 EOF 本身不证明模型有业务终态；终止标记、usage、异常与取消分别记录。记录代码不可吞掉或替换上游响应，也不在流式每个 chunk 等 OTLP HTTP。

尚需真实运行证实实际参数、各供应商异常、在途回调和元数据传播；计划安排纳入下一次获授权矩阵，当前没有发送 API 请求。新 gateway 独立 state/端口，旧共享 token 实例继续原样服务，不热切换已有实验。

## 8. 报告选择和冻结来源需要一并修复

`benchmarks/hackathon/report.py:128` 按 finished_at 选择，新的 running 可能被旧成功盖住；:109 用当前 checkout coverage 校验旧记录；:150 以 replay ZIP 相同限制比较。应共用 job/attempt 选择并记录所有候选，读取冻结条件，按明确变化轴比较。

还有一个实现细节：`outcome():69` 将 Playwright 所有 results 的 attachments 混合，再要求唯一 outcome。合法重试可能有多个附件，当前逻辑既可能错误拒绝，也无法表达最终尝试与正文冲突。应先选择明确的测试尝试，再核对最终状态与该次附件；不修改用例来适配报告。此项来自源码，未观察到真实误计分。

## 收尾判断

上述八类问题都已得到具体接线或兼容方案，没有剩余的产品选择或外部接口阻断需要用户决定。现有源码仍有这些缺口，本轮没有宣称已修复。

本轮证据来自互相独立的源码路径核对及既有真实数据；它能确定实施顺序和发现接口冲突，不能替代实现后的真实操作。未来验收按 plan 的范围分开记录；没有发生的故障和没有获授权的模型调用不补造结果，也不建立设施探针填空。
