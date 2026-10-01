# PR 初始快照与读取入口重复

2026-10-01。用户观察 `flash-root--hackathon--sheet` 的 PR2 provider session 中，context/user-message 已包含 PR description，模型随后仍读取同一 description，并要求委派核实、将必要修复纳入本地 GLM 运行。主线据此授权本页的调查、已证问题的最小 Braid 消息修正、技术说明、编译和真实离线材料操作，以及限定提交；未授权官网操作、收费试验或改变运行配方。

## 观测与解释

原始本地冻结包为 `runs/iteration13/local-20261001/model-cutover/flash-root--hackathon--sheet-f893bdb3298d69-workspace.zip`，官网保全包为 `runs/iteration13/hosted-recovery-20261001/sheet-first-workspace/workspace.zip`。两包共享 Braid run `20261001-074506-6e7af22b` 和 PR2 native session `01a0f675-edd9-7466-b938-3b1b3fd89594`。本地 JSONL 的 193 行是官网包 215 行的精确字节前缀；重读发生在原始 DeepSeek Flash 执行，不能归因于本次 resume。

定向证据在 `runs/iteration13/pr-context-duplication-20261001/`。`hosted/` 只抽取所需 Braid DB、物理会话材料和 PR2 JSONL，不把全部 rollout 导入主会话。该 JSONL 相对于两包的路径为 `template/.factory26/20261001-074506-6e7af22b/work/native-homes/pi-deepseek-fast-01a0f675-ea4a-7c20-a67e-762bfd5c2682/sessions/2026-10-01T07-55-18-874Z_01a0f675-edd9-7466-b938-3b1b3fd89594.jsonl`。

| 观察面 | 精确事实 | 能支持的判断 |
| --- | --- | --- |
| 首次真实用户消息 | JSONL 第4行，ID `4d8d42e0`，07:55:21.795Z。7559-byte `physical/01a0f675-ea49-7d33-9689-52b36d757da6/context.md` 是该 7721-byte 用户消息的精确前缀，在该消息只出现一次。 | `context.md` 是保全材料；Pi 将它拼入首条 prompt 一次。未发现同一首次请求收到两份全文。 |
| 首条末尾事件 | `PR #2 与 Issue #1 关联变为 true；读取 braid pr view 2`，另有“新 PR 工作”。DB event `01a0f675-de23-7e90-9a55-19c71a2a66a2` 发生于07:55:14.851Z，早于会话物化；同条快照已经给出关联和相关 Issue description。 | 首次输入要求再次读取一个已由当前快照提供的对象，存在已证的机械读取诱导。 |
| 模型行动 | 第5行已决定查看 PR，随后读取 braid-collaboration；第8行 ID `e03b79d0` 于07:55:47.837Z 执行 `braid pr view 2 --comments`，第9行返回。其1813-byte PR body 与首条快照逐字相同，SHA-256 为 `a3092bd3df3ad450df87cb3e963660bfd68d538b1d64363500ed17d98551bda9`。 | 确实发生同版本全文重读。技能读取前已经决定 view，不能据此指认技能导致这次动作；输入中的机械指令也不证明是模型唯一动因。 |
| 后续输入与恢复 | 第17、74、123、135、179行仅给评论事件；第194行09:32:28.233Z为 unknown 后恢复事实，未拼入 Context；第195行 assistant 的 model 为 `glm-5.3-flash`。DB 保持原 provider session，resume_count=1。 | 原始 DeepSeek 与恢复 GLM 的行为可按模型和时间区分；后续增量和 resume 没有重复注入全文，当前历史连续性不需要修改。 |

生产链为 `pr_create → link_in → metadata_changed`，关联事件在创建事务内发出；PR materializer 先渲染完整当前快照。`begin_agent_assignment` 消费 Assign 事件，保留 wake batch；`claim_runnable_turn` 因而给首轮 `wake_batch`，`render_event_references` 又呈现其中的关联读取指令。Pi `start_turn` 在接受首条 prompt 后清空待注入 Context；resume 不重新装载 Context。首轮与后续事件共用呈现入口，因此修正命令语气和共享阅读约定即可，不需要改变队列、事件消费或会话接口。

## 最小修改

`sources/braid/src/group/provider.rs` 明确当前上下文已给出的内容直接采用，读取入口用于补足缺失内容或核对后续变化；评论的义务是取得本条正文，已有正文可以复用。事件标题改为“相关更新与按需读取入口”。`sources/braid/src/objects.rs` 将 parent、title、comment、association 四类共享事件中的祈使“读取”改为“详情入口”或“正文入口”。变化事实、目标对象、CLI 命令和投递关系保持原样；事务提交结果未能确认时的具体核对要求保持原样。

