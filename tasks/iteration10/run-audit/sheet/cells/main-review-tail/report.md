# 主索引 34、36–39 原生审查

覆盖：5 个 SID、882 条原生记录，按时间和消息顺序读完。精确来源范围及机械省略见 `coverage.json`。以下 `061/065/067/069/075:Lx` 均指 `continuation02-root-native/` 下同序号 JSONL 的原生行；不是渲染文件行。会话 39 尾部的 148 次相同模型 429 与 33 条后台结果逐条登记，重复报错内容精确去重。范围内未运行实验、测试或改源码。

## #6 公式引擎安装路径：先发现真实 clean-clone 失败，再补前端先行路径

- `061:L28–41`：#6 首版取消提交 `shared/formula-engine/dist` 后，clean clone 的 `backend npm install && npm run start` 因 `Cannot find module 'hyperformula'` 失败。直接导入亦得 `ERR_MODULE_NOT_FOUND`；`file:` 依赖链接回共享引擎真实路径，那里缺运行依赖。因此“已有 dist”不能证明安装路径可用。这是实测失败，非推测。
- `061:L52–87`：#6 加共享引擎依赖安装和构建 bootstrap 后，第二次 clean clone 的 backend 启动、seed、公式 API 烟测 `A1=2/B1=20/C1=22`、formula API 8/8、前端构建与 Vitest 33/33 成功；`061:L90–107` 创建 PR #12 并向 #5/#6 反馈。该证据仅覆盖当时的 backend-first 顺序。
- `065:L5–9`：root 指出平台实际 **frontend install/build → backend install/start**，所以前一证明不足。#6 将 bootstrap 抽到 `scripts/bootstrap-shared-engine.cjs`，接上 frontend `prebuild`、backend `prestart`（`065:L16–30`）。在无 `dist/node_modules` 的 clean clone，frontend-first build 成功且生成共享引擎依赖/产物，backend 随后启动并完成公式值与 8/8 API 检查（`065:L31–52,L73–74`）。该 SID 结束时 Vitest 后台尚未回报（`065:L75–81`），不能把这轮说成全绿。`075:L82–83` 表明 PR #12 后来已在 develop；具体合入审查由主账定论。
- `065:L53–72`：宽泛 `pkill -f` 多次杀掉命令自身，随后 4831 仍返回 200。不能据此证明目标服务已停止，也不能给剩余响应指定所有者。这是验证环境清理的不确定性。

## PR #13、#11：本段准备复验，合入事实由后续原生行补齐

- `067:L5–21`：PR #13 把 FormulaBar Enter 的重复提交修复和 REQ-3 core 检查带至 head `2ecf101`，diff 限于相关文件；#6 注意到 moveCells 分支已有 cherry-pick，准备独立复验，但 `067:L36` 结束时仍在检查安装条件。本 SID 无独立测试通过或合并动作。`075:L12` 可见 PR #13 后来以 `3e55813` 合入。
- `069:L14–18`：PR #11 CSV 检查在读取预期导出值前等待 A4 显示 `3`，修复公式回填时序竞争；head `2ecf69b` 仅检查文件 6 行增 2 行删。`069:L26–27` 只开始准备独立工作树，未在本 SID 复验/合并。`075:L12` 可见 PR #11 后来以 `ff1c2a2` 合入。测试等待修复不能证明 CSV 产品逻辑曾有缺陷。

## #4 工作表：API 测试自错已改；UI 崩溃被局部修复，但此 SID 未形成最终交付

