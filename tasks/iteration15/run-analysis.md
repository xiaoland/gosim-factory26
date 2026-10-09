# 近期 I14 / I15 运行比较与改进依据

本次为开发侧只读分析，不向在途生成传递隐藏反馈、不启动模型或官网评测、不控制运行。分析冻结入口截至 2026-10-07 夜间；I15 stages 的原始事件与评分原件已更新到 Stage2 终态，因此下表覆盖了旧 packet 23:07 状态之后的事实。生成、打包、官网评测分别计时；本轮费用主口径采用token成本，金额未知不阻碍比较和改进。input/output/cacheRead分别保留；原生cost=0不表示免费。

## 分析优先级与两个可辨别热点

优先级是提高评分、降低token成本；耗时处于最低优先级，只用于寻找可能的高消耗、低收益或失效热点。长时间、大token、低分的共现不构成根因。本次只深化两处已有明确会话与评论证据的热点，从Agent当时实际看到的信息解释具体动作；未启动下列判别实验。

| 热点 | 观察与具体动作 | 当时可得信息 | 当前可支持解释 | 竞争解释、未知 | 后续控制变量或消融（待授权） |
| --- | --- | --- | --- | --- | --- |
| Evo从起点将全部实现交给唯一基础PR，实施会话242.796M tokens | 根初始会话01a11550第30行判断5处修改“小增量”；第46行已识别大量基线缺失。定向核原文件第32/46行的已存储决定，补得简短摘要：它意识单PR很大、考虑多PR/子Issue，仍选择单基础PR。第53行packet、15:54评论1将全范围交glm-2 | 已读技能主体、需求树、5修改点、基线代码；assignee list只显示next-login glm-2及“完整工作项”描述；actual system规定根负责共享基础并创建关联基础PR，没有全量业务单PR字面限制 | 选择A不是没考虑B；比较时把glm-2入口误判为唯一实施容量，并把“不拆整套基础职责”应用到全部缺失业务，再以协调开销支持单PR。runtime核next-login不等于容量，I11同policy8业务Issue排除单句policy充分决定 | 协调开销具体依据、next-login说明为何未被正确理解、基础/业务边界为何未被技能纠正仍未知。具体角色动作路径与抽象判据失衡可能促成误读，但不能代替实际已取证的决策前提；大PR导致评分低仍未证实，Evo未评分 | 固定同基线/需求/模型/runtime，先单独纠正next-login容量认知，再单独明确基础PR范围，再评价技能边界判据；比较是否形成独立能力成果、漏项、整合返工与最终评分/token，避免同时改全部因素。PR数量和最低耗时不是目标 |
| I14原Stage3评审failed后根反复选择“继续等”，84轮/168成功模型请求无评审推进 | review1物理会话01a1127c第181/200行连续403；根会话01a111ee第242行（北京时间03:02）读comment33、fetch、head、PR最新评论号；第244行明确说“reviewer-1验收进行中。无变化”；持续到第574/576行10:19仍同判断。10:23评论117@原reviewer，重新产生wake，10:56 Approved | 根这几轮取回的是冻结head与最新评论号；实际reviewer两turn已failed、pending请求未完成、provider sleeping/idle、wake已consumed。采样命令没有provider/turn终态查询，也未把具体403带入根当轮工具结果；普通提醒提供“检查进展”机会，但本证据未证明提醒正文告诉它失败 | 可支持的是信息获取与状态推断错误：从业务请求pending/无变化推出执行“进行中”，于是选择结束处理而非诊断/唤醒。直接继续原会话的干预证明失去后续wake是空等持续条件；供应商错误不是7小时请求延迟，更不是root已经看到403却故意忽略 | 为什么根只选PR/head工具仍未完全隔离：根指令/提醒如何表达跟进责任、公开状态发现能力、模型惯性均可能影响；若没有可用CLI暴露turn错误，仅要求根多看评论可能仍无法辨别。一次成功运维wake不证明所有错误都应无限自动重试，也不证明是唯一长期根因 | 在同一冻结失败状态的隔离副本、同模型与上下文下，分别仅给原提醒、给失败/无wake事实、给可查询执行状态指针，观察根是否选择诊断/有界唤醒而非重复PR查询；再单独移除周期提醒检验是否失去关键错误发现。只模拟/复现公开状态消费若涉及Factory测试则不采用，优先在获授权真实运行中用控制变量观察，不新增本仓库禁用测试。评价错误发现正确率与token消耗，墙钟只作后果记录 |