已展开的 fresh snapshot 可以直接用于工作；后续关联加入或解除、评论新建/编辑、折叠或截短导致正文缺失时，入口仍可取得必要信息。没有禁止模型在具体不确定性下主动核查，也没有新增版本协议、全文字符串去重、固定 SOP 或事件过滤。braid-collaboration 及独立技能文件不改，因为未找到本次重读由技能独立规定的证据。长期约定更新到 `sources/braid/docs/20-product-tdd/context.md`。

## 实际反馈与限制

`cargo check --locked --offline` 和离线 `cargo build --locked --offline` 通过，保留12条已有 dead-code warning；`git diff --check` 通过。首次 Cargo 命令在依赖离线选项之外仍触发 rustup 的固定 toolchain 安装，重叠 build 出现安装回滚错误，具体记录在 `cargo-check.log`、`cargo-build.log`。后续直接使用已安装、同为1.93.0的 stable Cargo/Rustc 离线顺序构建，成功日志为 `cargo-build-offline.log`，未扩大工具链修复。

在官网冻结 DB 的独立 SQLite backup 上，用实际编译 binary 执行 `pr view 2 --json body`、`pr unlink 2 --issue 1`、`pr link 2 --issue 1`、`pr comment 2` 和 `context pr 2`，均返回退出码0。`offline-cli-results.json` 保存完整回包；`offline-produced-events.json` 显示解除和恢复关联都通知现有两个消费者，评论仍提供单条正文入口。只修改离线副本，未启动 Braid 成员、provider 或模型。

`pr2-original-first-input.md` 保留冻结原生首条正文，`pr2-revised-first-input.md` 用同一正文、当前 renderer 的精确事件标题和真实 CLI 生成的关联 reference 组合。对照显示当前任务、关联 Issue 和事件事实均保留，读取入口已变为中性提示。`summary.json` 保存字节数、身份和本机 binary SHA-256（`86a45ef9f40eacfe931eaa973d990f468a292b036dc690620673f58b6fff71f0`）。这项反馈证明输入措辞及真实事件生产者的变化，不证明模型之后一定减少重读；行为反馈留给本地 GLM 的既定运行。未编写或运行 Factory/Braid 测试。

## 交接材料

本批只需从修改后的 `sources/braid/src/group/provider.rs` 与 `sources/braid/src/objects.rs` 重新构建 Braid binary。`sources/braid/docs/20-product-tdd/context.md` 和本页是说明材料；无需刷新 profile、技能、native home、Pi transport 或角色文件。实际恢复应保全停止现场和旧历史，在恢复副本覆盖新 binary，再沿原 offline-resume 边界继续。worker 在 offline-resume 重新生成 `local_instructions`；Pi 同时使用原 `--session` 和更新的 `--append-system-prompt`，本地负责人已核实 Pi 重建 base system 而保持同一 native session。本批不新增 reset 理由或改写历史。历史及已排队事件的 reference 不迁移，通用指令和按需事件标题提供接续语义，新产生事件使用中性入口。

Linux交付已完成：在上一版combined冻结源码上仅叠加 `828a3da` 的两个源码文件，保留成员目录修正 `4ce6d31` 与信号诊断 `727c2c0`。标准源码SHA256为 `5181c5b2dfb0f547b46775c7b5cdbcc20476ea83ee392275f438100f27a093aa`，Linux x86_64 release binary为 `5e98b9374d20870fc6dd45406b4b2d4efc41bf9e6fbb9f3edd4ff64ae8f50a73`。制品和构建/源码逐文件核对回执在 `runs/iteration13/pr-context-duplication-20261001/linux-combined/`；主线独立重算binary摘要一致。

首次构建虽然exit0，但归零tar时间与共享target使Cargo复用旧根包binary，交付前的实际摘要核对发现不符。原attempt归 `stale-cache-attempt/`；仅清理Braid根包的release缓存后离线实际重编译，未重新安装依赖或工具链。最终构建保留12条已有warning。

部署与两路本地实验的整合由主线和本地负责人承担。旧Debian数据已清除，用户已明确授权“有快照就恢复，没有就重新启动吧”：GitHub保留Mac完整快照的原生会话，Sheet干净启动。宿主迁移引起的transport和已授权成员迁移属于恢复接线，不是本提示修正的新要求。当前Linux制品已交付，包内身份及实际运行生效仍待本地启动回执。
