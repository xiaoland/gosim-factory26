# 从实际消费者审查 instruction 与 prompt

当前输入链大体可以让成员分清 Issue 设计、PR 实施、Braid 指派与原生协助，但仍有一个应优先修复的接线缺口：运行共同约束没有稳定传给所有消费者。根 Issue 关闭责任有一处主语冲突，可一并小改。原生 acceptance 还存在错误的验收语义，但进一步核实表明 review-required 本身不是完成/返回阻断；它不应成为新增开跑门槛。另有少量可合并重复。以下仅提出修正，不修改源码或提示词。

本审查先独立列出问题，随后才与 [review](../review.md)、[closure](../closure.md) 对账。没有读取官方隐藏测试、没有运行模型、bench、Factory/Corpus 测试或修改生成应用。只读获取当前预热镜像中的锁定依赖源码；该镜像尚未包含团队冻结制品。

## 输入重建与证据边界

[输入矩阵](input-matrix.md) 解释各层何时生效；[312 个 Braid session 索引](session-matrix.md) 与 [原生角色历史版本索引](native-role-matrix.md) 提供每个消费者的路径及 hash；[sources.json](sources.json) 是源材料清单。[定向摘录](excerpts.md) 保留关键原始片段。

旧两题实际经过多个接续版本。GitHub 和 Sheet 的 physical instructions 各有 6 种用户指引后缀，不能拿最终 `braid-request.json` 或 `submission/agent` 代表全程。例如 GitHub Issue #6 当时的 native-home vision 没有 `completionGuard:false`，而最终 submission 的同名文件已经有。下文把历史直接记录标为 A，当前源码/依赖可确定的装配标为 B，未在这两题观察到但可触发的情形标为 C。

Pi 基础 system 与 tool schemas 不在 JSONL 中完整逐轮持久化，本次以锁定 Pi 0.85.1、pi-subagents 0.56.0 的装配代码与生成材料交叉核对，不宣称已经拿到每一轮完整 HTTP 输入。所有 skill 描述/路径只是可发现元数据，只有显式追加 SOP 或实际 read 才把正文加入上下文。

## 1. 运行共同约束只到根 Issue，独立消费者有输入缺口

**重要程度：高；旧 A + 当前 B，具体错误后果 C。**

当前 `variants/pi-braid/run.py:164–166` 的根 prompt 才定义「禁止向本次 origin 之外…push、发布和修改」「3000 端口留给官方评测」「自检数据库…使用临时位置」「不得读取、搜索或下载外部验收测试」。它们属于每位执行者的运行边界。`native_files:53–54` 却只把 profile instructions 与后台尾部追加到各成员 system；这些边界没有进入那里。

`context.rs:386–387` 对子 Issue 的父项只输出 `Parent: …`，不是父正文。旧 GitHub `braid-state/physical/01a0e668-ddc1-7c13-8d26-9a2619cc285f/context.md`（Issue #5）完整说明了仓库资产功能、依赖、自检与 `--base develop`，却没有上述平台约束；同阶段 Issue #4–9 都没有 3000 约定。这里「没有 3000」只是定位线索，最终判断依据是完整输入，而非关键词搜索本身。旧部分后续评论和 PR 的 Context 补有运行说明，因此不能断言所有成员全程都不知道。

原生角色还有第二层丢失：五角色默认 `fresh`、`inheritProjectContext:false`、`inheritSkills:false`。`pi-args.ts:671–693` 使用 `--no-context-files`、`--no-skills` 和该角色独立 append prompt，父 Braid/profile/run prompt 没有继承。executor、browser-operator 可以运行命令和服务，但自身指令同样没有这些运行边界。旧抽取的实际原生 launch 主要是 vision，不能声称已经观察到 executor 因此污染初始状态。

这会让一个正确完成局部检查的负责人仍可能占用评测端口、复用交付数据，或者把「可以查询外部事实」延伸到不允许读取的验收材料。当前根 prompt 明说「交接时告知后续负责人这些约定」是有益补救，但把所有消费者恒定适用的约束交给逐层自由转述，正是缺口所在；它并不等于无机制。

**建议权威所有者：**由 `run.py::native_files` 生成一份短的本次运行共同约束，直接给所有 Braid profile 和需要命令/检索能力的原生角色。根 prompt 保留根工作项的产品范围、分工与交付目标；不要把整个根任务、Braid 内部对象模型或全量需求复制给所有子角色。保留 fresh 和父委派对局部范围的责任。这样改的是信息到达，不是增加审批或取消网络查询。

**对账：**现有树覆盖了原需求/状态在交接中丢失，但没有明确覆盖平台授权与环境约束本身的稳定传递；这是当前仍存在的新增遗漏。

## 2. 关闭 completionGuard 只修一层，acceptance 仍把只读结果套成实现与 reviewer 契约

