# iteration11 GitHub root 统筹全量审查

## 1. 范围与证据边界

本审查覆盖 `coverage.json` 中 `owner=issue:1` 的全部 25 个单元，共 1,584 records、4,072,705 字符。材料包括 root native session、vision transcript、三份 advisor transcript、subagent transcript/history；canonical view 均位于 `github/views/`。对应 record 范围见本目录 `read-receipts.json`。

四个目标外部约束也纳入判断：当时的运行分析说明（现已删除）、`requirements.yaml`、`issue-1-board.txt`，以及 root 已提供的 `cells/root/background-reset.md`。没有修改源码、`cells/root/`、主 `coverage.json`，没有运行测试。

**截断区分：** record 范围本身已逐单元覆盖；但某些原生运行输出有两类需要分开记录的截断：

- vision 的图片读取回执在 raw session 中存在，canonical view 只保留 `Read image file` 文本和路径调用；二进制图片没有复制进 view。raw session 实际发起 28 次 read，其中 `github-code-file-browser.png` 被重复读取 1 次，因此覆盖 27 个唯一 PNG。
- vision 最终结构化回答的 `stopReason=length` 是运行时模型输出截断，不是本审查工具显示截断。它在完成 27 张图的读取后，结构化清单写到跨图疑点第 2 项即停止；root 已消费此前逐图观察和前两组重复图结论，但不能把截断后的尾部当成完整 vision 报告。
- 个别 root PBB / shell 输出只保留 `tail`，这是运行时调用自身选择的输出截断；后续若有完整日志，必须以完整日志而不是尾部退出码判定。`read-receipts.json` 单列这些情况。

## 2. 结论摘要

1. **根统筹的共享基础决策链基本成立。** root 从 `origin/main` 建立并发布 `develop`，先形成产品/架构/seed/验收/UI 文档，再建立基础 PR #2，随后按依赖拆分 #3–#10。advisor 提出的 merge、commit、权限镜像、文案和拆分风险均被 root 采纳，最终落入架构契约和 Issue/PR 交接。
2. **需求数量标签滞后，但不能据此直接判定漏做。** 根 Issue、早期 advisor prompt 和 task packet 多次写“34 条原子需求”；当前 `requirements.yaml` 实际解析出 47 个 `ATOMIC`：REQ-1=5、REQ-2=7、REQ-3=6、REQ-4=8、REQ-5=9、REQ-6=12。Issue #3–#10 的拆分覆盖这些 ID 的模块范围，说明“34”首先是计数/版本标签问题；仍需把 47 个 ID 与每个子 Issue 的验收条目做一次显式映射，才可关闭漏项风险。
3. **vision 实际完成了 27 个唯一图片的读取（28 次 read，含 1 次精确重复），但结果消费是不完整的。** 读取路径覆盖文件清单中的 27 个 PNG；它确认两组重复图、文件名与画面不符、纯图标按钮的 accessible-name 风险。root 将这些结论写入 `docs/ui-reference-notes.md` 并在 root comment #1 使用。尾部结构化答案因长度截断，故不能宣称 vision 的逐图最终文本完整交付。
4. **advisor 结果被实质消费，而不是只作为背书。** 基础 advisor 的四项风险变成共享契约；M3 advisor 的 slash branch 路由风险变成 §7.1/§9 条目与测试；Access Denied advisor 改变了 M2/M3 的落地顺序，采用 API 404、UI 按 session state 分文案的方案 C。
5. **PR13 证据必须按生产者分层。** owner #113/#114 报告 code head `074f5b9` / packet head `d62907d` 的 95/95 Vitest、51/51 Playwright 和 platform-path；root 首轮 platform job 因正文自更新触发 context reset 丢失终态，后续同一 head 新 job 得到 51/51，但 Node 24 下的 Vitest 失败被管道退出码掩盖；Node 20 下并发负载又出现 94/95（restart timeout）。这些不能合并成一条无条件“root 独立全绿”结论。
6. **协作成本主要来自长任务重建、重复唤醒和命令界面误用。** root 多次把自己的正文回写回执当成外部更新，重复检查/编辑；`braid issue/pr comment view` 与 `--reply-to` 语法多次试错；PR11 先在旧 head 验证、后遇 force-push 和 M1 合并冲突，虽最终补齐了同一候选的独立复跑，但成本和证据生命周期都变长。

