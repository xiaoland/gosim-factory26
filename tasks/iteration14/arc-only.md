# I14 模型 API 授权边界

用户要求后续 I14 停止使用自有模型 API。四个 I14 variant 的源码入口因此只接受 `https://api.arc-bench.com/v1`，并在创建运行目录前核对所有模型 URL 输入。`OPENAI_API_KEY` 保留为平台输入别名；它与 `FACTORY26_API_KEY` 同时存在时必须相同，视觉密钥也不能另选。原生模板的两个 provider 和 cleaner 使用同一个 `FACTORY26_API_KEY`，e2e SDK 同样固定 ARC endpoint。

成员进程环境移除 Pi 0.85.1 能发现的非 ARC 供应商认证，包括继承的 `OPENAI_API_KEY`。Context7、Exa、ARC 平台记录、OTLP 和普通操作系统环境继续保留。现有 `subagents.modelScope` 严格接受 `factory26/*` 与 `factory26-visual/*`，因此已注册 ARC 模型的显式 override 仍可使用，其它 provider 的显式、继承和 fallback 模型会被拒绝。这个约束不限制工具或角色职责。

I14-0 dispatcher 在创建 operation 前校验选定连接，生成只含选定 ARC 模型认证的私有环境，并在启动前拒绝已有环境中的其它供应商认证。恢复工具若接续 I14，应先调用 variant 的 `arc_connection()`，以 `model_environment(key)` 构造成员环境，并用当前 `native_files()` 刷新原生材料；只更改 URL 不能移除旧供应商认证和旧子 Agent 配置。

2026-10-02 的编译与实际材料准备证据位于 `runs/iteration14/arc-only-20261002/`。四次 `--prepare-only` 均完成，九份原生模板的 endpoint、key 环境变量与 provider 范围一致；清理后不存在供应商认证变量。四个非 ARC URL 输入均退出 1，且未创建输出目录。操作没有启动模型。第一次准备把 Braid 目录误作为二进制传入，保留首次错误后改用已有二进制，第二次完成。

本次只更改 canonical 源码，未更改冻结 ZIP、manifest、dispatcher 副本、已有配置、native homes 或运行中的容器。这些约束随下一次重新冻结的 I14 制品生效；当前三项运行及五项排队制品不据此宣称已部署新保护。
