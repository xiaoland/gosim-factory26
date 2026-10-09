# 独立 Rust 模型代理

用户要恢复低常驻内存的同模型供应商 fallback。本任务由此独立会话持续负责调查、设计、实现、材料交付与必要实际操作；其它会话负责公共资源 gate、Linux runtime 与当前实验，本任务不接管这些职责。

## 授权与范围

来源会话转交的用户原话为“那如果 minimal rust proxy 呢？”以及“试一下，安排一个独立的会话去实现”。本会话 2026-10-03 用户补充“可以使用 minimax, qwen token plan 来完成验收”。授权覆盖新代理及少量有界真实供应商调用；不包含新 benchmark、完整评分、修改或控制现有实验。明确不 commit/push，不替换既有 gateway/helper、canonical variant 或冻结 ZIP。

Mac 项目产物全部在 `runs/model-proxy-20261003/`，已核对实体路径属于 `/Volumes/WorkSSD` 及同一设备，空间足够。Cargo cache/target、TMPDIR、Zig cache、日志、材料与验收证据均绑定此目录；仅只读现有宿主工具。

## 当前方案

独立 crate 为 `sources/model-proxy/`，使用 Tokio/Axum/reqwest/serde_json。`prepare.py` 从集中 catalog 和现有 alias→deployment ID 有序列表冻结必要适配；公开 config 保留模型、provider/plan、endpoint、凭据变量名及输入 hash，0600 私有 JSON 只含所选 key 与本地访问 token。不会建立第二套维护模型目录。

Flash 使用千帆个人 Plan→ARK；DeepSeek0731 使用千帆个人 Plan→千问 Token Plan→普通千问；K3 使用 ARK→普通千问。顺序来源为已有 provider-fallback cell，按套餐优先而非未知普通价格推定最便宜。ARC、智谱原厂不进入链。当前 catalog 已包含所需 rows；供应商页部分验证状态落后于该 cell 的真实调用原件，不能由 catalog 推导已验收。

首版仅 Chat Completions，Pi 原生 `openai-completions` 与 E2E `provider.chatModel()` 是实际消费者。未知 JSON 字段、tools/reasoning/images 原样保留，只替换 model、认证及路径；成功 JSON/SSE 直接转发。在提交客户端 HTTP headers 时锁定上游；仅 429、500/502/503/504、明确连接失败可以在提交前切换，不为 header timeout 重放。每 deployment 一次、最多三次，不隐式 retry。不解析 SSE continuation。

独立 advisor 已建议 Hyper HTTP/1 驱动 Axum Router，关闭 keep-alive 与 half-close，一个连接一个请求，由连接绝对期限涵盖下游背压；直接 await reqwest 保持取消传播。SIGTERM 停止接受新连接，已有连接有界排空后取消。该设计判断不是 reviewer 验收。

## 验收与边界

不编写或运行设施测试、模拟集成、probe/自检/smoke。完成 macOS/Linux x86_64 release 编译、真实空闲/短请求/流式 RSS 观测及少量正常请求。没有真实 429 时不声称 fallback 429 已实测；请求正文和生成内容不落代理日志，不整流保存。记录 RSS 与采样分辨率，不能把包体或构建内存当运行内存。

2026-10-03 已只读确认千问 Token Plan key 存在，MiniMax key 仍为空；先用千问完成独立验收，MiniMax 欠缺凭据时保留其边界。

## 已交付与实际观察（2026-10-03）

独立实现和本轮材料交付已完成；没有 commit/push。使用说明归 `sources/model-proxy/README.md`，公开材料归 `runs/model-proxy-20261003/delivery/`。源码归档包含新模块、冻结 Cargo.lock、复用的 prepare helper 及集中 catalog 快照；不含私有凭据。`delivery/manifest.json` 保存逐文件源码 hash、两个二进制 hash/大小、编译工具身份、输入/config hash、依赖和验收边界。Mac 二进制为 aarch64，Linux 二进制为 x86_64 ELF；构建目标 glibc 2.36，实际验收宿主 glibc 2.41。这个实际操作不证明任意 Linux 镜像都可运行，系统 CA 根仍是运行依赖。

