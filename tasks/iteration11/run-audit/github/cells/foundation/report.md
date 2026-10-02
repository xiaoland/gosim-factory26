> 覆盖声明待复核：下文原作者的全读声明尚未验证；主Agent已接手补读。准确范围见根coverage.json，不能将本报告当全文完成证明。

# GitHub iteration11 foundation PR #2 审查

## 覆盖与结论

本次模型核对只能记为部分读取，不能声称覆盖 6 个 PR #2 native 会话的全部独特正文。部分调用出现工具输出截断，脚本还只抽取了字段片段；因此 748 records、1,955,494 字符是 assignment 统计，不是模型已读量。已直接看到的 record 范围与未核对范围见 `read-receipts.json`；本报告中的结论只适用于列出的证据位置。

PR #2 已合入 develop，基础能力总体可消费：Node 20 ABI 路径、seed/权限/错误/copy 契约、临时数据库与随机端口 e2e、干净副本的逐目录 npm 路径最终均有证据。最重要的风险是环境边界曾真实击穿、平台检查缺少候选和作业身份导致并发重跑与长时间排障；这两项若不在后续整合验收层收口，业务模块会再次遇到“代码没变但基础不可用”或无法判断旧结果是否适用的问题。

## 发现 FND-1：Node 双版本造成真实 native ABI 崩溃（高影响，已修复但须保留验收边界）

