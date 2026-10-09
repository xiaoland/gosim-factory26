# I15 variant 与材料接线

当前采用材料（2026-10-08，reviewer语义更正）为 `runs/iteration15/materials/reviewer-request-session-20261008/overlay.tar`，SHA256 `38962b5fa124efa02e1ac6fcca057c46a06c22ade7ccd6925e58a986eebfc888`，22517760 bytes。新Linux Braid为 `17c3aa5d51ac4a4ea4c59f3bda7df26b37ed9bc6ac4a3c08bb0d8937a4357962`；每个候选重新指派独立reviewer Session，完成/取消走Unassign，改派停止旧Session后创建新Session，禁止同PR并行验收。去掉跨候选自动继承及PR锚运行消费，保留原Pi补丁输入、模型与其它I15配置。编译、CLI与原生反馈局限见 [reviewer更正](reviewer-session.md)，实际归档核对见同目录readback.json。该材料未热部署或启动模型/官网评测。

历史材料（2026-10-07，reviewer持久解释已撤回）为 `runs/iteration15/materials/runtime-integration-20261007/overlay.tar`，SHA256 `7fbf2347a2b235e81c7e2cee45da816171dc1188e9aa13a59b2441880c2225a3`、22,466,560 bytes。它包含每PR持久reviewer Session的新Linux Braid（8540ea7a…）、完整当前Pi补丁目标、原生245k独立压缩阈值和根负责人跟进指令。99个声明成员与实际底包/overlay/manifest SHA读回一致，overlay有46成员。接入范围、未采用的其它生产者修复及运行局限见 [Pi与运行时接入](runtime-integration.md)；旧 `materials/overlay.tar` 和 `pbb-e2e-isolation-20261007` 均作为保留历史，不作为当前推荐构建输入。下面保留其形成过程。


已从当前 `variants/pi-braid-i14-reviewer-cleaner-e2e` 派生独立 `variants/pi-braid-i15-reviewer-cleaner-e2e`。只改变入口身份、通用交付指令、三个 Braid 成员指令、reviewer profile tag、独立 builder 和 README；原模型、原生角色、扩展、工具及 materials 声明字节保持。Variant 索引已加入新入口。

reviewer 同时持有 `reviewer-only` 和 `single-reviewer-per-pr`。首次版本通用指令由 `native_files()` 拼入所有成员，要求直接读取原始需求、保留未取消基线、冻结审阅 base/head、旧审阅实际收口后才开始下一候选。reviewer 详细指令要求每执行隔离验收状态、允许多个原生子角色、conclude 前关闭自有进程并保存证据，以 conclude 作为专门会话最后动作。

builder 保留旧完整 standalone 底包及网关配方，强制传入 `--braid-binary` 和 `--braid-build-receipt`。接受 Linux x86_64 ELF64，并核对 receipt 的 `braid_binary_sha256`、`target`、`source_identity`；拒绝与底包旧 Braid 相同的 SHA。overlay 和 manifest 包含替换后的 `runtime/bin/braid`，外部 `package-identity.json` 将 `base_runtime_source` 与 `braid_replacement` 分别记录，不能把底包编译来源当作新 Braid 来源。实际打包方式见 variant README；没有修改公共 `scripts/package_agent.py`。

验证已完成：全部 Python AST、全部 JSON 解析；三个 profile 与 I14 比较仅 reviewer tag 变化；通用指令经现有 native_files 拼接消费；相对来源只有上述八个文件变化。没有运行测试、模型实验或包 smoke，也未 commit/push。Linux Braid编译由Braid owner完成，实际overlay已生成于`runs/iteration15/materials/overlay.tar`（22,128,640字节；SHA256 `f8624d31fd785e3da00693504ebc60d0917825ed1614db70b0b1ee1095ba1f45`），身份收据为同目录`package-identity.json`。实际归档读取确认reviewer tag、新binary SHA与manifest绑定一致；新Braid SHA256为`60b8f13c8ea780c690bb43b08c5cb7cf00ea6ff84029e06807f8be3bb17c76c2`。这是完整底包加overlay交付，不另复制844MB完整ZIP，未做模型或跨环境运行验证。

