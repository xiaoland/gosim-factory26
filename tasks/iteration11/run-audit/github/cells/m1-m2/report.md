# iteration11 GitHub：M1/M2 有界审查

## 1. 范围、证据与读法

本报告覆盖 assignment.json 中的全部 25 个材料单元：Issue #3 / PR #12（M1）以及 Issue #4 / PR #14（M2 的跨 PR 协调与 Access Denied 修复）；Issue #4 的后续 PR #13 证据也通过其 owner transcript 和 board 读取。权威材料是 `github/views/` 下的 transcript/history 和四个 board；没有修改源码、主 `coverage.json` 或其它 cell 文件，也没有运行测试。

材料约 6.9M 字符，按 transcript record 建立范围并读取定位段；对显示截断处已逐页补读一部分，另对 7 个长 view 完成 canonical `github/views/` Record 序列中所有 visible text、thinking、toolCall 参数、toolResult、details、custom semantic 字段的实际阅读（精确重复字段引用已完整阅读的 canonical 原处，未以 raw session JSONL 的首份输出代替）。仍有 5 个单元的中段未逐字补完。因此本 cell 的全过程覆盖状态为 **partial**（receipt 当前记录 20/25 个单元内容完成阅读（其中 13 个按字符页、7 个按 canonical Record 语义字段并精确去重），仍有 5 个单元中段 pending；字符页统计为已读 172 页、待读 120 页），对应范围和缺口见同目录 `read-receipts.json`，不能将本报告结论推广为 25 个单元的全量过程结论。原文位置以 `view` 文件名、record 范围和 board comment 编号标示。独立 clone 使用相同 `--head` 只作为交接/复核证据，不能据此推断共享物理 worktree。

## 2. 结论摘要

- **M1 已形成闭环并合并。** Issue #3 的设计把会话保留、全局撤销、非枚举错误、URL 驱动步骤和固定验收数据写成了可执行约束；PR #12 首个候选遗漏了完整字段错误收集和文档同步，随后在 D2/D7 复核中修正为 `af2d06d`，以 `a619edd` 合并 develop。最终 backend 50 tests、e2e 17、platform-path 均通过。
- **M1 的关键风险是“安全早返”与共享错误契约冲突。** 首个 `9d30be4` 用错误码早返避免账户存在性差异，却同时丢掉了错误密码字段；根因是候选实现把一个局部非枚举直觉当成完整验收契约。修复后仅在“错误 code”列保持已知/未知 byte-identical；“正确 code + 密码错误”的差异被文档化为固定 code、无 pending challenge 且必须恢复已注册账户这一需求造成的边界。
- **M2 的设计决策是把隐私差异放在已加载会话的 UI 层。** Issue #4 #73 采用：API 仍为 404；visitor（含过期/无效 cookie）显示 `Not found`+Sign in，已认证且无权限显示 `Access denied`；unknown/ungranted 在各自会话态内文本一致。PR #14 `9bedf84` 已合并为 `d70e6ac`，并在 PR #13 之前落地。owner transcript 报告的 PR #13 候选 `d62907d` 尚在等待根任务合并，虽已报告 95/95 Vitest、51/51 Playwright、typecheck/build/platform-path 通过；刷新证据另见 `824d29a`，不能把两者或其测试数字合并。
- **环境故障和实现缺陷已分离。** M1 中出现的 3 个 Vitest timeout 和 `Channel closed` 来自与 e2e 的 CPU/会话竞争，后续独立重跑通过；不能把它计为产品失败。PR14 的 shell backtick 展开是通信命令问题，已修正，不是应用缺陷。

## 3. M1：Issue #3 / PR #12

### 3.1 设计、验收初始条件与契约

Issue #3 初始 transcript（`2026-09-29T05-09-12-202Z...` records 1–35）先读需求、架构和实现，再建立 packet 和 PR。advisor transcript 明确了下列验收前提：