## 3. 原始需求、共享基础与任务拆分

### 3.1 需求入口和初始状态

root native `2026-09-29T04-24-34-972Z_01a0eb68...` records 4–26 首先读 Issue #1、`requirements.yaml` 和 reference 目录；确认仓库初始只有初始化 commit，`prerequisites.md` 为空，`requirements.md` 不存在，环境提供 Node 20.19.3、npm 10.8.2/10.34.5、`/usr/local/bin` 入口。root 没有因为缺少 `requirements.md` 停止，而是使用 YAML 与参考图的可读语义继续。

当前 YAML 的 47 个原子需求如下模块计数：

| 模块 | 原子需求数 | Issue 拆分 |
| --- | ---: | --- |
| REQ-1 Identity | 5 | #3 |
| REQ-2 Organization | 7 | #4 |
| REQ-3 Repository assets | 6 | #5 |
| REQ-4 Code/version control | 8 | #6 + #7 |
| REQ-5 Issues | 9 | #8 |
| REQ-6 Review/merge | 12 | #9 + #10 |

复核后的原子 ID 列表：REQ-3 为 `3-1`、`3-2-1`、`3-2-2`、`3-2-3`、`3-3`、`3-4`（6 项）；REQ-4 为 `4-1`、`4-2-1`、`4-2-2`、`4-2-3`、`4-3-1`、`4-3-2`、`4-3-3`、`4-4`（8 项）。六模块合计仍为 47。

root 的早期文档和评论把这套清单标成 34，且 advisor prompt 也沿用了 34；这是当前最明确的开放发现。拆分的依赖图本身是合理的：#2 基础 → #3/#5；#3 解锁 #4；#5 解锁 #6/#8；#6 解锁 #7/#9；#9（加 #7 的分支上下文）解锁 #10。下一轮应建立 `REQ-ID → Issue → PR/e2e` 表，避免“拆分覆盖”被误当成“验收覆盖”。

### 3.2 Advisor 促成的共享契约

基础 advisor transcript `200cbf14...` records 2–10 对 greenfield 方案指出四个高风险空白和一个依赖选择：

- commit/merge 缺少共同祖先和冲突语义；
- fork 是复制 commit 链还是共享不可变对象；
- 前端若自行复制权限梯子会漂移；
- exact accessible name 没有单一来源；
- better-auth 与固定验证码、自定义错误、五级仓库角色和 team hierarchy 的兼容性没有评估。

root 在 native `04-24-34...` records 52–54 消费这些判断，随后在 PR #2 方案和 Issue #1 comment #1 固化：

1. commit 全局不可变，fork 只复制 branch pointer；
2. merge 用逐文件三方比较，双方不同修改即冲突、禁用 merge；
3. 资源响应返回 `viewerPermission`，前端只读；
4. `copy.ts` 统一 exact accessible name 和错误文案；
5. Checks 按 `(compareCommitId, name)` 存储，新 commit 回到 pending；
6. seed 按业务键幂等 upsert，业务实体用唯一 token 隔离，不依赖全局计数；
7. better-auth 评估后自建，因为固定 code、字段错误、立即撤销 session、五级仓库角色和 team hierarchy 不传播都需要偏离默认插件流程。

