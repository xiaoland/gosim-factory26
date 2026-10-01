# Bub 原生 adapter 实施回执

2026-10-01。开工依据为用户“你也可以开始委派接入bub了”，范围见 [packet](packet.md)。本次独立于 I13 和 Console，不实现 Alma，不启动模型或旧实验。

## 交付与具体边界

Braid 新增 `src/provider/bub.rs` 与 `src/provider/factory/bub.rs`，复用现有 ProviderAgentSession、SessionFactory、queue 和 Unknown 恢复契约。Profile 接受 `adapter_type: bub`；local 请求接受可选 bub 配置并核对实际 Profiles，一次 local 仍只组成一个 adapter 类型。BubConfig 持有 executable/home、启动期限及可选凭据入口；模型与 reasoning 仍由 Profile 持有。本次没有改变 I13 默认 provider 或任一 variants/skills。

原生 stdio 按 JSON-RPC 2.0 传输。每物理会话拥有独立 process 和 BUB_HOME；真正加载的 `bub hooks` 必须证明 official session-prompt 与 builtin FileTapeStore，ACP initialize 必须支持 protocol 1/loadSession。工作目录为该成员 clone，system/profile 写入 `sessions/acp-server:<ACP_ID>/AGENTS.md`，技能仍独立。没有 user injection 的 ACP 通过持久化 Context 加首轮用户前缀承接既有 renderer 正文；native tape 保存确切正文后才停止加前缀，首次 prompt 前的空会话可恢复。

session/prompt 的响应为终态而非 admission，adapter 先记录本地 turn ID/TurnStarted，再异步等待 response；没有普通控制 RPC 的30秒期限。native session/update 保留具体 assistant/reasoning/tool/usage 内容，prompt error 保留完整 JSON-RPC error，EOF/无 terminal 为 Unknown。固定版 cancel 最终 no-op，因此发送 cancel 后关闭 owned stdin，让原生 shutdown 退出，再沿复用的进程组/后代停止并 wait 核实。空闲 release 同样 factory teardown。Codex 原进程停止代码提取到 `provider/process.rs` 供两者复用，Codex 保留原 immediate 路径；停止操作加互斥，防止两个同时 teardown 把在途停止误认为完成。

私有 steering 可另开不归本次 prompt response 的后台轮次，因此 Bub adapter 不发送该扩展，返回 Deferred；输入留在 Braid queue，下一空闲边界交付。load 会收养未知 ID 并改写 cwd，因此恢复前核对 Braid binding、唯一 native metadata ID/cwd 及准确 tape 路径。只有已提交过 prompt 且确切 tape 缺失才是 HistoryUnavailable；读取权限、类型、身份或 cwd 错误保留具体原因并阻断。已得创建 ID 后文件落盘失败仍返回 Materialization Some(ID)，缺少/无效 ID 为 CreatedWithoutIdentity。

消费证据读取该准确默认 tape，本次提交前的 entry watermark 排除以前相同正文；精确匹配保存的完整 native 用户正文，并要求随后 assistant message 或同 run_id 的 assistant tool_call。只剥离固定的 native channel/date 包装，user echo、工具结果或 acceptance 均不算消费。native_session_id 是默认 tape stem，provider session_id 是 ACP ID；Bub 没有原生身份 header，OTLP 用 recognized-path 明示较弱的路径关联。模型 usage 从 native event/run 的已报告字段按 run_id 去重，ACP usage_update 是上下文快照，不能累加。缺少字段保持未知。

持续约定已整合到 Braid 的 app-server、local、lifecycle 与运行说明，PRD 只扩展 adapter 的验收边界。完整语义不复制到 Factory 长期文档；Factory 这里只保存当前实施、授权和原始证据入口。

## 实际反馈与来源

证据根为 `runs/braid-provider-expansion/bub-20261001/`，不进入 Git。`source-identity.json` 保存实际 Cargo manifest、独立 target、平台、rustc、所有实际 Rust/Cargo 输入哈希、binary SHA-256 和固定上游来源。Braid 起点为 `8325ed6ed7e9b649e8e52eb8f6e53a8fb6f90f2e`，起点 index 为空；`baseline/worktree.diff`、`baseline/status` 及文件快照保存此前 dirty。漏单独复制的 local.md 从同一开始时 HEAD＋完整 dirty diff 恢复到快照，恢复命令与输出亦在证据根。没有从当前修改后的 local 文本倒推基线。

