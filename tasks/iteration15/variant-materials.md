# I15 variant 与材料接线

已从当前 `variants/pi-braid-i14-reviewer-cleaner-e2e` 派生独立 `variants/pi-braid-i15-reviewer-cleaner-e2e`。只改变入口身份、通用交付指令、三个 Braid 成员指令、reviewer profile tag、独立 builder 和 README；原模型、原生角色、扩展、工具及 materials 声明字节保持。Variant 索引已加入新入口。

reviewer 同时持有 `reviewer-only` 和 `single-reviewer-per-pr`。首次版本通用指令由 `native_files()` 拼入所有成员，要求直接读取原始需求、保留未取消基线、冻结审阅 base/head、旧审阅实际收口后才开始下一候选。reviewer 详细指令要求每执行隔离验收状态、允许多个原生子角色、conclude 前关闭自有进程并保存证据，以 conclude 作为专门会话最后动作。

builder 保留旧完整 standalone 底包及网关配方，强制传入 `--braid-binary` 和 `--braid-build-receipt`。接受 Linux x86_64 ELF64，并核对 receipt 的 `braid_binary_sha256`、`target`、`source_identity`；拒绝与底包旧 Braid 相同的 SHA。overlay 和 manifest 包含替换后的 `runtime/bin/braid`，外部 `package-identity.json` 将 `base_runtime_source` 与 `braid_replacement` 分别记录，不能把底包编译来源当作新 Braid 来源。实际打包方式见 variant README；没有修改公共 `scripts/package_agent.py`。

验证已完成：全部 Python AST、全部 JSON 解析；三个 profile 与 I14 比较仅 reviewer tag 变化；通用指令经现有 native_files 拼接消费；相对来源只有上述八个文件变化。没有运行测试、模型实验或包 smoke，也未 commit/push。Linux Braid编译由Braid owner完成，实际overlay已生成于`runs/iteration15/materials/overlay.tar`（22,128,640字节；SHA256 `f8624d31fd785e3da00693504ebc60d0917825ed1614db70b0b1ee1095ba1f45`），身份收据为同目录`package-identity.json`。实际归档读取确认reviewer tag、新binary SHA与manifest绑定一致；新Braid SHA256为`60b8f13c8ea780c690bb43b08c5cb7cf00ea6ff84029e06807f8be3bb17c76c2`。这是完整底包加overlay交付，不另复制844MB完整ZIP，未做模型或跨环境运行验证。

确定旧资源协议缺口已闭合：builder显式接收`--protocol-runtime`同版runtime（Pi0.85.1），叠加现成新resources helper到support/runtime两位置、native-managed、实际Pi launcher及bundle薄入口、三个变化dist模块。support/agent_support仅替换runtime_resource_environment当前函数，逐字比对确认其它函数与冻结底包保持。归档读取确认所有protocol_overlay SHA与manifest一致，实际RPC模块不再保留relieve_pressure旧分支。Braid owner定向核实当前Pi仍创建managed execution identity并通过helper launch，不再据factory状态查询移除误称缺少Pi接线。此闭环未运行包smoke或模型。

## Reviewer 指令与发现目录简化（当前交付）

用户授权“是的，按这个方向推进”。只修改I15，不改I14或在途运行；原共享skill description/body保持。reviewer默认发现从16缩至7项（braid-collaboration、arc-bench、svc-verification、e2e、agent-browser、svc-sub-agents、context7-docs）；完整底包的其它skills文件不删除。native_files按reviewer-only tag选择验收环境和专属目录，其它成员仍消费原RUN_CONDITIONS及16项目录，cleaner/原生角色/模型保持配方。reviewer不再收到框架、组件库、样式及持久化实现选型指导，只保留必要验收环境。独立instructions收短，明确一次“建立原始需求对应验收判据前读取svc-verification”的触发，可复用已读上下文，按问题读references；保留原始需求权威、候选冻结与串行交接、验收隔离、正式构建完整用户旅程、结论证据和结束自有进程等责任。

实际调用native_files只准备原生材料，不启动launcher、网关或模型。读回reviewer7项，两实施profile16项；两者最终user_instructions与上一版逐字一致；reviewer最终文本不含框架/组件/Tailwind/SQLite选型，唯一verification阅读触发。读回记录在`runs/iteration15/materials/reviewer-focused-final/readback.json`，profiles与launcher保存在该目录。reviewer最终文本由3146字符降为1427字符；这仅是输入材料变化，未证明模型触发或验收质量改善。

上一版overlay、receipt、run.py及reviewer instructions已保留在`runs/iteration15/materials/history/single-reviewer-protocol-f8624d31/`，其SHA为`f8624d31fd785e3da00693504ebc60d0917825ed1614db70b0b1ee1095ba1f45`。当前overlay仍为`runs/iteration15/materials/overlay.tar`，SHA为`77c090261f1a5886b7feb7afcc4879d5aca502bb637df215e854ef15f1645c33`，22,128,640字节；同目录package-identity.json记录当前身份。实际归档再次读回确认源码成员、原protocol配套SHA一致，未移除任何skills成员。AST/JSON通过；没有测试、包smoke、模型或官网实验，没有commit/push。

最终补充：结论明确Approved / ChangesRequested / Inconclusive三选一。before/after分别调用保存的上一版run.py和当前run.py实际native_files，量化最终profile文本（source instructions +追加环境），不是只计instructions.md；reviewer由3146字符/7630 UTF-8字节降为1427字符/3429字节，两个实施profile均3658字符且前后逐字相同，默认技能16→7与16保持由实际launcher读回。最终证据以reviewer-focused-final/readback.json为准；首次中间准备材料仍保留。