PR #2 后续 comment #6/#8 的六项契约增量又被 root 明确裁决并同步到架构：`users.email_verified`、`commit_parents`、`issue_milestones` 一对一、seed 默认启动且 `SEED=0` 关闭、HTTP cookie 不带 `Secure`、始终返回 `errors[]`。这说明基础 PR 的角色边界清楚：root 负责契约，deepseek-2 在独立 PR worktree 负责可消费实现；root 通过冒烟、单测、e2e、平台路径后才合入 `c338578`。

### 3.3 Skills 的实际消费

root 明确读取并消费了：

- `svc-design/SKILL.md`：先形成代表性旅程、列出失败路径和替代方案，再用独立 advisor 作为共享契约的前置判断；这对应基础 advisor、M3 路由 advisor、Access Denied advisor 三次实质咨询。
- `better-auth-best-practices/SKILL.md`：要求先按产品流程比较注册/登录/改密/恢复和持久 session，再选库；root 据此记录自建理由。
- `organization-best-practices/SKILL.md`：root 同次读取，注意插件可以覆盖组织/team/member，但不定义 repository、issue、review 权限，且默认 team inheritance 不能未经核对套用。

原始 root transcript 中还提到 `svc-sub-agents`、`svc-task-packet`、`svc-verification` 等计划读取，但 canonical evidence 里能直接确认的 skill 内容是 `svc-design` 和 Better Auth 两份；不能把计划读取当作实际消费。task packet 的实际维护行为则有记录：Issue 正文保持当前状态，过期 progress comment #3 被 hide 并保留 `--include-hidden` 追溯入口。

## 4. Vision 与 advisor 的消费闭环

### 4.1 Vision：读取完整，回传截断

vision raw transcript `1657f14b...` records 4–101 逐批读取 27 张图片，路径覆盖：

`github-sign-in.png`、`github-sign-up.png`、`github-password-reset.png`、`github-password-reset-1.png`、`github-repository-overview.png`、`github-code-file-browser.png`、`github-branch-selector.png`、`github-code-clone-menu.png`、`github-commit-history.png`、`github-commit-diff.png`、`github-create-branch.png`、`github-web-file-editor.png`、`github-issues-list.png`、`github-new-issue.png`、`github-pull-requests-list.png`、`github-milestones.png`、`github-fork-repository.png`、`github-compare-branches.png`、`github-organization-repositories.png`、`github-repository-search-results.png`、`github-repository-code-search.png`、`github-account-menu-sign-out.png`、`github-create-repository.png`、`github-default-branch-settings.png`、`github-repository-visibility-settings.png`、`github-password-settings.png`、`github-branch-protection.png`。

实际消费的高影响结论：

- `github-code-file-browser` 与 `github-repository-overview` 画面重复；
- `github-default-branch-settings` 与 `github-branch-protection` 画面重复；
- `github-account-menu-sign-out` 实际是未展开账户菜单的 Dashboard；
- `github-create-branch` 实际是 Branches 列表；
- visibility 图实际是 General 长设置页，默认分支下拉从该图取；
- 纯图标按钮、分段控件、复选框长 label 和 exact accessible name 是共同 UI 风险。

root 在 native record 41 读取 vision 结果，在 docs/UI notes 和 Issue #1 comment #1 登记上述结论，后续各子 Issue 使用了这些 a11y/重复图缺口。vision 最终回答 record 102 以 `stopReason=length` 终止；这只表示原生尾部未生成，record 102 已存在的可读字段已消费，图片二进制仍按 receipts 标为 canonical 过滤边界。

### 4.2 Advisor 三次结果