**重要程度：中，非阻断；旧 A + 当前依赖 B，可触发当前 C。**

旧 GitHub Issue #6 的真实父 task 是读 8 张参考图、返回可见英文文案，包含 “Create branch”“Commit changes”等产品控件文字。原生工具在 JSONL 49、51 行两次返回：

> Agent 'vision' was given an implementation task, but its tool allowlist has no mutation-capable tools.

父会话随后检查运行设施和角色配置、删改委派中的产品词语，才成功调用。这个历史问题并不是父任务真的要求写代码；当时的 native role 确实未禁 completion guard。当前 `agents/*/agents/vision.md:11` 与其它非实施角色已设 false，`completion-guard.ts:92` 也显式尊重 false，故**原来的 mutation-tool 误拒已经在当前配置修到对应入口**，不能继续记作完全未修。

但成功的 vision run `3645ce84-7bbd-4431-8414-03db112fbd78` 的 meta 又出现另一层：`exitCode:0`，`acceptance.status:"review-required"`，`inferredReason:["async write-capable or risky run"]`，criterion 为 `Implement the requested change without widening scope`，并要求 reviewer。原文和 hash 见 [摘录](excerpts.md)。只读角色完成观察，却被系统使用实现验收词汇描述，输出方向与角色责任不一致。

当前预热镜像 `pi-subagents/src/runs/shared/acceptance.ts` 与旧冻结末态该文件 SHA-256 完全相同。其 `inferLevel:77–142` 依据角色名/acceptanceRole、任务文本、async/risk 推断；没有读取 completionGuard 或实际 tools。`:112–120` 的 risky 分支直接生成实现 criteria 与 `{agent:"reviewer",required:true}`。目前五个角色均未声明 acceptanceRole，`settings.json` 又 `disableBuiltins:true`，目录中没有 reviewer。工具说明同时要求只读调用 “Omit acceptance”，因此父模型按说明省略后仍可能受到这套推断影响。不要把 completionGuard:false 理解成「所有原生实现验收推断都已关闭」。

进一步检查实际门语义：`acceptance.ts:1385–1392` 把缺少 review 记为 `non-blocking`；`:1017` 的聚合 blocker 仅检查非零退出码或 `acceptance.status===rejected`，后台 `subagent-runner.ts:5040` 的显式 acceptance gate 也只拦 rejected。**review-required 不自动阻止本次正常完成或隐藏输出**；历史 meta 的成功退出不能证明父已消费，同样不能证明返回被 review 阻塞。未取得这一例完整父完成消费链，不把它作为阻塞因果。

相同接线对 executor 更直接：普通异步实现任务会满足 writeTask，自动得到 reviewer 要求，但本团队只有 advisor/explorer/executor/browser-operator/vision。这不证明启动必然失败：实现 run 可以完成，父可以另选角色/提供 review；问题是默认返回要求没有与本团队提供的角色及 Braid 验收责任接通。advisor 是重要决定的独立判断者，不应仅因为默认字符串 reviewer 缺席就被默认为代码验收批准人。

**建议权威所有者：**原生角色声明应定义角色效果与验收性质，运行时 acceptance 必须尊重它，而不是从 UI 名词猜写权限。先在现有 pi-subagents 能力中明确只读角色与 executor 的实际 acceptance 契约；若显式 read-only 仍会被任务中的领域词推翻，就修原生分类边界，而不是让模型规避 “Create / Commit”。保留 Braid PR 的最终验收责任，明确局部原生返回需要哪种证据、由谁消费；不要为满足一个默认名字新增空壳 reviewer 或强制每个局部任务重复整体验收。当前可先保留 dispatch guard 的已落地修复，并在账本把“只读 guard 已修”与“acceptance 语义仍可能偏离但非阻断”分开。不要仅为这个 ledger 字段修改原生包或新增强制 review 流程；若后续真实返回使父追加无意义工作，再在原生 acceptance 的显式角色边界处理。本报告不应用修复。

**对账：**已有 closure 正确覆盖旧 mutation guard 修复，但“非实施角色停用实施 guard”不足以关闭本项剩余 acceptance/role 接线；新增遗漏。当前预热源码相同只证明机制还在，不证明新任务必然遇到相同词法分类，也不承诺效果收益。

## 3. 整合段给两个人同一个根关闭动作

**重要程度：中；旧末态 A + 当前 B。**

两个 profile 的 `instructions.md:9` 前半句以整合 PR 负责人为主语，要求「修复失败并复验，再合并交付、关闭根 Issue」；同段末尾又要求「整合 PR 完成后向根负责人交接，根负责人据此判断完整交付并关闭根项」。这不是两个不同条件下的规则：它们描述同一次整合完成后的同一个动作。

