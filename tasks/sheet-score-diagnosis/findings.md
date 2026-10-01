# Sheet 官方回放得分诊断

状态：诊断完成，未修改应用、Harness 或 Braid，未提交、未发起新官网运行。对象是来源 run `bd7ac1b232ba` 产生的应用，经已完成快照恢复后在 `1efffb84ae1b` 评分；交付 `main=402336217ef1329f71b8f15560cfbf19d514e82f`。恢复未重新调用模型，所以 58/100 不能作为修复版 Harness 从需求重新生成的分数。

## 结论与证据边界

官网聚合状态报告 58/100、58 个场景通过、42 个失败、8/24 功能项被认定实现。`deploy_agent`、`start_agent`、`run_tests` 均 completed，平台前端构建和后端启动有日志，`tests=[]` 且 traceability tests 为空。因此可以确定问题发生在交付应用的评分阶段，但**无法知道官方哪 42 例失败，也不能把本地发现逐一映射到官方失败项或量化每项的失分**。原始入口为 `runs/e20260928-completed-replay/sheet/official/tasks/hackathon--sheet/status.json`、同目录 `traceability.json` 与 `logs/d35b13da50c824b5.json`。

已确认的主要因果链是：根任务明确要求“覆盖全部需求、场景和明确指定的初始数据”，但共享基础子任务将正常启动种子缩成 `Q3 Sales`/`Sheet1`/`A1=Region`；交付的 `backend/store.js` 也只种 A1。需求 `REQ-5-1-1`、`5-1-2`、`5-2-1`、`5-3-1` 的共 26 条场景却都以 `A1:C6` 的 `Region/Sales/Status` 表头及 `East/1200/Open` 等记录为前提。官方回放工作区的实际 `Q3 Sales` 文件亦仅含 A1，没有 B1/C1/A2 等。这是实际交付状态与需求前置数据不一致，不依赖官方逐例错误。来源证据：`source-workspace.zip!template/requirements/requirements.yaml` 的上述四个 ATOMIC 节点及场景；`source-workspace.zip!template/.factory26/20260927-082825-d9c4f6ea/braid-state/braid.sqlite3` 的 `local_items` 中 issue #1/#2；`official/workspace-after-generation.zip!template/backend/store.js` 的 `seed()`；同 ZIP 的 `template/data/workbooks/wb-45a85bdd-143a-4f2a-932f-0fc363a7fbc2.json`。26 是需求场景前提的数量，不是已知官方失败数量。

自验收未发现此缺口的直接原因在其判据：`checks/home.spec.ts` 只断言默认工作簿的 A1=`Region`；`checks/dataops.spec.ts` 的 `createWorkbook()` 和 `seedGrid()` 先通过内部 API 创建独立工作簿并填入 `A1:C4`，排序、筛选、验证、透视都在人工准备好的数据上运行。因此全部 36 项可通过而默认工作簿仍不满足 REQ-5 场景入口。根负责人最终在 develop `8152b05` 上跑 backend 66/66、前端 build、Playwright 36/36，并据此判断“REQ-1~REQ-5 全覆盖”，随后合并为 main `4023362`；原生轨迹中的命令和工具结果位于 `source-workspace.zip!template/.factory26/20260927-082825-d9c4f6ea/work/native-homes/pi-glm-fast-01a0e358-cc03-7061-8c47-2a0c4752cfc8/2026-09-27T14-50-43-640Z_01a0e358-d037-725d-b5d2-b5a63bbeb207.jsonl` 第 28、49–56 行（其中第 51 行是检查输出；不是只凭评论声明）。整合 PR 的 `local_comments` #171 则记录最终验收结论。已从 ZIP 中的 bare Git 仓库独立核对 main 引用为上述提交，main 与验过的 develop `8152b05` 树 diff 为空。

## 上游生成链：需求如何在分工中缩减

本节的 `native/...`、`input/...`、`work/skills/...` 和 `braid-request.json` 均相对于 `runs/e20260928-completed-replay/sheet/source-workspace.zip!template/.factory26/20260927-082825-d9c4f6ea/`；这些是冻结来源 run 的原生材料，不是回放后新生成的轨迹。

冻结输入没有省略这项要求。`source-workspace.zip!template/.factory26/20260927-082825-d9c4f6ea/prompt.txt` 明写覆盖“全部需求、场景和明确指定的初始数据”，并要求正常启动准备需求初始数据。相邻 `input/requirements.yaml` 有 24 个 ATOMIC、100 个 scenario；REQ-5 四项共 26 个 scenario 的 GIVEN 均含 `A1:C6` 种子前提。该输入目录没有 `requirements.md`，但 prompt 对缺失格式已有“使用可读需求语义”的处理条件，YAML 可读且被多个 Agent 实际读取。因此不能把数据缺口归为 Harness 完全没有提供需求，也不能把缺失的 Markdown 文件单独认定为根因。