**原文位置。** 初始开发 API 进程由 Node `v24.10.0` 启动，而 `better-sqlite3` 产物按 Node 20 ABI 构建；`views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 394 原样给出 `NODE_MODULE_VERSION 115` 与运行期 `137` 不匹配、`ERR_DLOPEN_FAILED`，并显示 Node.js v24.10.0。随后 `views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 395/396 显示 `scripts/app-node.mjs` 将 API、web 进程切到 `/usr/local/bin/node v20.19.3`；`views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 39/40 又核对了 `APP_NODE`、`SEED`、cookie 约定。

**决定、动作与后果。** 根因是 portless/默认 PATH 把工具 Node 带进应用进程，安装和运行没有共享同一个 ABI 身份。修复层是 `app-node.mjs`、`dev.mjs`、`e2e/run.mjs` 统一显式使用交付 Node，并在 README/平台文档写清 `PATH=/usr/local/bin:$PATH`；这是基础设施层修复，不应由 M1–M6 各自猜测。修复前开发闭环直接崩溃；修复后 API 监听成功、Vite 就绪，最终平台 e2e 走 `/usr/local/bin/node`。

**边界与下一轮证据。** “平台 npm install 成功”单独不能证明开发运行安全，因为依赖可能已按另一 Node 构建。每个干净候选的下一轮证据应同时记录：安装 Node/npm、应用启动 Node、`better-sqlite3` ABI/加载结果和应用健康检查；若只出现 `Node 20` 的平台日志而没有应用进程身份，结论仍不完整。

## 发现 FND-2：平台检查作业缺少候选/作业身份，导致并发安装、误杀与重复排障（高影响，当前结果已闭环）

**原文位置。** 长会话在 `views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 397 启动了旧候选 `5aa7fd3` 的 clean-copy check；`views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 401 记录另一次平台 `pnpm install` 成功；`views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 394/395 是开发 API 的 ABI 失败/修复；`views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 415/417 显示平台任务长时间停在 frontend npm install，`views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 427 的镜像 packument 请求耗时 60 秒。第二个 native 会话的 `views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Records 25–60 记录了 `a7cc9b5` clean archive、root/frontend/backend 分目录安装、构建、启动和 5/5 e2e 的最终 PASS；`views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 32 另给出同 head 的 38/38 与 typecheck；`views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 60 显示平台整体 `EXIT=0`。PR board `views/pr-2-board.txt` comment #12 将该结果归档为 444 秒、Node 20.19.3/npm 10.8.2、frontend 203 包、backend 154 包、Playwright 5/5。

**决定、动作与后果。** 事实上的作业同时存在旧候选 `5aa7fd3`、中间候选 `52c2944` 和文档同步后的 `a7cc9b5`；长时间 registry latency 使安装过程看似不动，随后多次 poll、kill、重启。`views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 458/459（长会话后段）记录了一个任务被 `-15` 中断、另一候选仍在安装，`views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 460 记录本地 38/38、build、5/5 e2e 成功。中断是排障动作/环境等待的结果，不能归类为应用失败；最终应以候选 `a7cc9b5` 的 clean-copy `EXIT=0` 为交付证据。

重复安装有一部分是合理的：每次 head 变化都需要 clean archive 验证，且 backend native 包不能沿用错误 ABI。但并发执行多个候选、共享 registry/CPU，又没有在结果中绑定稳定的 candidate、job、revision 和日志路径，造成资源争抢、误读旧输出和额外等待。修复层应在开发侧验收编排器：先冻结候选，再串行执行一个有唯一 job id 的平台检查，输出中固定 candidate/revision/toolchain/exit/evidence path；旧作业只能标记 superseded，不能继续作为当前候选结果。该建议限定于开发侧审计编排，不应注入参赛运行。

**下一轮判别证据。** 需要看到一条完整且唯一的 `candidate -> job -> clean copy -> install/build/start/e2e -> exit` 链；若仍出现多个候选同时安装或只能靠“最近一次 tail”判断归属，说明共享基础仍未形成可消费的验收契约。

## 发现 FND-3：共享契约已从设计裁决落到实现、文档和测试（正向证据；下游接入边界明确）

**原文位置。** `views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 39/40 核对 `email_verified`、`commit_parents`、`issue_milestones`、`SEED !== '0'`、cookie 属性与错误契约；`views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 41 记录文档同步后的 38/38、typecheck 和平台检查状态。该会话 `views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 62 还确认 e2e runner 注入 `HOST`/`PORT`，使用与平台启动相同的服务路径。根 Issue 的六项裁决和文档同步在 `views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 10，以及 `views/pr-2-board.txt` comment #8 有完整原文。最终实现、文档和测试结果在 `views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Records 64, 82、`views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 166，以及 `views/pr-2-board.txt` comment #19 对应的合入核验中重复确认。

**决定、动作与后果。** 基础层把 backend 定为纯 ESM JS、密码哈希用 Node 内置 scrypt、seed 默认启动且 `SEED=0` 关闭、按业务键幂等且不覆盖用户数据；session cookie 为 httpOnly/SameSite=Lax、HTTP 交付不带 Secure；字段错误保留首项 `error` 并始终提供 `errors[]`；双父合并和单 issue 单 milestone 的 schema 也同步至 architecture。权限模型明确直接授权、团队授权和团队层级不传播，并由权限矩阵单测覆盖。这样的边界允许 M1–M6 直接消费，而不再各自复刻错误、seed、权限和 native 运行规则。

**边界与下一轮证据。** PR #2 的 38/38、5/5 主要证明基础契约和最小会话闭环；不证明后续模块对每个 seed 注册点、viewerPermission、copy 常量和事务路径的接入正确。每个业务模块应在自己的验收中点名调用共享实现，并用唯一业务 token 做隔离断言；不要把基础 PR 的最小冒烟当作全量业务验收。

## 发现 FND-4：seed、权限、临时数据库和通知交接的可消费性已给出实现入口，但仍需模块级消费证据（中影响）

**原文位置。** `views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Record 143/145 写入 Playwright runner、自有服务、临时数据库和随机端口的 e2e 拓扑；`views/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.txt` Records 308–329 记录 dev API/web health、浏览器注册/登录/账户菜单/登出和清理。`views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Records 39–40, 64, 82 记录 seed 注册表、`SEED=0`、权限 helper、copy 镜像和 38/38；`views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 166 / `views/pr-2-board.txt` comment #19 记录交接、合入和 73 个受控文件卫生核验。通知/交接方面，`views/2026-09-29T05-09-22-198Z_01a0eb91-4896-7103-ab15-33f22ed1e1c6.txt` Records 21, 23 记录根裁决、平台结果、合入后的交接；`views/2026-09-29T05-21-55-869Z_01a0eb9c-c89d-70d6-987e-5012a0cdbf58.txt` Records 25–27 记录合入后 develop 树与授权 head 一致、无交付制品污染。

**决定、动作与后果。** runner 自己拥有服务生命周期和临时 DB，避免污染开发数据；seed 幂等规则允许平台正常启动直接得到初始账户；权限和 copy 合约给业务模块提供单一消费入口；PR 合入后用 `c338578` 作为下游基线，交付卫生没有把 `node_modules`、dist、db 或 requirements 混入。通知写入曾遇到失效调用，但重新进入有效 turn 后 comment #12/#13/#14/#19 的结果和交接均可追溯。

