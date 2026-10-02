# Sheet 58 分新产物：隔离行为核对

状态：已完成有界复现。旧回放 `1efffb84ae1b` 和新回放 `fbcbda090229` 都是 58/100，但功能项分别为 8/24、7/24；官网没有逐例结果，不能据同分推定同一组失败。这里只报告从公开需求和新交付应用独立观察到的行为，不代替官方评分。

## 来源与条件

新输入为 `runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/sheet-artifact-replay.zip`，ZIP SHA256 `7cbb458d7d351d8149e8e72013b60fef5a8b12582fbb80eb94b138fd6c93ebca`。按内含 `replay-manifest.json` 提取并逐个校验了 113 个应用文件；manifest 的应用身份 SHA256 为 `9022b53b7a827a3dd29df7477a5645e2207450fb0aa25efd97ae0a527ac7f28f`。公开 `requirements.yaml` SHA256 `9cddf67be50748106289ed158648629a6c50c30a490d0eda5bd570c557440b96`，与旧轮相同。新交付 `main=3fb842a46362c6c676bb2e99f92453d46f8394d9` 来自官方回放记录；提取包没有 `.git`，故本次隔离复现独立核验的是 ZIP 文件身份，并未由提取目录重新验证 commit 关联。

应用文件原样提取到 `/tmp/factory26-sheet58-7r8aceep/app`，前后端 `npm ci`、前端 `npm run build`、`node@20.19.3 backend/scripts/prepare.cjs` 完成。以 Node 20.19.3、`HOST=127.0.0.1`、`PORT=48620`、全新 `DATA_DIR=/tmp/factory26-sheet58-7r8aceep/data` 启动独立服务。该目录、端口和浏览器会话仅供此次诊断，未接触冻结运行的数据目录或修改生成应用源码。构建发生在 macOS，官网运行在 Linux；这里的行为结果不冒充官网逐例环境。

原有 [`repro.mjs`](../repro.mjs) 直接运行时在第 20 行因 `body.worksheets[0]` 报 `TypeError`，因为新应用 GET 工作簿返回 `sheets`。这是旧诊断脚本与新 API 形状不兼容，不是产品行为失败。为保留相同判别问题，只在临时目录写了适配脚本 `/tmp/factory26-sheet58-7r8aceep/repro-adapted.mjs`，输出 `/tmp/factory26-sheet58-7r8aceep/result.json`。它在全新数据目录中读取默认 `Q3 Sales`，另建 `Diagnosis probe` 工作簿执行旧的混合值透视和数字验证探针；没有改变应用、需求或判据。脚本输出的 `active=Sheet2` 是浏览器先点击 Sheet2 后读取的状态，**不是首次打开状态**；首次打开的 Sheet1 已另由可见浏览器操作确认。

## 旧缺口重测

| 判别问题 | 新产物实际结果 | 与旧轮关系及界限 |
| --- | --- | --- |
| 默认 `Q3 Sales` | 首次从首页打开 Sheet1：A1=`Region`、A2=`East`、B2=`1200`、A3=`North`、B3=`800`，B1/C1/C2/C3 等为空；手动切到 Sheet2 可见 `Region/Sales/Status` 表头及 East/1200/Open、North/800/Closed、South/700/Open 三行。API 与可见 UI 相互印证。 | 旧轮只有 A1 的缺口已改变，不能沿用“A1-only”归因。REQ5 的若干 GIVEN 指 `A1:C6` 种子，但未明确在 Sheet1，WHEN 又含占位文字；完整表在 Sheet2、默认进 Sheet1 是入口风险，不是可直接判定的需求违约，也不能换算为 26 个失败。 |
| 含可解析数字和 `N/A` 的透视 SUM | 独立工作簿 A1:B3：East/1200、North/N/A。创建透视与设置 SUM 均 HTTP 200，输出 East=1200、North=0、Grand Total=1200。 | 旧产物同类请求 HTTP 400 `Value field requires numeric values`；这一旧缺陷在新产物已修，不能解释新一轮已知失分。 |
| 0–100 数字验证后写 `=101` | 规则设置 HTTP 200；写入公式 HTTP 200，持久化 `{raw:"=101", value:"101"}`。 | 旧轮也允许。公开 REQ-5-2-1 描述了无效输入须被拒绝，但没有明确数值验证应在公式计算结果哪个阶段执行；这是待澄清的语义候选，不能列为无歧义违约或官方失败。 |

上述公开契约见 [`requirements.yaml`](../../../runs/hackathon-capabilities/research/requirements/sheet/requirements.yaml) 的 REQ-5-1-2、REQ-5-2-1、REQ-5-3-1。新产物 `checks/req5-data.spec.ts` 通过内部 API 自建工作簿并填入 A1:C4，因而它的 PASS 不证明从默认 `Q3 Sales` 起步的路径；同时，这种局部 setup 本身也不是产品错误。

## 三条可见交互

在隔离服务上从首页点击 `Q3 Sales` 后，执行以下实际鼠标/键盘操作，并在需要处读取持久 API 状态：

1. 切到 Sheet2，从 A1 向 C4 鼠标拖拽，辅助树显示 12 格被选中。原有自检以 Shift+方向键选区，不能据此推断拖拽能力缺失。本次没有验证拖拽后的复制粘贴；一次通过自动化剪贴板的粘贴尝试没有提供可用剪贴板内容，不能算应用失败。
2. 选中表格后经 Data → Create filter → Status，取消 `Closed` 并应用。界面隐藏 North/Closed 所在第 3 行，保留 East/Open 与 South/Open；`GET .../filter` 返回 `hiddenRows:[3]`，源数据 Sheet2 A3 仍为 North，刷新浏览器后筛选仍在。此路径支持筛选、隐藏而不删源行、刷新持久化；未测 CSV 导出和透视在筛选后的语义。
3. 选中 Sheet2 空白 E1，经 Data → Data validation。辅助树显示 `Rule type` 可选控件；选 `Number range` 后，`Minimum`、`Maximum` 均为 text field，而非 spinbutton。改选 Dropdown，输入 ` Red , Blue ` 并保存后，E1 显示 `Open dropdown for E1` 控件，打开列出 Red、Blue。辅助树把下拉内容聚合为一个 `Options for E1` 节点，未枚举单个 option 的 ARIA role；**本次不能证明 option role 存在或缺失**。

三条操作没有新增可无歧义指向公开需求的产品违约。它们反驳“旧混合透视错误仍在”“自检只用 Shift 说明鼠标拖拽失败”“控件必然是 spinbutton”这几种推断。默认入口的表分配和公式越界仍是不确定问题；不应从本次少量正例推断其余 42 个官方失败不存在。

## 对评分归因的限制

新旧 requirements 相同、总分相同，只说明两个交付在聚合结果上相同。新种子已经改变，旧混合透视已修，几个可见交互正常，故**旧轮的已证缺陷不能直接充当新轮 58 分的原因**。新根对相互冲突种子作出 Sheet1/Sheet2 折衷，其实现和 `checks/req5-data.spec.ts` 使用的前提一致；自检 PASS 可以证明这些前提下的行为，但不能独立验证折衷对应官网场景入口。这里的判据闭环风险有原始证据，却仍不足以解释 42 个失败或 7/24 的项目映射。

要进一步区别解释，需要针对公开 24 个 ATOMIC 的入口、状态、动作、结果做独立抽样，并明确官网是否逐例准备 GIVEN 数据、默认打开哪张表。官方逐例报告未提供，本次没有访问隐藏测例、重评分或扩大为全套场景测试。
