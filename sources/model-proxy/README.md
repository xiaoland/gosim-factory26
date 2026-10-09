# Factory26 独立模型代理

这是 run-owned 的 Chat Completions 代理。客户端使用既有精确 alias；代理从集中模型目录冻结同模型有序 deployment 链，按已购套餐优先规则切换供应商。每个 deployment 的 `model_info` 是该 deployment 的模型描述单一来源：只有已核实的 `contextWindow`、`maxTokens` 和 `compat` 才会写入；routes 文件只表达顺序，不复制模型限制。实现与 Braid crate、资源 gate 和既有 LiteLLM 接线独立。`I14-dx-test` 的 DX 包与已移除的 `pi-minimal-vv-dx-test` 历史包曾实际采用该模块，并在 WSL 自费 BookStack 接续中取得过真实 200 响应；完整生成、评测及上游 transport 超时后的接续仍未通过验收。

当前目录中 ARK Coding Plan 的 `kimi-k2.7-code` 使用官方 Coding Plan 文档确认的 256k 上下文，并标记不支持 reasoning summaries；其 API `max_tokens` 硬上限 32768 由历史真实 ARK 400 响应确认（官方工具配置示例的模型输出限制为 32k）。ARK `kimi-k3` 使用官方工具配置文档确认的 1M 上下文、64k 最大输出。官方页面为动态文档，核对日期与链接保留在[模型配置 cell](../../tasks/finals-experiment-loop/cells/provider-model-config.md)；未核实的其它 deployment 不填默认上限。

## 冻结与使用

`prepare.py` 复用 `materials/model-gateway.json` 和既有的 `{alias: [deployment_id, ...]}` 路由格式。`routes-i14.json` 仅保存本轮候选 ID 和顺序，不复制模型、URL、密钥或另一套价格目录。Flash 为千帆个人 Plan→ARK；DeepSeek0731 为千帆个人 Plan→千问 Token Plan→普通千问；K3 为 ARK→普通千问。普通千问费用尚未取得精确价格；这个顺序不等于已证明全链最便宜。这个历史配方未包含 ARC 和智谱原厂；当前公共配方另按用户最新选择维护。

新 run 必须创建独立 state，冻结后不修改在途配置。以下示例只准备材料；state 在 Mac 上必须真实位于 WorkSSD。输入凭据可为 0600 dotenv 或现有 provider-env JSON，输出只包含实际选中的 key。

每个 alias 最多接受四个连续有序 deployment。GLM-5.3 的当前四链归[跨 variant 模型配方](../../materials/model-recipes/README.md)，历史 `routes-i14.json` 保留其原实验身份。Python 冻结器与 Rust 启动校验必须一起支持四链；配置仅在启动时加载，不提供在途 reload。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 sources/model-proxy/prepare.py \
  --catalog materials/model-gateway.json \
  --routes sources/model-proxy/routes-i14.json \
  --credentials .secrets/models.env \
  --state /Volumes/WorkSSD/Development/factory26/runs/my-run/model-proxy \
  --run-id my-run --listen 127.0.0.1:4021

factory26-model-proxy \
  --config /Volumes/WorkSSD/Development/factory26/runs/my-run/model-proxy/config.json \
  --credentials /Volumes/WorkSSD/Development/factory26/runs/my-run/model-proxy/.private/provider-env.json \
  > /Volumes/WorkSSD/Development/factory26/runs/my-run/model-proxy/events.jsonl
