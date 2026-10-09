# 夜间实验：当前独立判断

2026-10-03，北京时间。**推荐首轮 Flash/e2e 官网完整生成，同时验证实际工具采用与 OOM；随后独立审阅，仅修明确机械缺陷。构建先从保留 Linux runtime 派生，不先建设 Linux 构建域。** 实验设计仍待复核，未授权启动；本 cell 只保存决定、理由及未验前提。

## 有限串行实验

优先级为 e2e > reviewer/cleaner > GLM-5.3，本夜只做 GitHub。固定新版需求 SHA `9480921cb3b7ffdc5f32cb76011ecc1d5bf9bfbf2cba38e3a092355ac88a54f8`。GitHub 好结果仅支持向 Sheet 迁移的工作假设，不是 Sheet 成绩实证。历史 74 分及其应用不进入新生成输入。

最多三个有模型的候选机会，同时仅一个生成/改进阶段。废弃后重新生成占新机会；冻结的请求 fallback、同一执行明确接续、评价输运重入不增加候选。采用 self_funded、关闭比赛额度；官方反馈不进入生成或修复 Agent。

| 顺序或触发 | 动作与判断 |
| --- | --- |
| 首轮 | Flash/e2e 干净起点，官网完整生成、交付和评分。普通 baseline 不作为启动前置。 |
| 首轮应用 A 冻结后 | 另一个 Hosted run 消费 A，独立审阅并只修证据闭合的机械缺陷；有 B 时由这个 run 完整评分，已有有效分数不再 replay。无合格修复只发布 audit 终态，不重新交付 A；平台仍可能执行失败的后续评测步骤。 |
| 仍有明确比较问题且候选已预定 | 第三机会择一：同条件普通 baseline 比较工具方案；保留 e2e 的完整 reviewer 比较独立收口；已定位上下文窄修后的同根 e2e 复验。不能展开成三条队列。 |
| 首轮明确设施故障 | 范围内一次针对性修复后仍做官网完整 e2e；若需重新生成，占第二机会，剩余第三机会可审阅。原因未知或同错反复则保全并通知，不盲目换根。 |
| 无判别性疑问、只有语义/证据缺口、候选未准备好 | 结束并汇报，不凑满第三次，不默认启动 GLM。 |

同条件对照固定平台、根/成员、需求、Braid/Pi、共同材料、资源及供应商政策。e2e 包含浏览器版本变化，应解释为工具方案比较，不能将全部效果归因于 MCP。cleaner 只有能解决已证实的整理/重复成本且预先冻结时才进入分支；不同时改工具、角色和模型。不用任意高分阈值决定改 prompt。

## 自动修复的边界

机械修复需有明确公开约定、可重现违例和不需重新裁决语义的修正方向。语义不明、历史条件缺失或证据链不完整的项必须保留原内容、来源与不确定性，不删除、隐藏或改称已解决。一轮修复可完成既定机械缺陷集合的修改与必要回归，但不根据第二份官方分数继续针对性修补。

用户已允许直接修正明确上下文冗余、重复和无必要打断。可以删除确定重复的呈现或触发，必须保留事件身份、必要关联、新信息送达及未决事实；不能以“减少幻觉”为由丢弃矛盾证据或改订阅/生命周期。已完成的简短通知及 `a31eb888` 两技能改写进入共同基线，不再追加同义要求。[协作材料](../../collaboration-requirements/packet.md)已表达完整义务、原要求、真实入口和完成证据；仍需验证实际采用。

增量 A→B 应消费冻结应用和同份需求，用独立 native 工作目录完成审阅/修复，再发布派生应用；不迁移 completed Braid。此前 reviewer 入口从空应用初始化，不能据名称推断已有种子能力；当前具体入口由其 owner 收敛。若增量入口不成立，只有预先复核的完整 reviewer 候选可替代，并说明两者回答的问题不同。

## 第二轮承载：采用独立 Hosted seed audit

**推荐候选①，纳入实施复核；不先建设 Mac reviewer runtime。** 第二轮复用本夜本已需要生产的 Linux runtime、官网派发和取证路径。Mac `runtime.py prepare` 只准备 npm/cache，尚无完整 bin/node、Braid 与冻结来源；另建跨平台 runtime 只为让无改动审阅显示平台成功，不能改善审阅证据，反而增加本夜关键路径。此选择新增 seed/audit 发布分支，不是现成 `generation_only` 能力。

