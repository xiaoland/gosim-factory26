# 通用工作流程入口审计

2026-09-28，只读核对 `pi-braid` 当前源码的权威材料、打包与运行接线，以及 Braid 根 Issue、子 Issue、关联 PR 实际获得的内容。这里审计的是**入口与传递保证**，不是本轮 GitHub 低分的因果诊断，也不把“技能已安装”当作模型已阅读、采用或产品已通过。没有修改 prompt、启动实验或读取隐藏评测。

## 材料怎样到达成员

| 层 | 实际入口与保证 | 容易误认的边界 |
| --- | --- | --- |
| 公开任务材料 | `variants/pi-braid/run.py:109–111,135,157–164` 将 `requirements.yaml` 所在目录复制为运行 `input/`；根 prompt 要求读 YAML、`requirements.md` 与参考图，覆盖所有场景和指定初始数据、保留文案和可访问控件。`run.py:157–162` 还固定平台 Node 20.19.3、前后端包、启动顺序/端口、隔离自检数据及授权边界。 | `requirements.md` 可能不存在，prompt 已允许以可读语义处理；要求“阅读”不等于确实看过每张图。开发仓库的 `AGENTS.md`、PRD/TDD 不是参赛成员的自动系统指令：`scripts/package_agent.py:87–108` 只复制 variant、选定 skills、runtime 与 support。 |
| Factory variant/profile | `variants/pi-braid/build.py:14–18` 明选 14 个技能；`run.py:27–30,129–140` 再把同一 `MAIN_SKILLS` 复制到该运行并用 Pi launcher `--skill` 启用。`run.py:45–54` 把两个 profile 的 `instructions.md` 放入 `user_instructions`，`ROOT_PROFILE_ID` 是 `pi-glm-fast` (`run.py:26,141,167`)。内部角色由 `run.py:61–79` 复制并附对应方法正文/浏览器技能。 | 包内有技能、主会话列出技能、角色列出技能是三件事；方法正文并非全量预读。profile 的 `assignee_description` 只是 Braid 可指派能力说明，不是产品规格。开发侧 `svc dev` 及其 `svc.json` 不在这条参赛接线中。 |
| Braid 工作项 | `sources/braid/src/local.rs:359–368` 把 `request.prompt` 写为根 Issue #1 正文；`sources/braid/src/objects.rs:164–184` 确认根项正文就是该 prompt。`sources/braid/src/group/provider.rs:60–99` 对每个 Issue/PR 都拼入 Braid 通用协作说明及该 profile 的 `user_instructions`：Issue 负责需求、方案、验收依据，再创建/指派实施 PR；PR 承接计划、代码与验收。Pi adapter `sources/braid/src/provider/pi.rs:195–196` 以 append-system-prompt 送入该会话。 | Braid 提供工作项职责、对象与上下文，不选择产品方案、栈、UI 或验收方法；`docs/product-tdd/index.md:49–67` 也将这些留给 Harness/成员/SVC。它不读取 SVC packet 或自行指定某厂商子代理。 |
| 子项继承 | `sources/braid/src/context.rs:260–286,385–402` 的子 Issue 上下文包含**自身**正文/评论和父 Issue 引用，不展开父正文。关联 PR 的上下文则先呈现其关联 Issue 全文再呈现 PR 正文/讨论（`context.rs:289–325`）。`sources/braid/src/group/provider.rs:101–119` 的唤醒短消息要求成员再 `braid ... view --comments`。 | 根要求、相关初始数据、参考图路径和共享契约，必须由根写进子 Issue 或留下可直接读取的材料入口；不能假设子 Issue 继承根长 prompt。PR 若没有正确关联 Issue，不能靠同号对象自动取得设计依据。工作区 clone 不共享其它会话的私有推理。 |

实际旧工件可交叉印证该路径：`runs/e20260928-completed-replay/github/source-workspace.zip` 内 `template/.factory26/20260927-080209-0b57147a/{prompt.txt,braid-request.json,braid-state/braid.sqlite3}`。只读查询 `local_items`：根 #1 正文与 `prompt.txt` 同内容；子 #2–#7 各自写了所覆盖 REQ、完整 YAML 路径、种子/依赖与交付摘要，#3–#5 指向共享 `docs/architecture.md`，但没有自动复制根 prompt；关联 PR #8 正文承接 #7 的实现与检查，最终整合 PR #9 记录候选与检查。它证明**那次旧运行**的材料传递形状，不证明当前源码已被 continuation-03 或下轮自然采用，也不评价旧工件功能质量。

## 五个关键决定的接线强度