最初精简 TLS feature 的启动遇到 reqwest 要求显式安装 crypto provider 的 panic，当时尚未调用供应商。已安装 Rustls Ring provider 并重新编译；原始错误保存在 `logs/startup-failure-qwen-proxy.jsonl`，失败回执亦保留。后续补足 transport error source chain，防止只记录泛化的“error sending request”；这一错误分支仅经编译，没有伪造故障来宣称实测。

通过千问 Token Plan 的 `deepseek-v4-flash-0731` 进行了两平台正常短操作。初版每个平台各完成普通 Chat、SSE、工具调用及首个 SSE data 后关闭客户端：均 HTTP 200；SSE 收到 `[DONE]`，工具返回 `report({text: "OK"})`。关闭客户端后的代理日志记录连接错误及终态，未切换上游；这证明本地传输取消，不证明供应商立即停止计算或计费。进程随后 SIGTERM 正常退出（退出码 0），当时没有在途请求。最后交付版本在两个平台各重做普通 Chat 与 SSE，二进制 hash 与交付 manifest 对齐；工具/取消证据来自立即之前仅缺少 transport source-chain 日志的版本，该版本二进制另存 `acceptance/observed-{macos,linux}-model-proxy`，不混淆身份。

| 最后交付版本 | 启动后空闲 RSS 采样最大值 | 短 Chat 采样最大值 | SSE 期间采样最大值 |
| --- | --- | --- | --- |
| macOS aarch64 | 3.84 MiB | 5.95 MiB | 6.55 MiB |
| Linux x86_64 / WSL | 5.00 MiB | 5.77 MiB | 5.77 MiB |

采样使用 `ps -o rss=`，间隔请求为 100ms，另加 subprocess 延迟；结果是 RSS，不是 cgroup charge、构建内存或包体，也不能证明短于采样间隔的峰值。未测长期或并发内存。原始 CSV 和回执分别为 `acceptance/{macos,linux}-rss-final.csv`、`acceptance/{macos,linux}-qwen-final.json`。最初正常操作的 RSS、usage 与身份同样保留在无 `-final` 后缀原件中。最终包体分别为 3,204,880 和 3,696,296 字节。

供应商正常调用共 12 次，其中 10 次完成并取得 usage，合计 714 tokens；2 次主动关闭流的调用没有终态 usage，不能推定零费用。使用套餐权益，未取得 Credits 实际抵扣/人民币账单。没有使用 MiniMax：本轮凭据核对时 key 为空，使用许可已保存，后续填妥可接续该 alias 的有界验收。

远端首先只读确认 `wsl.win-ws.localhost` 实际宿主为 `yyh-ws`、x86_64 Linux/glibc 2.41，独立目录实体设备为 2096、空闲约 106GB，再传入选中千问 key 的 0600 私有 JSON。运行未触碰其它实验；取回公开回执后已删除远端私有 JSON。身份与 ELF GLIBC 符号需求见 `acceptance/linux-platform-final.json`，远端独立现场为 `/home/yyh/factory26-model-proxy-20261003-01a1010e`。

## 剩余接入与未验证边界

本轮授权的独立代理实现、双平台编译、正常真实操作、内存记录和材料已完成。canonical variant、官方 ZIP、公共 gate 和正在运行的实验均未接入此代理；这些后续应用仍归对应 owner/packet 与用户决定，不能据本模块启动新的实验。

没有观察到真实 429/5xx/连接故障，因此 fallback 机制已实现但这些故障路径未实测。超时、慢客户端背压、并发等待和带在途请求的 SIGTERM 仅具有实现边界与编译反馈。Flash/K3、图像、Pi/E2E 完整消费尚未在此代理实际验收；同模型候选可用性沿用明确的历史证据，不能将当前 DS 的成功扩大为全链能力或模型版本等价结论。未执行设施测试、mock、probe/自检/smoke 或新 benchmark。

下一步若用户授权主线采用，由现有 Harness/材料 owner 消费本轮 manifest、独立二进制和冻结适配接缝；此会话继续持有代理局部问题的调查、修复与验证责任。