现有 `reviewer/run.py` 将工作区置于 output/.factory26，在最终 `deliver()` 才复制应用到平台交付根；因此可以在本地 Harness 分支控制“只发布 B”。seed A 只进入独立工作区，不能预先复制到交付根，也不能让 history preview 提前交付 A。合格机械修复及验证成立才调用应用发布和 deliver，绑定 A→B；同一 Hosted run 随后的有效评分即为 B 成绩。修复尝试失败时也不把未验证副本作为 B。

无合格修复时 Harness 正常结束审阅，保存明确的 `audit_complete_no_eligible_change` 和逐项未决原因；不制造异常、空壳应用或伪 B 来控制平台。平台后续因缺少应用而 FAILED 的原始状态、错误和费用原样保留，同时单独记录 `application=not_published`、`score=not_applicable`。这不是应用零分或设施恢复触发；只有已读回绑定 run、A、需求和观察证据的完整 audit 回执才可认定审阅完成。单见 FAILED、报告缺失或进程中断均不能推定“无可修复项”。第二轮仍消费一次模型机会。

现有 `lab/exp/hosted.py:export` 只导出平台 JSON/logs，没有 workspace ZIP；旧 `hosted_monitor.collect` 会对 FAILED 尝试下载 template-bundle，但不证明“无应用”终态也一定可下载。最小改动是复用首轮 OOM 已需补齐的 ZIP 回收，并把有界 audit 终态摘要同步写入现有可导出的进程日志；详细证据留 workspace。只有摘要取回时可确认审阅报告声称的终态，不能宣称缺失的修复证明已验收。若平台实际未保留日志/报告，结果记 evidence_incomplete，停止该分支而不自动重跑或伪装成功。

**接受边界变化：能保证不重新交付/评 A，不能保证平台不启动后续步骤，也不能保证无应用运行免费。** 当前公开代码没有跳过评分的入口，失败收费及无应用导出行为尚未实测；保留平台原始 usage/错误，不能将未知费用说成零。授权后的真实第二轮同时验证这些行为，不另造模拟测试。若用户坚持完全不产生后续评测任务，或实际报告无法回收，①便不满足约束，届时才评估独立 Mac runtime；不靠新增未受平台支持的字段解决。

## OOM 与官网接线

官网完整生成覆盖 Braid/Pi、成员工具、构建、浏览器直到交付；应用 replay 只覆盖应用启动与评测，不能代替生成 OOM 验收。首轮同时取得 e2e 与 OOM 证据，避免另造压力试验。读回实际 OOM 修复 binary/runtime，不能只信 manifest 来源声明；历史曾出现声明新版本而实际 binary 仍旧的情况。

现成 Hosted 可派发单模型 self_funded 完整生成；多成员绑定与 Router 配置可由冻结 Harness artifact 承担，不因平台 metadata 缺候选字段就先新增 Hosted schema。包内 gateway、Chromium、Braid/Pi 与应用共享的实际内存限额及峰值须一起记录；不能将包外 gateway 成本隐去。具体 Router 进程接线归[供应商 owner](provider-fallback.md)，不在此重复设计。

**秘密应由受访问控制的 private artifact 或 deployment credential file，经实际支持的 secrets 入口装配。** 公开 ZIP、manifest、catalog 只保存引用与非敏感身份。private artifact 若需被平台消费，必须确认权限、实际解引用、变量作用域和回收方式；现有 credential_file 支持某个 API key，不证明会把多供应商变量自动注入 sandbox。这一入口由 provider owner 收敛，尚不能写成已验证能力，也不临时引入公网隧道。

Hosted 公开观察是 platform-export-only。已有路径是 Harness 在 workspace 保存 process/native/resource 原件，平台导出 ZIP，collector 定向读取；这不等于平台提供物理 inspect，也不等于 native 证据不可取得。当前包是否仍生产、新 collector 是否消费并绑定该 run，须实际核对。保留 cgroup 身份、真实限额、起止 oom/oom_kill、可得峰值/采样、原生及生成退出和应用发布。SIGKILL 不单独证明 OOM；缺字段保持 unknown。

