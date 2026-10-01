# PR 2 基础层全过程只读审查

## 范围与方法

coverage.json 截止 `2026-09-29T08:04:43.268468Z`。选中 cwd `pr-2` 的 32 个源，共 2,141 行；另完整读取原材料 `evidence/base-readme.md`（160 行）和 `evidence/git-history.txt`（273 行）。所有 JSONL 均按真实行序读取；索引、关键词命中和截断显示只用于导航。414 行 headerless native continuation 已与带 session header 的 47 行前缀分别纳入，未把它当作可略 artifact。逐源范围见 `read-ranges.json`。

阅读顺序是：根 Issue 的 D1–D3 与契约 v1 → PR 2 设计、advisor/vision → 基础实现 → Node/SQLite、平台路径、冒烟和冷副本排障 → v1.2 的 9×26 到 6×26 收敛 → merge 698afd2 → 合并后作为共享契约顾问处理 C/A/B/D-C14 的边界。此次没有修改源码、应用或测试，也没有运行测试；报告中的检查结果均来自已保存的原生会话工具结果。

## 总体判断

PR 2 的边界基本守住：交付 pnpm monorepo、共享类型、可重复迁移、幂等 Q3 Sales 种子、基础 API 1–6、选区和活动工作表端点、同端口静态服务、ARIA 网格、Vitest/Playwright/平台路径检查；业务层的工作表管理、行列结构、公式、范围、CSV 和数据组织留给后续 Issue。根契约从 Issue #1 comment #1 形成，v1.1 在派发后续业务前补齐 0 基索引、updatedAt、越界写入 400、粘贴扩张归 D、Node/SQLite 版本事实，v1.2 再将默认结构从 9×26 改为 6×26 并增加双向总量守卫。

审查没有发现应把 PR 2 认定为源码缺陷的证据。确有两类真实反馈：Node 20 下 better-sqlite3 13.0.3 会段错误；平台检查首轮因脚本只停 npm 直接子进程而留下孤儿 node。前者通过精确锁 12.6.2 和重新安装处理，后者修脚本递归停机后通过。另有 1000 行下朴素 Playwright `A1` 查询命中 112 个元素的真实验收失败，最终按根契约裁定改为 6×26；advisor 指出的“理论值 111 与实测 112 的差 1”没有形成独立故障证据，不能过度推断为额外渲染 bug。

## 关键契约形成链

### 根决定到 v1.1

根 Issue 先处理 requirements.yaml 的结构性损坏：308 个场景 WHEN/THEN 被同一占位短语替换，只有 ATOMIC 描述仍完整。D1 将 ATOMIC 描述定为验收权威，场景只提取种子数据和具体值；D2 选 Q3 Sales、Sheet1 A1:C4、A5:C6 空、Sheet2 空白；D3 定 React/Vite + Express/better-sqlite3、独立网格/公式引擎、SQLite 持久化。共享契约 v1 则固定表结构、事务、raw 原文、快照、选区矩形、错误体和 ARIA 角色。

PR 2 在 v1.1 形成后消费这些约束：row/col 0 基，A1=(0,0)；内容写入、导入、重命名、创建更新 updatedAt，选区和活动切换不更新；越界 cells/state 返回 400 且整批不落库，基础层不自动扩张，粘贴扩张归 D；better-sqlite3 12.6.2 作为平台 ABI 基线。后续 B、A、C、D 均能从 packet/README 找到这些入口，说明契约确实从根决定进入 Git 文档和实现，而非只停留在评论。

### 9×26 到 6×26：实际证据与猜测分开

- 实际证据：PR 2 初始实现和 packet 采用 9×26；smoke 使用朴素 `getByRole('gridcell', {name:'A1'})`。保存的浏览器实测是在 1000 行时同名查询 strict mode 命中 112 个元素；9 行只由选择器规则推出“当前初始 DOM 不含 A10”的风险缓解，未被这次 1000 行实测直接覆盖。
- advisor 的实质判断：6 行比 9 行多保留三次结构插入后的朴素定位余量；但也明确指出隐藏验收可能使用 exact/属性选择器、a11y 快照、总 DOM 数量、滚动性或 API rowCount，不能把“参考实现必然 ≤9 行”当作事实。
- 根侧决策：requirements 没有 ≥10 行或 Google Sheets 默认 1000 行的 ATOMIC 要求，v1.2 将默认结构固定为 6×26；同步 config、README、app tests、platform script 和 smoke 的 6/26 精确守卫。后续结构操作超过 9 行时，验收必须使用 `exact:true` 或 aria-label 属性定位。

因此 6×26 是对当前验收证据和契约空白的风险折中，不是证明产品应永远只有 6 行；“看起来像 Google Sheets”是视觉参考，不能单独推翻没有尺寸要求的 ATOMIC。越界写入保持 400 也不是实现偷懒，而是 v1.1 明确把结构增长交给 D/B 端点；advisor 提出的“越界自动扩展”属于替代方案，未被根契约采纳。

