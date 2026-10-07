# I15：单 reviewer 与验收隔离

用户授权：基于 I14 reviewer/cleaner/e2e 组合版推出 I15，“每个 PR 只能指定一个 reviewer”，更新 reviewer Braid Agent 指令，隔离并行验收的数据库等状态；补充“原始 requirements 视为绝对权威”。

本轮实现源码与必要文档，不启动新模型实验、不改在途 I14/Pi 运行。初次实现未获提交授权；后续用户明确“可以整理一些提交”，授权整理本任务的本地 Git 提交，未授权 push。保留共享工作区其它修改。Mac 产物全部存放 WorkSSD。

基线为 variants/pi-braid-i14-reviewer-cleaner-e2e，派生独立 I15。单 PR reviewer 约束需覆盖跨候选更新，不能误做成全运行只有一个 reviewer；不同 PR 仍可并行。当前 request 已限制单个负责人，但不同 request 会创建不同 reviewer，需核实并收敛。

root 负责整体判断与采用；advisor 已核实成员投递和停止语义。采用每 PR 一个当前 reviewer 责任与执行、跨候选串行交接；不复用跨 request 的 login。旧请求取消或完成并不等于物理停止，必须复用现有停止屏障收口；冲突指出旧请求，不自动取消。Braid owner `/root/i15_braid_owner` 负责机械约束、所属技术文档和编译/真实 CLI 操作；variant owner `/root/i14_combo_sequential_owner` 负责独立 I15、提示词、打包接线和 variant 索引。reviewer 指令包含原始需求权威、进程级独立数据库/缓存/上传/浏览器/服务/证据，原始交付数据只读复制，不污染候选。反馈使用编译与实际操作，不编写或运行 Factory/Braid 测试。

当前实施边界：只在 I15 显式启用单 PR 约束；原 I14 冻结运行及模型配方保持原身份。I15 不能沿用组合版旧 ZIP overlay 继承旧 Braid 二进制，打包必须实际包含新约束。原始 requirements 的绝对权威指业务验收标准，不允许 PR 描述、设计、自验降低标准。

打包决定：I14 组合版的 frozen-base 还持有当前共用 producer 未提供的 standalone gateway，因此 I15 保留专用 frozen-base overlay，强制提供新 Linux Braid 二进制并替换旧 binary，保存实际 SHA 与编译来源。此轮不扩展 gateway/context 接口或公共交付架构；没有新 Linux binary 时不能宣称完整新包已完成。

必要配套修复：定向接口核对确认旧底包 admission 依赖缺失的 resource sample，而当前 Braid 已无旧等待闭环。仅替换 binary 不可运行；采用现成同版 process-control helper、native-managed 与实际 Pi bundle/dist，局部更新 agent_support.runtime_resource_environment，不改变网关和模型。修复归 variant owner，Braid owner提供具体已有材料与接口证据。无新设施框架或模型实验。

已完成并采用：独立 `variants/pi-braid-i15-reviewer-cleaner-e2e`；单 PR 策略在 request、assign 与实际启动边界生效，完成/取消沿已有 Unassign 收口，blocked 分支同样进入停止路径。reviewer 原始 requirements 权威、每执行状态隔离和 conclude 前关闭自有进程的指令已进入实际 profiles；原模型、角色和工具配方保留。

编译与反馈：Mac debug、Linux release 通过；真实历史 run 的隔离 SQLite/Git 副本通过公开 CLI 观察同 PR 冲突、幂等、不同 PR 独立分配、默认旧行为及 completed/sleeping 不提前释放。来源与局限见 `runs/iteration15/braid-policy/verification.md`，variant 材料接线见 `tasks/iteration15/variant-materials.md`。

最终交付为冻结完整底包加 `runs/iteration15/materials/overlay.tar`，不是重复拷贝出的 ZIP。overlay 22,128,640 bytes、35 成员，当前 SHA256 `77c090261f1a5886b7feb7afcc4879d5aca502bb637df215e854ef15f1645c33`；身份与新 Braid/协议材料记录在同目录 `package-identity.json`。builder 强制新 Linux binary、其来源 receipt 与同版 protocol runtime，实际归档身份已核对。