1. 改密码保留当前 session、撤销其它 session；恢复密码撤销全部 session，且不自动登录。
2. 未知 email 与错误 code 必须返回完全相同的 `Verification code is invalid`；不能因 lookup 顺序泄漏账户。
3. step 2 和 success 由 URL 驱动，mount 不得 POST；成功不重定向，密码字段清空，`errors[]` 逐字段承载 code/password 错误。
4. 固定 code `123456`、需求密码 `New-password-456!` / `Required-password-789!`、已有用户/新用户/重复 username、其它账户隔离和返回后退行为都必须进入验收；不新增账户、不增加需求外校验。
5. sign-in/sign-out 使用 canonical API；导航角色、accessible name、按钮数量和成功文案属于可观察契约。

owner 随后写入 `docs/task-packets/identity-m1-issue-3.md`、架构 UI notes，并以 `07980ef`（`braid/issue-3-m1`，base `origin/develop c338578`）创建 PR #12。这里 Issue 设计和 PR 实现是分开的；M3 依赖、需求密码遗漏以及根裁定分别在 board #25/#26/#27/#31 留痕。

### 3.2 从候选偏差到修复的因果链

**原文位置 → 决定/动作 → 后果 → 根因与竞争解释 → 修复层/边界 → 下一轮证据**：

- PR #12 board #37 / Issue transcript `05-35-09...`：候选 `9d30be4` 对 unknown email 和 wrong code 做早返，验证了“错误 code 的已知/未知不可枚举”，但文档 §3/§9 仍旧，packet 有待根确认项，且 code 错误时没有收集密码错误。
  - 后果：单项 non-disclosure 测试能通过，但违反共享 `errors[]` 契约；候选的 A-C 文档验收也无法复核。
  - 根因：实现把防枚举作为唯一优化目标，未把“所有字段错误同时返回”当作同等级合约。一个竞争解释是隐藏测试可能只比较响应文本，但 Issue 的 API/前端字段契约和后续测试证明不能按此缩减范围。
- PR #12 board #41：owner 修正判断，要求已知/未知在 wrong-code 场景逐字节一致，同时恢复 code/password 全量错误收集，并补“wrong code + bad password vs unknown”回归断言。
  - 修复层：router/service 的错误聚合层，而不是仅改 UI 文案；保留 lookup 不早返的结构，错误 response 仍不携带账户/session 数据。
- Issue #3 advisor 后续复核：正确 code + bad password 对已知账户和未知 email 的剩余差异是需求内在边界，不是可任意消除的 bug。固定公开 code、没有服务端 pending challenge、且成功必须恢复已注册账户，意味着 unknown email 无法与 known email 的密码校验结果完全相同。用 unknown email 假成功会制造错误成功态，并可能带账户/session 数据，故被否决。
- `af2d06d`：补架构 §3 对“有意保留的 residual difference”说明、§9 entry 12、packet flip conditions、combined-errors backend regression；成功响应保持 `{ok,message}`。这将隐私边界从隐含实现选择提升到文档和测试可审计的层。
- M1 advisor 的完整复核还确认：`/register` 已用 `email_exists: "Email already exists"` 暴露邮箱存在性；reset 成功体仅 `{ok:true,message:"Password updated"}`，不签发 session/用户对象。因此 pretend-known 可技术实现但会与现有 `correctCodeUnknown → [code]` 测试锚点冲突；当前合并方案的真实残余是公开 `123456` 下的 code-correct existence oracle，不能把它描述成信息论上的完全防枚举。

### 3.3 验收结果与交接判断

在 `af2d06d` 上，owner 报告并由后续 transcript/board #56/#57 留证：`pnpm test` 50 pass、typecheck exit 0、Playwright e2e 17 pass、platform-path exit 0；PR #12 以 `--match-head-commit af2d06d` 合并为 `a619edd`，Issue #3 closed。测试覆盖了：forgot registered/unknown 的 byte-identical、reset wrong-code known/unknown、reset session 全撤销、change password 保留 caller 并撤销其它 session、其它账户隔离和字段错误聚合。独立参考 ref `d262e52` 的 49 Vitest/16 e2e 只作交叉证据；不能与正式 head 的 50/17 计数相加或合并成一项。

M1 的交接没有把两个相同 branch/head 的独立 clone 当作共享 worktree：glm-6 先在 PR worktree 实现；其未消费 owner 的修正评论时，owner 在 PR #46 明确宣布接管并继续修改。glm-6 后续给出的 `d262e52` 是独立等价的未提交/参考状态，不能替代最终 `af2d06d` 的合并身份。