第一处把技术角色预设与需求结构利用分开，是因为root已读结构且后面改变了基线理解，实际比较拆分后仍以错容量与过宽规则作用域选择原工作单位。同配方Stage1/2完整读需求、Stage2实际vision解14图后仍全范围交glm-2单PR，说明Evo五Modified锚定与未vision不足以解释通用倾向；I11反例要求继续区分输入模板、技能方法与模型采用。有限深化原件及未知见 `runs/iteration15/requirements-structure-inquiry/{decision-context.json,decision-context-notes.md,stages-root-decision-context.json}`；单纯再强调“完整理解需求”未必能改变A。第二处把当轮输入与运行真实状态分开，是因为事后开发者知道403不等于当时root知道403；改进应让根取得判别信息并负责判断，不能只批评它“没有积极检查”。

Evo引用入口为 `runs/iteration15/requirements-structure-inquiry/evidence.json` 的sessions[0].source及同文件comments1/75；上述行号指该完整原生JSONL物理行。I14引用入口为 `runs/iteration14/sequential-github-stages-20261006/manual-stage3/profiling/idle-causal-evidence.json` 的root_samples、native_403、failed_review_turns与manual_wake；UTC原件时间统一加8小时理解。第三处I15整合返工/官网低分目前仍作为候选热点：现有compact输出能证明确有权限、环境、accessible-name修复，但不足以重建每次具体A/B判断，故不补造它的根因；待有一个明确缺口的原任务输入→实现决定→review工具结果链再定向深化。

## 可比较的运行事实

| 执行与输入 | 模型身份 | 生成墙钟与终态 | 独立官网成绩 | 关键条件 |
| --- | --- | --- | --- | --- |
| I14 Stage1，旧空应用生成 | root/普通/reviewer Flash，高思考；advisor K3 | 历史恢复后最终 a11c2ca；本次未重建耗时 | 15/30 | 是正确接续链的既有起点，不是 10-06 多余 fresh Stage1；耗时待原 run 单独恢复 |
| I14 Stage2，继承 a11c2ca | 同上 | 10-06 19:40:37→23:29:44，3h49m07；Braid 完成，入口 seed/output 同名碰撞 exit1；从最终 1f273516 冻结 | 6/29 | 完整生成已完成；出口设施失败不等同业务零分 |
| I14 Stage3 原接续，继承 1f273516 | 同上 | 10-06 23:56:38→10-07 11:57:38，12h01m；人为 deadline 强杀137，无最终交付 | 无该终态最终评分 | 含7h26m08评审失败后空等，占61.88%；不能拿后续成绩归给它 |
| I14 Stage3 pre403 应用接续，从旧02:29候选2a951d4开始 | 同上 | 新 run 61978851，10-07 12:25:58→18:05:42，generation_seconds=20384.38，5h39m44；generated/delivered | 0/41，最终34db022c | 新原生会话，仅继承旧应用，不是完整检查点恢复；总成本还包括旧失败 run |
| I14 GLM root，空应用完整 REQ1–6 | root GLM-5.3，其余原组合角色 | 原10-06 20:58:49→10-07 08:59:49，12h01m强杀；15:09:50→20:44:16接续5h34m26完成；执行累计约17h35m26，日历23h45m27，其中停止间隔6h10m01 | 0/41，最终5655950 | 官网只提供Stage3题目，不能称完整REQ1–6总分；第一次恢复入口15:08:21四跳guard失败未调用模型 |
| I15 Stage1，空应用REQ1/2 | 原Flash/high + K3/DS角色，千帆优先 | 10-07 15:14:17→18:36:01，3h21m44；generated/delivered，最终1d455393 | 10/30 | 实际采用 reviewer 聚焦版 overlay77c；后续隔离改进未热入 |
| I15 Stage2，继承1d455393与限定Stage1原始参考 | 同上 | 18:36:01→23:25:45，4h49m44；generated/delivered，最终73dffb43 | 2/29，submission dee2e9b8-1b8f-44a7-a916-34e404a29c3e | Stage3已23:25:45实际启动；此分析未查询其进度 |
| I15 Evo GitHub，确切官方基线增量，114场景 | 原Flash/high组合身份 | Docker15:42:19→23:05:38，7h23m19；用户要求停止137、非OOM；原生generation_seconds=26581.82 | 无 | 实施自验114/114，尚无独立验收与自然交付；不得将停止现场归档当最终成功应用 |

