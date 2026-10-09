# Rust proxy 的 Harness 接入

2026-10-03。本会话持有网关接线、打包依赖闭包与实际兼容验收，来源会话 `01a0fd22-fe3b-7430-9707-4534e7758565` 负责采用结果和实验恢复。用户在运行实验主线已明确授权“sources/model-proxy 开发完成，建议现在就应用”，授权由创建本会话的任务消息转交。本次不 commit/push，不控制旧 Hosted run，不新增官网生成或评分，不继续账户或余额调查。

源码范围为 `scripts/model_gateway_service.py`、`scripts/agent_support.py` 的网关调用边界、`scripts/package_agent.py` 的网关依赖闭包、`sources/model-proxy/prepare.py` 的冻结适配接口及现有启用网关的 variant 调用。其它 owner 持有 checkpoint、恢复、controller、资源 gate 和 runtime builder；其改动必须保留。两个 direct variant 维持无 gateway 的既定配方。

接入沿用 `start_model_gateway/stop_model_gateway`，调用方显式选择 `implementation='rust'`。消费已选择的 run-local catalog config 和明确 alias→deployment 有序链，在 run 中另建不可复用的 Rust state；不暗选 `routes-i14.json` 或改变模型。公开配置记录来源 hash，私有凭据只交 proxy，Pi/E2E 获得本地 token、URL 和重写后的原生 bindings。代理进程由 run 持有，关闭核对出生身份、等待 8 秒宽限并有界收尾。健康只证明代理启动，模型兼容须由实际调用取得。

已核实独立交付 manifest：Linux x86_64 binary 为 `runs/model-proxy-20261003/delivery/model-proxy-linux-x86_64`，SHA256 `70c51af5826c12b94b3d1a1386c0c066c1847707de824d948398f3dac6933afe`，3,696,296 bytes；构建目标 glibc 2.36，之前实际 WSL 验收宿主 glibc 2.41。Rust 核心源码不在本次修改范围。Mac 产物均位于 WorkSSD，同设备容量已核实。

当前状态：接入与闭包可采用，Python 编译成功。正式回执为 [receipt.json](../../../runs/iteration14/resource-recovery-20261003/model-proxy-integration/receipt.json)，可直接消费的接口和材料依赖为 [consumer-contract.json](../../../runs/iteration14/resource-recovery-20261003/model-proxy-integration/consumer-contract.json)。没有 commit/push、修改 Rust 核心、控制旧 run 或新增官网生成/评分。

`agent_support` 的重复 LiteLLM 启停实现已改为共享 owner 转交；启用网关的 Cleaner、Reviewer、E2E 调用显式选择 Rust。`package_agent.gateway_sources()` 为两个包装入口提供同一源码列表及依赖 hash，包含 `model_gateway_service.py`、`hackathon_gateway.py`、既有两个兼容模块和由 `sources/model-proxy/prepare.py` 安装的 `model_proxy_prepare.py`。Rust 分支不加载兼容服务或 LiteLLM。`freeze_proxy` 只接受已选择 config、明确 routes 和选定凭据，拒绝未知参数、不同候选顺序或重新使用 state。CLI 现在要求显式 catalog/routes/credentials，不依赖部署机器的仓库默认目录。

本轮在 `wsl.win-ws.localhost` 实际宿主 yyh-ws 的独立目录 `/home/yyh/factory26-proxy-integration-20261003-01a1012f` 运行了相同接口；x86_64、glibc 2.41 与远端容量已核实。使用唯一已选千问 Token Plan 的 DeepSeek0731，短 Chat、SSE 和工具调用均 HTTP 200；SSE 收到 `[DONE]`，工具返回 `report({"text":"OK"})`，合计终态 usage 为 342 tokens。代理 SIGTERM 后退出码 0，无在途请求。`/proc/pid/status` 约每 100ms 采样，空闲最大 RSS 4.86 MiB、请求最大 5.75 MiB；这些不是 cgroup charge、长期或并发峰值。原件归 [Linux 回执](../../../runs/iteration14/resource-recovery-20261003/model-proxy-integration/linux-results/linux-operation-receipt.json) 与同目录 CSV、gateway.log、config 和 process-evidence。

实际读回确认客户端环境无所选上游 key 名称或值，proxy 也未通过环境继承上游 key，而是仅读取 0600 私有文件；E2E token/URL 为本地值，精确 alias 和 bindings 的 model/model_id 保持。源 gateway-config 字节未变。远端临时凭据与本地临时私有 archive 已删除；公开原件已回收至 WorkSSD。实际运行的 support hash 保存在回执；运行后仅增加源 routes 路径/hash 的来源记录，已编译，不冒称补充字段已经重跑真实调用。

材料 owner 仍需将上述 binary 复制到新 runtime 的 `bin/factory26-model-proxy`；controller owner 冻结 package producer 时须纳入 `sources/model-proxy/prepare.py`。恢复 owner 调用时显式传 `implementation='rust'`，采用完整 `pi_environment`，不要使用 update 留下旧凭据。两个 direct variant 保持直连，不据本次网关授权切换其原配方。接口参数与可消费 support 列表已冻结在消费回执，主线无需重复本轮调查或调用。

未验证范围为官网首次接续与实际 OOM/cgroup 效果、完整 Pi/E2E SDK、图像、Flash/K3、真实 fallback 错误、超时/并发/慢客户端/带在途请求的 SIGTERM，以及本地 authority writer registration 分支。本轮独立 WSL 操作没有 execution_context，该分支复用已有 `state_writer.spawn`，不以编译替代实际 authority 反馈。官网首反馈验收条件已写入 receipt，归主线恢复 owner 在原授权接续中取得；没有建立模拟上游、设施测试、probe 或 smoke。