### 3.4 原生 subagent、skills 与环境

Issue owner 使用原生 advisor 和 vision subagent，advisor 输出被用于 D1–D4、D7、返回后退和非枚举判断，vision 输出用于角色/页面验收；首次等待后因 console.log 未返回结构化结果而出现 null，随后通过 transcript 读取补救。 Vision transcript 已逐字读完：六张 M1 图中，账户菜单文件实际是 Dashboard、两张 reset 图都没有验证码；这些是参考材料与需求之间的边界，不能当作实现缺陷。后续 advisor 对 D2 边界做独立复核，实际改变了“只要错误码一致即可”的判断。该过程说明 subagent 结果消费有记录，但 native orchestration 的返回值约定应在下一轮先验证。

M1 早期出现 3 个 Vitest timeout（73 passed, 3 failed）和 e2e `Channel closed`；上下文显示同时运行 e2e、CPU 竞争和 session/instance churn，后续在固定 Node 20.19.3 / npm 10.8.2 环境下独立重跑通过。因此根因是环境排障，不是把失败断言隐性吞掉。与 M3 合并预览时另有 routes.tsx/架构 §9 冲突：必须保留 M1 `/settings` 嵌套路由和 `/password-reset` 页面，并给 M3 entry 重新编号；这项整合边界已在 transcript 留下，下一轮要以合并后 develop 的真实路由为验收初始条件。

## 4. M2：Issue #4 / PR #14，以及 PR #13 消费

### 4.1 设计分离与共享契约

Issue #4 #58/#68 把 M2 定义为组织、team、成员层级、direct member、remove member、grant 的需求；共享权限规则是 Owner→Admin，direct/team 取最高权限，team hierarchy 不传播。M2 owner 先设计 org router、seed 和前端 copy，并提出与 M3 `RepositoryMissing` 的语义冲突：REQ-2-2-3 要 logged-in `Access denied`，M3 原始读取路径是 `Not found`。

根任务 advisor 在 #73 采用方案 C，并明确这是会话态显示策略：

- API 继续 404，保持读取路径不变。
- session loading 完成后再 gate，避免先闪现 `Not found` 再改成 `Access denied`。
- visitor 包括 expired/invalid cookie，显示 `Not found` + Sign in；authenticated 无权限显示 `Access denied`。
- 每个 session state 内 unknown 与 ungranted 文本一致；不能宣称“API 无泄漏”，因为写路径仍可能 403。
- `errors.accessDenied` 由 PR14 提供，M2/PR13 消费同一常量，不重复添加；seed 用 insert-if-absent / conflict-safe 写法，顺序无关。

这次决策将 M2 的产品文案、M3 的 API 兼容和权限边界分到不同层，避免 M2 直接修改 M3 router。Issue #4 #77 接受该边界；#83 创建 PR #14，要求先于 PR #13 合并。

### 4.2 PR14 因果链和验收

PR14 transcript / board #86、#101–#106：在 `53532a0` 上实现 `9bedf84`，包括 session-aware `RepositoryMissing`、`errors.accessDenied` copy、架构 §7.1/§9 和 e2e。visitor 原有 not-found 测试保留，新增 `carol-writer` 无 grant 的登录态测试；unknown branch/path 仍走 pathNotFound。独立复核为 typecheck 0、Vitest 76/76、e2e 34/34、platform-path exit 0；root 冻结并确认 merge-tree clean，随后以 `d70e6ac` 合并。

根因是同一资源在不同会话态需要不同用户动作，而不是要改变 repository API 的资源存在性判断。竞争解释“把所有情况改成 Access denied”会使 visitor 失去 Sign in 引导并扩大信息差；“所有情况都 Not found”则不满足已登录用户的权限反馈。方案 C 同时保留 API 兼容和前端可操作性。

### 4.3 PR13 当前状态和下一轮判断

Issue #4 #114 的 owner transcript 记录 PR13 基于 `d70e6ac`、目标 head `d62907d`（测试代码 head `074f5b9`，随后补 packet 文档），实现组织、team、成员和 grant；后续刷新证据另记录候选 head `824d29a`，两者不能在未核对提交图前视为同一提交。它从 PR14 消费 `errors.accessDenied`，没有复制 key。`carol-writer` logged-in 为 `Access denied`、visitor 为 `Not found`；seed 同时覆盖 `acme-demo/org-handbook`、`org-private`，并验证无直接/team grant。报告的 95/95 Vitest、51/51 Playwright、frontend typecheck/build、platform-path 均通过。

