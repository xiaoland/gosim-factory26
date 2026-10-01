# Issue 4 / PR 9 全过程只读审查

## 范围与读法

本 cell 只读审查 coverage.json 在截止时间 `2026-09-29T08:04:43.268468Z` 选出的 Issue 4、PR 9 及其相关子代理材料。总账有 176 个源；本范围 36 个源、共 2,215 行：Issue 4 侧 713 行，PR 9 侧 1,502 行。每个源均按真实 JSONL 行序读取；索引、关键词命中和截断显示只用于导航，不计入已读。完整行账见同目录 `read-ranges.json`。

主审顺序是：Issue 4 读取权威需求与共享契约 → 基线与设计 → advisor/vision 原始输出 → PR 9 交接 → 实现、排障、修正、验收 → 合入后的跨任务回归和文档收口。无头源 `artifact:...01a0ebb6...jsonl` 的 91 行是 Issue 4 主会话的 native continuation，已和带 session header 的 42 行前缀分别读；没有把它当作可略 artifact。两个 session 副本只在已读完整 native 源上做精确前缀引用，未把副本索引当新增事实。

审查期间未修改源码、应用或测试，也未运行测试；报告中的测试结果均是证据源里已发生的动作与工具输出。

## 过程结论

Issue 4 的设计责任和 PR 9 的实现责任划分清楚：@glm-4 先以 requirements.yaml 的 ATOMIC 条目和根 Issue #1 契约为验收权威，读基线并咨询 advisor，形成 comment #35 的 D-B1…D-B6；@deepseek-6 以 `origin/develop @ 698afd2` 接 PR #9，完成实现、预演、修正和候选验收；根负责人随后裁定跨任务契约、验收偏离和合入。设计没有把公式重写（C/#5）或 pivot 约束/Refresh（E/#7）偷塞进 B；B 只移动 raw、range、selection 并标记 pivot stale，后续回归边界被保留在 packet 和 PR 正文。

Advisor 的反例直接支撑了几个最重要的选择：保留 `{index,count,side}`，结构操作在服务端同事务位移 selection，删除工作表优先激活右邻否则左邻，删除 range 使用 `r2 -= 1`，pivot 源表删除前先查依赖，且结构总量上限应防止全量 DOM 渲染失控。vision 子代理明确记录三张图只是中文 Google Sheets 风格参考，未展示对话框，不能从图推导英文文案或确认触发方式；实现以需求文本和 ARIA 约束为准。

## 重要发现（按因果链）

### 1. 结构位移的真实数据库陷阱被预演发现并修复

- **原文位置 → 决定动作**：PR 9 首轮预演在 `01a0ebc4-8814-...jsonl:约 70–90` 写入 `/tmp/probe-shift.mjs`；工具结果显示直接 `row = row + 1` 触发 `UNIQUE constraint failed`，offset 方式成功。实现因此在 `087032c` 使用 `SHIFT_OFFSET` 两阶段更新，插入和删除都先避开 SQLite 主键碰撞。
- **后果**：若只按数学上的原地加一更新，主键会在中间状态互撞，事务无法完成；offset 方案让 cells、selection、validation/filter/pivot range 在同一事务内完成位移。后续结构测试和最终 e2e 均通过。
- **原因与竞争解释**：原因是 SQLite 复合主键的更新顺序，不是业务映射错误；单纯按降序更新可缓解部分行插入，但不能统一处理列、范围和删除，不能替代已选的两阶段方案。
- **修复归属与边界**：B/PR 9 负责事务位移和 raw 原文迁移；C/#5 负责公式引用重写，E/#7 负责 pivot 行为与 Refresh。下一轮证据是 C 合入后的公式引用回归、E 合入后的 pivot stale/空范围回归。

### 2. 首轮 e2e 失败是测试状态逻辑缺陷，不是产品实现缺陷