报告区分“完整生成且未观察新增 OOM”“发生 OOM 后恢复完成”“尚未完成或资源证据不足”。一次成功只覆盖该负载。官网托管执行按用户最新要求设计；自管构建、controller、gateway、上传包及下载证据仍全部在 WorkSSD，不恢复任何无 WorkSSD 的自管远端。

## 构建裁决：先派生已有 Linux runtime

当前没有已证明 WorkSSD backing 的 Linux Docker 域；这不是旧 Linux 产物不能复用的证据。保留输入为 `runs/iteration13/i13-2-20261001/hosted-sheet-r2/agent.zip`，实际 SHA256 `7de33f7d23a910ec61e4b639275305cdd05222416ff01f2e757d55e58c1ff316`。本次只读比较确认：

- runtime/package-lock.json 与当前 harness/npm 锁字节一致，SHA256 均为 `9b7aa8110d9b2b2befeab075b0c11019a02445d900091e41044dad427d352e4a`。
- runtime-source 记录的全部 11 份原生/managed patch 摘要与当前 patch 文件一致。
- runtime/native-managed.mjs 与当前源文件字节一致。

这些证据支持复用 Linux Node/npm/native 工具作为来源，不证明旧 Braid、预算或 e2e 已符合当前交付。只复制 runtime 到新 WorkSSD 产物目录；原 ZIP 不变。用现有 cargo-zigbuild/zig 和已安装 Linux target 编译当前冻结 Braid，所有编译/cache/temp/log 输出在 WorkSSD。按实际源码、binary 与来源发布新身份；当前预算/support/技能及四 I14 定义由现有 producer 组装，保留 child 继承和按 Braid session 预算门控，不能重命名旧参赛包交付。

e2e addon 必须另行取得。当前 Dockerfile 使用 `npm ci --ignore-scripts`，锁含 Linux x64 预编译 esbuild；支持先尝试按锁取得目标平台文件，不支持把 Mac 默认安装结果当 Linux。必须包含匹配 Playwright 1.63 的 Chromium 和 Headless Shell，不能用旧浏览器替代。现有 finish.py 借 Linux ldd/dpkg 收集非 glibc 库；可以复用基础 runtime 中确实兼容的库，但不能仅凭同名 SONAME 宣布新版依赖闭合。

| 获准实施后待确认 | 决定 |
| --- | --- |
| Braid 与 bundled SQLite/libgit2 等依赖能交叉链接，ABI 符合官网目标 | 成功则无需先建立 Linux 构建域；若需持续改造工具链或改变依赖语义，保留原错并转向最小合规 Linux 构建能力。 |
| e2e Linux 包、匹配浏览器资源及动态库闭包可取得 | 成功则在 WorkSSD 文件装配；若必须执行 Linux 安装/配置才能得到正确产物，再解决该具体执行能力，不猜库或跳过 native 包。 |
| 官网真实入口采用新 binary/runtime，并完成实际 e2e 操作 | 才取得目标运行证据；静态 ELF、源码比较和文件存在均不能替代。失败按包装、动态加载、sandbox、OOM 原因分别处理。 |

现有 Rust target 不证明链接必成功，纯文件路线也不是成功承诺。它是一条有证据支持的优先尝试；出现明确 Linux 执行阻塞再建满足 WorkSSD backing 的最小域，不默认 whole-VM 迁移或使用 development-1/2。当前 layout v1/checkpoint v3 与 variant 定义/state 分离归基建 owner；消费其当前交付及公开生产接口，不复制旧流程或另造恢复体系。Router 与增量审阅 owner 持有各自接缝。

## deployment 价格与激活边界

首轮只激活 Flash、K3、DS0731；缺失的 ARK K3、普通 Qwen 0731 只补选定 deployment 行与精确 native selector 映射，不加载目录其余默认或 GLM secrets。价格与账户事实以[供应商调查](provider-fallback.md)为准，未知成本必须保留 unknown，不能从免费配额为零推断不可付费，也不能从历史 HTTP 200 推断余额持续可用。用户已要求重按价格复核，可以提出替换历史默认，不另设“必须再明确点名供应商”的门槛；执行仍待授权。