PR13 在该段读取截点仍为 Issue #4 的 open/待根合并状态；主审末尾证据随后确认最终合并为 `e9390cc`。因此“实现已验收”与“主线已交付”要分开记录：下一轮必须在根合并时核对 owner 报告的 `d62907d` 与刷新证据的 `824d29a` 到底对应哪个候选，保留 PR14 copy/gate，重新确认 seed 幂等和组织层级不传播，然后再把 develop→main 的最终验证作为交付证据。

补充的根任务 PBB 证据改变了 platform 验收的证据解释：首轮在 `d62907d` 上启动的 `pbb_44038_2d44e69d:bg001` 因 owner 自写正文触发 context reset，旧 Pi 实例关闭后没有留下可消费终态（metadata 仍 running，日志只到 12/51）；新会话没有消费旧 job，而是在另一目录重跑同一 head，最终 51/51 完成。该新 job 可作为有效结果，但首轮不应算作已完成或可恢复的终态。新会话附带的 Vitest 使用 Node 24 且管道通过 `tail` 掩盖了非零退出，不能作为测试通过证据；PR13 的应用 Node 20 测试应继续以 owner/独立复核的明确退出结果为准。根因属于正文自更新、后台作业与 Pi 生命周期的衔接边界，不是 PR13 业务断言失败。

## 5. 后续判别证据

1. **M1 集成边界：** 用合并后的 develop 运行 M1 + M3 同时存在的 `/settings`、`/password-reset`、routes.tsx 和架构 §9 编号检查；证明 M3 rebase 没有删掉 M1 页面/路由。
2. **M1 安全边界：** 保留 D1/D2/D3 flip conditions：改密码保留 caller、恢复全撤销且不自动登录、wrong-code known/unknown byte-identical；另单独断言正确 code + bad password 的 residual difference 只在需求允许的列出现。
3. **M2 会话边界：** 分别用 visitor、expired/invalid cookie、authenticated ungranted `carol-writer`、真正 granted 用户和未知路径复放；检查无 flash、copy 来自 PR14、API 404 行为未改。
4. **共享数据和交接：** 在 clean checkout 中以不同 seed/merge 顺序重复 insert-if-absent；确认独立 clone 的相同 head 仍只是交接证据，不发生非显式共享写入。
5. **交付状态：** PR13 在该段读取截点仍是 open/待根合并；主审末尾证据随后确认最终合并为 `e9390cc`。冻结 head 的 owner 与独立平台证据仍须分开记录，不能拼成同一执行者的全绿矩阵。
6. **后台验收寿命：** 同一候选启动 PBB 后若更新状态正文，必须能消费原 job 的终态或明确取消原因；不能因新 scope 列表为空就把旧作业当作不存在并无依据重跑。

## 6. 缺失与限制

assignment 中的 25 个 transcript/history 和四个 board 均有对应范围 receipt，但 5 个 view 的长输出仍存在显示截断中段未逐字补读；因此不能声称本 cell 的 view 内容全量已读。没有发现缺失 view 或需要凭据才能访问的证据；未读/未补完部分已在 receipt 标明。未读取/修改其它 cell 的材料，也未将 819 未启动 failed turn 计为模型响应；该项按父任务提供的 hotfix01 已知背景处理。

### 6.1 当前未完成字符页的精确清单

为避免把 record 范围误写成全文阅读，receipt 中仍为 `partial_display_middle_unresolved` 的单元是：PR #14 的 `06-50-15`（508,228）、`06-59-04`（414,749）；PR #12 的 `05-33-27`（452,536）；Issue #4 的 `06-06-09`（361,538）、`06-31-09`（1,250,796）。这些数字是 canonical `github/views/` 文件的实际字符数，不能用显示首尾或关键词命中替代逐页阅读。本轮已补齐的 Issue #3 四个 view 分别完整覆盖 records 1–108、1–218、1–180、1–149；其唯一语义投影实际阅读边界见 `read-receipts.json`，跨 view 的精确重复仅引用已读 canonical 原处。