- **基础 advisor：** root 采纳了共享 commit、merge、权限、copy、Checks、seed 与拆分原则，并把 M4 拆成 M4a/M4b、M6 拆成 M6a/M6b。
- **M3/M4 路由 advisor `1af7af9a...`：** 识别 REQ-4-3-2 的 `feature/api-v2` slash branch 反例，要求 `:branch` 单 URL segment 编码、`*path` 按段编码、裸路由代表默认分支、空分支 200/缺失 404 区分、diff 以 commitId 为键。root 在 Issue #5 #42、Issue #6 #44、PR11 docs/测试和最终 §9.13 中消费，且在 PR11 与 M1 合并时重排 §9 entry。
- **Access Denied advisor `06c0c378...`：** 先检查 requirements、现有 `RepositoryMissing`、`AuthProvider.loading`、seed 和 e2e，发现 REQ-2-2-3 的 `Access denied` 是登录态硬要求，而当时五处 `Not found` 断言均为 visitor；推荐方案 C：API 保持 404，RepositoryMissing 等 session loading 完成后，visitor 显示 Not found，authenticated ungranted 显示 Access denied。root 在 Issue #4 #73 采纳，建立 PR14，先合入 `d70e6ac`，再让 PR13 消费，不让 M2 rebase 修改 M3 文件。

## 5. 统筹过程、重建、交接与成本

### 5.1 成功的交接边界

root 先让 deepseek-2 作为独立基础 PR 实施者；PR #2 先后经历实现、docs sync、平台路径补证，最终在根首手 38/38、typecheck、e2e 5/5、platform exit 0 后合入 `c338578`。随后 #3/#5 并行，M1 PR12 合入 `a619edd`；M3 PR11 在 base 过时后出现 `docs/architecture.md` 与 `routes.tsx` 冲突，root 保留 M1 settings 嵌套路由、M3 repo routes，并把 §9 entry 11 重排为 13，最终同候选 `15c79a4` 两次独立复跑后合入 `53532a0`。

这里独立 clone/相同 head 是正常交接证据，不能解释成共享物理 worktree。PR11 owner 在 comment #65 明确撤回未提交 merge，root 负责整合；deepseek-5、glm-4 和 root 分别留下结构核对、模块验收与平台复跑证据。

### 5.2 重建与验收寿命问题

root `07-24` session records 24–28 启动 PR13 head `d62907d` 的 PBB `pbb_44038_2d44e69d:bg001`，随后自写 Issue 正文触发 context reset。新 session records 15–18 未消费旧 globalJobId，而是看到当前 scope 无 job 后在另一目录重跑同一 head。补充 background-reset 证据确认旧 metadata 仍 running、日志仅到 12/51、PID 已不存在；新 job 完成 51/51，可作为新一轮结果，不能作为旧作业的可恢复终态。

同一重建链路中，Node 24 下的额外 Vitest 失败被 `npm test | tail` 的 `$?` 掩盖；切回 Node 20 后 root 得到 94/95，唯一失败是并发安装/构建负载下 session restart 5 秒 timeout。owner #113/#114 报告的 95/95、51/51 是其自身代码 head/工作区证据，root 新 job 的 51/51 只覆盖 platform Playwright，不能把两者拼成同一执行者的全绿测试矩阵。

### 5.3 可观测成本和摩擦

`cost-summary.json` 截止 08:04:30 记录 root owner 533 responses、总 token 22,395,717（input 3,944,312、output 223,568、cacheRead 18,168,960、reasoning 92,577）；全 run 3,507 responses、总 token 366,214,602。root 的成本主要被长时间 PBB 安装/构建等待、PR11 旧 head→force-push→合并冲突复验、以及反复处理自写正文通知占用。

过程中的具体浪费点：

- 把自己的 Issue body 更新回执多次当作外部更新，重复查看状态和重写 packet；
- `braid issue/pr comment` 查看和 `--reply-to` 参数多次用错，产生错误调用；
- PR11 先验证 `37338ca`，随后分支 force-push 到 `7b35656`，再合并到包含 M1 的 develop；旧验证不能直接沿用，必须重跑；
- root 使用 `tail` 获取后台任务结果，造成 Vitest 汇总和第一次 e2e 失败细节丢失；后续才从完整日志/新 job 补证。

这些是流程与记录生命周期问题，不应直接归类为产品实现失败；但下一轮应把 job id、候选 head、Node 路径和完整日志入口在启动时写入 packet，正文更新不得让新 session 丢掉待消费终态。