## 重要发现（原文 → 动作 → 后果 → 原因/竞争解释 → 归属）

### 1. 原生 SQLite ABI 风险是真实环境缺陷，版本锁定有效

- **原文与动作**：PR 2 主会话实测 Node 20.19.3 + `better-sqlite3@13.0.3` 安装后 `require` 成功，但 `new Database()` SIGSEGV；12.6.2 和 11.10.0 在 Node20 读写正常，Node24 也正常。这个版本/Node 组合相关的现象支持原生模块 ABI 或预构建包不兼容等候选解释，但没有底层栈，不能称为已定位根因。advisor artifact `3ebac...advisor_0:43` 据此反对 WASM，建议精确锁版本；最终 README 明确锁 12.6.2，并说明 Node24 安装的 node_modules 不能跨 ABI 复用。
- **后果**：平台路径按 `/usr/local/bin/node` 重新 `npm install` 后可加载 SQLite；开发路径仍用 pnpm/Node24。WASM 未引入，因为其手动 export 持久化会在进程崩溃时丢最后一批事务，反而破坏重启持久化。
- **原因与竞争解释**：现有证据只把问题范围缩到 Node/原生模块版本或安装产物的兼容性，不能排除预构建包、工具链或其他运行时差异；它没有证明 Express、迁移逻辑或某个具体 ABI 符号是原因。未来平台无法访问 prebuilt、没有 node-gyp 工具链、或升到未覆盖 Node 版本，仍可能改变选择。advisor 曾建议提交 npm `package-lock.json`，但最终 README 有意不提交它，理由是开发镜像源的 lock 会污染平台网络；当前实际防线是精确 package version + 平台重装，而不是锁文件。
- **归属/下一证据**：PR 2 负责版本和平台证据；后续基础设施若改变 Node 入口，须重跑独立安装/加载/重启读写，不应只看 npm engine 警告。

### 2. 平台首轮失败是检查脚本停机缺陷，应用事实被独立保全

- **原文与动作**：平台路径首轮在前端安装、build、后端安装、SQLite load、启动、seed 和 HTTP 检查后，重启步骤报端口仍被占用；原始日志显示脚本只杀 npm 直接子进程，孤儿 `node src/index.js` 已被 ppid=1 接管。PR 2 修 `checks/platform-path.sh`，改为递归停止 npm→sh→node，并保留 first-round fail/run2 日志。
- **后果**：修复后 Node20.19.3、逐目录 npm install/build/start、同端口 SPA/API、seed、编辑后重启、错误体和 cleanup 全部通过；根评论 #18 采信“脚本缺陷而非应用缺陷”。
- **原因与竞争解释**：端口残留直接来自测试设施的进程树处理；不是把失败简单归类为环境问题，因为实际工具输出定位到了孤儿 node。仍不能据此推断所有平台环境安全，端口占用、安装时间和 prebuilt 下载仍是外部前提。
- **归属/下一证据**：PR 2 负责脚本 cleanup 和平台路径；后续新增服务检查应证明 owned-process cleanup，而不是依赖全机无 node 进程。

### 3. 6×26 收敛是验收风险修正，但其前提是可疑的验收驱动推演

- **原文与动作**：有两种需分开的证据。其一，保存的浏览器实测是在 **1000 行**时以朴素 `getByRole('gridcell', {name:'A1'})` 查询命中 112 个元素；这是前缀子串匹配的真实失败样本。其二，初版默认 **9×26** 本身没有被这条 1000 行实测证明失败；“插入后超过 9 行会遇到同类前缀风险”是根据选择器规则作出的风险推演。advisor 进一步指出 6 行能容纳结构插入后的朴素查询余量。根 #15 将 v1.1 的 9 行正式修为 6 行，PR 2 更新 `config.js`、README、测试和 smoke 总量守卫。
- **后果**：最终 head `0a08fdd` 的开发路径 backend 20/frontend 16 passed、smoke 3 passed，6 rowheader/26 columnheader 精确守卫可防上下漂移；后续 B 的结构操作超过 9 行时由 B 测试切换 exact 定位。API 仍显式持久 rowCount/colCount，未把网格或引擎能力限制为 6 行。
- **原因与竞争解释**：6 是针对 ATOMIC 坐标上限和一个假设中的非 exact 外部 harness 的风险折中；不是推断 Google Sheets 产品只需 6 行，也不是因为自研引擎只能处理 6 行。根的 v1.2 原文明确承认需求没有初始维度、26 列也没有需求明示，且“越界 400”是我方契约；它把“若外部 harness 使用朴素定位且与参考实现自洽”作为条件，而没有真实外部 harness 证据。advisor 对 1000 行命中 112 而理论 111 的差异只提出核查建议，后来没有证据证明多渲染一行，应保持不确定性。
- **归属/下一证据**：PR 2 负责默认常量和自建 smoke/平台守卫；B/A 负责结构操作/导入增长。实际 9→6 的后续动作是修改 `config.js`、smoke 的 6/26 总量断言、`app.test.js` state 载荷与 `checks/platform-path.sh`，并重新跑 PR2 的冒烟和全新副本平台路径；这些证据只证明 6×26 自洽通过，不能证明 9×26 会损害产品或外部验收。若产品后来明确要求滚动性或 ≥10 初始行，应重新开契约决策并调整定位纪律。