```

公开 `config.json` 包含实际模型/endpoint、凭据变量名、输入 hash 和限制，`config.sha256` 标识整份配置。`.private/provider-env.json` 为 0600，私有目录为 0700；其中包含所选供应商 key 与新生成的本地访问 token。`.private/client.env` 只包含本地 token 和 `/v1` URL，不包含上游 key。密钥值不进入公开配置或源码。适配器拒绝未知 alias/deployment、同一 alias 内重复 deployment、缺失引用和不支持的目录字段；不同 alias 共用同一供应商 deployment 是合法的，防止目录演化被静默丢弃。请求中的输出预算字段若同时出现且数值冲突会具体报错；若 deployment 有已确认 `maxTokens`，每次 attempt 都使用 `min(requested, maxTokens)`，不会为未提供预算的请求添加默认值，也不会把 `max_output_tokens`、`max_completion_tokens` 等字段互相改名。

Harness 通过 `tooling/scripts/model_gateway_service.py` 的 `start_model_gateway(..., implementation='rust', preserve_parameters=True)` 持有子进程。输入是 run-local 已选择 catalog config、明确的 `gateway_routes` 和 0600 `provider_env`；runtime 必须提供 `bin/factory26-model-proxy`。接口复用本模块的 `freeze_proxy`，不再选择模型或修改源 config；打包器将适配器冻结为 gateway 组件中的 `model_proxy_prepare.py`，无需在部署机器寻找仓库。配置及路由另存为 run-local 只读文件，新 state 拒绝覆盖。

启动必须同时读到本子进程匹配 run/config/listen 的 ready 事件、确认出生身份，以及 `/health/liveliness` HTTP 200。返回的 `pi_environment` 和 `bindings` 保持原模型及参数，仅改本地 URL/token；E2E 使用相同本地凭据，`E2E_MODEL` 仍是精确 alias。调用方须采用完整返回环境，不能用 update 将已移除的供应商凭据留在旧环境。上游 key 只交给代理私有文件，不继承给 Pi/E2E。Pi 继续使用 `openai-completions`，内部 DeepSeek selector 显式映射到 `deepseek-v4-flash-0731`。

`stop_model_gateway` 在信号前核对所持 PID 的出生身份，SIGTERM 后等待配置中的 8 秒宽限加 2 秒余量，超时才向同一进程发送 SIGKILL 并有界等待。网关原始 stdout/stderr 最多保留 8 MiB，达到上限后保留 capped 标记并继续排空，避免日志阻塞代理。身份与配置 hash 写入 run 的 `model-gateway.json`；不会按端口查找并停止别的 run。健康 200 不证明模型调用完整，真实调用及接入范围归[接入记录](../../tasks/iteration14/resource-recovery/model-proxy-integration.md)。

## 请求与失败合同

仅提供 `POST /v1/chat/completions`，使用 `Authorization: Bearer <local token>`。当前 Pi 与 E2E 都消费 Chat；没有 Responses、协议转换或 SDK 层。请求 JSON 保留未知字段与数值表示，只修改顶层 `model` 和已存在的输出预算数值；不会解释或删除 thinking/reasoning、tools、tool_choice、图像或供应商扩展字段。JSON 空白和字段排列不保留。上游认证及 URL 从冻结 deployment 获取；不会转发客户端任意认证、代理头或自定义请求头。每次 attempt 事件只记录 requested/effective/deployment/source 四类预算信息，不记录 prompt、完整 extra_body 或凭据。

成功响应体，包括 SSE 字节，使用背压直接转发，没有整流、完整响应缓存、SSE 解析或提示词持久存储。响应状态及端到端头保留，hop-by-hop 头和 Content-Length 去除；下游由 Hyper 重新定界。HTTP 响应交给 Hyper 就锁定上游，即使还没有 token。随后读取错误、空闲超时、SSE 内嵌错误都不会换供应商或续写；内嵌 SSE 错误由客户端解释。

每个 deployment 最多尝试一次，每条链最多四项。只有明确连接错误或 HTTP 429、500、502、503、504 可在提交前换下一项；千帆上游 HTTP 401 的完整 JSON `error.code` 精确为 `subscription_expired` 时，也可在提交前切换下一项；这是订阅失效的窄例外，截断或解析失败不匹配。ARC 上游 HTTP 402 的完整 JSON（顶层或 `error` 包装）同时精确匹配 `code=insufficient_balance`、`type=billing_error` 时，也可切下一项；依据历史原生错误 JSON，尚未通过真实耗尽请求重新验收。其它401/402/403/400、重定向仍直接结束。等待响应头与既有单请求 total 上限同为 600 秒；这避免在总时限内因独立的 90 秒 header 截止过早返回 504，不重置请求起点、不增加重放。没有 cooldown、同通道重试或按错误内容推测套餐恢复。`Retry-After` 不触发等待循环。reqwest retry 和 redirect 显式关闭；HTTP/1 且禁止上游空闲连接复用，排除内部对复用连接未发送请求的重连路径。

错误响应最多读取 4096 字节、最多等待两秒。attempt 事件记录实际序列化的 `request_body_bytes`；结果事件记录该 attempt 的 `elapsed_ms`。日志仍只记录 requested/effective/deployment/source、阶段和有界具体错误诊断，不记录 prompt、工具参数或凭据。错误诊断按请求字符串与实际凭据精确脱敏。最终 HTTP 错误仍用原状态及有界原始 body 返回，可能被截断，`x-model-proxy-error-truncated: true` 明示此情况。成功流的正文、工具参数和生成内容不写日志。日志中的 `complete` 表示读到上游 EOF，不证明供应商计费结束或客户端业务已接受结果。

## 资源与生命周期

冻结不设置请求体字节上限，也不设置本地活跃、等待请求或连接数量配额；请求直接采用所选供应商链，不通过人为槽位排队或拒绝。旧冻结配置中的这些配额字段只用于读取兼容，不再影响执行。连接建立最多 10 秒，上游响应头最多 10 分钟，下游请求头/体分别最多 30 秒，流读取空闲最多 60 秒。整个连接从接受到下游发送结束最多 10 分钟，包含所有候选尝试。请求体读取仍受 30 秒 `body_ms` 限制，读取失败返回 400 `body_read_error` 并记录有界的具体诊断。取消固定字节上限是为了容纳真实 Pi 的完整历史、工具结果和图片；不截断正文或替换 provider 上下文。启动配置最多 1 MiB，私有凭据最多 64 KiB。其它限制可在创建新冻结配置时明确调整，Rust 启动会校验数值范围。

本地仅监听 loopback HTTP/1，一连接一请求；关闭 keep-alive 和 half-close。Hyper 连接直接拥有 handler 和上游 stream，不另开后台转发任务。普通客户端关闭连接会取消本地上游传输；连接总期限还能在下游背压期间销毁连接。HTTP pipelining/额外未消费字节会影响即时 EOF 检测，绝对总期限仍有效；本接口不提供 pipelining 使用合同。取消传输不能证明供应商立即停止计算或计费。

SIGTERM/SIGINT 停止接受新连接，在途连接最多宽限 8 秒；到期取消全部连接并退出。健康入口无需 token，只反映本进程已启动和配置已加载，不代表供应商可用。日志写 stdout，owner 必须将其指向本 run 的受控文件；长期运行日志轮转由 owner 负责，不在代理内建立服务或存储系统。

Linux客户端显式取消reqwest 0.13.5默认的30秒TCP_USER_TIMEOUT，让已配置的请求总期限控制等待。该依赖默认值会在上传数据长时间未获ACK时先于总期限关闭连接；取消它不保证出口或供应商接收恢复，也不改变fallback或重试规则。

## 构建与交付

`Cargo.lock` 冻结依赖。Ring 是 Rustls 的显式 crypto provider；TLS 使用系统信任根，禁止跳转到未知 endpoint，不自动消费宿主 HTTP_PROXY。编译需 Rust 1.93 或相容版本。Mac 构建的 Cargo cache、target、TMPDIR 及 Zig cache 必须绑定 WorkSSD，不能调用默认写入 home 的构建流程。

```sh
CARGO_HOME="$PWD/runs/model-proxy-20261003/cargo" \
CARGO_TARGET_DIR="$PWD/runs/model-proxy-20261003/target" \
TMPDIR="$PWD/runs/model-proxy-20261003/tmp" \
cargo build --locked --release --manifest-path sources/model-proxy/Cargo.toml
```

Linux x86_64 使用 Cargo Zigbuild 的 `x86_64-unknown-linux-gnu.2.36` 目标；运行需要 x86_64 Linux、glibc ≥2.36 与系统 CA 根。交付目录与原件在 `runs/model-proxy-20261003/`，源码、二进制、依赖、配置身份及真实内存结果由该目录的 manifest 与验收回执记录。编译和实际操作是本模块的验证方式；不新增或运行 Factory 设施测试、模拟上游、probe、自检或 smoke。

2026-10-03 交付版本已通过千问 Token Plan 的真实短 Chat 与 SSE，两平台进程均正常退出。macOS 空闲 RSS 采样最大值为 3.84 MiB、SSE 最大值为 6.55 MiB；Linux/WSL 分别为 5.00 MiB、5.77 MiB。使用 `ps` 每约 100ms 采样，这只是短请求观察，未测并发、长期运行或 cgroup charge。工具调用与客户端取消在紧邻的上一构建完成，身份单独保存。真实 429/fallback、图像、Flash/K3、完整 Pi/E2E 接入及在途 SIGTERM 尚未实测；MiniMax 获准验收但 key 为空。准确范围与证据入口见 [任务记录](../../tasks/minimal-rust-model-proxy/packet.md) 和交付 manifest。