- `075:L17–29`：rebase 后结构单测 13/13；最初 `checks/api-req2.mjs` 有模板字符串闭合笔误，导致 API 检查根本无法运行。修正后首次 fresh 检查 52/54，两败均在 restore 用例（`075:L38–48,L110–115`）。忠实新环境重放（`075:L126–132`，尤其 `L131` 实际输出）证明两处断言自身错误：`insert-above(1)` 后行 1 空、Region 在 A2，删行 1 与预期不符；PUT 补 `validationId/style:null`，使 `JSON.stringify` 与旧裸 cell 不等。测试改为删行 2、按 `{raw,value}` 比较，fresh API 54/54（`075:L132–139`）。这是测试错误修正，不是产品修复。
- `075:L140–255`：首次完整 `checks/run.sh` 实际 `EXIT=1`；后台最终 `29 passed, 1 skipped`，worksheet 7 项失败（`075:L540`）。初读旧 `test-results` 中 Chromium `Socket path too long` 误把原因归于环境（`075:L230–250`）；agent 随后核对本次 `checks/results/20260928T070435`，发现当前失败是 `Add worksheet` 后 tab 不出现（`075:L251–255`）。旧 artifacts 不能作为本次失败的归因。该套运行期间代理又修改并重建前端，故整个 16 分钟 suite 也不是同一不可变版本的最终回归。
- `075:L269–317`：使用短 TMPDIR 的浏览器重现 `Unknown worksheet id`：后端已持久创建 Sheet3，但前端在新 activeSheetId 的 render 里仍以旧 state `engine` 调 `displayMap`，新工作表未在旧 engine 中，导致崩溃。代理把 engine 改为依据 `contentSignature` 同步 `useMemo` 计算；构建通过。`075:L318–327` 显示修复后的 bundle 能加载已创建 Sheet3、再增 Sheet4/Sheet5 并选中，清空旧 console 后没有新错误。这是局部行为反证，但此修复仅在未提交工作树，随后被 stash（`075:L409–412`），不等于已交付。
- `075:L328–350`：agent-browser 点击菜单 Delete 未弹对话框、DB 仍五表；代理怀疑工具 stale ref，尚无定论。不能写成产品删除确认框缺陷；需要可重复的浏览器 trace 或后续测试。
- `075:L351–408`：专项 Playwright 初次缺全局必填 `BASE_URL_CREATE`，没有执行测试；补齐后 7/7 失败（后台终局 `075:L585`），其中 Add 用例 error-context 明示已在 Sheet3 editor 中，却在 `page.reload()` 后再调用只适用于主页的 `openWorkbook`，等不到主页 listitem（`075:L390–397`）。代理改掉 7 处该模式，将真正“从主页重开”单独保留（`075:L399–406`），commit `07895e0`（`075:L407–408`）。修改后 **没有成功的专项再跑**，所以不能把 7/7 当产品全败，也不能把 spec 修正当已验证全绿。
- `075:L377–389`：REQ-5 PR #9 已到 develop `83f9e38`；#4 计划复用其 `shiftRangeSpec`，存储层规则/筛选/透视 range 均为 A1 字符串。`075:L409–430` 开始 rebase，冲突在 `backend/src/server.ts`、`Grid.tsx`、`EditorPage.tsx`；前两处已处理，最后一处尚未处理。`075:L431–614` 从 07:41:37 到 08:11:51 连续 148 个相同模型 429（资源耗尽）；其间仅收到后台结果和重复 issue 更新，没有可见代码动作、完成 rebase、push/PR 或最终复验。因此本 SID 截止 **#4 未完成**，须与后续 SID 的最终状态分开判断。

## 可操作判断

1. 全局 #4 结论应以更晚 PR/合入/同版验证为准。本段证实真实 UI crash、修复思路和临时浏览器通过，同时证实 rebase 卡在未解决冲突，不能以 54/54 API 或 29 passed 宣告整项完成。
2. 验证记录需保留运行的版本、服务器与产物的对应关系；诊断时先核对当前 run 的结果目录。这里旧 Chromium 错误与 `reload` spec 错误都曾覆盖真实信号，后又被原生日志反证。
3. 对模型 429 耗尽，应由续跑接管未完成的 rebase/验证，不能把后台结果自动视为代理已经整合或上报。当前迭代 10 的 PBB 注册、完成投递与 idle drain 修复可能改善后台结果送达；是否能处理连续模型资源耗尽造成的未提交冲突，需要后续运行证据。
