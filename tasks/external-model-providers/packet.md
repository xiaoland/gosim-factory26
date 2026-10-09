# 自购模型 API 接入调查

状态：本任务的接入调查、凭据入口、提供商文档拆分及集中LiteLLM路由配置已完成；实际通道调用和网关部署尚未验收，后续实验由各实验任务持有，本任务不授予新调用或恢复许可。持续维护的提供商、价格、套餐与验证状态入口为[模型提供商目录](../../docs/deployment/model-providers.md)，下文保留分阶段决定和证据。

用户希望用自行购买的 Kimi、GLM、DeepSeek API 组合进行本地开发，保留官方未来五天500额度及正式提交预算。

## 已核实的现状

`local_experiment.py` 只执行外部命令和保存原始 OTLP，不解释模型供应商。`arc_bench_adapter.py` 的 env-file 可以传任意变量，`arc_matrix.py` 命令入口目前为全矩阵选择同一 env-file。各 job 的命令本身可不同。

四个团队 variant 的 `run.py:native_files` 将所有文本模型写入同一 factory26 provider，使用一个 base URL 和 FACTORY26_API_KEY；视觉 provider 可单独配置。成员 profile、内部角色 Markdown 和模型 descriptor 固定实际模型与兼容参数。只替换根模型或 URL 不足以将混合团队分流到不同厂商。

raw 入口已有 endpoint/key 注入，但默认 URL 是官方网关，模型参数来自 raw_models.json，仍需依据目标 API 的实际模型名和协议重新选择。Codex 当前通过 LiteLLM Responses 兼容层接 Chat。

发布的官方 local_submit.py 在 OPENAI_API_KEY 非空时会用该值登录 meter.arc-bench.com；Docker 还会将宿主同名变量覆盖 env-file。自购API运行必须避免把第三方key交给此Meter路径，也不能意外继承官方key。不修改官方评测器，优先在接入边界显式隔离环境，provider独立key只供容器内客户端解析。

## 当前设计讨论

用户纠正：模型接入方案不能以Pi原生多provider为核心，应避免与具体Agent Harness耦合。此前建议不再采用。

已核实Braid现有边界：`provider/factory.rs:materialize_native_home` 为每个新物理会话创建 `<profile.id>-<uuid>` 的home，并复制对应binding.native_template；恢复会话复用原home。Pi设置PI_CODING_AGENT_DIR（不是PI_HOME），Codex设置CODEX_HOME。配置目录隔离不是凭据或网络安全隔离；进程仍继承父环境。不同profile的主会话因此可以采用独立客户端连接配置，不能据此假定同一profile内多模型子代理已经获得独立连接路由。

模型到上游供应商、endpoint和credential的映射应归独立于Pi/Codex/Braid的API接入边界。客户端在各自home内只保留接入该边界所必需的原生配置，实验调度与OTLP仍不解释模型路由。现有mixed profile内同时有DeepSeek、GLM、Kimi及视觉角色，单靠每profile独立home不足以解决其分流。

若采用统一API入口，优先评估已有兼容网关是否覆盖实际购买服务，不自制代理。其部署与计量独立于实验collector。优先候选为已有依赖LiteLLM（当前资源固定1.102.0）；Portkey为文档层面备选。尚未授权实现；需继续与用户讨论接口和模型身份，不能借此引入自动换模型/故障fallback。原生Chat/Responses差异仍由明确的兼容边界处理。

自购运行不得回退官方凭据，官方Meter的OPENAI_API_KEY登录路径需隔离。当前所有模型实验保持停止；无新增API请求或源码修改。

## 统一API调查结论（2026-09-24）

用户确认优先统一API；不能做到时，至少由Braid agent-profile配置模型与提供商。两条路径都应由profile选择provider/model，具体密钥保持外部引用。

LiteLLM官方文档提供Moonshot、Z.AI、DeepSeek接入，统一Chat以及Responses转Chat桥接；故架构可行。当前项目已经依赖1.102.0及局部Responses兼容hook，不能把latest文档当成冻结版本和目标厂商全链路已经验收。上游issue35878仍报告Responses桥接的reasoning参数与namespace/tool_search处理问题；仅凭入口存在不能承诺Codex全部工具语义等价。统一地址与鉴权可实现，推理档位、工具类型、视觉能力等仍须按具体模型保留能力边界。