## 7. 补审：Issue #4 canonical unit `06-31-09-547Z_01a0ebdc-29eb-731e-a7b1-66cc34026ee6`

### 7.1 阅读边界与方法

本补审完整覆盖 `github/views/2026-09-29T06-31-09-547Z_01a0ebdc-29eb-731e-a7b1-66cc34026ee6.txt` 的 Record 1–443；该 view 对应单一 native source，未以 raw JSONL 的首份/截断输出替代 canonical view。为避免 18k 字符显示上限，先从 canonical view 生成保留每个 Record、source、全部标量路径和值的唯一语义投影，再按 18,000 字符页从 0 读至 1,120,213；重复的精确 path/value 仅在后续 record 标注其首次 canonical 来源。投影包含 `thinking`、`details`、`custom`、tool-call arguments、tool-result/content、usage 和 stopReason。共覆盖 443 个 Record；唯一标量对 4,359 个，后续精确重复 4,886 个，缺失范围为空。详细 receipt 追加在 `read-receipts.json` 的 `supplementary_materials`。

### 7.2 因果链：Issue 设计 → PR13 实现 → 验收结果

- **原文位置**：Record 4/8/10、20–31，Issue #4 需求、PR13 packet 和 requirements.yaml 被依次读取；共享契约规定 Owner→admin、direct/team 取最高、team hierarchy 不传播，且 seed 名称最终以 M3 的 `acme-demo/org-handbook` / `org-private` 为准。
  **决定/动作**：owner 将 API、组织/团队/成员 UI、seed、grant 路由和 e2e 作为 M2 范围，并把 M3 的 Settings 入口、overview 页面和访问拒绝文案先登记为依赖。
  **后果**：Issue 设计没有被 PR implementation 偷换；真正可合并的验收初始条件必须包含 PR11/M3。
  **根因与竞争解释**：早期 `acme-docs` 文档名与 M3 org repo 名不一致，若按旧文档直接 seed 会造成重复/错误前提；owner 通过 #73/#77/#83/#87 改为共享业务键和 insert-if-absent。独立 clone 使用相同 branch/head 只是交接状态，不能解释为共享物理 worktree。
  **下一轮证据**：在 clean checkout 按不同 seed/merge 顺序重放，确认 org repo、成员、team、grant 计数与权限结果相同。

- **原文位置**：Record 42–64，backend org router、grants router、seed 和 mount 的实现记录；Record 81–143，前端 org pages、copy、routes 与 #73 方案 C 的消费。
  **决定/动作**：org router 增加 Owner-only 写、last Owner 防护、成员删除级联、team cycle 检测；grants router 在 M3 repos router 前挂载并做 admin-only upsert/role replacement；前端实现组织/People/Teams/Manage access，Settings 入口由 M3 合并后补齐。#14 提供 `errors.accessDenied` / `ACCESS_DENIED`，PR13 删除自己的重复 key，改为消费共享契约。
  **后果**：REQ-2 的 API 与 UI 层边界落地，M3 repository API 继续保持 404；已登录无授权用户由 #14 的 `RepositoryMissing` 显示 `Access denied`，访客显示 `Not found` + Sign in。
  **竞争解释**：把所有访问失败统一为 `Not found` 会丢失已登录用户的动作反馈；把所有情况改成 `Access denied` 会改变访客信息边界。#73/#104/#107 的证据支持按 session state 分开。

- **原文位置**：Record 169–190、201–218，首次 org-only 测试与诊断；Record 189 明确指出 `requireAuth` 工厂被直接作为 middleware，导致 `/api/orgs` 请求挂起。
  **决定/动作**：改用 `requireAuth()`；同时发现 test helper 原只提供 get/post，而测试使用 patch/delete，且测试把 response `body` 误读为 `data`。
  **后果**：中间轮出现 5 秒 timeout、18 failures；这些不是业务通过证据。修复后以 Node 20 环境重跑。
  **根因与竞争解释**：请求挂起来自 middleware factory 误用，`.data`/缺方法属于测试夹具契约错误；不是 SQLite 或权限模型已被证伪。Record 208/214/218 的探针和后续修复显示“常量 bind 通过、查询后 CHECK 失败”的现象是调试过程中的测试上下文问题，不应升级成产品根因。
  **下一轮证据**：只接受明确 exit status 的最终 run；不能把 `tail` 管道 exit 0 或 stale background job 当作 PASS。