- **原文位置 → 决定动作**：`01a0ebc4-8814-...jsonl:约 180–220` 的第一次 `bash checks/run-e2e.sh` 在 selection 场景因 Sheet2 locator 与测试自身创建/重命名后的状态不一致失败；PR 负责人保留 `/tmp/e2e-evidence/run1-*` 原始日志和截图，修正 3 个测试块后用 `SKIP_FRONTEND_BUILD=1` 重跑 12 个 smoke+B 场景全通过。
- **后果**：多消耗一次服务启动和定位时间，但没有掩盖失败；最终又补了 REQ-2-1-1 的 500 失败路径，候选 `014d7ed` 的最终全量 e2e 为 13 passed（smoke 3+B 10），并保留 `service-check-ly59ofyz` 及独立浏览器 e2e 证据。
- **原因与竞争解释**：直接原因是测试依赖旧 tab 名称/跨测试状态，应用的 tab 生命周期和 snapshot 更新并非该失败的证据。仍需把“首轮失败来自测试”与“产品无缺陷”分开：它只排除了该具体 locator 错误，不能替代跨候选的独立回归。
- **修复归属与边界**：PR 9 负责测试隔离、失败路径和证据保存；Issue 4 负责人负责按 comment #35 验收，根负责人负责合入后独立 e2e。C/E 仍有后续回归义务。

### 3. 共享校验 helper 的抽取保留了边界差异，并被根侧明确接受

- **原文位置 → 决定动作**：`01a0ebdc-4c7c-...jsonl:约 14–30` 发现 `assertWorksheetStateValid` 尚未抽取，PR 9 抽出并导出 helper；一次编辑造成 `store.js` 嵌套条件重复，随后在同一轮读取 793–808 行并纠正。`01a0ebe2-54c9-...jsonl:9,24,40–48` 记录根侧 #69/#70/#73：坐标/结构先检、raw 字符串检查后检的多缺陷优先级微差接受为已记录边界，不要求改动。
- **后果**：state 导入与 A 的导入可以消费同一形状；单缺陷文案、`INVALID_BODY` 和整事务回滚保持不变。候选 helper 和 app 树完成后再验收，没有把多缺陷载荷微差错误扩大成阻塞。
- **原因与竞争解释**：这是抽取时检查顺序的可观察差异，而不是数据落库不一致；若需求未来要求所有多缺陷载荷也逐字一致，才需要统一循环顺序。当前 ATOMIC 场景只构造单缺陷输入，根侧据此接受。
- **修复归属与边界**：B 负责 helper 形态及结构/selection 窄门；A/#3 在 helper 进入 develop 后切换其 Y-min 校验；D/#6 消费 state/selection；根侧负责跨 PR 文案契约。下一轮证据是 A rebase 后的调用点和整合 PR 的单缺陷文案回归。

### 4. 合入前后的版本身份被核实，避免把 packet 文档变化误当 app 变化

- **原文位置 → 决定动作**：PR 9 先因远端已有根 packet 提交而 push 被拒，`01a0ebc4-8814-...jsonl:约 220–245` 记录 fetch、packet 冲突解决和 rebase；`01a0ebe3-b491-...jsonl:约 80–99`、`01a0ebe7-3e5b-...jsonl:18–38` 核实 `ab88c7c..fb6c7da` 只改 packet，树 hash 保持 `fd1cfc...`，develop 合入为 `15abbf6`。
- **后果**：`014d7ed` 上取得的 backend 65 + frontend 19、typecheck、e2e 13 passed 证据可继续用于合入树；没有发生冲突消解漂移。后续评论把旧的 `ab88c7c` 候选、实际 head `fb6c7da`、app 候选 `014d7ed` 分开登记。
- **原因与竞争解释**：push race 来自根负责人并行写 packet，不是源码分支冲突；用 `--theirs` 解决 packet 冲突是有边界的，因为先核对了冲突文件只属 task packet。若冲突涉及 backend/frontend，不能复用此处理。
- **修复归属与边界**：PR 负责人负责 fetch/rebase/树核对；根负责人负责 `--match-head-commit` 验收和 merge。后续所有回归应以 develop 当前树和候选 tree hash 双重定位。

### 5. 结构上限和 selection 纵深防御的契约边界得到保全