Braid现有Profile含provider/model/reasoning。Pi适配器实际将provider传入CLI；调查时Codex的thread/start和resume传model，但未消费profile.provider，供应商主要由对应home的原生config决定。已按用户授权在两处传入modelProvider，空provider传null保留原生默认；不新增供应商注册表。配置注释提到llm_providers，但当前Config无该registry实现，不能用注释作实现证据。NativeHome按物理会话隔离已具备。

子代理配置边界：Braid profile管理成员主会话，Pi内部角色仍由variant持有。若采用独立API边界，内部角色可使用同一入口并按模型分流；若直连回退，仍需明确内部角色选择如何绑定provider，不把每个内部角色擅自提升为Braid成员。

依据：
- https://docs.litellm.ai/docs/response_api
- https://docs.litellm.ai/docs/providers/moonshot
- https://docs.litellm.ai/docs/providers/zai
- https://docs.litellm.ai/docs/providers/deepseek
- https://github.com/BerriAI/litellm/issues/35878
- https://portkey.ai/docs/product/ai-gateway/universal-api
- sources/braid/src/config.rs:146、provider/pi.rs:141、provider/codex.rs:307、provider/factory.rs:227。

此次仅查官方资料与本地源码，无模型请求、安装、网关部署或源码修改。

## 本轮实施与核验

用户授权的缺陷属实，已修sources/braid/src/provider/codex.rs两个会话入口，并修正Profile.provider注释及其协议说明。WSL实际冻结Codex0.155.0生成的JSON Schema确认ThreadStartParams和ThreadResumeParams均接受modelProvider字符串或null。没有调用模型。

项目根`.secrets/models.env`已创建，仅含KIMI/GLM/DEEPSEEK的API_KEY、BASE_URL空值；目录700、文件600，git check-ignore确认忽略。没有迁移或读取旧密钥。文件供用户在macOS工作树填写，尚未同步WSL，亦未接入自动加载。官方凭据另用`.secrets/arc-bench.env`，运行文档已改为项目内路径。

WSL隔离编译目录为`/tmp/braid-provider-fix-l0HLxm`，不覆盖现有WSL Braid源码，不更新实验运行二进制。首次offline检查因const-hex未缓存失败；联网获取锁定依赖后`cargo check --locked`成功，19条现有未使用代码等警告，无编译错误。当前不运行Factory自身测试或包smoke，实际模型验收需另行授权；不提交代码。

## 自购凭据实际调用（2026-09-24）

用户填写密钥并明确要求试用，授权本次最小直连调用，不恢复bench。已安全同步到WSL项目`.secrets/models.env`（600），三家`/models`均HTTP200；随后各一次Chat请求均HTTP200、finish=stop、答案391：kimi-k2.7-code总56tokens，glm-5.3-flash总74tokens，deepseek-flash总64tokens，合计194tokens。此次默认推理参数、非流式，无工具调用，不能据此声称流式/工具或统一网关已验收。Kimi的BASE_URL补齐/v1，其余原样。原始请求与脱敏响应在WSL `runs/external-api-check/20260924T041240Z/`，未使用官方ARC端点/凭据，无源码更改。


## 新增提供商配置（2026-10-02）

用户直接授权：“我找到了一些新的 AI 提供商，请你帮我更新我们的 models env”。本轮范围为项目内 `.secrets/models.env` 新增四家的独立 API_KEY 空值与已核实的 OpenAI 兼容 BASE_URL，并记录重点模型与价格备注。主 Agent 负责配置与核验，子 Agent provider_facts 负责 Command Code 和共绩官方资料核实，结果已采用。