- **原文位置**：Record 230、268、272–286、390–392、413，后续 rebase、typecheck/build、完整 e2e 和 platform-path 终态。
  **决定/动作**：PR13 rebase 到 PR14 合并后的 develop `d70e6ac`；backend Vitest 95/95、frontend typecheck/build、Playwright 51/51、`checks/platform-path.sh` exit 0，平台路径使用 Node v20.19.3。
  **后果**：在代码 head `074f5b9` 上实现验收闭环；后续 `0bd20f5`/`d62907d` 只有 packet/PR 文档增量，不能混淆为重新运行代码验证。PR13 仍需根负责人合并裁决，测试通过不等于主线已合并。
  **边界**：Record 328/342/346、379/390、432/440–443 还保留了 45/5、12/5 等修复前 e2e 失败，以及最终 51/51；失败是 selector/spec bug（`org` 未定义、团队页导航、strict text/label），修复后才是有效终态。Record 414/416/418/420/432 的 bg001–bg005 是 stale 中间结果，不能作为最终失败或通过重复计数。

### 7.3 root-full 25 单元覆盖声明的复核结论

对既有 `cells/root-full/read-receipts.json` 的可见回执复核如下：它确实记录了 owner=issue:1 的 25 个 canonical view、每个 Record 1..N 的顺序覆盖、20 个 complete 与 2 个 runtime `stopReason=length`，并明确 vision unit 的 Record 102 结构化回答尾部未生成；image binary 只保留在 raw session，canonical view 省略。因而“record sequence 已读”可以成立。

但这份回执没有为每个 view 提供可独立核验的 `details/custom/thinking/toolCall/toolResult` 字段投影，也没有逐源列出合并来源清单；仅凭该回执不能把“每个 Record 经过读取”升级为“每个字段和所有 merged-source payload 均已完整语义消费”。尤其 vision unit 已明确存在 runtime 截断，故其尾部结构化回答不能声称全读。对 root-full 的字段级/merged-source 全读声明应降级为：**record-level complete；普通 23 units 的字段消费按其执行者回执记载，但本审查无法独立证实；vision unit 明确 partial at Record 102；merged-source 字段级完整性未被回执充分证明**。这不是对 root-full 主报告的改写，只是本补审的证据强度判断。

### 7.4 重要判别结论

1. PR13 的 M2 业务实现和验收证据链最终闭合，但 Issue 设计、PR implementation、PR14 shared contract、根合并状态必须分开记录；`95/95` 是 PR13 owner/最终代码 head 的证据，不能与 PR14 的 `76/76` 或早期中间失败混为一项。
2. `Access denied` 的常量和 UI gate 属于 PR14；PR13 后续消费它而不是重复定义。seed 对 `org-private` 的无授权前提专门支撑 carol/written e2e，frontend-team 的既有 write seed 对应 org-handbook。
3. “测试通过仍待合并”是准确状态：代码验证以 `074f5b9` 为准，PR 文档 head 后续为 `d62907d`，develop 基线为 `d70e6ac`；最终是否交付仍以 root 的 merge evidence 为准。

### 7.5 后续状态修订（主审最终证据）

本报告 4.3、5、7.3 的“PR13 仍 open/待合并”“824d29a 待判别”只描述当时读取截点，不是当前最终状态。主审末尾证据已确认 PR13 最终合并提交为 `e9390cc`；`824d29a` 是 PR13 创建前仅 packet 的提交，不是刷新验收候选。故当前应分开保留：owner 自报 95/51 与 root 独立 94/95 的证据范围；PR13 已合入的事实以 `e9390cc` 为准。两者不能合并成一项“同一执行者全绿”测试结论。

同时，root-full 25 个 canonical view 的字段级补审已完成：record-level 顺序范围仍为每个 view 的 `1..N`；递归可读实质字段（thinking/details/custom/tool-call/tool-result 等）按精确重复复用首个实际来源，图片二进制和原生未生成尾部继续单列为材料边界。vision record 102 的 `stopReason=length` 不表示 record 102 已有字段漏读，只表示原生没有继续生成尾部。