Flash 的文字与视觉目前共用稳定 alias 和同一 Router，**首轮只冻结一条同时满足所有已启用文字、工具、视觉需求的链**。BigModel 已知单价及历史文本成功使其值得优先复核；若账户及全部启用能力就绪，推荐 ARK→BigModel 整体替换 ARK→普通 Qwen，保持两路。证据不足则保留原链并如实记录未验项，不能称已完成路由验收。普通 Qwen 价格未知，因此不能宣称 BigModel 已被证明更便宜。不得将文字/视觉偷偷排成两条同 alias 链，也不为此新增请求分类器、两套 gateway 或把文本 200 外推视觉。

GLM 不进入首轮依赖。后续实际选用时，若千帆已购 Plan 的 GLM 权益及部署能力确认可用，推荐千帆 Plan→ARK Coding Plan；先用已购权益并取得异供应商备用。权益仍未知则推荐 ARK Coding Plan→千帆普通 API，使用已知套餐与已知活动单价，移除没有成本/权益依据的 Qwen 长链。千帆普通的活动价是 4.8/16.8/1.2 元/M，不代表优于已包含的套餐用量；未选 deployment 不装配秘密。新供应商尚未真实调用是开工时相同的实际验收门槛，不是永久排末端的理由；专门验证千帆普通时亦可预先将其置主位。

同供应商 plan→payGo 可以覆盖套餐耗尽，不能宣称隔离共享模型池、区域容量或账户限流；不同 key/endpoint 不足以证明独立。DS0731 保留 Token Plan→普通 Qwen 的同 ID 链，K3 保留 ARK→普通 Qwen，不因千帆 GLM 便宜而换模型。按具体 429 原因执行一次冻结 fallback，保留原错；两路都不可用便有界终止，不能轮转到无精确版本/能力证据的通道或临时扩大成本政策。

## 存储、证据与结束条件

所有自管项目产物，包括 temp/socket/cache/log、runtime/store、容器 overlay/volume，必须实际位于 WorkSSD。写入前解析路径并核对真实挂载身份；路径前缀、同名远端目录、事后下载都不够。外部既有工具或凭据可以只读消费，不能因此迁移整个用户 home；工具的项目新写入须明确导向 WorkSSD。`TMPDIR` 不能覆盖源码硬编码或工具独立缓存。

旧不完整运行、外置目录和 Factory 自建镜像已清理，保留集及终态以[清理回执](storage-cleanup.md)为准，不重复清理或把旧现场作为依赖。本次保留包的源码/runtime 比较与历史评分只证明各自覆盖的事实，不证明新制品或新官网接线已运行。

不设用户未要求的 12 小时 kill；沿已有采集和十分钟监控读摘要，连续约 30 分钟无语义进展触发定向诊断，不直接判 stale 或重启。既定预算继续有效。首轮官网生成/e2e/OOM 证据与必要派生评分闭环后，若无第三机会的判别理由即停止汇报；未闭合项如实保留。此轮只做只读调查和本 cell 编辑，没有编译、生产、prepare、模型或实验启动。

**关键路径裁决：首轮应分阶段交付，不等待整棵实验树实现。** 首轮必需的公共基建接口、当前 Linux/e2e 制品、私有 Router、预算/WorkSSD 边界及证据生产就绪，且取得对应启动授权后，即冻结首轮 ZIP/输入并开始官网完整生成。seed 入口、职责和报告由原 owner 在首轮期间继续准备；不能原位改变已冻结首轮制品，模型实验仍严格串行，不等第三候选。资源采集必须从首轮进程起点生产，正常/异常结束都保留原件及应用/native 来源；首请求前 Router、平台 run 身份与 JSON/logs 保存、保全/停止责任也不能延后。当前 adapter 的 terminal bundle 下载与定向解析可以首轮期间接线，但事先指定已有 workspace-bundle 回收途径及责任人，提前终止时也能保全，不能依赖“首轮会跑很久”。第二轮实际派发前才要求 seed gate、报告回收和有 B 才发布的完整冻结包；未就绪则保留 A 并汇报，不能让后继功能阻塞首轮。OOM 原件不可事后补造，未回收到只报告 unknown。
