# 本地与官网评分校准

目标是确定同一交付应用、同一 task 的本地成绩能否预测官网成绩。不同 variant 或不同生成应用的分差不能用来判断环境。本 cell 只记录校准证据与下一步，不改 SVC Corpus 或已冻结的参赛包。

## 已观察

- 官网 `pi-team-mixed/BookStack` run `6e786f33bc1b` 为 13/34。本地用官网该 run 的可下载应用源、同一公开 34 项 ARC 测试重评，得 26/34；19 个用例的通过状态不同。首次本地评测记录在 WSL `runs/parity/mixed-bookstack-local/evaluation/20260923-090434-3fe5f40c/`，逐例差异在同 run 的 `evidence/parity-report.json`。这是同一可下载文本源的比较，仍不是完整字节级等同的官方容器复现。
- 官网与本地构建出的 frontend JS/CSS 文件名与大小完全相同：`index-D3A5dvR7.js`、`index-D0Yaq9jz.css`。官网 source API 未原样返回 `frontend/public/logo.png` 的二进制字节，所以完整应用 hash 尚不能相等；这个 PNG 缺失没有改变当前 JS/CSS bundle。
- 官网 requirement YAML/Markdown 与 WSL `third_party/arc-bench` 现有文件哈希不同：官网 YAML 682 行，本地 671 行。该差异会影响生成任务的输入；本次同应用重评的测试命令并不读取 requirement 正文，不能把 13→26 的评分差额直接归于这项差异。
- 官网日志显示 Runner 镜像 `regt3h8hc.arc-bench.com/arcbench-runner:latest`、Node/npm 构建应用、Playwright 单 worker、每例 10 秒。现有 Docker credential store 没有该 registry，manifest 请求返回 HTTP 401 Basic Auth；精确镜像尚不可取得。本地 WSL 评测使用 Node 20.19.3 与 `@playwright/test` 1.61.1；官网镜像中的 Playwright 版本尚未证实。
- 官网 source API 展示评测后的 `backend/data/data.json`；应用的 `store.js` 首次启动会创建它，测试也会修改它。官网 `workspace-files.json` 中，生成时冻结的 `.factory26/20260922-180358-082ab69d/application/backend` 仅有 `src` 和包文件，没有 `data/`；根工作区却有 `backend/data/data.json`。交付应用的 `.gitignore` 也排除该文件，故不能将评测后数据库当作交付前输入。本地没有把它带入复现。
- 官网 source API 对根工作区与 `.factory26/.../application/` 中的 `backend/src/server.js`、`store.js`、`frontend/src/App.jsx`、`Shelves.jsx`、`Login.jsx` 返回逐字节相同的哈希；至少这些关键源码在冻结交付与评测后之间没有变化。不能再用“下载的是评测后不同源码”解释分差。
- 同一干净应用在 WSL 绑定单核、同样单 worker/10 秒重评后仍为 26/34，失败集合与首次完全相同；证据为 WSL `runs/parity/mixed-bookstack-local-1cpu/evaluation/20260923-091250-7e07faa1/`。仅凭 WSL 多核或一次性时序抖动不能解释 13/34。
- 官网 source API 对 `tests/helpers.ts` 和样本 spec 返回 404；官网测试字节身份尚不可取。WSL 公开仓库的 `@playwright/test` 是 1.61.1，主办方 local-simulation 文档的基础镜像指向 1.57.0；现有证据不足以断言官网实际 Node Playwright 包版本。
- 在隔离 benchmark 副本中安装 `@playwright/test` 1.57.0 及其 Chromium 143.0.7499.4，仍得到 26/34，失败集合与 1.61.1 完全一致；证据在 WSL `runs/parity/playwright-157-run/evaluation/20260923-091908-d2b2e970/`。因此这两个浏览器版本不能解释官网 13/34。
- 2026-09-23 查询公开 `code-philia/arc-bench` 的 `main` 为 `ddc7e40`（2026-09-21），而本地冻结评测源是 `1eb0183`（2026-09-16）。新版本 BookStack 的 `helpers.ts`、四个 spec 和 requirements 均已变化；新版 `expectTextsVisible` 断言在第 134 行，恰与官网报错 `helpers.ts:134` 对上，而旧版在第 137 行。但在 WSL `runs/parity/arc-bench-ddc7e40/` 的隔离副本中，同一应用得到 **30/34**、34 项全部执行完毕，证据为 `runs/parity/mixed-bookstack-ddc7e40/evaluation/20260923-092447-47c42c17/`。因此公开版本差异确实存在，却没有解释官网 13/34；不能把行号匹配当作环境校准完成。原始 pinned checkout 未移动。
- 官网 mixed/BookStack 的 requirement YAML 与 `ddc7e40` 公开 YAML 在统一 CRLF→LF 换行后逐字节相等；官网文件是 682 行 CRLF，公开仓库是 682 行 LF。结合 helper 行号，这强烈支持官网使用相近的新版赛题输入，但仍未取得官网测试源哈希。
- 最新公开版本还改变了 Keep 与 BookStack 两题的 requirements 和测试 helper。因此当前并行 WSL run 若仍用 `1eb0183`，必须按“旧公开测试模拟分数”报告，不能与官网逐点相减。
- 第二个同应用对照：官网 `pi-team-deepseek/BookStack` run `d853830ddb0a` 为 27/34；将其可下载文本源在 WSL 用 `ddc7e40` 测试首次重评为 20/34，证据在 `runs/parity/deepseek-bookstack-ddc7e40/evaluation/20260923-093430-2740b1d9/`，逐例对照在同 run 的 `evidence/parity-report.json`。两边共同失败正好是 7 个 Tags／Edit／Favorite 入口用例；本地额外失败 REQ-6.2.1、6.3.1、6.3.2、7.1、7.2、8.1、9.1。这七项首先是 `page.goto('/')` 的 `ERR_CONNECTION_REFUSED`，说明本地应用服务在测试中途消失；20/34 是不健康的模拟分数，不能拿来推断官网测试宽松。官网 source API 没返回该应用的二进制 logo，但该图的 `alt=""`，可访问名来自相邻 `BookStack` 文本，失败现场也显示 `button "BookStack"`；logo 缺失不能解释这些连接错误。
- DeepSeek 本地应用在 REQ-6.1.3 超时结束与 REQ-6.2.1 开始之间失联，`application.log` 没有异常栈；评测器的正常 `stop(proc)` 只在全套测试结束后调用。事后 `dmesg` 没有对应时间的 OOM kill 记录，故首次退出原因仍未知。随后对同一冻结应用做了一次受控重评，仅在服务全程存活时比较分数。
- 受控重评已完成：WSL `runs/parity/deepseek-bookstack-ddc7e40/evaluation/20260923-094130-6b0306f8/summary.json` 记录 34 项全部执行、27/34，失败的 7 项与官网 DeepSeek/BookStack 完全相同。上次 20/34 的额外 7 项确实是本地服务失联造成，不能当成真实评分差异。这是一个同应用、同题、同失败集合的成功校准样本；mixed/BookStack 的 17 项差异仍未解释，不能据此宣称所有本地评分与官网一致。
- 对 mixed/BookStack 的独立逐例诊断确认：官网 21 个失败均为 10 秒超时，其中 17 个等待按钮、4 个等待页面标题，未见 `ERR_CONNECTION_REFUSED`；本地新版同应用仅失败 4 项，均卡在按钮。失败形态支持“可见 DOM／数据或测试合同不同”，不足以区分具体是官网隐藏测试、部署包装还是初始状态。官网可下载的 `backend/data/data.json` 是评测后的文件，不应作为初始状态植入本地重评，否则会污染校准。
- 官网 mixed/BookStack stdout 与本地新版 `test.log` 的前 34 项测试顺序一致（REQ-1.1、1.2、2.1、2.2、3.1、4.1……9.1）。测试顺序不同不能解释当前分差；同名用例内容是否逐字节相同仍未知。

## 待验证的因果分叉

1. 新版测试仍与官网相差 17 例。官网测试源字节不可取，需在代表用例上确认官方部署、初始数据、测试入口或隐藏的测试改动。不要继续扩大公开版本尝试来猜答案。
2. 检查官网应用部署与数据重置时点、测试工作区及端口合同。测试 helper 的 `firstVisible` 在候选不可见时回退第一个 button，仍可能放大运行态差异，但单核复测已排除简单的 CPU 数量解释。
3. 优先取得官网镜像的不可变 digest 或官方可下载 runner 制品；无来源的近似镜像不能称为官网一致。

同包的本地 GLM/BookStack 8/34 与官网 mixed/BookStack 13/34 属于**不同 variant**，不是校准配对。官网 GLM/BookStack 完成后才能直接比较该 variant 的两处成绩。