I14 Stage2 与 I15 Stage2的需求范围相同，但前阶段应用不同，且后者 reviewer/约束材料不同；4h49m44比3h49m07多约1h00m37，分数6→2并不建立某个单一改动导致退化的因果。两次Stage3零分也不能证明GLM root与Flash root无差别：任务输入、生成路径、恢复与时长均不同，而且失败集中在共同前置导航。

## 耗时到底花在哪里

I14 原Stage3已有可靠的关键路径剖析，应直接采用，而非重拉rollout：设计16分钟，实施/首次构建67分钟，自验修复72分钟，首轮评审25.5分钟，失败空等446分钟，恢复后评审33.5分钟，后续合并/种子修复/协调约60分钟。其403请求直接耗时只有秒级，全部非complete请求累计约318秒（有重叠），供应商错误通过“pending评审失去wake，根负责人误判活性”放大为7小时。84轮根检查、168正常模型请求没有产生评审语义进展，故HTTP200、token增长和容器running都不是进展判据。

I15 Stage1的已保存观察提供近似阶段边界：前约14分钟需求设计，16:11已经实施，17:29已进入评审，18:17:22 Approved，18:36终态。精确ready时间尚未重建，因此只能说首轮review约48分钟（从17:29观察到18:17），Approved后整合交付约19分钟，不能据此把其余时间全部归为实现。独立review曾30/31，单场景复测3/3；原密码登录HTTP200用了8.75秒，超出页面断言采样窗口。耗时问题包括验收等待条件与真实服务延迟失配，不应先断言业务故障或“改大timeout就解决”。

I15 Stage2：18:36启动，20:39首次review已开始，21:17:25 Approved；21:30 PR2已合入，最终整合PR3实施继续，22:53第二review仍在验收，22:57:59 ChangesRequested，23:07第三review，23:25终态。首业务PR Approved后又花约2h08m20，其中包含写路由权限/事务修复、breadcrumb、Node24动态库启动失败、并发Chromium/Vitest timeout复跑、accessible name修复、重复全量Stage1/2验收。仅依据compact证据不能精确扣出每个问题的净损失，但“实现PR通过后，整合仍补发现共享边界缺口并再验”是明确热点。

Evo唯一基础PR从15:53交接给实施者，22:40请求review，实施串行约6h47m。基线健康验证只约12分钟；114场景一次最终e2e用时121.43秒，不能把7h23m统称为测试时间。root于15:54明确写“本阶段唯一基础实现PR”，实施覆盖114场景；主分析owner另保存定向证据 `runs/iteration15/requirements-structure-inquiry/evidence.json`：巨大PR起初已覆盖52 ATOMIC/114 scenarios，根先列树/count/提取Modified段，再全部交glm-2；不是中途扩张。77次根idle提醒、跟进会话86个toolCalls，其中73条命令含pr view，多数draft查询；没有git diff调用。但首轮基线代码查读存在，不能据缺diff断言完全没有检查。reviewer后来报告两个并发vitest共享database.db导致11失败并转独立副本串行复跑；这是Agent归因，未独立复现，但足以定位验收状态隔离的采用缺口。

## Token成本、阶段与角色分布

本次在远端一次有界只读聚合终态run的 `work/native-homes/*/sessions/*.jsonl`，只返回数值，不回收完整rollout。Evo补充沿本地frozen现场相同路径只读聚合，未做远端查询。原件为 `runs/iteration15/run-analysis-20261007/native-usage.json`。这是Pi保存的assistant usage累计，不是供应商结算账单；不覆盖PBB内部另存会话或gateway独立请求，不能代替全run完整token账。恢复后的多文件历史也未按上游request ID去重，因此GLM完整run值应作为现存会话账面总量，不能用于精确费用比较。

| 会话采集范围 | input | output | cacheRead | 账面totalTokens |
| --- | ---: | ---: | ---: | ---: |
| I14 Stage2 Flash，7文件/1112 assistant | 7,394,464 | 381,091 | 125,707,072 | 133,482,627 |
| I14 pre403 Stage3 Flash，9文件/2167 assistant | 12,786,207 | 443,438 | 235,036,480 | 248,266,125 |
| I14 GLM完整run Flash | 27,074,998 | 1,257,929 | 471,483,008 | 499,815,935 |
| 同run GLM root | 956,296 | 131,830 | 25,212,928 | 26,301,054 |
| I15 Stage1 Flash，6文件/628 assistant | 4,135,642 | 217,282 | 58,434,752 | 62,787,676 |
| I15 Stage2 Flash，6文件/1182 assistant | 6,655,302 | 320,294 | 124,400,960 | 131,376,556 |
| I15 Evo GitHub Flash，4文件/1032 assistant | 7,561,130 | 312,765 | 251,123,776 | 258,997,671 |