确定旧资源协议缺口已闭合：builder显式接收`--protocol-runtime`同版runtime（Pi0.85.1），叠加现成新resources helper到support/runtime两位置、native-managed、实际Pi launcher及bundle薄入口、三个变化dist模块。support/agent_support仅替换runtime_resource_environment当前函数，逐字比对确认其它函数与冻结底包保持。归档读取确认所有protocol_overlay SHA与manifest一致，实际RPC模块不再保留relieve_pressure旧分支。Braid owner定向核实当前Pi仍创建managed execution identity并通过helper launch，不再据factory状态查询移除误称缺少Pi接线。此闭环未运行包smoke或模型。

## Reviewer 指令与发现目录简化（上一冻结交付）

用户授权“是的，按这个方向推进”。只修改I15，不改I14或在途运行；原共享skill description/body保持。reviewer默认发现从16缩至7项（braid-collaboration、arc-bench、svc-verification、e2e、agent-browser、svc-sub-agents、context7-docs）；完整底包的其它skills文件不删除。native_files按reviewer-only tag选择验收环境和专属目录，其它成员仍消费原RUN_CONDITIONS及16项目录，cleaner/原生角色/模型保持配方。reviewer不再收到框架、组件库、样式及持久化实现选型指导，只保留必要验收环境。独立instructions收短，明确一次“建立原始需求对应验收判据前读取svc-verification”的触发，可复用已读上下文，按问题读references；保留原始需求权威、候选冻结与串行交接、验收隔离、正式构建完整用户旅程、结论证据和结束自有进程等责任。

实际调用native_files只准备原生材料，不启动launcher、网关或模型。读回reviewer7项，两实施profile16项；两者最终user_instructions与上一版逐字一致；reviewer最终文本不含框架/组件/Tailwind/SQLite选型，唯一verification阅读触发。读回记录在`runs/iteration15/materials/reviewer-focused-final/readback.json`，profiles与launcher保存在该目录。reviewer最终文本由3146字符降为1427字符；这仅是输入材料变化，未证明模型触发或验收质量改善。

上一版overlay、receipt、run.py及reviewer instructions已保留在`runs/iteration15/materials/history/single-reviewer-protocol-f8624d31/`，其SHA为`f8624d31fd785e3da00693504ebc60d0917825ed1614db70b0b1ee1095ba1f45`。上一冻结overlay保留为`runs/iteration15/materials/overlay.tar`，SHA为`77c090261f1a5886b7feb7afcc4879d5aca502bb637df215e854ef15f1645c33`，22,128,640字节；同目录package-identity.json记录当前身份。实际归档再次读回确认源码成员、原protocol配套SHA一致，未移除任何skills成员。AST/JSON通过；没有测试、包smoke、模型或官网实验，没有commit/push。

最终补充：结论明确Approved / ChangesRequested / Inconclusive三选一。before/after分别调用保存的上一版run.py和当前run.py实际native_files，量化最终profile文本（source instructions +追加环境），不是只计instructions.md；reviewer由3146字符/7630 UTF-8字节降为1427字符/3429字节，两个实施profile均3658字符且前后逐字相同，默认技能16→7与16保持由实际launcher读回。最终证据以reviewer-focused-final/readback.json为准；首次中间准备材料仍保留。

## I15独立E2E状态转移方法（最新可供后续采用材料）

用户授权“好的，那么开始改进（仍然是I15）”。只为I15新增本地skills/e2e同名技能与独立business-state-transitions reference，builder将skills目录叠加到本包，reviewer增加一句引用。共享harness/I14及已冻结在途运行不变，7/16发现目录保持。方法采用冻结e2e API，引入局部有期限的可见成功/失败终态与首次失败/复测条件记录，不改变全局timeout/retry。新overlay为runs/iteration15/materials/e2e-state-transitions-20261007/overlay.tar，SHA68b13ba014cf41f28900e3ce60ff076f69fd025ffe1ad7ab0a9787a4032c62e9，22,138,880字节；旧77c090...原件仍保留。实际native_files、launcher和归档读取证据在新目录readback，未启动模型、smoke或官网。本次实现记录归tasks/e2e-acceptance-state-transitions/packet.md；新方法尚未被当前stagechain采用。