第一个可见的信息损失发生在根 Issue 分解。`source-workspace.zip!template/.factory26/20260927-082825-d9c4f6ea/native/000-2026-09-27T08-28-33-780Z_01a0e1fa-ee74-7496-8057-33ac36fbaa2a.jsonl` 第 10 行先用脚本输出每项描述前 200 字和 scenario 数；第 12–13 行用 `grep -n -i "seed|initial data|Q3 Sales|Region" requirements.yaml | head -40` 搜种子，实际输出止于文件前部 REQ-1 的 A1 种子，没有 `A1:C6`；第 21–25 行再生成并阅读 `/tmp/req-atomics.md`，其中包含完整 ATOMIC description 和 scenario **名称**，但脚本没有提取任何 scenario 的 GIVEN/WHEN/THEN 步骤。这个摘要让根 Agent 看到了 REQ-5 的功能描述，却没有通过所用摘要看到该功能的 `A1:C6` 前置数据。第 28 行由其创建的子 Issue #2 把共享启动种子明确写成 `Q3 Sales`、`Sheet1`、`A1=Region`；子 Issue #6 转交 REQ-5 的功能和原始 YAML 路径，却没有写默认种子契约。第 46 行根 Agent 起草的整合清单也仅列“首页显示 Q3 Sales”，未断言 B1/C1 或销售记录；第 62 行自述“21 个 ATOMIC、约 80 个场景”，与 YAML 实数 24/100 不符。这里的可证结论是**摘要和分工缩小了验证对象**，而不是根 Agent 完全没有访问原始 YAML。

这种缩减沿两条工作线固化。共享基础的 DeepSeek Agent 在 `native/002-2026-09-27T08-34-04-479Z_01a0e1ff-fa3e-76a4-96af-f5f14c6abe63.jsonl` 第 5 行读取子 Issue #2，第 11–22 行集中阅读 REQ-1 等范围（包括 A1 种子），然后实现启动种子；第 136 行写出的 `home.spec.ts` 只查 A1。REQ-5 的 GLM Agent 在 `native/030-2026-09-27T10-01-17-464Z_01a0e24f-d398-73ea-9cdf-0bdef55f18c4.jsonl` 第 11–16 行直接阅读 REQ-5 YAML 原始步骤，工具结果多次出现 `A1:C6`，因此对该 Agent 不能称“未读需求”。但其第 126 行写的 `dataops.spec.ts` 用内部 API `POST /api/workbooks` 新建工作簿，再 `PUT .../cells` 自填 A1:C4；测试不打开默认 `Q3 Sales`。这是**读后判据偏移**：它验证了操作在人工准备状态下可行，没有验证“从官网场景规定的默认入口和状态开始”。根整合 PR 只重跑这套局部检查，36/36 的结论并未填补入口状态的空白。

## 技能接线、协作与模型的证据边界

`braid-request.json` 的两套 profile `user_instructions` 均要求先在 Issue 中联合设计需求、技术与验收方案，并明确“使用 SVC 相关技能设计检查、解释结果”“局部旧 PASS 不代表当前整体验收完成”。冻结包的 `work/skills/svc-verification/SKILL.md` 也确实存在，正文要求检验输入、状态、历史、边界和失败条件，并限定 PASS 只能证明已检查的行为及条件；`browser-checks/SKILL.md` 又指向它。故 SVC/V&V **已提供且有文字接线**。对 `work/native-homes/` 下 682 个来源原生 JSONL 的可见 assistant 工具调用参数做精确检索，没有找到对 `svc-verification` 路径的读取；可见读取 `browser-checks/SKILL.md` 4 次、`svc-design/SKILL.md` 1 次、`svc-implementation/SKILL.md` 2 次。这个检索只能说明轨迹中**没有显式选读验证技能**，不能排除 Pi 启动时展示技能元信息、其他未记录的自动注入，也不能单靠零读取次数判断 Agent 从未接受验证指引。行为层面则可确定，其最终检查在这条默认种子链上没有满足该技能提出的“输入和状态足以区分需求与似是而非实现”的判据。

协作机制的可改处不是增加一段“请认真验收”的口号：现有 prompt 和 profile 已有完整覆盖、SVC、整合验收等文字。缺的是在需求→Issue→检查之间保存可核对的场景前提，尤其“正常启动提供的数据”应由共享基础拥有、由 REQ-5 消费、由根整合检查。子 Issue #2 的实现忠于其明确的 A1 契约；子 Issue #6 的测试忠于其人为准备的功能数据；两者各自的 PASS 无法证明跨 Issue 的启动契约。根整合负责人把测试数目和覆盖标题当作完整行为证明，未将测试 setup 对回 scenario GIVEN。这一分工交界是目前最有证据的 Harness/协作改进点。

冻结 `braid-request.json` 记载根、REQ-5、最终整合使用 `glm-5.3-flash`（high），共享基础使用 `deepseek-v4-flash`（high）；各原生 JSONL 的模型字段与之相符。根对 24/100 的误数、摘要遗漏和后续过度解释确是模型执行中的判断失误，但本次只有这一条生成轨迹，没有保持任务和流程不变的模型对照。共享基础又按根写下的窄契约交付，因此不能由 58 分直接推出“换强模型即可修复”，也不能排除模型能力对其他 42 个失败场景有影响。