| 提供商 | 环境变量前缀 | OpenAI Base URL | 模型意图 |
| --- | --- | --- | --- |
| 方舟 Coding Plan | ARK_CODING_PLAN | https://ark.cn-beijing.volces.com/api/coding/v3 | 优先 glm-5.3-flash，套餐专用 key |
| 共绩算力 | GONGJI | https://api.suanli.cn/v1 | 普通备选，未指定重点模型 |
| Command Code GOAT | COMMAND_CODE | https://api.commandcode.ai/provider/v1 | 优先 glm-5.3-flash，API ID 为 z-ai/glm-5.3-flash |
| 百度千帆 | QIANFAN | https://qianfan.baidubce.com/v2 | 优先 GLM-5.3，账户实际 API ID 待模型列表核实 |

千帆官网国庆活动页面标示输入 0.0048、输出 0.0168 元/千 tokens，换算为输入 4.8、输出 16.8 元/M。用户确认此前报价是换算错误（“hhh对，抱歉是我换算错了”），已统一修正 env 备注。价格不写入运行计费参数；活动期间为 2026-09-24 至 2026-10-07，不能作为长期固定价。

依据为 [方舟个人版 Pi 接入](https://docs.volcengine.com/docs/ark/coding-plan-personal-ai-pi?lang=zh)、[共绩快速上手](https://docs.suanli.cn/llm/quickstart)、[Command Code Provider API](https://commandcode.ai/docs/provider)、[GOAT 套餐](https://commandcode.ai/docs/plans/goat)、[Command Code Flash 发布](https://commandcode.ai/blog/glm-5-3-flash-aka-ox-alpha-is-live-with)、[千帆模型列表](https://cloud.baidu.com/doc/qianfan-api/s/Dmba8k71y)及[千帆国庆活动](https://cloud.baidu.com/product/qianfan_home/campaign.html)。

已确认原有配置保留、新增 key 为空、文件权限 600、Git 忽略及 zsh 语法检查通过。本轮未调用模型、同步 WSL、切换网关路由或启动实验。现有网关不会仅凭新增环境变量自动选择这些提供商；下一步是填写新 key，实际接入与调用按后续授权范围执行。

## 统一提供商目录整理（2026-10-02）

用户在确认现有资料分散后回复“嗯，整理一下”，授权形成统一目录并接入文档索引。已创建 `docs/deployment/model-providers.md`，汇总9条自购通道与ARC，区分凭据已填、目录验证、实际调用和完整接入验收；按量价格与订阅套餐分表，保留币种、缓存写入收费、时段、活动期限和未知项。主 Agent 负责文档与索引，provider_facts 负责原厂三家的官方价格核实，其结果已采用。

此次只读本地凭据文件的字段、公开端点和是否已填，不输出密钥。现状与上一阶段不同：方舟、共绩、千帆 key 已由用户填写，GOAT仍为空。新通道尚未实际调用验证。千问普通API及ARC的具体单价、共绩选定模型单价、方舟当前套餐成交价仍未知；已留下对应官方查询入口，未用原厂价格或过期促销代替。

仅整理文档和核实公开价格；不调用模型，不修改 env，不同步远端，不切换路由或恢复实验。旧阶段证据保留原身份，持续事实以后更新统一目录。本轮核验为文档读回、相对链接目标检查及本任务文件空白检查，没有编写或运行Factory/Braid测试。


## 选型范围修正与方舟套餐核实（2026-10-02）

用户明确不使用 `kimi-k2.7-code-highspeed`、`deepseek-flash`（实际为DeepSeek V4.1 Flash），并给出方舟 Coding Plan 个人版套餐概览。已从目录价格表删除这两类模型，正文明确排除V4.1及转接到它的原厂旧别名；K2.7 Code与其它通道的0731 V4 Flash保留，历史调用原件不改。未改实验配方、env或源码。

通过浏览器读取用户指定官方页面及其链接的优惠规则：Lite/Pro原价40/200元每月，2026-06-08至11-08期间最多首两月9.9/49.9元，资格共享且名额有限。目录已补入期限、额度刷新与工具使用条件，区分方舟Ark与ARC Benchmark。账户实际购买档位、剩余优惠资格及额度数值未查询。官网概览最近更新为2026-09-29，优惠规则最近更新为2026-07-27。Web文本工具未能读到正文，浏览器实际页面正文为本轮采用依据。


## 文档拆分与 LiteLLM 网关方案（2026-10-02，已授权实施）

用户提出将目录拆成多个文件，并计划由LiteLLM作为模型提供商网关，避免手动维护切换客户端地址及模型名称。用户随后回复“开始”，授权按本节范围拆分文档、改造现有网关与集中原生配置并进行离线核验。实际网关部署、模型请求及暂停实验恢复不属于本轮范围。

只读调查owner gateway_design_evidence核实：现有hackathon_gateway.py已经启动LiteLLM Proxy，版本冻结为1.102.0；model_list由Python硬编码提供商映射生成，并将客户端model_name与上游wire model绑定为同一字符串。wrap已自动注入地址与run临时token；callback持有鉴权、OTLP、参数处理和Responses兼容。FACTORY26_MODEL_BINDINGS已支持上游model_id及热恢复保全，继续消费网关绑定即可。独立advisor gateway_judgment建议采用原生LiteLLM配置与按路由版本冻结的实例，不再造请求路由层。

文件职责：model-providers.md收缩为选型入口、可用状态和链接；model-providers/下按供应商整理价格、套餐、验证日期与来源，千问普通API与Token Plan归同页分通道；操作方法更新已有hackathon.md和recovery.md。一份原生LiteLLM配置作为可执行映射权威，声明稳定model_name、上游litellm_params.model、api_base及密钥变量引用；文档不再人工复制完整路由表，私有env保留密钥。

客户端使用明确模型身份，如glm-5.3-flash、glm-5.3、kimi-k3，避免fast/smart等角色别名破坏现有预算判定；DeepSeek保留0731版本边界。切换供应商只选择集中配置中的通道，新实验冻结该配置与hash并启动/复用相同冻结配置的实例，wrapper注入地址。每个alias只有一个获选上游，避免LiteLLM同名条目的自动负载均衡；不对在途实例改全局alias，不引入自动fallback、数据库UI权威或自制token级路由。

LiteLLM能集中维护别名、接入及兼容，不能自动确定账户权限、套餐抵扣、免费额度或供应商别名版本。公开成本表仍不等于账户账单。保留run身份、供应商/套餐通道、wire ID、非敏感endpoint与配置身份；工具、流式、视觉以及Responses语义按实际通道核验。验收先离线配置编译/读取，再在获准的最小真实请求中确认相同客户端alias经两份冻结配置抵达各自上游，且新实例切换不改变旧实例。不得引入Factory/Braid测试或用假探针代替实际反馈。

公开接口依据：[LiteLLM原生配置与model alias](https://docs.litellm.ai/docs/proxy/configs)、[OpenAI兼容端点](https://docs.litellm.ai/docs/providers/openai_compatible)、[配置文件与数据库权威](https://docs.litellm.ai/docs/proxy/model_management)。当前官方文档不构成冻结1.102.0全部新通道的已验证保证。


### 开工与责任

开工授权原话：“开始”。gateway_design_evidence继续持有网关源码、原生配置、操作文档和离线配置生产核验；主Agent持有提供商分页面、目录索引、packet及集成核对。现有git工作区包含大量其它任务修改，各负责人只改所持有接缝，保留既有改动。下一步先完成集中路由配置及离线prepare，再采用实际产物核对alias、供应商、wire ID和冻结身份。没有付费调用、远端部署或实验恢复授权。


## 实施结果与证据（2026-10-02）

提供商文档已拆为短入口及9个供应商页面。价格、套餐、有效期、验证边界和官方来源留在各页；端点、wire model与凭据变量引用以 `harness/model-gateway.json` 为唯一可执行目录。DeepSeek原厂排除通道、千帆未知请求ID及ARC官方网关未混入自购路由。

现有启动器消费原生目录，默认选择5个明确模型alias，每个alias只保留一个上游。`--route ALIAS=DEPLOYMENT_ID`可覆盖新实例选择，未知alias、重复选择及配置漂移会被拒绝。实例保存实际非敏感endpoint、供应商、套餐、wire ID及catalog/config SHA；密钥保留环境引用。wrapper继续注入临时地址与凭据，并消费schema1 attempt/incarnation身份及旧run变量。

主Agent采用负责人实际生产的默认及方舟Flash两份离线prepare产物，独立读回确认同alias对应不同deployment、不同config SHA，默认产物未被第二次选择修改。非敏感快照和service记录归档于 `runs/external-model-providers/20261002-gateway-prepare/{default,ark-flash,wrapper}/`；没有复制gateway.env或上游凭据。提供商10个页面的相对链接均可解析，任务文件空白检查通过。

这些证据证明配置生产与绑定接缝，不证明LiteLLM启动成功或上游受理。尚未启动网关、调用模型、同步远端或恢复实验；各通道工具、流式、视觉与Responses语义的实际验收留在另行授权的运行范围。本任务不引入Factory/Braid测试、自检或smoke入口。


负责人完成最终集成修复后，`python3 -m py_compile scripts/hackathon_gateway.py scripts/hackathon_gateway_compat.py`及空白检查通过。绑定marker和请求日志上下文补齐config SHA及incarnation；所选凭据的校验直接读取catalog实际环境变量引用，不依赖provider名称推导变量名。实际离线wrapper的撤销绑定已读回并归档为 `wrapper/binding-readback.json`，身份为 `attempt-readback-02 / inc-02`；临时客户端env已删除。该回执来自最后补齐marker/日志字段之前的实际运行，不将其写成补齐后已完成请求验收。操作说明提供方舟Flash准备命令，并明确prepare-only产物不能原目录再次启动。


## 千帆个人套餐与普通API分通道（2026-10-03）

用户补充已购买Coding Plan并指定 `https://qianfan.baidubce.com/v2/tokenplan/personal`，要求区分普通API与套餐。主Agent将此前填入QIANFAN的key按用户购买归属迁入独立QIANFAN_TOKEN_PLAN前缀；用户随后明确“普通千帆和coding plan 千帆我都配置好了”，已只读确认两套key及端点均已填，保留用户现有值。普通API使用QIANFAN前缀与/v2，个人套餐使用QIANFAN_TOKEN_PLAN前缀与/v2/tokenplan/personal；不共享默认凭据。

provider_facts负责官方通道及请求ID核实，结果已采用：[个人版快速开始](https://cloud.baidu.com/doc/qianfan/s/kmracfgi2)及[个人版说明](https://cloud.baidu.com/doc/qianfan/s/Dmrabu8b6)确认套餐专属URL、专属key及GLM-5.3请求IDglm-5.3；[普通模型列表](https://cloud.baidu.com/doc/qianfan/s/rmh4stp0j)确认普通API同一请求ID。harness/model-gateway.json新增qianfan-token-plan-glm-5.3与qianfan-glm-5.3两个候选deployment，稳定alias均为glm-5.3，现有默认选择不变。每个实例仍只选一个上游。

提供商页面已区分普通活动报价与套餐权益；套餐档位、成交价及账户额度未知，不用普通API价格代替。配置JSON解析、env语法、相对链接、600权限、Git忽略及任务文件空白检查通过。没有读取或输出key值到工具结果，没有模型请求、网关部署、远端同步或实验恢复。本轮为声明式配置及文档变更，没有编写或运行Factory/Braid测试，也未重新声称已通过运行时验收。


## 新增MiniMax官方M3（2026-10-03）

用户直接授权“新增 minimax 官方，可用 minimax-m3”。主Agent负责私有env、原生catalog及提供商文档，provider_facts只读核实官方中国区端点、请求ID及价格。采用[OpenAI SDK说明](https://platform.minimax.cn/docs/api-reference/text-openai-api)：Base URL为https://api.minimax.cn/v1，上游wire ID为MiniMax-M3，客户端稳定alias为minimax-m3。旧文档域名重定向至minimax.cn，本轮未推定旧API主机仍有效。

私有env新增MINIMAX_API_KEY空值和MINIMAX_BASE_URL，保留现有所有凭据。catalog新增minimax-official-m3普通按量deployment，其default仅适用于新minimax-m3 alias。选择时显式使用--alias minimax-m3 --route minimax-m3=minimax-official-m3；省略--alias仍按现有启动器行为装配整个目录，所有获选凭据须已填。没有改其它alias的默认通道。独立供应商页记录标准输入≤512K时2.10/8.40/0.42元/M，>512K时4.20/16.80/0.84元/M（输入/输出/缓存读取），priority另按1.5倍计费；M3缓存写入价未知。Token Plan未作为本次购买通道配置。

gateway_design_evidence持有共享读取边界修复：read_assignments允许未选中提供商的空字符串占位，仍验证变量名及字符串类型；selected_refs仍要求获选key及endpoint非空。这是新增空key时避免阻塞其它显式alias所需的范围内修复，未改其余现有路由、JSON环境或排序逻辑。

负责人编译scripts/hackathon_gateway.py成功；主Agent采用结果并完成catalog JSON解析读回、env语法、600权限及Git忽略、相对链接和任务文件空白检查。本轮没有Factory/Braid测试、模型调用、网关启动、部署或实验恢复。MiniMax key尚未填写，官方能力与价格核实不构成账户权限或完整兼容验收。


## ARC 首道与千帆个人 Token Plan 下架（2026-10-08，完成）

本次授权原话：“ARC API 额度恢复了，可以加到自费 API 运行的配方中，作为第一道”；随后“可以将千帆 Token Plan 从配方下架了”。用户补充事实：“ARC的旧模型ID就是0731版本，这是早就确认的事情”。实现 owner 为 `arc_recipe_owner`；本次更改公共自费路由、ARC catalog 与私有环境引用、代理 ARC 余额耗尽的窄 fallback、配方与 ARC 文档，保留其他工作区修改，未提交。

五个公共模型均已前置 ARC，所有公共链都已移除 `qianfan-token-plan-*`，其余顺序保留。供应商 catalog 的千帆能力条目与历史冻结路由保留，不据“配方下架”删除历史证据。DeepSeek 稳定 alias `deepseek-v4-flash-0731` 显式映射 ARC wire ID `deepseek-v4-flash`。GLM-5.3 与 K3 最长四道，沿用现有四道实现，没有扩容或新增配方机制。私有 `.secrets/models.env` 新增 ARC 两个引用，复用已有 ARC 账户凭据，没有输出、更换或外传密钥。

只读 `GET https://api.arc-bench.com/v1/models` 返回 HTTP 200 并列出五个所需 wire ID，完整清单与收据归 `runs/arc-self-funded-20261008/`。默认 Python CA 首次缺失 issuer、未取得 HTTP 响应，使用已有 certifi 信任库后成功；没有关闭证书校验。实际 `freeze_model_channel` 对 I14-dx-test 与 pi-minimal-vv-dx-test 完成材料装配，selected catalog 与 provider-env 已独立冻结，千帆凭据不再进入新装配。公共五模型通过 Python proxy 冻结器生产配置。Rust release 编译通过（29.63 秒），使用本次二进制与本次冻结四道配置启动独立代理，取得 ready 及本地健康 HTTP 200，SIGTERM 正常退出；没有模型请求、设施测试或模拟上游。装配、编译与启动证据同归上述目录，全部 Mac 产物与 cache/TMPDIR 位于 WorkSSD。

历史原生错误原件 `runs/finals-experiment-loop/validation/bookstack-wsl-native-error.json` 显示 HTTP 402 / code=insufficient_balance、type=billing_error、access key balance is exhausted。它是原生 errorMessage JSON，不是独立 raw HTTP 响应体。代理仅对 ARC+HTTP402+完整可解析JSON（顶层或 error 包装）+上述精确 code/type 允许切下一道；其余认证错误不放开，原错误诊断继续保留。编译已通过，实际余额耗尽 fallback 没有通过收费调用重现，当前余额没有查询，目录与健康响应不证明生成、工具或流式通过。

只更新下一次装配输入；未启动、停止、改写或恢复任何已有 run。Stage3 与 finals-experiment-loop 的既有冻结身份、用户停止要求仍归原任务记录，本次额度恢复不恢复它们。新二进制仅位于本次编译产物，未同步远端或部署到在途实例；新运行要沿自身装配合同采用当前源与新二进制。后续无本轮必做事项；如需真实生成及耗尽切换验证，另按具体运行范围授权。