token就是本轮采用的成本量纲，不等待账单。cacheRead同样代表模型反复消费历史上下文的负担，但不与未缓存input假设同价；金额仅保留一条边界：原生cost全0并非实付，TokenPlan/CodingPlan与按量fallback不能用同一单价换算，官网评测也另计。

同范围Stage2的账面totalTokens，I14为133.483M/I15为131.377M，后者为前者98.42%；output为381.1k/320.3k，后者84.05%。官网成功场景6/2，对应观测到的累计token/官网成功场景约22.247M/65.688M，约2.95倍。此比率只比较同一29场景题目的本阶段生成增量，不包含前阶段应用成本；两份继承基线不同，也有会话采集范围差异，不能把它当每场景可预测费用或I15某个改动的因果效应。它揭示主要问题是质量收益变差，而非这批记录中token总量明显增加。Stage1与Stage2需求范围不同、Evo无独立成功场景、零分Stage3不作除零“成本效率”。

Evo的四份会话可进一步按已有provider/session对应角色划分，根初始与后续跟进物理会话分别计：

| Evo角色 | assistant数 | input | output | cacheRead | totalTokens | 单次输入账面峰值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 根初始 | 39 | 274,172 | 12,870 | 972,672 | 1,259,714 | 45,446 |
| 根跟进 | 164 | 1,073,478 | 14,238 | 3,804,864 | 4,892,580 | 45,019 |
| 实施 | 717 | 5,670,412 | 260,871 | 236,864,896 | 242,796,179 | 537,393 |
| reviewer | 112 | 543,068 | 24,786 | 9,481,344 | 10,049,198 | 125,726 |

单次峰值是单条assistant usage的input+cacheRead+cacheWrite，不是totalTokens反推的context大小，也不证明全部token都是当前业务正文、或已包含尚未返回的请求。实施峰值记录于2026-10-07T15:05:03.492Z（23:05:03北京时间），reviewer峰值23:05:06；原生用量是否准确映射真实供应商context仍需runtime语义核对。实测账面537k明显超过用户约245k操作目标，为本轮压缩/reset修复提供直接负担证据，不能据此修改模型真实容量。

实施占本次Evo主会话账面token约93.75%，根初始+跟进约2.38%，reviewer约3.88%。根跟进164条assistant、4.893M tokens与77次idle提醒的定向记录相对应，但不能直接把这164条全部认定无效轮询，也不能用平均数伪造单次提醒成本。改进优先级因此分开：根检查质量主要影响失效发现与关键路径，纯token省量主要落在长实施会话、重复历史输入与返工。删除根监督会降低2%左右账面消费，却可能重新引入I14长空等；应修检查内容与必要唤醒，避免把“少跟进”当节省方案。

Evo停止现场已可取得主原生会话账面258.998M tokens，约97.0%为cacheRead；停止前7h23m执行的用量不能冒称完整交付成本，也仍不覆盖其它内部会话或供应商账单。

I15 Stage2比Stage1约2.09倍账面tokens，其中cacheRead占约94.7%，对长上下文反复往返的优化价值明确，但不能从cacheRead反推出峰值context或“需要在多少k reset”。I14 Stage2与I15 Stage2账面总量近似（133.48M / 131.38M），墙钟却差约1小时，支持优先查整合关键路径、环境启动和复验，而不是先按tokens认定模型更慢或更贵。

## 评分与自验为何脱节

I15 Stage1官网10/30，失败分为2条Sign out `.dialog`不可见、14条60秒timeout、4条导航目标缺失（Repositories/acme-docs）。14条只有总timeout，没有动作trace，不能断言14个业务功能全部错误。前10个注册、登录、找回密码场景全通过，说明不是应用整体未启动。自验30/31后复测通过与官网10/30差距，应从公开旅程的入口、对话框呈现、组织导航、业务种子与父层规则检查，而不是只追叶子assert。

I15 Stage2官网2/29：2条Search成功场景（S2/S3）通过，2条Search S1/S4因 `/acme-docs/i` heading匹配两个h1而失败，3条创建仓库60秒timeout，22条缺可见navigation target。heading错误证明相关页面已打开，不能归为仓库完全不存在。进一步定向取证确认两处h1分别来自布局owner/repo与种子README标题，自验使用较窄的owner/repo匹配；公开需求只要求相应标题存在，没有唯一性。因此当前证据支持检查语义差异，不足以判产品违约，也不将隐藏locator转为新增产品要求。

