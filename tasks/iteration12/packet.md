# I12：连续工作、明确协作操作与人工语义诊断

2026-09-30。当前阶段：核心修复及新版 Console 已落地，两题从零生成已启动并有真实模型响应。原摘剪接续已停止并保留证据。
授权原话：“其它的各项处置我都同意，请你应用它们为 I12 并且从 I11 的运行状态中再次进行摘剪……另外 I12 还实现一个实时的可交互的 web console”。

## 目标与边界

减少上下文整理重新制造工作、冲突验收纪律与讨论操作范围歧义；让用户在本轮通过原生Issue/PR语义介入，发现更深语义问题，再从真实交互提炼指引。
I12是独立variant，不覆盖I11冻结输入与证据。模型及凭据沿用本地I11自有API配方。
人工介入是本轮实验条件，console属于开发工具，不进入无人值守参赛制品；本轮不得自动正式参赛。
最新修正：“Braid console建议重新制作……有独立的目录（不需要额外的git repo）……至少不是plain HTML/CSS/JS”；“计划让I12从0开始实现，而不是I11的裁剪结果”。两题不继承I11应用、Issue/PR、Git与原生会话；复用的是工具环境和冻结Harness。模型、两份官方需求及资源配方保持不变。
不新增或运行Factory/Braid/SVC/设施测试、模拟探针；通过编译、语法、真实对象操作及已授权生成观察取得反馈。

## 实施树与分工

```text
I12
├─ 1. Braid连续性与操作范围［i12_braid_continuity］
│  ├─ 区分上下文更新、未完成处理的接续与真实新输入
│  ├─ 自编辑/自然完成不重新制造处理请求；中断与新消息不丢
│  └─ resolve/unresolve说明thread根、范围、变化；局部整理用hide理由
├─ 2. 工作材料［主线］
│  ├─ 删除“新SHA本身不使证据失效”的专门规则，保留变化与证据的判断方法
│  ├─ 历史交付记录不镜像全局最新状态
│  └─ 清退摘剪对象中冲突的“head变化即全量重验”纪律
├─ 3. 从零生成［i12_runtime_deploy］
│  ├─ 原摘剪尝试cancelled，保留证据与前期CLI/消息核验
│  ├─ 同需求、自有API及4GiB/2CPU，标准入口初始化空应用/Git/Braid/会话
│  └─ 复用共享runtime，不重复安装runner和浏览器；真实空seed、新对象与模型响应已核实
├─ 4. 交互console［i12_console_rebuild］
│  ├─ 独立braid-console目录，React/TypeScript/Vite/Ant Design/TanStack Query
│  ├─ 实时查看Issue/PR/负责人/讨论，编辑、评论与thread回复
│  ├─ 写入复用Braid CLI外部对象事务及通知机制
│  └─ 记录人工介入来源；显式registry控制读写，旧摘剪只读
└─ 5. pi-minimal验收技能支线［pi_minimal_verification］
   ├─ 仅svc-verification及其references，不引入Braid/其它SVC技能或新角色
   └─ 原生技能和材料接线已落地；本次不启动支线实验
```

## 推进与验收

先核实实际调用/API和分支，再并行实施；核心源码预演反馈已明确自然完成和reset结算竞态，不能只改消息措辞。
Console使用明确的当次binary/state身份；从零使用标准variant入口，不使用continue-in-place。保留已有runtime，避免重复复制安装工具。
验收包括Linux编译、真实CLI读取/写入回执、浏览器实际查看和操作指定I12对象、真实模型响应/消息消费。既有检查结果保持原始归属，不将复制/Running或模型自述当产品完成。
启动前检查模型路由、版本、恢复身份和人工介入标记；沿用3+8周期观察，不把每5秒页面刷新变为Agent调用。
原始I11两题已核实交付：GitHub main `442dc1cf776f144688d8ad667a76dd026f553e27`，Sheet main `10cba2ad888fd60f283382158c1bfb00b0fad240`；两者根Issue关闭，最终PR合入，生成出口成功。
按用户“既然交付……尽快上传到官网进行评测”的指示，冻结同一应用重放包，SHA256 `bc4cab139ed9cf3c282a1b3359ed1d6a8e5f552dcf13efda30144a44fb5076fc`。
官网 submission `87acf1919de7`，Sheet run `fe617f4f8526`（59/100），GitHub run `e68661975b53`（4/100）；均为 `self_funded`，部署、应用启动和评分阶段完成。重放不调用模型，不重新生成，不将隐藏评分反馈带入I12。原始journal见 `runs/iteration11/final-replay-20260930/official/`。

## 当前实施状态

Braid Linux编译完成；自编辑及自然完成后的reset只更新Context，真实中断保留接续，讨论resolve回执明确范围。
SVC专门的SHA规则已移除，保留按相关变化与实际条件判断证据的方法，I12角色的交接指引已收敛。摘剪正文改动仅属于退役现场，不会带入从零生成。
Console新版位于独立braid-console目录，React生产构建通过，旧plain页面及执行路径已移除。当前只登记两个从零现场并允许人工介入；CLI在各自容器中执行，保持Braid已存Git路径的环境身份。真实HTTP与浏览器已读取两题根Issue和PR #2，不为核验随意发表新评论。入口是 http://127.0.0.1:8765/；部署及旧评论证据归console记录。
原I12摘剪尝试：GitHub run `pi-braid-i12--hackathon--github-690b8b3f871be2`，Sheet run `pi-braid-i12--hackathon--sheet-6c9d2806b4fac4`，已按最新决定cancelled/exit-15，容器不存在、cleanup完成、gateway绑定撤销，workspace及全部原生证据保留。停止前两根已有真实模型响应并成功读取#333/#567，wake为consumed；说明前期console消息接线可用，不是完整生成验收。证据见 `runs/iteration12/deployment/stopped/receipt.json`。
从零GitHub run `pi-braid-i12--hackathon--github-715fa714f396de`、Sheet run `pi-braid-i12--hackathon--sheet-8559b80ecb7f15` 已启动，初始Git树为空，每题新DB初始只有根Issue、无评论、一个成员与一次处理；原生会话已有真实工具调用，当前正在建立共享基础并拆分需求。每题4GiB/2CPU，自有API模型配方不变，3+8 watcher持续采集。评分仍使用冻结应用官网self_funded重放；尚未交付或评分。
pi-minimal支线已显式接入完整svc-verification与references，主会话及独立advisor可按问题读取；保留agent-browser快速反馈和主会话自动化最终验收。源码及材料路径核对完成，没有更新现有冻结官网制品或启动支线实验。
父仓库I12实现、console及导航提交 `86ec49e`。Braid/SVC本次改动叠加在之前已批准但尚未提交的I11材料上；没有可靠开工前基线用于分离时，不猜测暂存或夹带提交。运行身份来自完整dirty源码冻结及材料清单，而非声称HEAD等于制品。

## 产物入口

- [Braid修复](braid.md)：实际边界、代码与编译/行为证据。
- [恢复摘剪（已退役）](recovery.md)：来源、取舍、变更账和限制。
- [Console](console.md)：接口、部署与实际操作证据。
- [WSL部署](deployment.md)：材料刷新、资源、真实响应与监控回执。
- [pi-minimal验收接线](../pi-minimal/verification.md)：支线范围、实际采用方式及未验证项。
- 原因原始材料：[I11补充归因](../iteration11/runtime-stalls/packet.md)。