**独立判断**：这不是已证实的产品缺陷。已知真实失败是 1000 行下自建 Playwright 的非 exact `A1` 查询命中 112 个元素；需求没有初始尺寸，也没有外部评测器使用非 exact 定位的证据。自建 smoke 本可统一改用 `exact: true` 或 `aria-label`，因此把默认产品尺寸从 9 收紧到 6 主要是在为自建验收选择器和一个未证实的隐藏 harness 假设优化。6×26 的新构建/冷验证通过说明改动可行，但没有给出“必须改 6”的因果证据；应把它记录为验收驱动的可疑过度收敛，保留“无产品损害证据”的结论。

### 4. 主动 advisor 既产生了有效决策，也暴露出合并后回唤醒成本

- **有效反馈**：早期 advisor 改变了两个关键选择：better-sqlite3 精确锁定、纯 JS ESM 零构建；第二轮 advisor 质疑“参考实现必然 ≤9 行”的假设并把 6 行的增长余量说清楚。vision artifact 只提供首页/编辑器布局观察，并明确截图不是英文文案和功能契约。
- **合并后有效反馈**：基础负责人在 C/#5 将 `shared/` 从纯类型变成运行时模块后，实测前端显式 `.js` 导入在 `allowJs` 未设时 TS7016；`allowJs` 方案可行但需归 C/PR10。进一步探针发现前端 `allowJs` 没有 `checkJs` 时，shared JS 同时使用 `document`/`process` 仍 exit 0；后端 checkJs 才会报错。该反馈催生 D-C14 独立 `shared/tsconfig` 静态门，最终归 PR10，并要求门在 `SKIP_FRONTEND_BUILD` 之外、include 同时覆盖 `.js` 和 `.d.ts`。
- **低收益回唤醒**：PR 2 合并后多次被 issue comment/回执重新唤醒，只做 `git diff`、正文状态和归属核对；在 #69/#70、B/C/A 的后续消息中基础层反复确认“无动作”。这些是正常协作中的边界守护，不能直接认定 Harness 缺陷，但重复读取、queued receipt、`sleep 60` 监看和无动作回复占用注意力。有效规则是：收到新契约事实或能改变基础层状态的证据才复核；纯投递回执和已确认的归属可引用首次原处。
- **归属/下一证据**：PR 2 只保持冻结；运行时 shared 模块和静态门归 C/PR10，A/B/D 的消费回归按各自 packet 负责。基础层不应为后续模块预先开窄 PR。

## 验收、Git 完整性与冷副本

PR 2 先在候选上完成 backend 20、frontend 16、build、Playwright smoke；v1.2 后重新以全新副本和临时 DB 验证 6×26。`698afd2` merge parents 为初始化 `2914d2d` 与 PR head `c344b3b`，合入树与候选树 `ce7b5e6` 逐字节一致；因此合入没有冲突漂移。Git history 还显示后续业务 PR 是在该冻结基线上继续，而不是回写基础实现。

重复 cold 的有效部分是：平台 Node20 的全新安装、开发 Node24 的 frozen install、临时 DB 重启、seed 不重复、编辑 B2 和选区持久化、SPA 深链、统一错误体。无效/低收益部分是同一 6×26 证据多次通过后台延迟回显重读，以及一次参数错误的 with-service 调用后再重跑；这些应保留原始失败和最终结果，但报告只引用首次原因与最终成功。

## 后续消费边界

1. A/#3 消费 0 基坐标、state 不变量、updatedAt 和幂等种子；其 CSV 足迹不得被基础层默认尺寸误判为固定 6 行。
2. B/#4 消费显式 row/col 结构端点；结构增长超过 9 后使用 exact/aria-label 定位，并在其事务内迁移范围和 selection。
3. C/#5 负责公式求值、raw 引用重写及 shared runtime；`shared/tsconfig` 静态门和 `.js` 环境中立证据归 C/PR10。
4. D/#6 负责粘贴扩张、范围和 undo/redo；基础层只提供 state 回放端点及越界/事务不变量。
5. E/#7 消费 validation/filter/pivot 模型；基础层没有提前实现业务行为。

## 限制

本 cell 只覆盖 coverage 中 cwd `pr-2` 的 native/相关 artifact，并补读 base-readme 与 git-history；未把其它 PR 的全部原生链路纳入。所有选中源在 `read-ranges.json` 标为完整行范围，未读/截断为空。报告不把原生会话中的成功结果当作本轮重新执行的测试。