I14 Stage2的23失败全部停在navigation target缺失；已有独立确切评分镜像HTTP与真实浏览器Search→acme-docs→刷新验证通过，故“种子不存在”与“公开Search刷新必坏”已被排除。冻结应用遗漏UnoCSS虚拟样式导入已独立确认，是Stage1继承缺陷；官网前置导航动作仍未知，不能把该样式缺陷宣称为全部评分根因。I14两份Stage3最终0/41均为40条导航缺失+1条评测端 `uniqueAccount is not defined`，分数合法回执须保留，但不能把评测端ReferenceError归为应用缺陷。

## 可行动的改进依据

以下是根据上述输入与行为证据提出的候选干预，不是仅从耗时/token相关性宣布根因。排序以评分与token收益为先；运行失活处置是交付前提，耗时仅提供定位线索。

1. 任务拆分应利用requirements的父层模块、业务主体、共享状态与场景旅程形成可独立交付成果。Evo从起点唯一PR串行处理114场景，I15普通每阶段也主要一个业务PR；Braid并行优势没有被充分使用。优先分离认证账户、组织与权限、仓库资产、文件/版本、Issue、PR/合并等完整能力，并显式确定共同实体/授权/导航约定与集成责任；不是强制每叶子一Issue，也不把共同前提扩成所有业务实现。
2. 在各成果自己的独立验收中同时评价入口、权限负面路径、供给状态、父层约束、参考图和完整操作结果。先确定验收责任，再实现；不要依靠最后整合PR重做一切来补全契约。I14 pr-viewer供给遗漏、I15写路由requireAuth遗漏与heading/accessible name复修是具体收益依据。
3. 已授权的根负责人跟进修复应直接检查pending工作的实际turn/provider状态、最新有效动作和错误，并对失去wake的已失败任务作有界处置。I147h26m空等有直接运维修复证据，这是最强的时间收益；无需增加普通检查频率。
4. 已授权context界限修复应以Pi原生压缩与Braid reset真实身份落实；减少重复读长需求与重复全量验收是配套改善。现有usage支持上下文反复消费很大，但不提供阈值正确性的独立证明。
5. 统一实际验收runtime与隔离边界的采用：Node24/native ABI、portless整命令解析、双vitest同库、Chromium与vitest并行争用都消耗关键路径。复用当前已修运行时材料比新增一个通用设施层更直接；本报告不证明pi-minimal-vv修复已经进入I15，需材料owner逐项读回。

上述结论不自动授权新实验。下一次获授权比较应固定同一需求、基线、模型与运行材料，以“能力任务边界→实际独立交付/验收→整合返工→官网最终成绩”观察拆分收益。当前不根据少量不可控对照推荐GLM root或把短输入、少技能读取当实际收益。

## 证据入口与未解项

- I14顺序链：`tasks/iteration14/sequential-github-stages-20261006/packet.md`；原Stage3精确profiling：`runs/iteration14/sequential-github-stages-20261006/manual-stage3/profiling/{analysis.md,summary.json}`；pre403终态：`manual-stage3-pre403-2a951d4/final-terminal.json`及同目录stage3-self-test-r3。
- GLM完整：`tasks/iteration14/glm53-root-full-github-20261006/packet.md`，`runs/iteration14/glm53-root-full-github-20261006/selftest/terminal-status-20261007T2100.json`及official-evaluation/records/self-test/result.json。
- I15顺序链：`runs/iteration15/github-stages-20261007/events.jsonl`；阶段review时间来自各有时间戳的status原件；评分来自stage1-self-test-r2与stage2-self-test的records/self-test/result.json。stage2官网submission为dee2e9b8，未重复提交。
- Evo：`runs/hackathon-evolution/i15-evo-github-20261007/{current-business-observation.json,implementation-final-e2e-observation.json,docker-terminal.json}`及final-frozen/freeze-receipt.json。

仍未知：I14历史Stage1精确成本/墙钟，包括Evo在内的完整token账、PBB内部用量、I15各复验故障净墙钟、官网timeout场景实际卡点。不等待账单，不为补齐这些未知穷尽rollout，也未探测评测器或私有端点；已有结论足以支持本轮任务边界、根跟进与runtime采用调查。
