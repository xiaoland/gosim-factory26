# ARC Stage 2 重评与 Stage 3 需求、测试核查

## 当前决定与授权

用户要求整理申诉材料并自行发送邮件；本轮进一步要求：“请重写邮件正文，甚至重组证据资料，你的论证思路不完整不清晰”。本轮授权覆盖邮件、证据说明、统计索引和本 packet 的更新。未修改参赛应用、Harness、评测器或原始下载包，未联系主办方。

材料采用 ARC 网站工作区下载包原件及保存的平台元数据、前端资料，排除志愿者复测站点的结果、截图、链接及观察。中文正文删除冗余“正式”措辞。任务仍处于供用户审阅和发送的材料准备阶段，发送不等于申诉完成。

## 当前交付

- [邮件正文](email.txt)
- [发送用附件](../../runs/deadline-20261003/appeal-materials-20261006/arc-stage2-stage3-official-evidence-20261006.zip)
- [证据论证与定位](../../runs/deadline-20261003/appeal-materials-20261006/official-evidence/evidence-notes.txt)
- [逐场景索引](../../runs/deadline-20261003/appeal-materials-20261006/official-evidence/scenario-index.csv)
- [来源与校验](../../runs/deadline-20261003/appeal-materials-20261006/official-evidence/provenance.json)

原始过程调查归[两题零分调查](../deadline-20261003/pi-zero-analysis/packet.md)，其中历史外部复测观察不作为本次申诉证据。旧稿在 appeal-materials-20261006/history-before-argument-rewrite/ 保留，不用于发送。本侧未接管主线执行或子 Agent。

## 提交和来源

Submission aea08b61772c；Stage 2 run 32db20c04573（0/29）；Stage 3 run d86b43e8c891（0/41）。

Stage 2 原包：runs/deadline-20261003/pi-zero-analysis-20261006/stage2/workspace-template-bundle.zip，SHA256 a9d0b2ff728a6dd8f227798678b86754e39c33aed15a4a537c8bef55086cacfe。
Stage 3 原包：runs/deadline-20261003/pi-zero-analysis-20261006/stage3/workspace.zip，SHA256 ed0f1b8537892fb57cee85c5531211559daa41914752d388b40f96f77b4c87b2。
下载记录分别位于原包同目录 download-manifest.json 与 download-metadata.json。原包大文件按需提供。

报告配置指向 /workspace/tests，输出到 /workspace/template/.arc/playwright-report.json；同包 Runner 事件在 Evaluating result / run_tests 记录匹配统计。归属论证采用这些材料与下载来源，不以路径命名或公开本地模拟文档单独证明线上来源。

## 论证与请求

Stage 2：29 条结果全部在 Chromium 启动时报告可执行文件不存在。应用可达不证明业务正确，浏览器启动失败也没有验证业务行为。preflight 在更早时刻通过，不能证明评测时仍完好或独立判定责任。请求核查环境变化并排除阻断后，对原应用重评。

Stage 3 测试错误：REQ-6-3-3 Scenario 2 在测试代码第 22 行调用未定义的 uniqueAccount，第 24 行才登录。这是独立、直接可定位的测试执行错误，请求修复与受影响场景重评。

Stage 3 需求核查：下载包需求引用四个未展开节点，prerequisites.md 为空。只能称为“工作区保存的材料”，Agent 实际输入快照一致性尚未证明。需求已有部分登录及 seed 说明，不能把缺节点等同于前置行为完全未说明。

Stage 3 应用侧已核查：原包源码的首页渲染 owner/repo 仓库链接；仓库页提供 Issues 和 Pull requests；对应列表以标题链接到详情页。种子代码包含两个仓库及 26 条标题查找失败涉及的全部 21 个不同 Issue/PR 标题。源码核查证明实现存在，未复现运行，不能证明评测时初始化、数据加载和页面显示成功。

不利证据同样保留：compare 页入口名为 New pull request，前端没有名为 Compare 的导航链接；首页仓库名包含 owner/，不等于裸 branch-protection-demo。前者对应 3 个失败，后者对应 2 个，均不作为“测试漏走仓库导航”的佐证。邮件问题 3 收紧到 Issues 和 Improve onboarding 两个代表场景的实际导航路径。

用户指出“这些入口确实未实现难道不是我们应该去核查的吗”。据此完成上述应用侧核查，将 12 个源码原件直接从原 ZIP 加入证据包，证据说明 C 增加实现位置、命名差异及验证边界。主办方需要提供的是实际评测页面及测试导航记录，应用源码可查清的事实由我们先提供。此前两条导航路径的纯假设写法已替换。

报告没有失败时 URL、DOM、完整 helper 源码或导航轨迹；所引用 error-context.md 不在下载包内。不能断言测试停在首页或跳过仓库，也不能把代码实现等同于运行时成功。需求缺漏若影响生成，仅重跑同一应用未必补救，需主办方决定统一处理方式。

## 阶段接续与空白起点的新证据

用户要求改变论证模式并核查平台是否自动接续。保存的平台任务列表明确支持“有前阶段应用则接续，否则空白启动”，因此不采用“必须顺序运行却完全未说明”的断言。官网前端对两种来源有提示，创建 run 未传来源字段，支持平台选择来源的解释；未取得服务端选择与复制代码，具体 run 的初始来源未知。

启动前任务列表 Stage2、Stage3 source_run_id=blank；本次三个 run 在约一分钟内启动，前一阶段尚未完成。列表来源状态不能当作 per-run 配置证明。平台任务摘要中的接续/空白说明未出现在包内 YAML，但 Agent 实际输入可能另有渠道，需核对输入快照。

邮件问题3改为本次应用来源、平台选择规则、空白启动时前置需求与开发范围的传达；导航作为需要评测现场继续解释的症状，不作为已证实的阶段接续根因。附件新增 platform/ 下三份资料及证据说明 D，原有应用实现与不利证据保留。

## 当前邮件全文重写

用户明确要求“重写整个正文”，并要求删除过度的“我们不以……”等自我限定表达。现行 email.txt 全文以三个问题组织：浏览器启动故障与原应用重评；uniqueAccount 测试错误与受影响场景重评；本次阶段初始应用、空白启动的实际前置输入和接续条件。正文保留必要的来源措辞，详细证据局限、不利事实和导航差异继续放在附件 C、D。邮件由用户发送，未代发。

## 核验与接续

本轮重新计算两个原包 SHA256，将 22 个原件逐字节与 ZIP 成员比较一致；派生统计逐条遍历 70 个 result，不重复计算 error/errors。附件共 30 个文件，ZIP 内容与目录一致，来源清单中的每个长度与 SHA256 均核对。

下一步由用户审阅并自行发送。主办方答复后，根据具体证据更新判断；不自动重评、监控或联系。Stage 2 完成条件为故障核查和有效重评回执；Stage 3 完成条件为测试错误处理、前置需求与导航约定明确答复及相应补救安排。