- **原文位置 → 决定动作**：advisor 原始输出 `99522..._advisor_transcript.jsonl:72` 读取 Grid 全量渲染并据此建议 10000 行/256 列上限；Issue 4 主 continuation `01a0ebb6-d347-...jsonl:约 35–65` 记录根侧 v1.3 裁定：上限只在结构端点生效，state/import 不加应用层上限；selection 四角+anchor 和 state.lastSelection 各有边界门。
- **后果**：PR 9 没有把结构防护误推广成全局 state 限制，保持 A 导入足迹和 D 回放的契约；结构操作仍防止一次 API 请求制造后续全量 DOM 渲染灾难。结构写入返回完整 workbook snapshot，state 端点保持 `{updatedAt, worksheet}`。
- **原因与竞争解释**：限制全局看似更安全，但会破坏已有 import/state 足迹语义；完全不设结构上限则与无虚拟化网格的真实风险冲突。当前分层是风险和兼容性之间的最小边界。
- **修复归属与边界**：B 负责结构端点上限和两道 selection 门；A 负责导入足迹；D 负责粘贴扩张与回放；根负责人负责契约裁定。下一轮要检查 D 的结构端点调用是否尊重上限和 snapshot 消费。

## 子代理、skills 与注意力成本

- Issue 4 在设计阶段先读 `svc-task-packet/SKILL.md`、`svc-design/SKILL.md`，并按设计 skill 先咨询 advisor；advisor 用具体反例而非泛化建议，vision 只承担布局事实并明确材料局限。职责匹配良好。
- PR 9 的主代理消费了 Issue 4 的 packet、PR #2 基线、根评论 #38/#39/#54/#57，并把新增 helper、失败路径、候选证据回写 packet/PR；没有把相关子代理的中间输出冒充验收结论。后续独立浏览器 e2e 作为第二来源登记到 packet，降低“作者自证”风险。
- 主要浪费来自重复读取 issue/PR 正文、queued/delivered 回执和多次后台状态轮询；Issue 4 主会话还多次错误尝试 `braid comment create`，之后才改用 `braid issue comment`。这些不改结果，但增加工具调用与上下文噪声。
- 环境排障有实际价值：PR 9 区分 `/usr/local/bin/node v20.19.3` 与 runtime node v24.10.0，使用项目 wrapper/with-service 取得可复现验证；一次 `/tmp/probe-shift.mjs` 相对路径导入失败后修正到 worktree 路径。最终 e2e 后检查到其它 worktree 的残留 Playwright/backend 进程，说明 cleanup 证据必须按 worktree/service-check 归属，不能把全机进程列表直接归因于 PR 9。
- 另有低价值但可追踪的文档收口：PR 正文曾暂留旧 head `ab88c7c`，后续改为 `fb6c7da`；Issue/E 误写为 PR #7 的 typo 被更正为 Issue #7。它们没有改变 app tree，但会影响后续证据导航。

## 后续证据与责任边界

1. C/#5 合入后，验证公式引用从 B 的 raw 原文迁移切换为 C 的 rewrite，并以 B 的结构操作测试作为输入边界。
2. E/#7 合入后，验证 pivot source range 位移、stale、删除空范围和 Refresh；当前 B 的“先查 source 再删”和空范围删除 pivot 行是已记录局部决定，不能当成 E 已验收。
3. A/#3 rebase 后确认其导入路径消费 `assertWorksheetStateValid`，并确认六条规范错误文案在单缺陷场景逐字一致。
4. D/#6 接入结构端点和 snapshot 回放后，验证 `count`、selection、上限和 undo/redo 不跨越各自契约边界。

## 限制

本报告只覆盖 coverage.json 中 cwd 为 `issue-4` 或 `pr-9` 的源及 Issue 4 的两项子代理 artifact；未把其它 Issue/PR 的完整链路当作本 cell 的读集。选中源在 `read-ranges.json` 均标为完整读取，未读/截断为空；重复副本注明其可引用的完整源。报告没有重新执行任何命令型验证。