PR 负责人可按前句关闭根项，根负责人却还承担接收结果与判定整体范围的责任。末句足以让谨慎模型推断正确分工，因此这里只确认指令有歧义，不将旧轮根关闭问题全部归因于此。Braid 自动 `Closes` 在默认分支的结算是另一套显式对象语义，也不能替代负责人闭环决定。

**建议权威所有者：**保留同段最后的根负责人判断/关闭规则，从前半句只删「关闭根 Issue」；整合 PR 负责人负责候选、验收、合并与交接。Braid 通用 Issue/PR 系统说明继续定义通用对象能力，不必再复制 Factory 根关闭策略。

**对账：**原有树写清了生命周期机制和 Issue/PR 分工，但该句仍在当前两个 profile 中，属于未被当前修复消除的小遗漏。

## 4. 常驻重复可局部收敛，但不应以压缩为目标撤掉角色自包含

**重要程度：低；当前 B。**

当前 profile `instructions.md:21` 已说「开发服务器或 watcher 用 bash 的 service:true…主动停止」，`run.py:31–33` 追加的 BACKGROUND_COMPLETION_RULE 又说一次。PBB `background-bash.ts:997–1001` 的 description、promptSnippet、promptGuidelines 也分别教同一工具选项。原生 browser-operator 的正文要求命名 session，`run.py:75–79` 再注入 agent-browser 全文，其中再次定义命名和交接。它们基本一致，不是行为矛盾；需要收敛的是重复维护位置。

两份 profile 当前各 2678 字符且内容相同；并不是一个会话同时收到两个副本。设计/调查/实施 workflow 当前分别 2944/2974/3108 字符，作为相应角色的常驻 SOP 有独立目的。browser-operator 固定注入的 agent-browser SKILL 为 5345 字符；该角色还收到它的可发现元数据，若按元数据再 read 会重复正文，但本次没有据此声称发生了实际二次读取。不要把所有 14 个技能正文总和算作成员固定 prompt，亦不把缓存输入、每轮历史和系统大小相加成可兑现收益。

**建议权威所有者：**保留 PBB 对字段及实际完成机制的解释；Factory 后台尾部只保留本运行需要的有限任务/服务/结束回应约束，profile subagent 段保留 ID 类型与恢复规则即可。browser session 操作以 agent-browser skill 为权威，角色正文可只声明必须遵守并明确返回/效果边界。按需求才评估 5345 字符中通用 check runner 说明是否需要在只做探索的 browser 子角色常驻；不以本报告建议自动删掉它。两套 profile 的磁盘相同内容暂不必为去重引入新模板机制。

**对账：**当前维护负担建议，不是冻结阻断，也不声称能提高分数。

## 已核对但不判为缺陷

- 当前 Issue 系统明确设计及关联 PR 分派，PR 系统明确计划、预演、实施与验收；profile 对 root/子项的流程进一步说明适用范围，SVC 提供方法。三者有重复概念但职责一致，不应只为统一措辞删除。
- advisor 的当前前置咨询触发条件明确排除了普通委派 ROI；SVC 的 “Use a child Agent when … repay …” 是一般方法，profile 又明确 skill 不改变授权和最终判据，未构成必须抛给人类的审批冲突。当前自主设计/实施技能未发现要求无人值守任务等待人类批准的硬条件。
- 浏览器探索报告不能替代最终可重复验收，与 vision 解释参考图、executor 做局部反馈分别适用不同命题。不能把不允许一次手工报告充当整体验收误读为禁止页面探索或禁止读图。
- explorer 的 Context7/Exa 通过 bash+mcporter，可与“不得读外部验收测试”同时成立：允许外部事实查询不等于允许参考评测器。真正问题是后者未稳定传给每位消费者，见问题 1。
- 原生 async 回执中 “return control to the user” 是通用交互措辞，Factory 说无人介入且后台完成会唤醒；在这套运行语义下结束当前回应不等于等待人类，也不等于关闭 Issue。PBB 当前已有 service 字段，不能把旧版缺失当作当前提示承诺未接线。新完成时序是否正确仍待主线既定运行证据。
- 当前 Braid 把稳定 description、增量 comment、更正/hide/resolve 及 reset 时机一起解释，概念先定义再使用，未要求把每步日常状态都转成 task packet。原生子角色不继承这套协作正文是合理的边界，不能为了补问题 1 而整段复制。
- 主模型是否有图像能力不改变明确的 vision 分工；vision 的 read 工具、visual 模型与只读输出匹配。模型/角色目录可发现与真实调用成功是不同证据。本审查不以 advisor、explorer、executor 的零调用数量作为失败证明。

本轮可以优先处理问题 1 的输入接线，顺手消除问题 3 的一句歧义；问题 2 保留非阻断的准确账本状态，问题 4 留给局部维护。没有必要给模型讲述更多 Harness 内部架构，也没有必要新增一套审批、角色或任务文档体系。
