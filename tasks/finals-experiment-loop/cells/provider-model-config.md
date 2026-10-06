# Provider deployment 模型配置

2026-10-07 用户补充：LLM gateway/model proxy 必须按 provider deployment 保存模型参数；例如 ARK Coding Plan 的 Kimi K2.7 与其它提供商的输出上限不能共用一个默认值。本 cell 记录本次实现的事实、边界和主线接线要求；可执行的模型描述归 `harness/model-gateway.json`，不在 recipe 中复制。

## 采用决定

每条 deployment 的 `model_info` 是该 deployment 的模型描述单一来源。已核实的字段直接写在该对象中：`contextWindow`、`maxTokens` 和 `compat`；未核实的字段省略，不用 catalog 默认值填充。recipe/route 只表达 deployment 顺序。

接线时经 advisor 再次核对，ARK 的 `chat_completions`、`reasoning_summaries` 是供应商能力说明，不是 Pi `compat` schema，已移入 `capabilities`，不投影进原生配置。当前 K2.7 沿用 variant 已有的 `compat`、`reasoning` 与 thinking 配置，只消费已确认 contextWindow/输出上限；未来只有完整、已核实的 Pi schema 描述块才替换 compat。没有该块时保持原值，不能把“不支持 reasoning summaries”改成禁止推理或删除 thinking。

Rust proxy 在 freeze 时完整保存选中 deployment 的 `model_info`。每次 attempt 从原始请求读取已有的 `max_tokens`、`max_output_tokens`、`max_completion_tokens`：多个字段数值冲突时具体返回错误；有 `maxTokens` 时将每个已存在字段限制为 `min(requested, maxTokens)`，不为未提供的请求增加默认值，也不把字段互相改名。attempt 日志记录 `requested`、`effective`、`deployment`、`source`、实际序列化的 `request_body_bytes` 及结果 `elapsed_ms`，不记录 prompt、完整 `extra_body` 或凭据。

LiteLLM 使用实际安装版本提供的 `async_pre_call_deployment_hook`，该 hook 位于具体 deployment 已由 Router 选定、请求尚未发送的边界；不在 `async_pre_call_hook` 中猜首选 provider。旧 `GATEWAY_PRESERVE_PARAMETERS` 删除参数分支已退役，原始 `thinking`、reasoning 和预算字段默认保留；只有选中 deployment 有明确描述时才做上述输出上限收敛。

## ARK 官方证据

火山方舟官方 Coding Plan 文档的模型配置页列出 `kimi-k2.7-code`，并说明其 OpenAI 兼容 Base URL；同页的模型限制表在搜索返回内容中给出 Kimi-K2.7-Code 的上下文窗口 **256000**、最大输出 **32000**。官方 OpenCode 配置页同样给出该模型的 `limit.context: 256000` 与 `limit.output: 32000`。官方 Codex 配置页确认该模型不支持 `model_supports_reasoning_summaries = true`。本目录的 `maxTokens` 表示 provider 接受的请求 `max_tokens` 上限，而非文档中的建议输出长度：历史真实 ARK 400 已明确返回“`max_tokens` 最大允许 `32768`”，因此冻结值为 **32768**；这条运行证据见 `tasks/pi-minimal/sequential-stage2-stage3-20261006/packet.md:114`。当前链接：

