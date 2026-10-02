# Hackathon 能力改造实施计划预演

日期：2026-09-25。范围是对照 `packet.md`、`design.md`、`implementation.md`、`svc-routing.md` 与当前消费者确认能否线性实施；没有修改源码、SVC、runtime 或冻结包，没有运行测试、模型或 benchmark。

结论：方案可以落地，`scripts/agent_support.py:copy_skill` 已覆盖拆分后的标准技能目录，不需要新的 registry、preset 或兼容层。实施前需要把三个接口细节写死：活动 variant 的五技能源目录和运行时物化路径、主会话选中的领域技能如何传给 fresh executor、每个 fresh 角色只得到哪一个 SVC 方法入口。归档路径可以通过一次历史快照保持，不需要迁移归档实现。

## 已核实的消费者边界

`copy_skill(source, destination)` 复制 `SKILL.md` 和存在的 `references/`、`assets/`、`scripts/`，并复制许可文件；它不复制维护者文件或 CLI。这正好满足五个独立技能的分发边界。`scripts/package_agent.py:assemble` 只按 variant 的 `skills=(...)` 元组调用这个函数，默认源目录是 `harness/skills`，因此只需调整材料目录和元组，不需要改复制协议。

当前活动 `pi-team-mixed` 仍有三处旧入口：

- `variants/pi-team-mixed/build.py` 打包 `svc`；
- `variants/pi-team-mixed/run.py` 复制 `svc`，主 Pi launcher 用 `--skill .../svc/SKILL.md`，并把 `svc/references/methods/{explore,implementation,design}` 直接附加给 explorer、executor、specialist；
- 两套 mixed 原生角色 Markdown 的 frontmatter 和主 instructions 仍写 `svc`。

其它旧入口属于有意保留的历史消费者：`pi-team-glm`、`pi-team-deepseek`、`pi-team-vv` 三个归档 variant 继续使用 `svc`，`variants/native-hackathon/hackathon_main.py` 也继续生成 `skills/svc`。当前 `harness/skills/svc` 是指向 `sources/svc` 的目录链接；它还不是归档快照。

## 三条使用路径

### 1. 主 Pi 选择领域技能，再让 executor 读相关资料（示例）

这条路径是一个可行例子：构建阶段把 HyperFormula、Handsontable、Better Auth、组织插件和 accessibility 技能复制到同一个 `work/skills`，主会话可按需求选择具体技能并在委派中引用相应的 `SKILL.md` 或 reference，fresh executor 也可从同一物化目录自主发现和按需读取。主会话不必先选库或 skill；技能名和路径只是普通委派材料引用，不是新增协议。领域技能只提供何时使用、边界、版本和资料导航，不要求安装库，也不把某个库写成固定技术栈。

随后返回的 `rehearsal-native.md` 已确认主 Pi 和子代理均登记元数据、按需读取正文；子代理不继承父 launcher 参数，因此 implementation.md 明确了每个角色自己的技能列表。

### 2. fresh explorer/executor 只预装自身 SOP

当前 `native_files()` 将旧 SVC 方法正文直接拼入角色 instructions，同时 frontmatter 又声明 `svc`；原生接口核实表明声明只增加元数据，不造成第二份正文。
explorer、executor、specialist 分别保留 investigation、implementation、design 的一次方法正文，路径迁到新技能的 references/workflow.md。
其余可选技能按 implementation.md 的角色表注册；浏览器角色得到验证与可访问性入口，但不预装设计和委派方法。

技能元数据和一次预装方法可以并存；真正重复来自多次正文追加或角色源文件维护了同一方法的副本。
完整 reference 留在共享运行材料目录中，不灌入每个角色的 instructions；executor 可在委派范围内自主补足必要信息。

### 3. SVC 拆分后独立安装，同时保留归档原材料

实施顺序应先把当前 `harness/skills/svc` 物化为迁移前的普通目录快照，再在 `sources/svc/skills/` 建立五个自足技能。活动 mixed 的打包源只登记五个新目录；归档 variant 仍从历史 `harness/skills/svc` 取得旧入口。`scripts/package_hackathon.py` 是原生 Hackathon 包唯一需要改源路径的消费者：从 `sources/svc` 改为历史 `harness/skills/svc`，ZIP 内仍写入 `skills/svc/...`，这样旧 `hackathon_main.py` 无需改路径。

这保留了归档包、历史运行和原有 ZIP 路径，避免把归档实现迁移成新方法。当前 `harness/skills/svc` 的目录链接必须被替换为快照；否则 SVC worker 删除或移动根入口后，三个归档 variant 和原生包会随工作树变化。

## SVC 依赖与领域技能检查

拆分提案明确要求技能之间只用可选能力名称沟通，不能使用越出自身目录的相对链接；这满足独立安装要求。实施时只需逐个确认每个新 `SKILL.md` 引用的 `references/`、`assets/`、`scripts/` 都在本技能目录内，不能通过复制同一正文或共享相对路径解决缺口。

领域技能属于资料，不应改 `harness/npm/package.json`、npm lock、runtime 或应用依赖。入口必须写“选型时何时有用”和“保留自有适配层”，不能写成必须使用 HyperFormula、Handsontable 或 Better Auth。该边界在设计与实施稿中已有，实施验收只需检查新增材料和构建输入没有偷偷加入库安装。

## 最少修订后的线性顺序

1. 保存当前 `harness/skills/svc` 的完整普通目录快照，登记源仓基线；不要先移动源文件。
2. SVC worker 在 `sources/svc/skills/` 生成五个自足入口；同步 SVC 的 README、AGENTS、CONTRIBUTING、USER_MANUAL，并把活动可选源目录明确映射到 `harness/skills/svc-*` 或同等唯一位置。不要让 `run.py` 默认的 `HERE/skills` 和 `package_agent.py` 默认的 `harness/skills` 指向两套材料。
3. 能力材料 worker 添加短入口和按需 reference；确认它们只作为可选资料，不改 npm/runtime。把 `harness/skills/README.md` 与 `docs/deployment/index.md` 中关于单一 `sources/svc` skill 的活动说明改成五技能集合；历史 Hackathon 文档继续描述旧包。
4. 主 Agent 更新活动 mixed 的 build 元组、run 复制列表、主 launcher、角色 frontmatter 和方法路径；为主会话保留五个短入口，为 fresh 角色只配置职责所需 SOP，普通委派消息可引用已选领域技能的路径，但不要求主会话先选，也不增加协议字段。
5. 仅在获授权的活动包构建中观察新材料是否进入预期路径；旧 `skills/svc` 通过现有归档文件关系保留，不额外构建或运行归档包。实际 native loader、打包产物和真实运行验收留到开工授权后，不在本次预演运行。

## 预演收敛

主 Agent 在原生接口证据返回后，将上述元数据、SOP 和子会话参数结论整合到 implementation.md，并修订了本报告早期将技能声明误看作可能全文注入的假设。

准备阶段未留下需要新增机制的接口阻断。
实际新材料、Agent 采用情况和官网得分仍属开工后的交付与实验，不能由本预演代替。