| 决定 | 已明确写入 | 仅按需可取 / 尚未接线 | 对实际协作的含义 |
| --- | --- | --- | --- |
| 需求、用户路径和状态 | 根 prompt 明确完整需求、场景、种子、英文文案和可访问控件 (`run.py:157–159`)；Braid Issue 职责明确先澄清需求/方案/验收 (`group/provider.rs:73–82`)。`svc-design/SKILL.md:10–12` 和 `references/product.md:3–18` 可指导代表性用户旅程、状态、失败与假设。 | 根 prompt 紧接“阅读”就要求**先拆分**，没有明确在首批派发前识别跨模块用户路径、初始数据所有者或会改变分工的产品决定。SVC 产品方法是可选技能，Braid 不校验已读取。 | 有完整需求入口，但“设计已足以支撑拆分”尚靠根成员判断；子项写得细不等于跨项旅程已被统一决定。 |
| 视觉、交互、图标 | 参考图在需求包，当前 profile 指引 `variants/pi-braid/agents/pi-glm-fast/instructions.md:13` 指定相关图和问题交给原生 vision，并读取带来源报告。`impeccable/SKILL.md:7–19` 已装入，要求看实际页面层级、文案、状态、图标是否有意义；`fixing-accessibility/SKILL.md:6–12` 已装入，要求按实际 AX 树和键盘路径验证。 | 仓库有 `harness/skills/frontend-design/SKILL.md:7–15`，包含产品语境、视觉系统、交互与内容的前置选择，但 **不在** `build.py:15–18`、`run.py:27–30` 或任何当前原生角色 `skills` 中；README 的介绍不是运行接线。没有指定图标库/组件集或统一的图标语义契约，只有通用视觉原则。 | 视觉核对和 reference 解读有入口；“在拆分前决定跨页面设计语言、组件/图标的一致性”仍是可做但未被明确交接的工作。不能因为技能目录存在就声称它生效。 |
| 技术栈、组件和跨模块边界 | 根 prompt 只固定平台交付接口及 Node 版本；profile `instructions.md:3` 要求尽早发布共享契约，消费者基于已合入成果推进。`svc-design/references/technical.md:3–14` 可指导状态归属、接口、并发、恢复、最小可消费契约；`run.py:61–78` 将该 design workflow 直接附给 advisor 内部角色。 | 没有根级特定框架、存储或组件架构裁决，也没有在**派发首批子项之前**形成简明全局技术方案的显式门槛。Braid 只给设计职责，不替 root 选栈；advisor 是可用角色而非固定审批。旧 GH 子 #2 自行选 Vite/React/Express/JSON 并承担共享架构，说明该路径能工作，但这是拆分之后的决定。 | 共享基础 owner 与发布契约已经明确，足以避免完全无序；若栈/数据模型/跨页面组件影响多个子项，必须在相关消费项开工前显式记录并交接。 |
| 任务拆分与继承 | 根 prompt `run.py:159` 明确按独立可验证结果拆分、紧密需求合并、共享基础唯一 owner、依赖达到后分批指派、并行独立工作。SVC `svc-task-packet/references/planning.md:33–38` 指出依赖只阻塞消费方，当前 `svc-sub-agents/SKILL.md:34–39` 要求把场景前提/初始状态交给负责人。 | 这些 SVC 规则是按需技能；Braid 不复制父正文或自动补全子项材料。根没有被明确要求在拆分决定前列出关键跨项用户路径、视觉/技术共有约束。 | 真正的传递单位是子 Issue 正文/讨论及可读材料路径。可把首次跨模块决定写进根/共享基础项，再在受影响子项引用，不需让 Braid 固定工作法。 |
| 验收约定与证据 | 根 prompt `run.py:160–163` 定义可启动、隔离自检、停止自有服务及禁止读取外部验收；profile `instructions.md:5,9` 要求最终候选的可重复检查、首轮退出与环境条件，避免旧局部 PASS 代替整体验收；Braid PR/Issue 职责把实现验证和结论消费分开 (`group/provider.rs:73–99`)。`svc-verification/SKILL.md:10–30` 可指导判据、前提和证据边界。 | 没有在 root 拆分前逐项机器生成的验收矩阵，也不应该把题目断言塞入 Harness；Braid 不判断应用是否满足产品。技能指导需要 Agent 实际采用，check 的结果也只支持它实际覆盖的条件。 | 当前文字足够定义“谁在何处取得证据、何时不复用旧 PASS”；每个子项仍须把自己消费的具体场景、数据前提和可重复检查交给关联 PR。 |

## 版本边界与建议

上述接线表以**当前源码**为准。`runs/harness-releases/20260928-collaboration-v2/release.json` 记录的新包于 11:58 UTC 形成，`packaged-materials.json` 的 `run.py` SHA-256 与当前源码一致（`cd3a76...`），但 release 明说只供新包，continuation-03 未热更新；随后新增的检查工具也不在该包。attempt-09 的来源与保留工件见 `tasks/braid-product-reaudit/cells/attempt09-package-preparation.md:3–31`；本地没有 continuation-03 的完整 Braid 工作区，不能把今天源码细节或 27 日旧 ZIP 冒充该冻结会话的实际 prompt。27 日旧 ZIP 的 profile 曾以一段明确的“在 Issue 中分析产品需求、共同设计技术与验收”开头；当前源码 profile 不再有该段，依靠 Braid Issue 职责与按需 SVC 方法。两版不可混称。

**决策级结论：**目前不是“没有设计能力”：完整需求、分工、共享契约、视觉检查和验收原则都可达。但最弱的入口是**首批拆分前的跨项产品/技术/视觉判断**，以及它怎样简明传给子项；`frontend-design` 当前完全未接线。若后续决定改指引，最小范围是 root prompt 在首次派发前要求识别少数会改变任务边界的用户旅程、种子/状态所有者、参考图/组件一致性与共享接口，并把决定或未决项写进对应 Issue；各子项携带相关材料与验收前提。不要把这改成 Braid 强制流程、固定框架/图标库、指定厂商 subagent 或一套新的大模板。这里只提出入口修正方向，**没有修改 prompt 或打包**；实际采用须在获授权的新鲜运行看子项描述、独立 PR 交接及最终证据链，而非看技能列表或任务数量。