最小可区分改进应分两步验证。先不换模型，让根任务从 YAML 机械保留 ATOMIC 数、scenario 数及每个 GIVEN 的初始状态/数据，在 Issue #2 写出默认种子所有已指定单元格，在 Issue #6 标出其消费关系；整合检查至少从全新 DATA_DIR、可见首页进入 `Q3 Sales` 并读取表头与三条指定记录，再执行一个 REQ-5 操作。若这条链仍漏掉或误实现种子，才有证据指向模型读取/推理或实现能力问题；若本地通过，仍需获授权的新官网运行才可测量分数收益。这个改动优先落在需求交接/验收材料的结构化检查或明确责任边界，而不是把所有场景全文塞进 system prompt。若之后要比较模型，固定同一冻结需求、分工和验收门槛，仅替换模型，观察其是否独立满足场景前提；不能用本次快照回放作对照。官方逐例报告缺失仍限制任何分数因果量化。

## 隔离行为复现

从官方回放 ZIP 提取 `template/` 顶层应用（排除 `.factory26/`）到临时目录，在该目录安装依赖并构建前端；以 `DATA_DIR=/tmp/factory26-sheet-diag/node20-repro-data HOST=127.0.0.1 PORT=48534 npx --yes node@20.19.3 backend/server.js` 启动独立实例，运行 `node tasks/sheet-score-diagnosis/repro.mjs http://127.0.0.1:48534`。运行后服务已停止。`repro.mjs` 只访问给定的本机端口，并在隔离数据目录中创建一个诊断工作簿；复跑须换新的空 DATA_DIR。

复现输出：默认 `Q3 Sales` 的 A1=`Region`，B1/C1/A2/B2 均为空；含 `East/1200` 和 `North/N/A` 的透视 SUM 请求返回 HTTP 400 `Value field requires numeric values`，虽源值字段仍有可解析数字 1200；0–100 数值验证范围内输入公式 `=101` 返回 HTTP 200，显示 101。透视结果与需求“SUM/AVERAGE 只聚合可解析数字、仅当值字段没有可解析数字时报错”冲突：`backend/src/pivot.js` 的 `aggregate()` 对每个分组分别抛错。验证行为由 `backend/src/validation.js` 的 `checkValueAgainstRule()` 对公式原文直接放行造成；如果“无效值”按公式计算后的显示值判断，它也违反数值范围契约，但需求未单独明说公式结果的验证时机，故把这一点列为待澄清边界。自验收透视测试仅用了全数值数据及全非数值字段，没有混合分组；验证测试使用普通字面量 101，没有公式结果。**这些复现证明实现边界有缺口，但不证明对应官方测试一定失败。**

另用隔离实例上的 Chromium 经可见 UI 打开 `Q3 Sales`，读到 A1=`Region`、B1/C1/A2 为空；选 B2，打开 Data → Data validation，设置 0–100 Number range，再在 Formula bar 输入 `=101` 并回车，网格 B2 显示 `101`、公式栏保留 `=101`、无错误提示。此操作没有使用 API 预填或改应用代码，证实上述两个缺口可从浏览器观察。

本机为 macOS，但上述 API 复现已在与平台版本一致的 Node 20.19.3 上重复，结果相同。官方平台为 Linux；来源 run 的原生轨迹确实记录最终 36/36 通过。本机直接复跑其整套 Playwright 时，首批 Ctrl+V 剪贴板用例在 macOS 未触发粘贴，故中止，未将该跨平台结果解释为官方 Linux 失败。官方回放的持久化文件也独立佐证了默认种子缺口。

## 未知事实与下一轮判别

- 官网不提供失败逐例、测试名、截图或功能项映射，无法给 58/100 做完备归因。官方工作区的 19 个 JSON 工作簿是评分后的状态，可证明部分浏览器操作发生过，但不能据它们反推每例的通过与失败。
- 默认种子缺口对 REQ-5 的实际失分权重未知；其场景前提与交付状态冲突是确定的。透视混合数字及验证公式是否被官方覆盖未知。
- 下一轮若要验证修复收益，先在已授权的应用实现范围内补足正常启动种子，再从全新空 DATA_DIR 按**可见 UI**读取 `Q3 Sales` 表头/记录并执行至少一条排序、筛选、验证、透视链路；不要由内部 API 替这条链路预填。混合数值透视和公式验证各保留一个边界行为检查。这样可分别区分“默认入口缺数据”和“操作本身语义错误”。若这些本地用例通过后仍需官方分数证明，须按仓库实验规则取得针对冻结新产物的新授权，不能用现有回放成绩替代。

任务范围内只新增本 packet 与 `repro.mjs`。建议在后续实现时把“需求前置数据”设为跨子任务验收契约，并由整合验收直接检查交付默认状态；36 项自检可继续用于回归，但“文件有测试”或“36/36”不等于需求全部实现。