## 6. 开放发现与下一轮判别证据

1. **47 项需求映射：** 生成一张完整 `REQ-ID → Issue #3–#10 → PR → e2e/platform` 表；重点确认 REQ-4/REQ-6 拆分后的共享依赖没有只登记在父模块摘要里。
2. **vision 尾部：** 若 UI 需要引用跨图尾部结论，应从 raw session 的 record 102 或原图片重新取得；canonical view 的 runtime `stopReason=length` 只限定未生成的原生回答尾部，不等同于已存在的可读字段漏读。
3. **PR13 验收：** 分开记录 owner `074f5b9/d62907d` 的 95/51 报告、root PBB 新 job 的 51/51、Node20 94/95 的负载 timeout；在空闲 Node20 环境用明确退出码重跑 backend test，再决定是否合并。
4. **后台作业恢复：** 同一候选启动 PBB 后更新正文，旧 job 必须保留 globalJobId 和终态入口；若取消，metadata、退出原因、新 session 的重跑依据必须一致，不能以 scope 无 job 推断不存在。
5. **共享契约覆盖：** PR13 合并前保留 PR14 `errors.accessDenied`，M4a/M4b 消费 §7.1/§7.2 的 branch/path 编码和 `pathNotFound` 边界；M5 后续已发现 `triage+` 速记错误，说明 47 项需求映射仍能继续发现共享权限问题。
6. **成本控制：** 用一次有界的完整日志收集替代 `tail` 管道；将 root 正文状态更新与长 job 结果消费解耦；把“运行时输出截断”“审查工具显示截断”“作业终态丢失”作为三种不同 receipt 状态。

## 7. 缺失与限制

25 个 owner=issue:1 view 均存在且 record 范围完整；vision 的图片二进制未在 canonical view 中保存，这是材料格式边界而非缺图。vision 结构化最终回答发生运行时长度截断；部分长 PBB/CLI 输出在原生管道中因 `tail` 已丢失中段，不能补称为完整原始输出。其余结论只引用实际读到的 record、board comment 和 root background-reset 证据。

## 8. 冻结 canonical 的字段级补审（最终口径）

在既有每个 view `Record 1..N` 全量读取的基础上，补做了递归字段审计：对 25 个 canonical view 的所有可读 JSON 字段，逐层核对 `message.text`、`thinking`、工具参数命令/内容、tool result 文本、`body`、`patch`、`diff`、错误与 outcome 等实质字段；同一精确字符串只在首个实际来源消费，后续位置保留 canonical record 定位并复用，不把遍历脚本本身当作阅读证据。该审计覆盖 25 个 view、1584 条 record，递归语义投影原始 3,335,563 字符；精确值去重投影 3,092,172 字符，另有已由既有完整 record 消费、无需重复打印的长值和包装元数据。字段级可读内容没有缺口。

明确边界：`id/timestamp/session/usage/toolCallId` 等包装字段按既有 receipt 规则跳过；canonical 中图片二进制只有 hash/类型占位，raw session 才保留二进制。vision record 102 的 `stopReason=length` 只说明原生在该处没有继续生成回答尾部，不代表审查漏读 record 102 已存在的字段；因此把它记录为“未生成的原生尾部”证据缺口，而不是把可读 canonical 字段标为 partial。27 张唯一图片的具体视觉结论仍以 record 41 已消费的 vision 结果为准，尾部未生成部分不外推。

## 9. 结论修订

root-full 的 frozen canonical 可读实质字段现已完整消费。后续使用时应区分三类边界：原生从未生成的回答尾部、canonical 过滤掉的图片二进制、以及工具显示层截断；不能把第一类或第二类反推成已存在但未审查的文本。PR13 当前最终合并状态以主审末尾证据 `e9390cc` 为准；本报告不沿用早期候选或“待合并”描述。