本轮实现收尾。没有新模型运行、官网评测、Factory/Braid 测试、包 smoke 或 commit/push；未实测新运行的原生 teardown，生命周期反馈以现有实现和隔离历史 CLI 操作为限，真实运行验证待后续运行授权。没有改动在途 I14/Pi 或将隐藏反馈注入生成。

后续调查：用户提出可能简化 reviewer instruction/skills，并怀疑 svc-verification 触发或加载性能。此轮先只读定向抽样 reviewer rollout 与技能发现/加载接口，区分未触发、失败、读后未采用；不因未出现技能名直接断言故障，不跑模型、不改在途运行。I14 稳定 owner 负责实际样本，root 负责指令/目录与加载实现；具体简化范围依据反馈确定。

用户纠正“发现、加载性能”指技能触发、摄取和实际采用的可靠性，并要求参考 matt-skills。已读 mattpocock/skills 当前 writing-for-agents 及 SKILL-MECHANICS（https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents）：context pointer 的措辞决定触发；必需材料应先强化指针而非直接删除；信息分层和消除重复服务稳定行为。前述85ms/2ms只能说明两个文件读取调用成功，不能回答用户的语义问题。四样本显示相同指令下是否读取不同，属于触发一致性线索；具体注意负担/description/skill正文采用的因果仍待运行比较。建议为reviewer缩小默认发现面，先把“按原始需求建立验收判据”设为清晰入口及一次skill触发，并以验收计划/判据/实际旅程证据评价，不以读取次数评价。本次尚未修改源码或启动模型。

reviewer 简化开工：用户明确授权“是的，按这个方向推进”。variant owner `/root/i14_combo_sequential_owner` 接续负责 I15 reviewer 专属默认技能目录（16→7）、清晰单次 svc-verification 触发、职责指令去重和实际 profile 消费、overlay 更新。root/实施者目录及文本保持；原技能文件继续打包，共享 SVC description/body 不改。原始需求权威、冻结候选、每执行隔离、完整旅程、证据与 conclude 收口边界必须保留。只做材料接线/语法/归档核对，不新增模型/官网运行或 Factory/Braid 测试。之前 overlay/identity 保留历史副本，实际行为收益仍须后续运行反馈。

reviewer 简化已完成并采用。实际 native_files 前后材料生成及 launcher/profile 读回确认：reviewer 默认目录16→7，最终职责指令+环境3146→1427字符；两实施profile指令逐字不变、目录仍16。唯一 svc-verification 触发明确为原始需求验收判据建立前读取，保留所有硬边界及三种结论。原skills文件、模型/角色/cleaner和工具配方保持。现有builder已重产overlay，旧材料保存在 materials/history/single-reviewer-protocol-f8624d31；新身份见上文及 package-identity.json。证据见 variant-materials.md 与 runs/iteration15/materials/reviewer-focused-final/readback.json。本轮无模型/官网运行，触发及验收质量的改善未实测，不把输入变短当行为收益。

提交整理已执行：`6f5b0680 feat(braid): 限制每个 PR 的当前评审责任` 仅包含 Braid 本轮 policy、blocked 收口及其 local 技术说明；`7b8f5519 feat(i15): 派生组合版并聚焦独立评审职责` 包含完整 I15 独立目录、variant 索引及唯一必要 support 初始化函数。共享混合文件按 hunk 提交，其它通知文案、运行设施与历史任务修改保留工作区。最后单独提交本 packet、材料反馈及技能调查和工作主题入口。没有推送。

提交依赖核对：HEAD 已有 Braid 相关 schema/方法/Unassign 与 SessionManager 接口；隔离 HEAD 上仅本轮补丁适用性检查通过。I15 源码没有 task_context import，不需纳入该未跟踪文件。builder 使用的 scripts/runtime_resources.py 已在 HEAD；只补充 agent_support.runtime_resource_environment 的同版配置函数。包的 gateway、Linux binary 和 protocol runtime 仍来自明确的外部冻结材料，不能把 clone 当成材料已就绪。原编译和实际 CLI 反馈属于其冻结源码现场，未启动新模型或物理 teardown 验证。