源码与安装固定 Bub `94d13be8b3b7854dd8acd44251f3ac4502fd3d85`、bub-contrib `b511ad2d4ba5622f267de5076d1bbb62119ea6ff`。同一 contrib 提供 ACP、session-prompt、bub-mcp，SDK 固定 agent-client-protocol 1.0.0rc2；`native-dependencies.txt` 保存实际隔离环境。首次 uv 安装遇到 Bub 本地 URL 与 bub-mcp 声明的 Git URL 冲突，原工具错误转录在 dependency-install-error.txt；随后用 task-local dependency-overrides.txt 统一两个固定本地源码来源，完成安装。上游源码未修改，没有全局安装/配置写入或凭据读取。

| 原始材料 | 已观察结果 |
| --- | --- |
| build-final.log | 显式 `--manifest-path sources/braid/Cargo.toml --bin braid`、任务独立 CARGO_TARGET_DIR 编译成功；13条既有 dead-code warnings，无新编译错误。 |
| braid-help.txt、braid-local-help.txt、braid-cli-operations.json | 新编译 binary 的真实 help 均 exit 0。 |
| bub-help.txt、bub-acp-help.txt | 隔离安装的真实 native CLI help 均 exit 0，stdio 为默认支持的 transport。 |
| bub-hooks.txt | 实际 system_prompt 包含 builtin、session-prompt，provide_tape_store 为 builtin；插件 gate 所需来源可读取。 |
| acp-operation.json、acp-transcript.jsonl、acp-stderr.log | 未发 prompt，真实 initialize/new 后进程 exit 0；重启 initialize/load 同一真实 ID后 exit 0，acp-sessions.json 保留同一 ID/cwd。 |
| native-system-read.txt | 用该真实 ACP ID读取原生 system hook，执行了 official session-prompt，指向 `sessions/acp-server:<ACP_ID>/AGENTS.md`，保留 native 默认 system。 |
| owned-increment.diff、shared-owned.diff、final-worktree.diff | 本次相对开始时 dirty 的增量，以及最终已跟踪实际源码组合，供审核和恢复。 |

实际创建的 no-model session 为 `f125db58cc9d43e8aad82e596506725f`。没有虚构 conversation/tape、模拟 fixture、Factory/Braid/SVC 测试、smoke/probe、自检或模型实验；新会话未执行 prompt，因此没有 user/assistant tape，这也是首轮前 metadata 可存在而模型历史尚为空的真实条件。

独立 advisor 先核对固定上游协议和既有 consumer 契约，再只读审核最终接线与原始材料，建议的两处创建身份/metadata 唯一性小修已完成。角色身份不作为验收证据；结论依据编译、实际 CLI/协议、实际 hook 与确切来源记录。

## 提交与未验事项

Braid 增量提交为 `76747f2db174237501d948c36b5321ad3ffd75ae`（16路径），binary SHA-256 为 `5e82f88d368fe54e4d3425a88f586242e7729c980930c7cf4d2d60e80f49bfaa`。提交仅收本批相对开始时 dirty 的增量，保留 config、agent_session、factory/pi、queue/group/cli/store 及文档既有修改。本次依赖实际开始时已有的 HistoryUnavailable 等接口；因此编译身份是记录过的实际工作区源码组合，不能把裸 HEAD 或仅当前增量 commit 冒称同一构建。既有 `sources/braid/target` 指向 third_party/braid/target；本次未使用该链接构建，独立 target 与 binary 哈希见 source-identity.json。

本次可以证明源码编译、真实 CLI、native plugin 读取、新建和重启 load 身份接线。prompt 完成、原生工具、活动取消与进程树清理、精确消费 receipt、真实用量及完整 Braid 任务效果都未运行模型验证。FileTapeStore 以外的 native storage、不可靠 steering extension 和多 adapter 混用不在当前接入范围，不能据本轮成功扩大兼容声明。没有 push。