- [Coding Plan 个人版概览](https://docs.volcengine.com/docs/ark/coding-plan-personal-plan-overview?lang=zh)
- [Coding Plan 接入 OpenCode](https://docs.volcengine.com/docs/ark/coding-plan-personal-ai-opencode?lang=en)
- [Coding Plan 接入 Codex](https://docs.volcengine.com/docs/ark/coding-plan-personal-ai-codex?lang=en)

同一官方 OpenCode 配置页给出 ARK `kimi-k3` 的 `context: 1024000`、`output: 65536`，因此该 deployment 也写入已核实的两个数值。其它 provider/model 尚未取得同等明确的官方限制证据，本轮不填猜测值。页面由动态文档渲染，核对日期为 2026-10-07；若官方页面后续变更，应更新 catalog 与本 cell 的证据时间，不用运行时探测覆盖冻结描述。

## Native 绑定消费要求

主线接线时，native role/profile 的模型绑定应消费当前选中 deployment 的完整 `model_info` 描述块：

1. 以 route 选中的 deployment 为准，不从稳定 alias 或 recipe 的第一项推 provider；
2. `contextWindow` 用于构造上下文预算时取该 deployment 已确认值；
3. `maxTokens` 仅作为请求已有输出预算的上限，不应在 native 层无请求时凭空加预算；
4. 只有完整且已核实的 Pi schema `compat` 块才整体替换原值。`capabilities.reasoning_summaries=false` 不投影到 Pi compat，也不删除原 thinking/reasoning；
5. 每次 run 保存实际 deployment、requested/effective 输出预算和描述来源，在途 run 沿用自己的冻结配置；restart 是新 run，按当前装配重新冻结，不改写来源 run。

未覆盖的兼容差异仍应让 provider 返回具体错误并保留原始诊断；不能为了成功而删除 thinking、reasoning、tools 或供应商扩展字段。

## 已交付的接线

`lab/arc_bench/harness_services.py` 在包内从 `inputs/model-gateway.json` 与
`inputs/gateway-routes.json` 冻结 Rust proxy；Hosted 从 `.private/provider-env.json`
读取选定凭据，本地只读取 catalog 声明的环境变量。包内 proxy state 位于
`.private/model-proxy/<run_id>`，不是可迁移的实验 data；native 通过
`FACTORY26_BASE_URL`、`FACTORY26_GATEWAY_TOKEN` 与 `FACTORY26_MODEL_BINDINGS`
使用 loopback。descriptor 的键覆盖 `factory26/<alias>`、I14 的 visual selector，
以及 `deepseek-v4-flash` 到 `deepseek-v4-flash-0731` 的显式 wire alias；同一 alias
多 deployment 的 native `contextWindow`/`maxTokens` 取已确认值的最小值，Rust
request attempt 仍按具体 deployment 使用各自上限。

两个 DX builder 接受 `--catalog`、`--provider-env`、`--model-proxy`，并把 catalog、
route、私有 provider-env、adapter 与 Linux proxy 放入包。当前源码已在 Mac 完成
release 编译；Linux 产物需由可用的 Linux 构建环境生成到
`runs/provider-model-config-20261007/delivery/model-proxy-linux-x86_64` 后，才能
进行带 proxy 的最终包构建。sfp7 本次独立构建因 crates 下载 SSL/超时未取得产物，
没有因此发起模型请求。

## 接续验收反馈

2026-10-07 run `bf51263913f7414d9d50207deaa417c8` 的保存 config 原始
`body_bytes` 为 4194304；gateway request 7 只记录了
`body_limit_or_read_error`，而同一 run 的 `events.jsonl` 中最近一次图像工具结果
单行约 1.64 MiB、最终 `agent_end` 证据约 4.41 MiB，支持请求体确实超过 4 MiB，
不是业务零分。该证据促成取消固定请求体字节上限：合法的 Pi 历史和图片可能超过旧
4 MiB 限制，不能通过截断或替换上下文来“修复”。新 proxy 仅保留 body read timeout、
JSON 解析和具体有界的 `body_read_error` 诊断，并让 fallback attempts 重用同一个可变
JSON，避免整份图片/历史重复 clone。Linux binary 已重新编译供两个 builder 使用；旧
run 与原始错误保留不覆盖。

## P2 传输诊断

独立接续 run `a0d8fdab6eea4fe295c1bbcff65bca41` 的 gateway 原始日志显示：request 1、3
在 QIANFAN_TOKEN_PLAN 上取得 HTTP 200 并完整读完；request 2、4、5、6、7 均在
`SendRequest` 阶段约 30.1–30.6 秒后得到 `Connection timed out (os error 110)`，
`connect=false`，且没有收到上游 HTTP 状态或 request id。旧 proxy 的配置为
`connect_ms=10000`、`headers_ms=90000`、`total_ms=600000`，因此这些 30 秒终态不是
proxy 配置的 connect/header/total deadline，也不是本地 body cap；`connect=false` 不能
证明 TCP 建连从未发生，更准确地说是上游发送阶段的连接写入/等待失败。

同一保存现场的原生 session 在 request 1 前已有约 4.4 MiB 历史，request 2/3 前约
5.0 MiB，request 4 之后约 6.7 MiB；这支持“请求体变大后暴露 provider/路径限制或
瞬时网络故障”的候选，但 request 3 在相同量级成功，不能仅凭这些材料断言 Qianfan
有固定 body 上限。WSL 宿主没有 proxy 环境变量，Docker 使用默认 bridge；事后对
`qianfan.baidubce.com` 两个 DNS IPv4 地址分别强制解析，HTTPS HEAD 均约 0.1 秒返回
404，证明核对时宿主 DNS/直连可用，但不能回溯证明失败时容器内的发送路径可用。

因此本次没有扩大模糊 transport fallback，也没有修改 provider、切换 route 或再发
模型请求。可操作接续是：保留该失败和未知上游受理/计费事实；若继续验收，使用新
proxy 运行并先让 gateway 记录每次实际序列化请求字节数，再按“请求大小、解析地址、
发送阶段”与错误时点相关分析。仅在取得同一时段的容器内网络/请求大小证据后，才决定
是否是 provider body 限制或执行域网络故障；不能用宿主事后 HEAD 成功替代该证据。