**边界与下一轮证据。** “基础有入口”不等于“业务模块已调用”：下一轮应在每个模块记录 seed 注册、权限响应中的 viewerPermission、copy 常量引用、临时 DB/唯一 token 和服务收尾。出现只在模块文档中声明而没有请求/响应或 e2e 证据时，应判为未验证消费。

## 发现 FND-5：工具故障、上下文重置和重复通知已被区分为设施事件，不应污染应用结论（中低影响）

**原文位置。** `views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 69–80 显示错误尝试 `braid comment create`、随后帮助查询和两次“当前调用已失效”写入失败；`views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Records 169, 174, 175 显示 PR 页的 execution failed 与 context reset、provider session 状态和后续重新核验。`views/2026-09-29T05-22-42-044Z_01a0eb9d-7cfc-7139-9690-5d1ad293d768.txt` Record 15–20 也记录错误子命令、帮助查询和正确的 `pr comment` 接口；`views/2026-09-29T05-23-36-876Z_01a0eb9e-532c-717d-ab89-8add147aa62e.txt` Record 20–24 复述最终 PR 已合入且证据链完整。PR board `views/pr-2-board.txt` comment #14/#19 进一步把 context reset 和合入后的状态分开。

**决定、动作与后果。** 错误子命令和失效写入调用没有改变源码、候选或最终测试结果；context reset 的“execution failed”也不能直接当作代码失败。正确处理是保留原错误、确认写入是否生效，再用当前有效会话重读 board/PR/branch 状态。当前材料完成了这条区分，但工具输出仍曾在多个会话中反复复制，增加了审计成本。

**下一轮判别证据。** 任何“失败”通知都应同时给出 operation、candidate/revision、exit code 或 provider lifecycle；只有能落到应用进程/测试进程和对应候选的失败才升级为应用缺陷。开发侧 run-monitor 可以帮助编排这类证据，但不应作为参赛运行时依赖。

## 发现 FND-6：基础交付卫生没有覆盖 core dump，后续模块可能把运行崩溃变成大体积交付污染（中影响，跨单元已暴露）

**原文位置。** foundation 的 clean-copy hygiene 在 `views/2026-09-29T04-58-28-477Z_01a0eb87-4efd-7459-8477-889fdba3a0b9.txt` Record 33/34 列出的 `.gitignore` 只覆盖 `node_modules/`、`dist/`、数据库、测试输出、日志和环境文件，没有 `core.*`、`*.core` 或等价的 core dump 规则；该 view Record 34 的受控/ignored 文件清单因此不能把这类产物视为基础交付卫生的一部分。实际下游 M3 报告 F1 已记录 PR 中出现约 363 MB 的 core 文件并后续清理，说明这不是纯理论风险（见 `/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github/cells/m3/report.md`）。

**决定、动作与后果。** 共享基础的 `.gitignore` 与平台/PR hygiene 检查应把 core dump 当运行产物处理，并在发现 native 进程被杀或崩溃时保留产生者、信号和清理动作的证据；这属于开发交付层，不应把 core 文件静默混入业务 PR，也不应在没有 signal/producer 证据时把它归因给某个进程。当前 M3 已完成清理，但 foundation 原始边界未覆盖该类产物。

**下一轮判别证据。** 干净 archive 的交付清单应明确排除 `core.*`、`*.core` 及平台生成的诊断文件；若发生 core，报告必须同时给出 signal、进程身份、生成路径和是否进入 Git/候选，否则只能标为待证的实现侧假设。

## 覆盖边界与遗留问题

- 本单元只对 PR #2 的部分 native 会话正文及 `views/pr-2-board.txt` 做了直接核对；未把 coverage 统计当作模型阅读证明。
- 在已直接看到的记录中，clean-copy 平台 PASS、38/38、5/5、typecheck/build 和合入树一致性有原生会话/board 位置；中途 `-15`、ABI 崩溃和失效工具调用均按设施事件与应用事件分开归因。其余 records 尚未完成全文核对。
- 后续整合验收仍需补：候选冻结与唯一 job/revision 绑定、所有下游模块真正消费 seed/permission/copy/错误/Node 契约，以及最终候选的全量平台路径。
